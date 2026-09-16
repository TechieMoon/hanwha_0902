# Output Parser (구조화된 출력 파싱) 실습

LLM의 답변을 자유 텍스트가 아니라 미리 정한 구조(스키마)를 가진 파이썬 객체로 바로 받아오는 방법을 실습했다. `PydanticOutputParser`로 직접 파싱 과정을 구성해보고, 마지막에는 `with_structured_output()`으로 더 간단하게 같은 결과를 얻는 방법까지 비교했다.

## 1. 준비

```python
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

llm = ChatOpenAI(
    temperature=0,
    model="gpt-4.1-mini"
)
```

구조화해서 정보를 추출할 대상은 미팅을 제안하는 비즈니스 이메일 본문(`email_conversation`)이다. 발신자, 수신자, 제목, 요청 사항, 미팅 일정 등이 섞여 있는 텍스트에서 필요한 정보만 골라내는 것이 목표다.

## 2. Output Parser 없이 그냥 요약해보기 (자유 텍스트)

```python
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template(
    template="다음의 이메일 내용중 중요한 내용을 추출해 주세요.\n\n{email_conversation}"
)

chain = prompt | llm
answer = chain.stream({"email_conversation": email_conversation})
for chunk in answer:
    print(chunk.content, end="", flush=True)
```

이렇게만 물어보면 결과는 사람이 읽기엔 좋지만 형식이 자유로운 텍스트라서, 프로그램이 특정 필드(날짜, 이메일 주소 등)만 꺼내 쓰기는 어렵다. 이 문제를 `PydanticOutputParser`로 해결한다.

## 3. 원하는 출력 구조를 Pydantic 모델로 정의

```python
class EmailSummary(BaseModel):
    person: str = Field(description="메일을 보낸 사람")
    email: str = Field(description="메일을 보낸 사람의 이메일 주소")
    subject: str = Field(description="메일 제목")
    summary: str = Field(description="메일 본문을 요약한 텍스트")
    date: str = Field(description="메일 본문에 언급된 미팅 날짜와 시간")

parser = PydanticOutputParser(pydantic_object=EmailSummary)
```

각 필드의 `description`은 LLM에게 "이 필드에는 어떤 내용을 넣어야 하는지" 알려주는 설명으로 쓰인다. 이 스키마를 `PydanticOutputParser`에 넘기면, "이 형식대로 답해달라"는 지시문 생성과 "실제로 온 답을 이 형식으로 파싱"하는 것을 모두 담당해준다.

## 4. 파서가 요구하는 출력 형식(포맷 지시문) 확인

```python
print(parser.get_format_instructions())
```

`get_format_instructions()`는 "LLM이 어떤 형태(JSON 스키마)로 답해야 하는지"를 설명하는 텍스트를 만들어준다. 이 텍스트를 프롬프트에 그대로 끼워 넣으면 LLM이 그 형식에 맞춰 JSON을 출력하도록 유도할 수 있다.

## 5. 포맷 지시문을 반영한 프롬프트 작성

```python
prompt = PromptTemplate.from_template(
    """
You are a helpful assistant. Please answer the following questions in KOREAN.

QUESTION:
{question}

EMAIL CONVERSATION:
{email_conversation}

FORMAT:
{format}
"""
)

prompt = prompt.partial(format=parser.get_format_instructions())
```

`{format}` 자리에 포맷 지시문을 `partial()`로 미리 고정해두면, 이후 호출 시에는 `question`, `email_conversation`만 채우면 된다.

## 6. parser 없이 체인 호출 → 원본 텍스트를 직접 파싱

일부러 `prompt | llm`까지만 연결해서 LLM이 실제로 어떤 원본 텍스트(JSON 문자열)를 출력하는지 먼저 확인한다.

```python
chain = prompt | llm

response = chain.stream(
    {
        "email_conversation": email_conversation,
        "question": "이메일 내용 중 주요 내용을 추출해주세요."
    }
)

output = ""
for chunk in response:
    text = chunk.content
    if isinstance(text, str):
        print(text, end="", flush=True)
        output += text
```

LLM은 마크다운 코드블록(` ```json ... ``` `)에 감싸인 JSON 텍스트로 응답한다. 이 텍스트를 `output`에 모아둔 뒤, 파서로 직접 파싱한다.

```python
structured_output = parser.parse(output)
print(structured_output)
```

`parser.parse(output)`을 호출하면 코드블록 표시까지 포함된 텍스트를 알아서 처리해서 `EmailSummary` 객체로 변환해준다. 이제 `structured_output.person`, `structured_output.date`처럼 필드 단위로 값을 꺼내 쓸 수 있다.

## 7. parser까지 체인에 직접 연결하기

매번 텍스트를 모았다가 따로 `parser.parse()`를 호출하는 대신, 체인 자체에 `| parser`를 붙이면 자동으로 파싱까지 끝난 객체를 바로 받을 수 있다.

```python
chain = prompt | llm | parser

response = chain.invoke(
    {
        "email_conversation": email_conversation,
        "question": "이메일 내용 중 주요 내용을 추출해주세요."
    }
)

print(response)  # 곧바로 EmailSummary 객체
```

## 8. 더 간단한 방법: with_structured_output()

`PromptTemplate` + `PydanticOutputParser`를 직접 조합하지 않고, `with_structured_output()`을 쓰면 모델이 함수 호출(도구 호출) 방식으로 곧바로 정해진 스키마의 객체를 반환하도록 LangChain이 대신 처리해준다. 포맷 지시문을 프롬프트에 직접 넣을 필요도 없다.

```python
llm_with_structured = ChatOpenAI(
    temperature=0,
    model="gpt-4.1-mini"
).with_structured_output(EmailSummary)

answer = llm_with_structured.invoke(email_conversation)
print(answer)
```

프롬프트 템플릿 없이 이메일 본문 문자열을 그대로 넘겨도 `EmailSummary` 객체가 바로 나온다. 다만 `date` 필드처럼 원문에 명시되지 않은 정보(연도 등)는 모델이 임의로 채워 넣을 수 있어서("2024-01-08"처럼), 구조화 출력이라고 해서 내용까지 항상 정확한 것은 아니라는 점도 확인했다.

## 정리

| 방식 | 특징 |
|---|---|
| `prompt \| llm` + `parser.parse(output)` | 프롬프트에 포맷 지시문을 직접 넣어야 함. LLM 원본 응답(JSON 텍스트)을 직접 확인할 수 있음 |
| `prompt \| llm \| parser` | 체인 안에 파서까지 포함. 호출하면 곧바로 구조화된 객체가 나옴 |
| `llm.with_structured_output(Schema)` | 포맷 지시문을 직접 작성할 필요 없이, 모델의 구조화 출력 기능(함수 호출)을 그대로 활용. 가장 간단 |

세 방식 모두 결과적으로 LLM의 답변을 사람이 읽는 텍스트가 아니라 **프로그램이 바로 다룰 수 있는 구조화된 데이터**로 얻는다는 목적은 같다.
