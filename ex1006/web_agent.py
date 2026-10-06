from langchain_openai import ChatOpenAI 
from langchain_tavily import TavilySearch 

# 웹 검색 도구: 검색 결과를 최대 3개까지 가져온다.
tool = TavilySearch(max_results=3)
# LLM에 연결할 도구 목록
tools = [tool] 

# 답변 생성과 도구 사용 여부 판단을 맡는 LLM
llm = ChatOpenAI(model="gpt-4o")
# LLM에 도구 설명서를 연결 (LLM은 tool_calls로 '실행 요청'만 만들고, 실제 실행은 tools 노드가 한다)
llm_with_tools = llm.bind_tools(tools)

from typing import TypedDict, Annotated 

from langgraph.graph import StateGraph, START, END 
from langgraph.graph.message import add_messages 

# 그래프 상태: 대화 메시지 목록. add_messages 리듀서로 새 메시지가 계속 뒤에 쌓인다.
class State(TypedDict):
    messages: Annotated[list, add_messages]
    
# State 구조를 가진 그래프 설계도
graph_builder = StateGraph(State)

# chatbot 노드: 지금까지의 대화 전체를 LLM에 보내고, 응답(AIMessage)을 messages에 추가한다.
# 응답에는 최종 답변이 들어 있거나, 도구 실행 요청(tool_calls)이 들어 있다.
def chatbot(state: State):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# "chatbot"이라는 이름으로 노드 등록
graph_builder.add_node("chatbot", chatbot)

import json 
from langchain.messages import ToolMessage 

# 도구 실행 노드: LLM이 요청한 tool_calls를 실제로 실행하고 결과를 ToolMessage로 돌려준다.
# (랭그래프의 ToolNode를 직접 만들어 보는 버전)
class BasicToolNode:
    """
        마지막 AIMessage에서 요청한 도구를 실행하는 노드
    """
    
    def __init__(self, tools: list) -> None: 
        # 도구 이름 -> 도구 객체 (LLM이 요청한 이름으로 도구를 찾기 위함)
        self.tools_by_name = {tool.name: tool for tool in tools}
        
    def __call__(self, inputs: dict):
        # 마지막 메시지(= chatbot이 방금 만든 AIMessage)를 꺼낸다.
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("ERROR: 입력에 메시지가 없습니다.")
        
        outputs = [] 
        # LLM이 요청한 도구 호출을 하나씩 실행 (한 번에 여러 개를 요청할 수 있다)
        for tool_call in message.tool_calls:
            # 요청받은 도구를 LLM이 정한 인자(args)로 실행
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            # 결과를 JSON 문자열로 바꿔 ToolMessage로 감싼다. tool_call_id로 어떤 요청에 대한 결과인지 표시
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result, ensure_ascii=False),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"]
                )
            )
        # 도구 결과 메시지들을 반환 -> add_messages로 대화 뒤에 추가된다.
        return {"messages": outputs}
    
# 도구 실행 노드를 만들어 "tools"라는 이름으로 등록
tool_node = BasicToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

# 라우팅 함수: 마지막 AIMessage에 도구 호출 요청이 있으면 "tools"로, 없으면(최종 답변) END로 보낸다.
def route_tools(
    state: State,
):
    """
    마지막 메시지에 도구 호출이 있는 경우, ToolNode로 라우팅하고 그렇지 않으면 END로 라우팅
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"ERROR: 입력에 메시지가 없습니다. 상태: {state}")
    
    # tool_calls가 비어 있지 않으면 도구를 실행해야 한다는 뜻
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools" 
    return END 

# chatbot 다음은 route_tools의 반환값에 따라 tools 또는 END로 분기
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {"tools": "tools", END: END}
)

# 도구 실행 결과를 들고 다시 chatbot으로 -> LLM이 결과를 읽고 답하거나, 도구를 또 요청한다 (반복)
graph_builder.add_edge("tools", "chatbot")
# 시작 -> chatbot
graph_builder.add_edge(START, "chatbot")
# 실행 가능한 그래프로 컴파일. langgraph.json이 이 graph 변수를 랭그래프 서버에 올린다.
graph = graph_builder.compile()


# 아래는 6.2.4 실행 방법별 예제. 하나씩 주석을 풀어서 실행해 봤고, 지금은 맨 아래 astream()만 켜져 있다.
###############################################################
# invoke(): 그래프를 끝까지 실행한 뒤 최종 상태(messages 전체)를 한 번에 받는다. graph.png도 여기서 저장했다.
# response를 raw로 출력
# if __name__ == "__main__":
#     try:
#         image = graph.get_graph().draw_mermaid_png()
#         with open("graph.png", "wb") as f:
#             f.write(image)
#     except Exception:
#         pass 
    
#     response = graph.invoke(
#         {
#             "messages": ["Langgraph가 무엇인가요?"]
#         }
#     )
    
#     print(response)


#################################################################
# pretty_print(): 메시지를 종류(Human/AI/Tool)별로 보기 좋게 출력
# response를 pretty_print로 출력
# def invoke():
#     response = graph.invoke(
#         {
#             "messages": ["Langgraph가 무엇인가요?"]
#         }
#     )
    
#     for msg in response["messages"]:
#         msg.pretty_print()
        
# if __name__ == "__main__":
#     invoke()


######################################################
# ainvoke(): invoke()의 비동기 버전. asyncio.run()으로 실행한다.
# 비동기 방식으로 요청하기
# async def ainvoke():
#     response = await graph.ainvoke(
#         {
#             "messages": ["Langgraph가 무엇인가요?"]
#         }
#     )
    
#     for msg in response["messages"]:
#         msg.pretty_print()
        
# if __name__ == "__main__":
#     import asyncio 
#     asyncio.run(ainvoke())


###########################################################
# updates 모드(stream()의 기본값): 노드가 끝날 때마다 그 노드가 바꾼 값만 받는다.
# stream()의 updates 모드를 활용해 실행 결과 확인하기 
# def stream():
#     response = graph.stream(
#         {
#             "messages": ["Langgraph가 무엇인가요?"]
#         }
#     )
#     for chunk in response:
#         for node, state in chunk.items():
#             print("---", node, "---")
#             print(state)
#             print("=" * 60)
            
# if __name__ == "__main__":
#     stream()


######################################################
# values 모드: 노드가 끝날 때마다 그 시점의 상태 전체를 받는다.
# stream()의 values 모드를 활용해 실행 결과 확인하기
# def stream_values():
#     response = graph.stream(
#         {
#             "messages": ["Langgraph가 무엇인가요?"]
#         },
#         stream_mode="values"
#     )
    
#     for chunk in response:
#         for state_key, state_value in chunk.items():
#             print("--- 현재 상태 ---")
#             for msg in state_value:
#                 print(f"{type(msg).__name__}: {msg.content[:50]}")
#             if state_key == "messages":
#                 state_value[-1].pretty_print()
#             print("=" * 60)
            
# if __name__ == "__main__":
#     stream_values()

##############################################################
# messages 모드: LLM이 만드는 답변을 토큰 조각 단위로 받는다. (print가 조각마다 줄을 바꾸므로 print(token.content, end="")로 하면 한 줄로 이어진다)
# stream()의 messages 모드를 활용해 실행 결과 확인하기
# def stream_messages():
#     response = graph.stream(
#         {
#             "messages": ["Langgraph가 무엇인가요?"]
#         },
#         stream_mode="messages"
#     )
    
#     for token, metadata in response:
#         print(token.content)
#         # print(metadata["langgraph_node"])
        
# if __name__ == "__main__":
#     stream_messages()


###########################################################
# astream(): stream()의 비동기 버전 (updates 모드). 지금 켜져 있는 실행 코드
# astream()를 활용해 실행 결과 확인하기 
async def astream():
    response = graph.astream(
        {
            "messages": ["Langgraph가 무엇인가요?"]
        }
    )
    async for chunk in response:
        for node, state in chunk.items():
            print("---", node, "---")
            print(state)
            print("=" * 60)
            
if __name__ == "__main__":
    import asyncio 
    asyncio.run(astream())