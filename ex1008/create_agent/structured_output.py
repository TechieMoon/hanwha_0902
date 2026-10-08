from pydantic import BaseModel, Field 
from langchain_openai import ChatOpenAI 
from langchain.agents import create_agent 
from langchain.agents.structured_output import ToolStrategy

from dotenv import load_dotenv

load_dotenv()

# 에이전트가 최종 결과로 돌려줄 형식(스키마). Field의 설명도 LLM에게 전달된다.
class ContactInfo(BaseModel):
    """연락처 정보 스키마"""
    name: str = Field(description="이름")
    email: str = Field(description="이메일 주소")
    phone: str = Field(description="전화번호")
    
model = ChatOpenAI(model="gpt-4o-mini")
# response_format=ToolStrategy(스키마): 스키마를 'ContactInfo'라는 도구로 만들어 LLM에게 주고,
# LLM이 그 도구를 호출하면서 넘긴 인자로 ContactInfo 객체를 만든다.
agent = create_agent(
    model=model,
    tools=[],
    response_format=ToolStrategy(ContactInfo)
)

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "다음 텍스트에서 연락처 정보를 추출해줘: John Doe, john@example.com, (555) 123-4567"
    }]
})

# 구조화된 결과는 messages가 아니라 structured_response 키에 ContactInfo 객체로 들어온다.
contact = result["structured_response"]
print(f"이름: {contact.name}")
print(f"이메일: {contact.email}")
print(f"전화번호: {contact.phone}")