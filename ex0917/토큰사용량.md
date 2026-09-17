# 토큰 사용량(Token Usage) 추적 실습

LLM 호출 비용은 보통 입력/출력 토큰 수에 비례해서 청구된다. `get_usage_metadata_callback()`을 이용하면, `with` 블록 안에서 이루어진 호출들의 토큰 사용량을 모델별로 자동 집계해서 확인할 수 있다.

## 1. 콜백과 모델 준비

```python
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-5.6-luna")
```

`get_usage_metadata_callback`은 `with` 블록으로 사용하는 컨텍스트 매니저로, 그 블록 안에서 호출된 LLM들의 토큰 사용량을 자동으로 집계해준다.

## 2. 호출 1번의 토큰 사용량 확인

```python
with get_usage_metadata_callback() as cb:
    result = llm.invoke("대한민국의 수도는 어디야?")

print(cb.usage_metadata)
```

출력:

```txt
{'gpt-5.6-luna': {'input_tokens': 14, 'output_tokens': 16, 'total_tokens': 30, ...}}
```

`with get_usage_metadata_callback() as cb:` 블록 안에서 `llm.invoke()`를 호출하면, 그 호출에 사용된 토큰 수가 `cb.usage_metadata`에 모델 이름을 key로 하는 dict 형태로 쌓인다(`input_tokens`, `output_tokens`, `total_tokens` 등을 포함).

## 3. 여러 번 호출한 토큰 사용량 합산하기

```python
with get_usage_metadata_callback() as cb:
    result = llm.invoke("대한민국의 수도는 어디야?")
    result = llm.invoke("대한민국의 수도는 어디야?")

usage = cb.usage_metadata

input_tokens = sum(data["input_tokens"] for data in usage.values())
output_tokens = sum(data["output_tokens"] for data in usage.values())
total_tokens = sum(data["total_tokens"] for data in usage.values())

print(f"총 사용된 토큰수: {total_tokens}")
print(f"입력 토큰수: {input_tokens}")
print(f"출력 토큰수: {output_tokens}")
```

출력:

```txt
총 사용된 토큰수: 60
입력 토큰수: 28
출력 토큰수: 32
```

같은 `with` 블록 안에서 `invoke()`를 여러 번 호출하면, 그 블록 안에서 이루어진 모든 호출의 토큰 사용량이 `cb.usage_metadata`에 누적된다. `usage_metadata`는 `{모델명: {input_tokens, output_tokens, ...}}` 형태의 dict이므로, `.values()`를 순회하면서 각 모델의 토큰 수를 더하면 전체 합계를 구할 수 있다(여러 모델을 섞어 써도 모델별로 따로 집계되고, 합산하면 전체 총량을 구할 수 있다).
