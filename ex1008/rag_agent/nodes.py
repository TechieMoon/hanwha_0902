from dotenv import load_dotenv 

load_dotenv()

from langchain_openai import ChatOpenAI 
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import ToolMessage

from retriever import retriever, retriever_tool 
from state import AgentState 

llm = ChatOpenAI(model="gpt-4o")

def chatbot(state: AgentState):
    """
    검색(Retriever) 도구를 바인딩한 LLM 모델에 현재 메시지 상태를 입력하여 응답을 생성합니다.
    질문이 주어지면 검색 도구를 도구 호출하거나 일반 답변하며 종료할지 결정할 수 있습니다.
    """
    print("----- [CHATBOT] -----")
    messages = state["messages"]
    llm_with_tools = llm.bind_tools([retriever_tool])
    response = llm_with_tools.invoke(messages)

    return {
        "messages": [response],
        "question": messages[-1].content
    }

def retrieve(state: AgentState):
    """
    현재 질문을 기반으로 관련 문서를 검색합니다.
    """
    print("----- [RETRIEVER] -----")
    question = state["question"]
    relevant_doc = retriever.invoke(question)
    context = ""
    for doc in relevant_doc:
        context += f"Page {doc.metadata['page'] + 1}: {doc.page_content}\n"

    last_message = state["messages"][-1]

    if hasattr(last_message, 'tool_calls') and len(last_message.tool_calls) > 0:
        tool_call_id = last_message.tool_calls[0]['id']
        tool_message = ToolMessage(
            content=context,
            name="retriever",
            tool_call_id=tool_call_id,
        )
        return {"message": [tool_message], "context": context}
    else:
        return {"message": [context], "context": context}

def context_organizer(state: AgentState):
    """
    검색된 결과를 정리합니다.
    """
    print("----- [CONTEXT ORGANIZER] -----")
    context = state["context"]

    context_organizer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                당신은 검색증강생성(RAG)을 위한 검색문서를 정리하는 전문가입니다.
                아래의 검색된 결과 문서를 확인하고, LLM이 해당 문서를 정리된 형태로 참고할 수 있도록
                문서의 불필요한 공백 등을 삭제하거나 정렬을 다시하여 정리된 형태로 반환해주세요.
                내용을 삭제하는 것을 최소로 합니다. 페이지 번호 정보를 절대 삭제하지 마세요.
                """
             ),
             (
                "user",
                """
                검색 결과: {context}
                """,
             )
        ]
    )

    context_organizer = context_organizer_prompt | llm 
    organized_context = context_organizer.invoke({"context": context})

    return {"context": organized_context.content, "messages": [AIMessage(organized_context.content)]}

