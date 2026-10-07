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