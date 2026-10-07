from dotenv import load_dotenv 

from langchain_openai import ChatOpenAI 
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse 

from tools import tools 

load_dotenv()

basic_model = ChatOpenAI(model="gpt-4o-mini")
advanced_model = ChatOpenAI(model="gpt-4o")

@wrap_model_call
def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
    """대화 복잡도에 따라 모델을 동적으로 선택하는 미들웨어"""
    message_count = len(request.state["messages"])
    print(f"현재 대화 메시지 수: {message_count}")
    
    if message_count > 10:
        model = advanced_model
        print("복잡한 대화 감지: 고급 모델(gpt-4o) 사용")
    else:
        model = basic_model 
        
    return handler(request.override(model=model))

agent = create_agent(
    model=basic_model,
    tools=tools,
    middleware=[dynamic_model_selection]
)

if __name__ == "__main__":
    from pathlib import Path 
    from langgraph.checkpoint.memory import MemorySaver

    save_path = Path(__file__).parent / "middleware_wrap_model_call.png"
    graph_image = agent.get_graph().draw_mermaid_png()
    with open(save_path, "wb") as f:
        f.write(graph_image)

    agent_with_memory = create_agent(
        model=basic_model,
        tools=tools,
        middleware=[dynamic_model_selection],
        checkpointer=MemorySaver()
    )

    config = {"configurable": {"thread_id": "test-thread"}}

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

        print(f"🤖 응답: {response["messages"][-1].content}")