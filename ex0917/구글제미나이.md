# Google Gemini 모델(ChatGoogleGenerativeAI) 실습

지금까지는 OpenAI(`ChatOpenAI`) 모델만 써봤는데, 이번엔 **Google Gemini** 모델을 LangChain으로 호출하는 방법을 실습했다. LangChain은 모델 제공사가 달라도 거의 동일한 인터페이스(`invoke`, `stream`, 프롬프트/체인 연결 방식 등)로 쓸 수 있게 감싸주기 때문에, `ChatOpenAI` 대신 `ChatGoogleGenerativeAI`로 바꿔도 사용법 자체는 크게 다르지 않다.

## 1. Gemini 모델로 기본 스트리밍 호출

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

answer = llm.stream("자연어처리에 대해서 간략히 설명해줘")

# ChatOpenAI 예제에서는 chunk.content를 썼지만, 여기서는 chunk.text로 텍스트를 꺼낸다.
for chunk in answer:
    print(chunk.text, end="", flush=True)
```

`ChatOpenAI`와 동일하게 `.stream()`으로 스트리밍 호출한다. 다만 각 chunk에서 텍스트를 꺼낼 때 OpenAI 쪽 예제들에서는 `chunk.content`를 썼는데, 여기서는 `chunk.text`를 쓴다. 둘 다 메시지 청크에서 실제 텍스트를 꺼내는 역할은 같다.

## 2. 프롬프트 템플릿 + 체인으로 연결

```python
from langchain_core.prompts import PromptTemplate

model = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

prompt = PromptTemplate.from_template(
    "예/아니오 질문에 대답하세요. {question}는 과일입니까?"
)

chain = prompt | model

answer = chain.stream({"question": "사과"})
for chunk in answer:
    print(chunk.text, end="", flush=True)
```

`PromptTemplate`과 `prompt | model` 체인 구성 방식도 OpenAI 때와 완전히 동일하다.

## 3. 안전 설정(safety_settings)

```python
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    safety_settings={
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    },
)
```

Gemini는 `safety_settings`로 성적/혐오/괴롭힘/위험 콘텐츠 등 카테고리별로 응답을 얼마나 엄격하게 차단할지 설정할 수 있다. `HarmBlockThreshold.BLOCK_NONE`으로 지정하면 해당 카테고리에 대한 차단을 하지 않는다.

## 4. 멀티모달: 이미지를 보고 시 쓰기

지난번(9월 15일)에 `ChatOpenAI`로 실습했던 멀티모달(이미지 입력) 패턴을 Gemini로 그대로 반복했다.

```python
import base64
from langchain_core.messages import HumanMessage, SystemMessage

llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")

system_prompt = "당신은 시인입니다. 당신의 임무는 주어진 이미지를 가지고 시를 작성하는 것입니다."
user_prompt = "다음의 이미지에 대한 시를 작성해주세요."

# 이미지를 base64로 인코딩
with open("jeju-beach.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

# 멀티모달 메시지 구성: content를 리스트로 만들어 텍스트와 이미지를 함께 담는다.
messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(
        content=[
            {"type": "text", "text": user_prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
            },
        ]
    ),
]

answer = llm.stream(messages)
for chunk in answer:
    print(chunk.text, end="", flush=True)
```

로컬 이미지를 base64로 인코딩해서 `data:image/jpeg;base64,...` 형태로 만들고, `SystemMessage`로 역할을 부여한 뒤 `HumanMessage`의 `content`를 리스트로 구성해서 텍스트와 이미지를 함께 전달한다. `.stream()`으로 호출하면 모델이 이미지를 보고 시를 지어서 스트리밍으로 출력해준다.

## 정리

`ChatOpenAI` → `ChatGoogleGenerativeAI`로 모델만 바꿔도 프롬프트 템플릿, 체인 연결(`|`), 스트리밍 호출, 멀티모달 메시지 구성 방식은 거의 그대로 재사용할 수 있었다. 차이가 나는 부분은 `chunk.text`처럼 세세한 응답 객체의 속성 정도였다.
