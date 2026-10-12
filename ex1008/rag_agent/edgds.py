from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o")

class Grade(BaseModel):
    """관련성 확인을 위한 점수 스키마"""

    binary_score: str = Field(description="문서가 질문과 관련이 있는지 여부, 'yes' 또는 'no'")

def decide_to_generate(state):
    """
    답변을 생성할지, 아니면 질문을 다시 생성할지 결정합니다.
    """

    print("----- ASSESS GRADED DOCUMENTS -----")
    if state.get("retry_num", 0) >= 3:
        return "generate"

    grader = llm.with_structured_output(Grade)

    grader_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                당신은 검색된 문서가 사용자 질문과 관련이 있는지 평가하는 평가자입니다.
                문서가 사용자 질문과 관련된 키워드나 의미를 포함하고 있다면 관련성이 있다고 평가하세요.
                엄격한 테스트일 필요는 없습니다. 목표는 잘못된 검색 결과를 필터링하는 것입니다.
                문서가 질문과 관련이 있는지를 나타내는 'yes' 또는 'no'의 이진 점수를 제공하세요.
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

    if not conetxt or not question:
        print("---ERROR: Missing context or question, defaulting to generate---")
        return "generate"

    score = chain.invoke({"question": question, "context": context})
    grade = score.binary_score

    if grade == "no":
        print(
            "---DECISION: RETRIEVED DOCUMENT ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        print("---DECISION: GENERATE---")
        return "generate"

