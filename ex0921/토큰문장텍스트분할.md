# 토큰/문장 기준 텍스트 분할 실습

지금까지는 글자 수(character) 기준으로 텍스트를 나눴는데, 이번에는 다른 기준으로 나누는 두 가지 분할기를 실습했다. 하나는 LLM이 실제로 처리하는 단위인 토큰(token) 수를 기준으로 나누는 방식(`CharacterTextSplitter.from_tiktoken_encoder`, `TokenTextSplitter`)이고, 다른 하나는 자연어 문장 구조를 이해해서 문장 경계를 지키며 나누는 방식(`SpacyTextSplitter`)이다. 같은 용어집 텍스트(`data/appendix-keywords.txt`)로 실습했다.

## 1. CharacterTextSplitter.from_tiktoken_encoder(): 토큰 수 기준으로 분할

```python
from langchain_text_splitters import CharacterTextSplitter

text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="o200k_base",
    chunk_size=300,
    chunk_overlap=0,
)

texts = text_splitter.split_text(file)
print(len(texts))
```

출력: `11`

`CharacterTextSplitter`를 글자 수가 아니라 토큰(token) 수 기준으로 쓸 수 있게 해주는 생성자다. `tiktoken`은 OpenAI 모델들이 텍스트를 토큰으로 쪼갤 때 쓰는 라이브러리로, `encoding_name="o200k_base"`는 GPT-4o 계열 모델이 사용하는 인코딩이다. 내부적으로는 기존 `CharacterTextSplitter`처럼 구분자(`\n\n`)를 기준으로 나누되, 길이를 잴 때 글자 수 대신 토큰 수를 사용한다는 점이 다르다.

첫 번째 조각을 출력해보면, 글자 수 기준(210자)으로 나눴을 때보다 훨씬 더 많은 용어(Semantic Search, Embedding, Token, Tokenizer 일부)를 한 조각에 담고 있다.

## 2. TokenTextSplitter: 토큰 경계로 직접 분할

```python
from langchain_text_splitters import TokenTextSplitter

text_splitter = TokenTextSplitter(
    encoding_name="o200k_base",
    chunk_size=300,
    chunk_overlap=0,
)

texts = text_splitter.split_text(file)
print(texts[0])
```

`TokenTextSplitter`는 `from_tiktoken_encoder`처럼 구분자를 먼저 고려하는 게 아니라, 텍스트를 토큰으로 인코딩한 뒤 그 토큰 시퀀스를 `chunk_size` 토큰 단위로 곧바로 잘라내는 더 직접적인 방식이다. 그래서 문단이나 문장 경계를 무시하고 토큰 개수만 맞춰 자를 수도 있다.

## 3. SpacyTextSplitter: 문장 경계를 지키는 분할

```python
import warnings
from langchain_text_splitters import SpacyTextSplitter

warnings.filterwarnings("ignore")

text_splitter = SpacyTextSplitter(
    chunk_size=200,
    chunk_overlap=50,
)

texts = text_splitter.split_text(file)
print(texts[0])
```

`SpacyTextSplitter`는 spaCy 자연어 처리 라이브러리로 문장 경계를 실제로 인식해서, 문장 중간이 아니라 문장과 문장 사이에서 나누는 분할기다. `warnings.filterwarnings("ignore")`는 spaCy 관련 부수적인 경고 메시지를 숨기기 위한 설정이다.

- `chunk_size=200` : 조각 하나의 최대 글자 수.
- `chunk_overlap=50` : 조각들 사이에 50자 겹침.

첫 번째 조각을 확인해보면, 앞서 글자/토큰 수 기준 분할기들과 달리 문장 단위를 존중해서 나뉜 것을 볼 수 있다(spaCy가 문장을 인식해 줄바꿈을 삽입하면서, 원문에는 없던 개행이 문장 사이에 추가되어 있다).

## 정리

| 분할기 | 분할 기준 | 특징 |
|---|---|---|
| `CharacterTextSplitter` | 글자 수 + 지정 구분자 | 구분자로만 나누고 더 잘게 쪼개지 않음 |
| `RecursiveCharacterTextSplitter` | 글자 수 + 여러 구분자 순차 시도 | chunk_size에 최대한 맞춰 재귀적으로 분할 |
| `CharacterTextSplitter.from_tiktoken_encoder` | 토큰 수 + 구분자 | 길이 계산만 토큰 기준, 구분자 기반 분할은 동일 |
| `TokenTextSplitter` | 토큰 수(직접) | 토큰 시퀀스를 그대로 잘라 문장/구분자 무시 가능 |
| `SpacyTextSplitter` | 문장 경계(NLP) | spaCy로 문장을 인식해 문장 단위를 지키며 분할 |

같은 텍스트라도 무엇을 "글자 수"로 셀지, 어디를 "경계"로 볼지에 따라 조각의 모양이 크게 달라진다. LLM에 넣을 때는 실제 처리 단위인 토큰 기준 분할기가 컨텍스트 길이를 더 정확히 맞출 수 있고, 사람이 읽기 좋은 의미 단위가 중요할 때는 문장 경계를 지키는 `SpacyTextSplitter` 같은 방식이 유리하다.
