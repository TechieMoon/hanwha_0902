# CommaSeparatedListOutputParser 실습

LLM의 답변을 **쉼표로 구분된 리스트**(파이썬 `list`) 형태로 바로 받아오는 `CommaSeparatedListOutputParser`를 실습했다. 앞서 실습한 `PydanticOutputParser`와 원리는 같다: 파서가 "이런 형식으로 답해줘"라는 포맷 지시문을 만들어주고, LLM이 그 형식대로 답하면 파서가 그걸 다시 파이썬 객체로 변환해준다. 다만 이번엔 복잡한 스키마 대신 **문자열 리스트 하나**만 받으면 되는 단순한 경우다.

## 1. 파서 · 프롬프트 · 모델을 체인으로 연결

```python
from dotenv import load_dotenv
load_dotenv()

from langchain_core.output_parsers import CommaSeparatedListOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# "a, b, c" 형태의 쉼표 구분 답변을 파이썬 리스트로 변환해주는 파서.
output_parser = CommaSeparatedListOutputParser()

# 이 파서가 원하는 출력 형식(쉼표로 구분해서 답하라는 지시문)을 자동 생성.
format_instructions = output_parser.get_format_instructions()

prompt = PromptTemplate(
    template="List five {subject}.\n{format_instructions}",
    input_variables=["subject"],
    # format_instructions는 미리 고정해두고, 호출 시에는 subject만 채우면 된다.
    partial_variables={"format_instructions": format_instructions},
)

model = ChatOpenAI(temperature=0)

# 프롬프트 생성 -> LLM 호출 -> 쉼표 구분 텍스트를 리스트로 파싱, 세 단계를 하나의 체인으로 연결.
chain = prompt | model | output_parser
```

- `CommaSeparatedListOutputParser()` : 쉼표로 구분된 텍스트를 리스트로 바꿔주는 파서.
- `get_format_instructions()` : 파서가 요구하는 출력 형식을 설명하는 지시문 텍스트를 자동으로 만들어준다.
- `partial_variables` : 프롬프트의 `{format_instructions}` 자리를 미리 고정해서, 실제 호출 시에는 `{subject}`만 채우면 되게 한다.

## 2. 체인 호출: 결과가 바로 파이썬 리스트로

```python
chain.invoke({"subject": "대한민국 관광명소"})
```

출력:

```txt
['경복궁', '남산타워', '부산 해운대해수욕장', '제주도 성산일출봉', '경주 불국사temples']
```

결과가 문자열이 아니라 바로 파이썬 리스트로 반환된다. 별도로 `split(",")` 같은 후처리를 직접 할 필요가 없다.

## 3. 스트리밍으로 호출하기

```python
for s in chain.stream({"subject": "대한민국 관광명소"}):
    print(s, flush=True)
```

출력:

```txt
['경복궁']
['남산타워']
['부산 해운대해수욕장']
['제주도 성산일출봉']
['경주 불국사temples']
```

`chain.stream()`으로 호출하면 리스트 전체가 한 번에 오는 게 아니라 **항목이 하나씩 파싱될 때마다** 원소 1개짜리 리스트 chunk로 흘러나온다.

## 정리

| 파서 | 반환 타입 | 용도 |
|---|---|---|
| `PydanticOutputParser` | 정의한 Pydantic 모델 객체 | 여러 필드를 가진 복잡한 구조 추출 |
| `CommaSeparatedListOutputParser` | `list[str]` | 항목 나열처럼 단순한 리스트 하나만 필요할 때 |

두 파서 모두 "포맷 지시문 생성 → LLM 호출 → 텍스트를 원하는 파이썬 객체로 파싱"이라는 동일한 구조를 따르며, `prompt | llm | parser` 체인으로 연결하면 세 단계가 한 번에 처리된다.
