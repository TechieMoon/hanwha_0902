from dotenv import load_dotenv

# .env의 OPENAI_API_KEY를 불러온다.
load_dotenv()

# tools_condition: 마지막 메시지에 tool_calls가 있으면 "tools", 없으면 END를 돌려주는 미리 만들어진 조건 함수
from langgraph.prebuilt import tools_condition
from langgraph.graph import StateGraph, MessagesState, START, END

# 이 폴더의 다른 파일에서 상태, 노드, 조건부 엣지를 가져온다. (그래서 rag_agent 폴더가 import 경로에 있어야 한다)
from state import AgentState
from nodes import chatbot, retrieve, context_organizer, generate, transform_query
from edges import decide_to_generate, check_hallucinations

# 내부 상태는 AgentState(question, context 등 포함)로 쓰고, 입력은 MessagesState(messages만)로 받는다.
# 그래서 사용자는 {"messages": [...]}만 넣으면 되고, 나머지 값은 노드들이 채운다.
graph_builder = StateGraph(AgentState, input_schema=MessagesState)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("retriever", retrieve)

# 1) 시작 -> chatbot: LLM이 검색 도구를 쓸지(=PDF에서 찾아야 하는 질문인지) 결정한다
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {
        "tools": "retriever",  # 도구 호출이 있으면 검색
        END: END,  # 없으면 chatbot의 답변으로 바로 종료 (예: 인사, PDF와 상관없는 질문)
    }
)

graph_builder.add_node("context_organizer", context_organizer)
graph_builder.add_node("transform_query", transform_query)
graph_builder.add_node("generate", generate)

# 2) 검색 -> 검색 결과 정리 -> 관련성 평가(decide_to_generate)
graph_builder.add_edge("retriever", "context_organizer")
graph_builder.add_conditional_edges(
    "context_organizer",
    decide_to_generate,
    {
        "transform_query": "transform_query",  # 관련 없음 -> 질문 다시 쓰기
        "generate": "generate",  # 관련 있음(또는 이미 3번 다시 씀) -> 답변 생성
    },
)
# 3) 다시 쓴 질문으로 재검색 (retriever -> context_organizer -> 평가 순환)
graph_builder.add_edge("transform_query", "retriever")
# 4) 답변 -> 환각 평가(check_hallucinations)
graph_builder.add_conditional_edges(
    "generate",
    check_hallucinations,
    {
        "not supported": "generate",  # 근거 없음 -> 답변 다시 생성 (답변은 최대 3번까지 만들고 종료)
        "support": END  # 근거 있음 -> 종료
    }
)

# 랭그래프 서버(langgraph.json)가 이 graph 변수를 불러간다.
graph = graph_builder.compile()


if __name__ == "__main__":
    # 그래프 구조를 그림으로 저장한다. 실행한 위치(현재 폴더)에 graph.png가 생긴다.
    # (draw_mermaid_png는 기본으로 외부 Mermaid 서비스를 사용해서, 인터넷 연결이 없으면 실패할 수 있어 try로 감쌌다)
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(png_bytes)
    except Exception:
        pass

    # stream: 노드가 하나 끝날 때마다 {노드 이름: 그 노드가 돌려준 값}을 하나씩 내보낸다.
    response = graph.stream(
        {
            "messages": [
                "구개음화가 뭐야?"
            ]
        }
    )

    for chunk in response:
        for node, value in chunk.items():
            if node:
                print("---", node, "---")
            # 노드가 messages에 추가한 첫 메시지를 출력한다. (도구 호출만 한 chatbot 응답은 내용이 비어 있다)
            # stream은 노드가 돌려준 값을 리듀서를 거치기 전 그대로 내보내므로, 모든 노드가 메시지 객체를 돌려줘야 .content를 읽을 수 있다.
            if "messages" in value:
                print(value['messages'][0].content)

        print("=" * 60)
