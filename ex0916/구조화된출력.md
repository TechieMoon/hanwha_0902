# with_structured_output()으로 구조화된 출력 받기

질문에 답하면서 답변(`answer`)과 출처(`source`)를 함께 구조화된 객체로 받는 방법을 실습했다.

## 1. 원하는 출력 구조를 Pydantic 모델로 정의

```python
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class AnswerWithSource(BaseModel):
    answer: str = Field(description="사용자의 질문에 대한 답변")
    source: str = Field(
        description="사용자의 질문에 답하기 위해 사용된 출처(웹사이트 주소 등)"
    )
```

`answer`, `source` 두 필드를 가진 모델을 정의한다. 각 필드의 `description`은 모델에게 "이 필드에는 어떤 내용이 들어가야 하는지" 알려주는 설명으로 쓰인다.

## 2. LLM에 구조화된 출력 연결

```python
llm = ChatOpenAI(temperature=0)

# AnswerWithSource 스키마에 맞는 구조화된 객체를 바로 반환하는 모델.
llm_with_structure = llm.with_structured_output(AnswerWithSource)
```

`with_structured_output(AnswerWithSource)`를 호출하면, 모델이 `AnswerWithSource` 스키마에 맞는 객체를 바로 반환하도록 LangChain이 처리해준다.

## 3. 질문에 답변 + 출처 함께 받기

```python
answer = llm_with_structure.invoke("대한민국의 수도는 어디인가요?")
print(answer)
print(answer.answer)  # 답변만 따로 꺼내기
print(answer.source)  # 출처만 따로 꺼내기
```

질문 문자열을 그대로 넘기면 `answer`, `source` 필드를 가진 `AnswerWithSource` 객체가 바로 반환된다.

```python
answer2 = llm_with_structure.invoke("세종대왕의 업적은 무엇인가요?")
print(answer2)
```

## 정리

`with_structured_output(스키마)`를 모델에 바로 붙이면, 프롬프트에 포맷 안내문을 직접 작성하지 않아도 원하는 필드(`answer`, `source`)를 가진 객체를 곧바로 받을 수 있다. 반환된 객체는 `answer.answer`, `answer.source`처럼 필드 단위로 바로 접근할 수 있어서 후처리가 간편하다.
