# ChatOpenAI로 LLM을 처음 호출해보는 예제 (한국어 -> 영어 번역기)
from langchain_openai import ChatOpenAI 
from dotenv import load_dotenv 

# .env의 OPENAI_API_KEY를 환경변수로 불러온다.
load_dotenv() 
# 사용할 OpenAI 모델 지정
llm = ChatOpenAI(model="gpt-4o")

# (역할, 내용) 튜플 리스트로 대화 메시지를 구성한다.
messages = [
    (
        # system: 모델의 역할과 행동 규칙을 정해주는 메시지
        "system",
        "당신은 사용자가 한 말을 영어로 번역하는 유능한 번역기입니다.",
    ),
    # human: 사용자가 실제로 입력한 메시지
    ("human", "안녕하세요."),
]
# 메시지를 모델에 보내고 응답(AIMessage)을 받는다.
ai_msg = llm.invoke(messages)
# AIMessage 전체 출력 (번역 결과는 ai_msg.content에 들어 있다)
print(ai_msg)
