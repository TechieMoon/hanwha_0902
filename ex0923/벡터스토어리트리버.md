# VectorStore를 Retriever로 활용하기

벡터 스토어(FAISS)를 LangChain의 `Retriever` 인터페이스로 변환해서 쓰는 법을 실습한다. 기본 검색, MMR(다양성 고려), 점수 임계값 기준 검색을 비교하고, `ConfigurableField`로 체인을 재구성하지 않고도 실행 시점에 검색 옵션을 바꾸는 패턴까지 다룬다.

```python
from dotenv import load_dotenv

load_dotenv()
```

출력:

```txt
True
```

## 1. 벡터 스토어 구축

한글 용어집 텍스트를 300자 단위로 분할해서 FAISS 벡터 스토어를 만든다. Retriever 실습을 위한 기본 재료다.

```python
from langchain_community.vectorstores import FAISS 
from langchain_openai import OpenAIEmbeddings 
from langchain_text_splitters import CharacterTextSplitter 
from langchain_community.document_loaders import TextLoader 

loader = TextLoader("./data/appendix-keywords.txt", encoding="utf-8")

documents = loader.load() 

text_splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=0)

split_docs = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings()

db = FAISS.from_documents(split_docs, embeddings)
```

## 2. VectorStore를 Retriever로 변환

`as_retriever()`를 호출하면 벡터 스토어가 LangChain의 `Retriever` 인터페이스로 바뀐다. 벡터 스토어 자체는 `similarity_search()` 같은 메서드를 직접 호출해야 하지만, `Retriever`로 감싸면 체인(Chain)이나 LCEL 파이프라인에 `.invoke()`로 바로 연결할 수 있다. 아무 옵션도 주지 않으면 기본 유사도 검색(`similarity_search`)과 동일하게 동작한다.

```python
retriever = db.as_retriever()
```

기본 retriever로 질의해본다.

```python
docs = retriever.invoke("임베딩(Embedding)은 무엇인가요?")

for doc in docs:
    print(doc.page_content)
    print("=====================================================")
```

출력:

```txt
정의: 임베딩은 단어나 문장 같은 텍스트 데이터를 저차원의 연속적인 벡터로 변환하는 과정입니다. 이를 통해 컴퓨터가 텍스트를 이해하고 처리할 수 있게 합니다.
예시: "사과"라는 단어를 [0.65, -0.23, 0.17]과 같은 벡터로 표현합니다.
연관키워드: 자연어 처리, 벡터화, 딥러닝

Token
=====================================================
정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.
예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.
연관키워드: 자연어 처리, 임베딩, 의미론적 유사성
LLM (Large Language Model)
=====================================================
Semantic Search

정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.
예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.
연관키워드: 자연어 처리, 검색 알고리즘, 데이터 마이닝

Embedding
=====================================================
정의: 크롤링은 자동화된 방식으로 웹 페이지를 방문하여 데이터를 수집하는 과정입니다. 이는 검색 엔진 최적화나 데이터 분석
... (일부 생략)
```

## 3. search_type="mmr": 다양성을 고려한 검색

MMR(Maximal Marginal Relevance)은 관련성뿐 아니라 결과 간의 다양성도 함께 고려한다. `fetch_k`(먼저 넉넉히 가져올 후보 수), `k`(최종 반환 개수), `lambda_mult`(관련성 vs 다양성 비율, 1에 가까울수록 관련성 중시)를 조절할 수 있다.

```python
retriever = db.as_retriever(
    search_type="mmr", search_kwargs={"k": 2, "fetch_k": 10, "lambda_mult": 0.6}
)

docs = retriever.invoke("임베딩(Embedding)은 무엇인가요?")

for doc in docs:
    print(doc.page_content)
    print("==============================================")
```

출력:

```txt
정의: 임베딩은 단어나 문장 같은 텍스트 데이터를 저차원의 연속적인 벡터로 변환하는 과정입니다. 이를 통해 컴퓨터가 텍스트를 이해하고 처리할 수 있게 합니다.
예시: "사과"라는 단어를 [0.65, -0.23, 0.17]과 같은 벡터로 표현합니다.
연관키워드: 자연어 처리, 벡터화, 딥러닝

Token
==============================================
Semantic Search

정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.
예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.
연관키워드: 자연어 처리, 검색 알고리즘, 데이터 마이닝

Embedding
==============================================
```

## 4. search_type="similarity_score_threshold": 점수 기준 필터링

개수(`k`) 기준이 아니라 유사도 점수가 `score_threshold` 이상인 문서만 반환한다. 얼마나 관련 있는 문서만 걸러낼지가 중요할 때 유용하다.

```python
retriever = db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.8},
)

for doc in retriever.invoke("Word2Vec은 무엇인가요?"):
    print(doc.page_content)
    print("=======================================================")
```

출력:

```txt
정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.
예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.
연관키워드: 자연어 처리, 임베딩, 의미론적 유사성
LLM (Large Language Model)
=======================================================
```

## 5. search_kwargs로 세부 옵션 지정

`search_kwargs={"k": 1}`처럼 검색 관련 옵션을 딕셔너리로 넘겨 반환 개수 등을 조절한다.

```python
retriever = db.as_retriever(
    search_kwargs={"k": 1}
)

docs = retriever.invoke(
    "임베딩(Embedding)은 무엇인가요?"
)

for doc in docs:
    print(doc.page_content)
    print("=======================================================")
```

출력:

```txt
정의: 임베딩은 단어나 문장 같은 텍스트 데이터를 저차원의 연속적인 벡터로 변환하는 과정입니다. 이를 통해 컴퓨터가 텍스트를 이해하고 처리할 수 있게 합니다.
예시: "사과"라는 단어를 [0.65, -0.23, 0.17]과 같은 벡터로 표현합니다.
연관키워드: 자연어 처리, 벡터화, 딥러닝

Token
=======================================================
```

## 6. ConfigurableField로 실행 시점에 검색 옵션 바꾸기

`configurable_fields()`를 쓰면 retriever를 새로 만들지 않고도, 매 호출(`invoke`)마다 `config` 인자로 `search_type`이나 `search_kwargs`를 바꿔서 실행할 수 있다. 체인을 재구성하지 않고 런타임에 검색 전략을 유연하게 바꾸고 싶을 때 쓰는 패턴이다.

```python
from langchain_core.runnables import ConfigurableField 

retriever = db.as_retriever(search_kwargs={"k": 1}).configurable_fields(
    search_type=ConfigurableField(
        id="search_type",
        name="Search Type",
        description="The search type to use",
    ),
    search_kwargs=ConfigurableField(
        id="search_kwargs",
        name="Search Kwargs",
        description="The search kwargs to use",
    ),
)
```

`config`로 `search_kwargs`(k=3)만 바꿔서 실행한다.

```python
config = {"configurable": {"search_kwargs": {"k": 3}}}

docs = retriever.invoke("임베딩(Embedding)은 무엇인가요?", config=config)

for doc in docs:
    print(doc.page_content)
    print("============================================")
```

출력:

```txt
정의: 임베딩은 단어나 문장 같은 텍스트 데이터를 저차원의 연속적인 벡터로 변환하는 과정입니다. 이를 통해 컴퓨터가 텍스트를 이해하고 처리할 수 있게 합니다.
예시: "사과"라는 단어를 [0.65, -0.23, 0.17]과 같은 벡터로 표현합니다.
연관키워드: 자연어 처리, 벡터화, 딥러닝

Token
============================================
정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.
예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.
연관키워드: 자연어 처리, 임베딩, 의미론적 유사성
LLM (Large Language Model)
============================================
Semantic Search

정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.
예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.
연관키워드: 자연어 처리, 검색 알고리즘, 데이터 마이닝

Embedding
============================================
```

`config`로 `search_type`을 `similarity_score_threshold`로, `score_threshold`를 0.8로 지정해서 실행한다.

```python
config = {
    "configurable": {
        "search_type": "similarity_score_threshold",
        "search_kwargs": {
            "score_threshold": 0.8,
        },
    }
}

docs = retriever.invoke("Word2Vec은 무엇인가요?", config=config)

for doc in docs:
    print(doc.page_content)
    print("=======================================================")
```

출력:

```txt
정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.
예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.
연관키워드: 자연어 처리, 임베딩, 의미론적 유사성
LLM (Large Language Model)
=======================================================
```

`config`로 `search_type`을 `mmr`로 바꿔서 실행한다.

```python
config = {
    "configurable": {
        "search_type": "mmr",
        "search_kwargs": {"k": 2, "fetch_k": 10, "lambda_mult": 0.6},
    }
}

docs = retriever.invoke("Word2Vec은 무엇인가요?", config=config)

for doc in docs:
    print(doc.page_content)
    print("=====================================================")
```

출력:

```txt
정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.
예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.
연관키워드: 자연어 처리, 임베딩, 의미론적 유사성
LLM (Large Language Model)
=====================================================
정의: 크롤링은 자동화된 방식으로 웹 페이지를 방문하여 데이터를 수집하는 과정입니다. 이는 검색 엔진 최적화나 데이터 분석에 자주 사용됩니다.
예시: 구글 검색 엔진이 인터넷 상의 웹사이트를 방문하여 콘텐츠를 수집하고 인덱싱하는 것이 크롤링입니다.
연관키워드: 데이터 수집, 웹 스크래핑, 검색 엔진

Word2Vec
=====================================================
```

## 정리

| 기능 | 코드 |
|---|---|
| Retriever로 변환 | `db.as_retriever()` |
| 기본 검색 | `retriever.invoke(query)` (= `similarity_search`) |
| MMR 검색 | `search_type="mmr"`, `search_kwargs={"k", "fetch_k", "lambda_mult"}` |
| 점수 임계값 검색 | `search_type="similarity_score_threshold"`, `search_kwargs={"score_threshold"}` |
| 반환 개수 제한 | `search_kwargs={"k": N}` |
| 실행 시점에 옵션 변경 | `.configurable_fields(search_type=ConfigurableField(...), search_kwargs=ConfigurableField(...))` 후 `invoke(query, config={"configurable": {...}})` |

`ConfigurableField`를 쓰면 retriever 객체를 새로 만들지 않고도, 체인을 실행할 때마다 다른 검색 전략을 적용할 수 있다는 게 핵심이다.
