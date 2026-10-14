from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 조건부 엣지(다음에 갈 노드를 고르는 함수)에서 평가자로 쓸 LLM
llm = ChatOpenAI(model="gpt-4o")

# with_structured_output에 넘길 출력 형식. LLM의 답이 이 형식(binary_score 하나)으로만 돌아오게 강제한다.
class Grade(BaseModel):
    """관련성 확인을 위한 점수 스키마"""

    binary_score: str = Field(description="문서로 질문에 답할 수 있는지 여부, 'yes' 또는 'no'")

# context_organizer 다음에 실행되는 조건부 엣지. 반환값이 다음 노드 이름이 된다.
def decide_to_generate(state):
    """
    답변을 생성할지, 아니면 질문을 다시 생성할지 결정합니다.
    """

    print("----- ASSESS GRADED DOCUMENTS -----")
    # 질문을 이미 3번 다시 썼으면 더 평가하지 않고 답변 단계로 간다. (재검색이 끝없이 반복되지 않게 막는 장치)
    # 평가 기준 변경: 원래(교재 코드)는 "관련 키워드나 의미가 있으면 yes, 엄격할 필요 없음"이었다.
    # 실제 실행에서 정의 조항이 빠졌는데도 'yes'가 나와 재검색이 일어나지 않아서, "답하기에 충분한가"를 보도록 바꿨다.
    if state.get("retry_num", 0) >= 3:
        return "generate"

    grader = llm.with_structured_output(Grade)

    grader_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                당신은 검색된 문서로 사용자 질문에 답할 수 있는지 평가하는 평가자입니다.
                질문에 답하는 데 꼭 필요한 핵심 내용(예: 개념을 묻는 질문이면 그 개념의 정의나 적용 조건)이 문서에 들어 있으면 'yes'를 주세요.
                질문과 관련된 단어가 나오기만 하고 답의 핵심이 빠져 있다면 'no'를 주세요.
                'yes' 또는 'no'의 이진 점수를 제공하세요.
                """
            ),
            (
                "user",
                "검색된 문서: {context} \n\n 사용자 질문: {question} \n\n 관련성 점수:"
            ),
        ]
    )

    chain = grader_prompt | grader

    question = state.get("question", "")
    context = state.get("context", "")

    # 평가할 재료가 없으면 평가하지 않고 답변 단계로 보낸다.
    if not context or not question:
        print("---ERROR: Missing context or question, defaulting to generate---")
        return "generate"

    score = chain.invoke({"question": question, "context": context})
    grade = score.binary_score  # 'yes' 또는 'no'

    if grade == "no":
        # 관련 없는 문서 -> 질문을 다시 써서 재검색
        print(
            "---DECISION: RETRIEVED DOCUMENT ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        print("---DECISION: GENERATE---")
        return "generate"

class GradeHallucinations(BaseModel):
    """생성된 답변의 환각 여부를 판단하기 위한 점수 스키마"""

    binary_score: str = Field(
        description="답변이 사실에 근거하고 있는지 여부, 'yes' 또는 'no'"
    )

# generate 다음에 실행되는 조건부 엣지. 답변이 검색 결과(context)에 근거하는지(환각이 아닌지) 평가한다.
def check_hallucinations(state):
    """
    생성된 답변이 문서에 근거하고 질문에 답하는지 판단합니다.
    """

    print("----- CHECK HALLUCINATIONS -----")
    # 답변을 이미 3번 만들었으면 더 평가하지 않고 마지막 답변으로 종료한다. (추가한 부분)
    # 원래는 평가가 계속 'no'면 generate만 무한히 반복하다가 기본 재귀 한도(25단계)에 걸려 GraphRecursionError가 났다.
    if state.get("generate_num", 0) >= 3:
        print("---DECISION: MAX GENERATION REACHED, END---")
        return "support"

    question = state["question"]
    context = state["context"]
    answer = state["answer"]

    structured_llm = llm.with_structured_output(GradeHallucinations)

    system = """당신은 LLM이 생성한 답변이 검색된 사실들에 근거하고 있는지 평가하는 평가자입니다.
    'yes' 또는 'no'의 이진 점수를 제공하세요. 'yes'는 답변이 사실들에 근거하고 있음을 의미합니다."""
    hallucination_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("user", "질문: {question} \n\n 사실 집합: \n\n {context} \n\n LLM 생성 답변: {generation}"),
        ]
    )

    hallucination_grader = hallucination_prompt | structured_llm

    score = hallucination_grader.invoke(
        {"question": question, "context": context, "generation": answer}
    )
    grade = score.binary_score
    if grade == "yes":
        # 근거 있음 -> 종료
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        return "support"
    else:
        # 근거 없음 -> generate로 돌아가 답변을 다시 만든다. (위의 generate_num 검사로 최대 3번까지)
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"
