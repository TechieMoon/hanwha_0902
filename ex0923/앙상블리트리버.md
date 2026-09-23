# 앙상블 리트리버 (Ensemble Retriever)

성격이 다른 두 검색기 — 키워드 기반 BM25와 임베딩 기반 FAISS — 를 `EnsembleRetriever`로 결합해서, 가중치(weights)로 두 방식의 반영 비율을 조절하는 법을 실습한다.

```python
from dotenv import load_dotenv 

load_dotenv()
```

출력:

```txt
True
```

## 1. BM25 Retriever + FAISS Retriever + Ensemble 구성

`BM25Retriever`는 키워드(단어 빈도) 기반 검색기, FAISS retriever는 임베딩 기반 의미 검색기다. 서로 성격이 다른 두 retriever를 `EnsembleRetriever`로 묶으면, `weights`(여기서는 [0.7, 0.3])로 각 retriever의 반영 비율을 조절해 두 방식의 장점을 함께 활용할 수 있다.

```python
from langchain_classic.retrievers import BM25Retriever, EnsembleRetriever
from langchain_community.vectorstores import FAISS 
from langchain_openai import OpenAIEmbeddings

doc_list = [
    "I like apples",
    "I like apple company",
    "I like apple's iphone",
    "Apple is my favorite company",
    "I like apple's ipad",
    "I like apple's macbook",
]

bm25_retriever = BM25Retriever.from_texts(
    doc_list,
)

bm25_retriever.k = 1 

embedding = OpenAIEmbeddings()
faiss_vectorstore = FAISS.from_texts(
    doc_list,
    embedding,
)
faiss_retriever = faiss_vectorstore.as_retriever(search_kwargs={"k": 1})

ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, faiss_retriever],
    weights=[0.7, 0.3],
)
```

## 2. 세 가지 검색 방식 비교

같은 질의("my favorite fruit is apple")로 앙상블/BM25/FAISS 각각의 검색 결과를 비교한다. BM25는 "apple"이라는 단어가 그대로 들어간 문서를, FAISS는 의미상 "과일"과 관련된 문서를 우선시하는 경향을 보인다.

```python
query = "my favorite fruit is apple"
ensemble_result = ensemble_retriever.invoke(query)
bm25_result = bm25_retriever.invoke(query)
faiss_result = faiss_retriever.invoke(query)

print("[Ensemble Retriever]")
for doc in ensemble_result:
    print(f"Content: {doc.page_content}")
    print()

print("[BM25 Retriever]")
for doc in bm25_result:
    print(f"Content: {doc.page_content}")
    print()

print("[FAISS Retriever]")
for doc in faiss_result:
    print(f"Content: {doc.page_content}")
    print()
```

출력:

```txt
[Ensemble Retriever]
Content: Apple is my favorite company

Content: I like apples

[BM25 Retriever]
Content: Apple is my favorite company

[FAISS Retriever]
Content: I like apples
```

## 3. ConfigurableField로 weights를 실행 시점에 조절

vectorstore_retriever 실습과 마찬가지로, `configurable_fields()`를 쓰면 `EnsembleRetriever`를 새로 만들지 않고도 `weights`를 실행할 때마다 바꿀 수 있다.

```python
from langchain_core.runnables import ConfigurableField

ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, faiss_retriever],
).configurable_fields(
    weights=ConfigurableField(
        id="ensemble_weights",
        name="Ensemble Weights",
        description="Ensemble Weights",
    )
)
```

`weights=[1, 0]`으로 설정하면 BM25 결과만 반영된다(키워드 기반).

```python
config = {"configurable": {"ensemble_weights": [1, 0]}}

docs = ensemble_retriever.invoke("my favorite fruit is apple", config=config)
docs
```

출력:

```txt
[Document(metadata={}, page_content='Apple is my favorite company'),
 Document(id='b9657323-3bd3-49ea-a998-8a36db2525fb', metadata={}, page_content='I like apples')]
```

`weights=[0, 1]`으로 설정하면 FAISS 결과만 반영된다(의미 기반). 두 결과의 순서가 다른 것을 확인할 수 있다.

```python
config = {"configurable": {"ensemble_weights": [0, 1]}}

docs = ensemble_retriever.invoke("my favorite fruit is apple", config=config)
docs
```

출력:

```txt
[Document(id='b9657323-3bd3-49ea-a998-8a36db2525fb', metadata={}, page_content='I like apples'),
 Document(metadata={}, page_content='Apple is my favorite company')]
```

## 정리

| 구성 요소 | 역할 |
|---|---|
| `BM25Retriever` | 단어(키워드) 빈도 기반 검색. 질의에 등장한 단어가 그대로 포함된 문서를 우선시 |
| FAISS retriever | 임베딩 기반 의미 검색. 단어가 정확히 겹치지 않아도 의미가 비슷한 문서를 찾음 |
| `EnsembleRetriever(retrievers=[...], weights=[...])` | 여러 retriever의 결과를 가중합해서 통합 순위를 매김 |
| `.configurable_fields(weights=ConfigurableField(...))` | retriever를 새로 만들지 않고 `invoke(..., config=...)`로 실행마다 weights를 바꿔 적용 |

키워드 검색과 의미 검색은 서로 놓치는 부분이 다르기 때문에, 앙상블로 묶으면 한쪽만 쓸 때보다 더 안정적인 검색 결과를 얻을 수 있다.
