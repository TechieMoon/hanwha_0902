# CharacterTextSplitter 실습

긴 텍스트를 하나의 구분자(separator) 기준으로 잘라서 지정한 글자 수 단위의 조각(chunk)으로 나누는 `CharacterTextSplitter`를 실습했다. 예시 데이터로는 AI 용어를 정의해둔 한글 용어집(`data/appendix-keywords.txt`)을 사용했다. 이 노트북은 텍스트 분할만 다루기 때문에 LLM API를 호출하지 않고, 그래서 `.env`나 API 키 로딩도 필요 없다.

## 1. 원본 텍스트 준비 및 미리보기

```python
with open("./data/appendix-keywords.txt", encoding="utf-8") as f:
    file = f.read()

print(file[:500])
```

출력(앞부분 일부):

```txt
Semantic Search

정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.
예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.
연관키워드: 자연어 처리, 검색 알고리즘, 데이터 마이닝

Embedding
...
```

AI 용어들이 각각 정의·예시·연관키워드 형식으로 정리되어 있고, 용어 사이는 빈 줄(`\n\n`)로 구분되어 있다.

## 2. CharacterTextSplitter 설정

```python
from langchain_text_splitters import CharacterTextSplitter

text_splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=210,
    chunk_overlap=0,
    length_function=len,
)
```

`CharacterTextSplitter`는 지정한 `separator`를 기준으로 텍스트를 나누는 가장 단순한 형태의 텍스트 분할기다.

- `separator="\n\n"` : 빈 줄(문단 구분)을 기준으로 우선 나눈다.
- `chunk_size=210` : 조각 하나의 최대 글자 수.
- `chunk_overlap=0` : 조각들 사이에 겹치는 부분 없음.
- `length_function=len` : 글자 수를 셀 때 사용할 함수(기본 `len`).

## 3. create_documents()로 Document 리스트 만들기

```python
texts = text_splitter.create_documents([file])
print(len(texts[0].page_content))
print(texts[0])
```

출력:

```txt
197
page_content='Semantic Search

정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.
예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.
연관키워드: 자연어 처리, 검색 알고리즘, 데이터 마이닝

Embedding'
```

`create_documents()`에 텍스트 리스트를 넘기면, 각 텍스트를 위 설정대로 나눈 뒤 조각마다 `Document` 객체로 감싸서 반환한다. 첫 번째 조각(`texts[0]`)은 `chunk_size=210`을 넘지 않는 선에서 `\n\n` 구분자를 기준으로 "Semantic Search" 항목 전체를 담고, 다음 항목("Embedding")의 제목까지만 포함한 뒤 잘렸다(실제 글자 수는 197자).

## 4. 여러 문서 + 문서별 metadata 한 번에 넣기

```python
metadatas = [
    {"document": 1},
    {"document": 2},
]

documents = text_splitter.create_documents(
    [
        file,
        file
    ],
    metadatas=metadatas
)

print(documents[0])
```

출력:

```txt
page_content='Semantic Search
...
Embedding' metadata={'document': 1}
```

`create_documents()`는 텍스트를 여러 개 리스트로 넘길 수도 있고, 이때 `metadatas` 인자로 각 원본 텍스트에 대응하는 메타데이터를 함께 지정할 수 있다. 여기서는 같은 `file` 텍스트를 두 번 넣으면서, 각각 `{"document": 1}`, `{"document": 2}`라는 메타데이터를 붙였다.

## 5. 전체 조각 개수 확인

```python
len(documents)
```

출력: `64`

`file` 하나를 나누면 32개의 조각이 나온다. 같은 텍스트를 두 번 넣었으니 총 조각 개수는 32 × 2 = 64개가 된다.

## 6. metadata가 조각마다 올바르게 유지되는지 확인

```python
documents[1].metadata
```

출력: `{'document': 1}`

`documents[1]`은 첫 번째 원본 문서(`file` 첫 번째 사본)에서 나온 두 번째 조각이다. 원본 문서가 여러 조각으로 나뉘어도 그 원본에 지정했던 metadata가 모든 조각에 그대로 상속되는 것을 알 수 있다.

## 7. split_text(): Document가 아닌 순수 문자열로 받기

```python
text_splitter.split_text(file)[0]
```

출력: 3번의 `texts[0].page_content`와 동일한 내용의 문자열.

`create_documents()`가 `Document` 객체 리스트를 반환하는 것과 달리, `split_text()`는 나눈 결과를 `Document`로 감싸지 않고 순수 문자열 리스트로 반환한다. metadata가 필요 없이 텍스트 조각 자체만 필요할 때 더 가볍게 쓸 수 있는 저수준(low-level) 메서드다.

## 정리

| 메서드 | 반환 타입 | metadata 지정 |
|---|---|---|
| `create_documents(texts, metadatas=...)` | `Document` 객체 리스트 | 원본 문서별로 지정 가능, 모든 조각에 상속 |
| `split_text(text)` | 문자열 리스트 | 불가(순수 텍스트만) |

`CharacterTextSplitter`는 하나의 `separator`만 기준으로 나누기 때문에, 그 구분자로 나눈 조각이 `chunk_size`보다 크면 더 잘게 쪼개지 않고 그대로 둔다(반면 `RecursiveCharacterTextSplitter`는 여러 구분자를 순서대로 시도하며 최대한 `chunk_size`에 맞춘다). 여러 문서를 한 번에 나눌 때는 `metadatas`로 원본 출처를 함께 기록해두면, 나뉜 조각이 어느 원본에서 왔는지 나중에도 추적할 수 있다.
