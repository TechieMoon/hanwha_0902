
from typing import TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")

# 런타임 컨텍스트 스키마: 실행할 때 따로 넘겨주는 정보 (대화 메시지와는 별개로, 상태에 저장되지 않는다)
class UserContext(TypedDict):
    user_role: str

# 실행할 때 넘긴 context의 user_role에 따라 시스템 프롬프트를 바꾼다.
@dynamic_prompt
def role_based_prompt(request: ModelRequest[UserContext]) -> str:
    """사용자 역할에 따른 시스템 프롬프트 생성"""
    # request.runtime.context로 invoke(..., context=...)에 넘긴 값을 읽는다. 없으면 기본값 'user'
    role = request.runtime.context.get("user_role", "user")

    if role == "expert":
        return "전문 용어를 사용하여 상세하게 답변하세요."
    elif role == "beginner":
        return "쉬운 말로 간단하게 설명하세요."

    return "친절하게 답변하세요."

# 도구 없이 미들웨어만 쓰는 에이전트. context_schema로 컨텍스트 형식을 지정한다.
agent = create_agent(
    model=model,
    tools=[],
    middleware=[role_based_prompt],
    context_schema=UserContext,
)

# 같은 질문을 역할만 바꿔서 두 번 실행한다.
query = {
    "messages": [
        {"role": "user", "content": "Python 데코레이터를 설명해주세요."}
    ]
}

# 전문가 역할 -> '전문 용어를 사용하여 상세하게 답변하세요.' 프롬프트
expert_result = agent.invoke(
    query,
    context={"user_role": "expert"}
)

# 초보자 역할 -> '쉬운 말로 간단하게 설명하세요.' 프롬프트
beginner_result = agent.invoke(
    query,
    context={"user_role": "beginner"}
)

print("전문가용 답변:")
print(expert_result["messages"][-1].content)

print("\n초보자용 답변:")
print(beginner_result["messages"][-1].content)
