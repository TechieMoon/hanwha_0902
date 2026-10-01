# ChatOpenAI로 첫 LLM 호출하기 (번역기)

`langchain_openai`의 `ChatOpenAI`로 OpenAI 모델을 호출해서, 한국어 문장을 영어로 번역하는 가장 간단한 예제를 실습했다. 에이전트 개발 환경(가상환경, `.env`의 OpenAI API 키)이 제대로 준비됐는지 확인하는 첫 실행용 코드다.

## 코드

```python
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
```

## 메시지 구성

`invoke()`에 `(역할, 내용)` 튜플 리스트를 넘기면 LangChain이 알맞은 메시지 객체로 바꿔서 모델에 보낸다.

| 역할 | 변환되는 메시지 | 용도 |
|---|---|---|
| `"system"` | `SystemMessage` | 모델의 역할·규칙 지정 ("영어로 번역하는 번역기") |
| `"human"` | `HumanMessage` | 사용자 입력 ("안녕하세요.") |

## 실행 결과

`print(ai_msg)`는 `AIMessage` 객체 전체를 출력한다. 번역된 문장은 `content`에 들어 있고(예: `"Hello."`), 그 외에 `response_metadata`(모델 이름, 토큰 사용량 등)와 `id`가 함께 출력된다. 번역 결과만 보고 싶으면 `print(ai_msg.content)`를 쓰면 된다.

## 정리

- `ChatOpenAI(model="gpt-4o")`: 사용할 모델 지정
- `load_dotenv()`: `.env`의 `OPENAI_API_KEY`를 불러와서 코드에 키를 직접 쓰지 않는다
- `llm.invoke(messages)`: system/human 메시지를 보내고 `AIMessage`로 응답을 받는다
