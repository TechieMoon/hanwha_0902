from dotenv import load_dotenv 

from langchain_openai import ChatOpenAI 
from langchain.agents import create_agent 
from langchain.agents.middleware import before_model, dynamic_prompt, AgentState, ModelRequest
from langgraph.runtime import Runtime 

from tools import tools 

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")
BLOCKED_WORDS = ["바보", "멍청이", "나쁜말"]

@before_model 
def content_filter_middleware(state: AgentState, runtime: Runtime):
    """
    금지어를 필터링하는 미들웨어
    - 그래프에 'content_filter_middleware' 노드가 추가됨
    - 금지어 감지 시 예외 발생으로 중단
    """
    if state["messages"]:
        last_msg = state["messages"][-1]
        content = getattr(last_msg, 'content', str(last_msg))
        
        for word in BLOCKED_WORDS:
            if word in content:
                print(f"[before_model] 금지어 감지: '{word}'")
                raise ValueError(f"부적절한 표현이 감지되었습니다: '{word}'")
            
        print(f"[before_model] 입력 검증 통과")
        
    return None 

@dynamic_prompt 
def random_tone_prompt(request: ModelRequest) -> str:
    """
    랜덤하게 말투를 변경하는 미들웨어 
    - 존댓말 또는 반말 프롬프트를 랜덤 선택 
    - @wrap_model_call 기반이므로 노드 추가 X
    """
    import random 
    
    if random.choice([True, False]):
        print(f"[dynamic_prompt] 존댓말 모드")
        return "당신은 친절한 AI입니다. 항상 존댓말로 정중하게 답변하세요."
    else:
        print(f"[dynamic_prompt] 반말 모드")
        return "너는 친근한 AI야. 항상 반말로 편하게 답변해."
    
agent = create_agent(
    model=model,
    tools=tools,
    middleware=[
        content_filter_middleware,
        random_tone_prompt,
    ]
)