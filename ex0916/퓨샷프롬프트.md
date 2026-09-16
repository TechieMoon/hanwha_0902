# Few-Shot Prompting (예시 기반 프롬프트) 실습

`FewShotPromptTemplate`을 이용해서, 질문에 답하는 방식(추론 과정)을 몇 가지 예시로 미리 보여준 뒤 실제 질문을 던지면 LLM이 그 예시들의 패턴을 따라 답변하도록 유도하는 **Few-Shot Prompting**을 실습했다.

## 1. LLM 준비

```python
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    temperature=0,
    model="gpt-4.1",
)
```

- `temperature=0` : 출력의 무작위성을 최소화해서 매번 비슷하고 일관된 답변을 얻는다.
- `.env` 파일에 저장해둔 `OPENAI_API_KEY`는 `load_dotenv()`로 불러온다.

Few-Shot 예시 없이 일반 질문을 그대로 스트리밍으로 물어보면:

```python
question = "대한민국의 수도는 뭐야?"

answer = llm.stream(question)
for chunk in answer:
    print(chunk.content, end="", flush=True)
```

`llm.stream()`은 답변을 한 번에 받는 대신, 생성되는 대로 chunk(토큰) 단위로 흘려보내준다.

## 2. Self-Ask 스타일 예시 데이터 만들기

Few-Shot 예시는 복잡한 질문을 여러 개의 하위 질문(추가 질문)으로 쪼개고, 각 하위 질문에 대한 중간 답변을 거쳐 최종 답변에 도달하는 **Self-Ask(자문자답) 형식**으로 구성했다.

```
이 질문에 추가 질문이 필요한가요: 예.
추가 질문: (하위 질문 1)
중간 답변: (하위 질문 1에 대한 답)
추가 질문: (하위 질문 2)
중간 답변: (하위 질문 2에 대한 답)
...
최종 답변은: (최종 결론)
```

```python
examples = [
    {
        "question": "스티브 잡스와 아인슈타인 중 누가 더 오래 살았나요?",
        "answer": """이 질문에 추가 질문이 필요한가요: 예.
추가 질문: 스티브 잡스는 몇 살에 사망했나요?
중간 답변: 스티브 잡스는 56세에 사망했습니다.
추가 질문: 아인슈타인은 몇 살에 사망했나요?
중간 답변: 아인슈타인은 76세에 사망했습니다.
최종 답변은: 아인슈타인
""",
    },
    # ... (네이버 창립자, 율곡 이이 어머니, 올드보이/기생충 감독 예시 총 4개)
]
```

이렇게 "질문을 잘게 쪼개서 단계적으로 답하는" 예시를 여러 개 보여주면, 새로운 질문에도 LLM이 같은 방식으로 단계적 추론을 하도록 유도할 수 있다(Chain-of-Thought와 유사한 효과).

## 3. example_prompt로 예시 1개 포맷하기

`FewShotPromptTemplate`에 각 예시를 어떤 텍스트로 끼워 넣을지 정하는 것이 `example_prompt`다.

```python
from langchain_core.prompts import PromptTemplate

example_prompt = PromptTemplate.from_template(
    "Question:\n{question}\nAnswer:\n{answer}"
)

print(example_prompt.format(**examples[0]))
```

출력:

```txt
Question:
스티브 잡스와 아인슈타인 중 누가 더 오래 살았나요?
Answer:
이 질문에 추가 질문이 필요한가요: 예.
추가 질문: 스티브 잡스는 몇 살에 사망했나요?
중간 답변: 스티브 잡스는 56세에 사망했습니다.
추가 질문: 아인슈타인은 몇 살에 사망했나요?
중간 답변: 아인슈타인은 76세에 사망했습니다.
최종 답변은: 아인슈타인
```

## 4. FewShotPromptTemplate으로 예시 + 실제 질문 합치기

```python
from langchain_core.prompts.few_shot import FewShotPromptTemplate

prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    suffix="Question:\n{question}\nAnswer:",
    input_variables=["question"],
)

question = "Google이 창린된 연도에 Bill Gates의 나이는 몇 살인가요?"
final_prompt = prompt.format(question=question)
print(final_prompt)
```

- `examples` / `example_prompt` : 앞서 만든 예시들과 렌더링 템플릿
- `suffix` : 예시들 뒤에 붙는, 실제로 답을 구해야 할 새 질문. **의도적으로 답(Answer) 없이 질문까지만** 작성해서 LLM이 그 뒤를 예시와 같은 패턴으로 이어 쓰도록 유도한다.
- `input_variables` : `format()` 호출 시 채워야 하는 변수 목록

`final_prompt`를 출력하면 예시 4개 + 새 질문이 하나의 긴 프롬프트로 합쳐진 것을 볼 수 있다.

## 5. 완성된 프롬프트를 LLM에 그대로 호출

```python
answer = llm.stream(final_prompt)
for chunk in answer:
    print(chunk.content, end="", flush=True)
```

출력(요약):

```txt
이 질문에 추가 질문이 필요한가요: 예.
추가 질문: Google은 언제 창립되었나요?
중간 답변: Google은 1998년에 창립되었습니다.
추가 질문: Bill Gates는 언제 태어났나요?
중간 답변: Bill Gates는 1955년 10월 28일에 태어났습니다.
추가 질문: 1998년에 Bill Gates의 나이는 몇 살이었나요?
중간 답변: 1998년 - 1955년 = 43년. Bill Gates는 1998년에 43세였습니다.
최종 답변은: 43세
```

예시로 보여준 "추가 질문 → 중간 답변 → 최종 답변" 패턴을 그대로 따라서, 새로운 질문도 하위 질문으로 쪼개 단계적으로 답한 것을 확인할 수 있다.

## 6. 체인(prompt | llm | StrOutputParser)으로 재구성

`prompt.format()`으로 직접 문자열을 만드는 대신, LangChain의 파이프(`|`) 문법으로 체인을 구성할 수도 있다.

```python
from langchain_core.output_parsers import StrOutputParser

prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    suffix="Question:\n{question}\nAnswer",
    input_variables=["question"],
)

chain = prompt | llm | StrOutputParser()

answer = chain.stream(
    {"question": "Google이 창립된 연도에 Bill Gates의 나이는 몇 살인가요?"}
)

for chunk in answer:
    print(chunk, end="", flush=True)
```

- `chain.stream({"question": ...})`처럼 변수 딕셔너리를 넘기면 `FewShotPromptTemplate → llm → StrOutputParser` 순서로 자동 처리된다.
- `StrOutputParser()`는 LLM이 반환하는 메시지 청크(`AIMessageChunk`)에서 텍스트(`content`)만 뽑아 순수 문자열 스트림으로 바꿔준다. 그래서 `chunk.content`가 아니라 `chunk` 자체를 바로 출력하면 된다.

## 정리

| 방식 | 특징 |
|---|---|
| `prompt.format()` + `llm.stream()` | 프롬프트 문자열을 직접 만들어서 호출. 중간 결과(`final_prompt`)를 눈으로 확인하기 좋음 |
| `prompt \| llm \| StrOutputParser()` | 체인으로 묶어서 변수 딕셔너리만 넘기면 됨. 출력도 바로 문자열로 받아 후처리가 편함 |

두 방식 모두 결과적으로 Few-Shot 예시를 통해 LLM이 **복잡한 질문을 스스로 하위 질문으로 나누어 단계적으로 추론**하도록 유도한다는 점은 동일하다.
