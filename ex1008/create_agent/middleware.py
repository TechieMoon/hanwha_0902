from dotenv import load_dotenv 

from langchain_openai import ChatOpenAI 
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse 

from tools import tools 

load_dotenv()

# 가벼운 모델(기본)과 고급 모델 두 개를 준비
basic_model = ChatOpenAI(model="gpt-4o-mini")
advanced_model = ChatOpenAI(model="gpt-4o")

# @wrap_model_call: 모델을 호출하는 순간을 감싸는 미들웨어. 호출 직전에 요청(request)을 바꿀 수 있다.
# 그래프에 노드가 추가되지 않는다. (저장한 그래프 그림이 기본 create_agent와 같다)
@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """대화 복잡도에 따라 모델을 동적으로 선택하는 미들웨어"""
    # 지금까지 쌓인 메시지 수 (사람·AI·도구 메시지를 모두 센다)
    message_count = len(request.state["messages"])
    print(f"현재 대화 메시지 수: {message_count}")
    
    # 메시지가 10개를 넘으면 대화가 길어졌다고 보고 고급 모델로 바꾼다.
    if message_count > 10:
        model = advanced_model
        print("복잡한 대화 감지: 고급 모델(gpt-4o) 사용")
    else:
        model = basic_model 
        
    # request.override(model=...)로 이번 호출에 쓸 모델만 바꿔서 실제 모델 호출(handler)로 넘긴다.
    return handler(request.override(model=model))

# 미들웨어를 등록한 에이전트 (그래프 그림 저장용)
agent = create_agent(
    model=basic_model,
    tools=tools,
    middleware=[dynamic_model_selection]
)

if __name__ == "__main__":
    from pathlib import Path 
    from langgraph.checkpoint.memory import MemorySaver

    # 그래프 구조를 PNG로 저장 (이 파일과 같은 폴더)
    save_path = Path(__file__).parent / "middleware_wrap_model_call.png"
    graph_image = agent.get_graph().draw_mermaid_png()
    with open(save_path, "wb") as f:
        f.write(graph_image)

    # MemorySaver: 같은 thread_id로 부르면 이전 대화를 기억하는 체크포인터.
    # 턴마다 대화가 쌓여야 메시지 수가 늘어나므로, 메모리가 있는 에이전트로 실행한다.
    agent_with_memory = create_agent(
        model=basic_model,
        tools=tools,
        middleware=[dynamic_model_selection],
        checkpointer=MemorySaver()
    )

    # thread_id가 같으면 같은 대화로 이어진다.
    config = {"configurable": {"thread_id": "test-thread"}}

    # 앞 턴의 결과를 이어받는 질문들 ("결과에", "그 결과에서")
    questions = [
        "15와 7을 더해주세요.",
        "결과에 3을 곱해주세요.",
        "그 결과에서 10을 빼주세요.",
        "100을 5로 나눠주세요.",
        "25와 25를 더해주세요.",
        "1000에서 500을 빼주세요.",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'=' * 50}")
        print(f"🔄️ 턴 {i}: {question}")
        print('=' * 50)

        response = agent_with_memory.invoke(
            {"messages": [question]},
            config=config
        )

        # 마지막 메시지 = 최종 답변. (f-string 안에 바깥과 같은 따옴표를 쓰는 문법은 파이썬 3.12부터 가능)
        print(f"🤖 응답: {response["messages"][-1].content}")