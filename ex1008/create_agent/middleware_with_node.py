from dotenv import load_dotenv 

from langchain_openai import ChatOpenAI 
from langchain.agents import create_agent 
from langchain.agents.middleware import before_model, dynamic_prompt, AgentState, ModelRequest
from langgraph.runtime import Runtime 

from tools import tools 

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")
# 입력에 이 단어가 있으면 차단한다.
BLOCKED_WORDS = ["바보", "멍청이", "나쁜말"]

# @before_model: 모델을 호출하기 '전에' 실행되는 미들웨어.
# 그래프에 'content_filter_middleware.before_model' 노드로 추가되고, 모델을 호출할 때마다 매번 거친다.
@before_model 
def content_filter_middleware(state: AgentState, runtime: Runtime):
    """
    금지어를 필터링하는 미들웨어
    - 그래프에 'content_filter_middleware' 노드가 추가됨
    - 금지어 감지 시 예외 발생으로 중단
    """
    # 마지막 메시지를 검사한다. 첫 호출에서는 사용자 입력이지만,
    # 도구 실행 뒤 두 번째 호출에서는 도구 결과(ToolMessage)가 마지막 메시지다.
    if state["messages"]:
        last_msg = state["messages"][-1]
        content = getattr(last_msg, 'content', str(last_msg))
        
        for word in BLOCKED_WORDS:
            if word in content:
                print(f"[before_model] 금지어 감지: '{word}'")
                # 예외를 던지면 그래프 실행이 멈추고, 호출한 쪽(아래 try/except)으로 에러가 전달된다.
                raise ValueError(f"부적절한 표현이 감지되었습니다: '{word}'")
            
        print(f"[before_model] 입력 검증 통과")
        
    # None을 반환하면 상태를 바꾸지 않고 그대로 model로 진행
    return None 

# @dynamic_prompt: 모델을 호출할 때마다 시스템 프롬프트를 새로 만들어 넣는 미들웨어 (노드 추가 없음)
@dynamic_prompt 
def random_tone_prompt(request: ModelRequest) -> str:
    """
    랜덤하게 말투를 변경하는 미들웨어 
    - 존댓말 또는 반말 프롬프트를 랜덤 선택 
    - @wrap_model_call 기반이므로 노드 추가 X
    """
    import random 
    
    # 모델 호출마다 무작위로 고르므로, 질문 하나를 처리하는 동안에도 호출마다 말투가 바뀔 수 있다.
    if random.choice([True, False]):
        print(f"[dynamic_prompt] 존댓말 모드")
        return "당신은 친절한 AI입니다. 항상 존댓말로 정중하게 답변하세요."
    else:
        print(f"[dynamic_prompt] 반말 모드")
        return "너는 친근한 AI야. 항상 반말로 편하게 답변해."
    
# 미들웨어는 리스트에 넣은 순서대로 적용된다.
agent = create_agent(
    model=model,
    tools=tools,
    middleware=[
        content_filter_middleware,
        random_tone_prompt,
    ]
)

if __name__ == "__main__":
    from pathlib import Path 

    # before_model 노드가 추가된 그래프 구조를 PNG로 저장
    save_path = Path(__file__).parent / "middleware_with_node.png"
    graph_image = agent.get_graph().draw_mermaid_png()

    with open(save_path, "wb") as f:
        f.write(graph_image) 

    # 테스트 1: 금지어가 없는 입력 -> 정상 실행
    print("=" * 50)
    print("테스트 1: 정상 입력")
    print("=" * 50)
    response = agent.stream({"messages": ["15와 7을 더해주세요."]})
    for chunk in response:
        for node, value in chunk.items():
            if node:
                print(f"\n--- {node} ---")
            if value and "messages" in value:
                print(value["messages"][0].content)

    # 테스트 2: 금지어가 있는 입력 -> before_model에서 ValueError로 차단
    print("\n" + "=" * 50)
    print("테스트 2: 금지어 포함 입력")
    print("=" * 50)
    try:
        response = agent.stream({"messages": ["바보야 10과 5를 더해줘"]})
        for chunk in response:
            for node, value in chunk.items():
                if node:
                    print(f"\n--- {node} ---")
                if value and "messages" in value:
                    print(value["messages"][0].content)
    except ValueError as e:
        print(f"❌ 차단됨: {e}")