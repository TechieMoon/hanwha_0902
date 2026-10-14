import re

from dotenv import load_dotenv

# .env의 OPENAI_API_KEY를 불러온다. (ChatOpenAI를 만들기 전에 불러와야 한다)
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import ToolMessage, AIMessage

# 6.5.3에서 만든 벡터 DB(vectorstore)와 검색 도구(retriever_tool, 이름은 pdf_search)
from retriever import vectorstore, retriever_tool
from state import AgentState

# 에이전트가 쓸 검색기. 6.5.3의 retriever는 k=3이었는데, 실제 실행에서 "구개음화가 뭐야?"의 정의 조항(245쪽)이
# 상위 3개에 들지 못해서 5개를 가져오도록 따로 만들었다. (retriever.py의 k=3 검색기와 검색 도구는 그대로 둠)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})


# 모든 노드가 같이 쓰는 LLM
llm = ChatOpenAI(model="gpt-4o")


def chatbot(state: AgentState):
    """
    검색(Retriever) 도구를 바인딩 한 LLM 모델에 현재 메시지 상태를 입력하여 응답을 생성합니다.
    질문이 주어지면 검색 도구를 도구호출 하거나 일반 답변하며 종료할지 결정할 수 있습니다.
    """
    print("----- [CHATBOT] -----")
    messages = state["messages"]
    llm_with_tools = llm.bind_tools([retriever_tool]) # [ 1 ] LLM에게 검색 도구 명세를 알려 준다
    response = llm_with_tools.invoke(messages) # [ 2 ] 검색이 필요하면 tool_calls가 담긴 AIMessage, 아니면 일반 답변

    return { # [ 3 ]
        "messages": [response],
        # 마지막 메시지(= 사용자 질문)를 검색에 쓸 질문으로 저장한다.
        # 그래서 retrieve는 LLM이 tool_calls에 넣은 검색어가 아니라 사용자 질문 원문으로 검색한다.
        "question" : messages[-1].content,
        # 새 질문이 들어올 때마다 횟수를 0으로 되돌린다. (추가한 부분)
        # 랭그래프 스튜디오처럼 같은 스레드에서 대화를 이어 가면 상태가 남아 있어서,
        # 되돌리지 않으면 앞 질문의 횟수가 다음 질문에 그대로 이어진다.
        "retry_num": 0,
        "generate_num": 0,
    }

def retrieve(state: AgentState):
    """
    현재 질문을 기반으로 관련 문서를 검색합니다.
    """
    print("----- [RETRIEVER] -----")
    question = state["question"]
    relevant_doc = retriever.invoke(question) # [ 1 ] 질문과 가장 비슷한 청크 5개 (k=5)
    context = ""
    for doc in relevant_doc: # [ 2 ] 청크마다 쪽 번호를 붙여 문자열 하나로 만든다
        # PyPDFLoader의 page는 0부터 시작해서 +1을 했다. (이 PDF는 DB에 저장된 page_label과 page+1이 같았다)
        context += f"Page {doc.metadata['page']+1}: {doc.page_content}\n"


    # Tool 호출에 대한 응답 메시지(검색 결과) 생성
    last_message = state["messages"][-1]

    # chatbot에서 바로 온 경우: 마지막 메시지가 tool_calls가 있는 AIMessage다.
    # tool_calls 다음에는 같은 tool_call_id를 가진 ToolMessage가 와야 대화 기록 형식이 맞는다.
    if hasattr(last_message, 'tool_calls') and len(last_message.tool_calls) > 0:
        tool_call_id = last_message.tool_calls[0]['id']
        tool_message = ToolMessage( # [ 3 ]
            content=context,
            name="retriever",
            tool_call_id=tool_call_id
        )
        return {"messages": [tool_message], "context": context} # [ 4 ]
    else:
        # transform_query에서 다시 온 경우: 마지막 메시지가 다시 쓴 질문(AIMessage)이라 tool_calls가 없다.
        # 원래는 {"messages": [context]}처럼 문자열을 그대로 넣었는데, 그러면
        #  1) add_messages가 문자열을 HumanMessage로 바꿔서 검색 결과가 사용자 메시지처럼 기록되고,
        #  2) agent.py의 출력 루프가 .content를 읽다가 AttributeError가 났다.
        # 그래서 AIMessage로 감싸도록 고쳤다.
        return {"messages": [AIMessage(context)], "context": context}


def context_organizer(state: AgentState):
    """
    검색된 결과를 정리합니다.
    """
    print("----- [CONTEXT ORGANIZER] -----")
    context = state["context"]

    # 원래(교재 코드)는 LLM에게 "내용은 지우지 말고 공백만 정리하라"고 시켰다.
    # 그런데 실제 실행에서 LLM이 원문에 없는 문장을 넣고 예시를 빼는 등 내용을 고쳐 썼고,
    # 그 문장이 답변의 출처(쪽 번호)를 틀리게 만들었다. 환각 평가도 정리본과 비교하므로 이 오류를 잡지 못했다.
    # 그래서 LLM을 쓰지 않고 코드로 공백만 정리하도록 바꿨다. 내용과 쪽 번호는 원문 그대로 남고, LLM 호출도 1번 줄어든다.
    lines = []
    for line in context.split("\n"):
        line = re.sub(r"[ \t\u3000]+", " ", line).strip()  # 연속된 공백(전각 공백 포함)을 하나로
        if not line:
            continue  # 빈 줄 제거
        if re.match(r"Page \d+: ", line) and lines:
            lines.append("")  # 청크(쪽)마다 빈 줄로 구분
        lines.append(line)
    organized_context = "\n".join(lines)

    # 정리된 문서로 context를 바꾸고, 대화 기록에도 남긴다.
    return {"context": organized_context, "messages": [AIMessage(organized_context)]}



def transform_query(state: AgentState):
    """
    더 나은 질문을 생성하기 위해 쿼리를 변환합니다.

    Args:
        state (dict): 현재 그래프 상태

    Returns:
        state (dict): 재구성된 질문으로 question 키를 업데이트
    """

    print("----- [TRANSFORM QUERY] -----")
    question = state["question"]

    # 검색 결과가 질문과 관련이 없다고 평가됐을 때 실행된다. 벡터 검색이 잘 되도록 질문을 다시 쓴다.
    system = """
    당신은 질문을 다시 작성하는 전문가입니다. 입력된 질문을 벡터 저장소 검색에 최적화된 더 나은 버전으로 변환하세요.
    입력을 살펴보고 질문의 핵심적인 의미와 의도를 파악하여 개선된 질문을 만들어주세요."""
    re_write_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            (
                "user",
                "다음은 초기 질문입니다: \n\n {question} \n 한국어로 개선된 질문을 작성해주세요.",
            ),
        ]
    )

    question_rewriter = re_write_prompt | llm

    better_question = question_rewriter.invoke({"question": question})
    # question을 새 질문으로 바꾸고 retry_num을 1 늘린다. (처음이면 retry_num이 없으므로 1)
    return {"question": better_question.content, "messages": [better_question], "retry_num": state["retry_num"] + 1 if state.get("retry_num") else 1}


def generate(state: AgentState):
    """
    검색된 문서와 질문을 기반으로 답변을 생성합니다.
    """
    print("----- [GENERATE] -----")
    question = state["question"]
    context = state["context"]

    retry_num = state.get("retry_num", 0)

    if retry_num >= 3: # [ 1 ] 질문을 3번 다시 써도 관련 문서를 못 찾은 경우
        # 답을 지어내지 않도록, 답하지 못한다고 알리고 검색 결과로 답할 수 있는 다른 질문을 제안한다.
        rag_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """당신은 검색된 문서를 통해 해결할 수 있는 질문을 추출하는 어시스턴트입니다.
                    사용자가 해결하고자 한 질문이 있었으나 검색 컨텍스트가 충분하지 않은 상황이므로, 주어진 검색 결과 내에서 답변할 수 있는 질문을 새롭게 작성해 나열하세요.
                    사용자에게 질문에 대한 답변을 하지 못함에 양해를 구하고, 다른 질문의 기회와 선택지를 제공하는 친절한 가이드를 하세요.
                    """,
                ),
                (
                    "user",
                    "질문: {question} \n\n검색 결과: {context} \n\n답변:",
                ),
            ]
        )
    else: # [ 2 ] 관련 문서를 찾은 경우: 검색 결과를 근거로 답하고 출처(쪽 번호)를 붙인다
        rag_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """당신은 질문-답변 업무를 수행하는 어시스턴트입니다. 검색된 컨텍스트를 사용하여 질문에 답변하세요.
                    답변을 모르는 경우, 모른다고 말하세요.
                    답변은 간결하게 작성하고, 반드시 답변의 출처(페이지 번호)를 함께 명시해주세요.


                    """,
                ),
                (
                    "user",
                    "질문: {question} \n\n검색 결과: {context} \n\n답변:",
                ),
            ]
        )

    rag_chain = rag_prompt | llm
    response = rag_chain.invoke({"question": question, "context": context})
    # answer에 답변을 저장해서 다음 단계(check_hallucinations)가 평가할 수 있게 한다.
    # generate_num은 답변을 만든 횟수. check_hallucinations가 이 값으로 재생성을 멈춘다. (추가한 부분)
    return {"question": question, "answer": response.content, "messages": [response], "generate_num": state.get("generate_num", 0) + 1}
