# Chroma 벡터 스토어 실습

Chroma는 로컬에서 바로 실행할 수 있는 오픈소스 벡터 데이터베이스다. 문서를 저장/조회/수정/삭제하는 기본 CRUD, 로컬 디스크에 영구 저장(persist)하기, 유사도 검색과 metadata 필터링, `Retriever`로 변환해서 MMR(다양성을 고려한 검색) 쓰기까지 실습한다. 후반부에는 이미지까지 함께 다루는 멀티모달(Multimodal) 검색도 다룬다.

```python
from dotenv import load_dotenv

load_dotenv()
```

출력:

```txt
True
```

## 1. 문서 로드 및 분할

두 개의 한글 용어집 텍스트 파일(NLP 용어, 금융 용어)을 각각 불러와서 600자 단위로 분할한다.

```python
from langchain_community.document_loaders import TextLoader
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=0)

loader1 = TextLoader("data/nlp-keywords.txt", encoding="utf-8")
loader2 = TextLoader("data/finance-keywords.txt", encoding="utf-8")

split_doc1 = loader1.load_and_split(text_splitter)
split_doc2 = loader2.load_and_split(text_splitter)

# 각각 몇 개의 조각으로 나뉘었는지 확인
len(split_doc1), len(split_doc2)
```

출력:

```txt
C:\Users\user\AppData\Local\Temp\ipykernel_9472\1429941262.py:1: DeprecationWarning: `langchain-community` is being sunset and is no longer actively maintained. See https://github.com/langchain-ai/langchain-community/issues/674 for details and migration guidance toward standalone integration packages.
  from langchain_community.document_loaders import TextLoader

(11, 6)
```

## 2. Chroma DB 생성(인메모리)

`Chroma.from_documents()`로 문서를 임베딩해서 바로 벡터 DB를 만든다. `persist_directory`를 지정하지 않으면 메모리에만 존재하고, 노트북(프로세스)이 종료되면 사라진다. `collection_name`은 하나의 Chroma 저장소 안에서 데이터를 구분하는 이름표 역할을 한다.

```python
db = Chroma.from_documents(
    documents=split_doc1,
    embedding=OpenAIEmbeddings(),
    collection_name="my_db"
)
```

## 3. 로컬 디스크에 영구 저장하기

`persist_directory`를 지정하면 벡터 데이터가 해당 경로(`./chroma_db`)에 실제 파일로 저장되어, 다음에 다시 불러와 쓸 수 있다.

```python
DB_PATH = "./chroma_db"

persist_db = Chroma.from_documents(
    documents=split_doc1,
    embedding=OpenAIEmbeddings(),
    persist_directory=DB_PATH,
    collection_name="my_db"
)
```

저장된 DB를 다시 불러올 때는 `from_documents()`가 아니라 `Chroma(...)` 생성자에 같은 `persist_directory`와 `collection_name`을 지정한다. (새로 임베딩하는 게 아니라 이미 저장된 데이터를 그대로 불러오는 것이다.)

```python
persist_db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=OpenAIEmbeddings(),
    collection_name="my_db",
)
```

`get()`으로 저장된 데이터(문서 내용, ID, metadata 등)를 확인한다.

```python
persist_db.get()
```

출력:

```txt
{'ids': ['379be493-af9d-46d6-a275-505a1e80b758',
  'd52b6ce5-93b2-46e6-806d-683b7ecaa226',
  '88e1938e-b55b-4607-9672-cac6471f45c2',
  '52728813-d42a-49a7-82d3-f1573479d8f3',
  '11d6e47b-9577-4b92-a6d8-8de85f65439b',
  '32a37ccf-e374-4445-a661-5c0b5539499f',
  '8893c3fb-1438-4b71-a482-986b16b50675',
  '6421242f-75ae-4596-b574-312bb46ab5e6',
  '62ab29f3-38f4-4d1c-b6c4-95f400794ede',
  '764f8ea6-a13b-4f9d-9719-6897092e5135',
  '5e647cfb-989f-4960-87b3-7a5d3be4affe',
  '27d2361d-c0c7-4010-a6e4-084c17abd703',
  '3e24fc07-51f5-4566-ae5c-309b2c7f4fdd',
  'eef988f8-0c4f-42f8-950c-8d0aea2ffda1',
  '63
... (일부 생략)
```

같은 `persist_directory`라도 `collection_name`이 다르면 완전히 별개의 컬렉션이다. `my_db2`는 아직 아무 데이터도 넣지 않았으므로 `get()` 결과가 비어 있다.

```python
persist_db2 = Chroma(
    persist_directory=DB_PATH,
    embedding_function=OpenAIEmbeddings(),
    collection_name="my_db2",
)

persist_db2.get()
```

출력:

```txt
{'ids': [],
 'embeddings': None,
 'documents': [],
 'uris': None,
 'included': ['metadatas', 'documents'],
 'data': None,
 'metadatas': []}
```

## 4. from_texts(): 문자열 리스트로 바로 DB 만들기

`Document` 객체 없이, 문자열 리스트만으로도 바로 벡터 DB를 만들 수 있다.

```python
db2 = Chroma.from_texts(
    ["안녕하세요. 정말 반갑습니다.", "제 이름은 올트먼입니다."],
    embedding=OpenAIEmbeddings(),
)
```

`get()`으로 잘 들어갔는지 확인한다.

```python
db2.get()
```

출력:

```txt
{'ids': ['1d7c043c-0dc7-46dc-8f52-2873ce2e07f1',
  'f43ab40e-9939-46fb-acab-b6cfcc65e890'],
 'embeddings': None,
 'documents': ['안녕하세요. 정말 반갑습니다.', '제 이름은 올트먼입니다.'],
 'uris': None,
 'included': ['metadatas', 'documents'],
 'data': None,
 'metadatas': [None, None]}
```

## 5. 유사도 검색(similarity_search)

가장 기본적인 검색: 질의와 의미적으로 가까운 문서를 반환한다(기본 4개).

```python
db.similarity_search("TF IDF에 대하여 알려줘")
```

출력:

```txt
[Document(id='4822232c-3076-4e28-a65d-911560e36c2a', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: TF-IDF는 문서 내에서 단어의 중요도를 평가하는 데 사용되는 통계적 척도입니다. 이는 문서 내 단어의 빈도와 전체 문서 집합에서 그 단어의 희소성을 고려합니다.\n예시: 많은 문서에서 자주 등장하지 않는 단어는 높은 TF-IDF 값을 가집니다.\n연관키워드: 자연어 처리, 정보 검색, 데이터 마이닝\n\nDeep Learning\n\n정의: 딥러닝은 인공신경망을 이용하여 복잡한 문제를 해결하는 머신러닝의 한 분야입니다. 이는 데이터에서 고수준의 표현을 학습하는 데 중점을 둡니다.\n예시: 이미지 인식, 음성 인식, 자연어 처리 등에서 딥러닝 모델이 활용됩니다.\n연관키워드: 인공신경망, 머신러닝, 데이터 분석\n\nSchema\n\n정의: 스키마는 데이터베이스나 파일의 구조를 정의하는 것으로, 데이터가 어떻게 저장되고 조직되는지에 대한 청사진을 제공합니다.\n예시: 관계형 데이터베이스의 테이블 스키마는 열 이름, 데이터 타입, 키 제약 조건 등을 정
... (일부 생략)
```

`k`로 반환 개수를 지정할 수 있다.

```python
db.similarity_search("TF IDF에 대하여 알려줘", k=2)
```

출력:

```txt
[Document(id='4822232c-3076-4e28-a65d-911560e36c2a', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: TF-IDF는 문서 내에서 단어의 중요도를 평가하는 데 사용되는 통계적 척도입니다. 이는 문서 내 단어의 빈도와 전체 문서 집합에서 그 단어의 희소성을 고려합니다.\n예시: 많은 문서에서 자주 등장하지 않는 단어는 높은 TF-IDF 값을 가집니다.\n연관키워드: 자연어 처리, 정보 검색, 데이터 마이닝\n\nDeep Learning\n\n정의: 딥러닝은 인공신경망을 이용하여 복잡한 문제를 해결하는 머신러닝의 한 분야입니다. 이는 데이터에서 고수준의 표현을 학습하는 데 중점을 둡니다.\n예시: 이미지 인식, 음성 인식, 자연어 처리 등에서 딥러닝 모델이 활용됩니다.\n연관키워드: 인공신경망, 머신러닝, 데이터 분석\n\nSchema\n\n정의: 스키마는 데이터베이스나 파일의 구조를 정의하는 것으로, 데이터가 어떻게 저장되고 조직되는지에 대한 청사진을 제공합니다.\n예시: 관계형 데이터베이스의 테이블 스키마는 열 이름, 데이터 타입, 키 제약 조건 등을 정
... (일부 생략)
```

`filter`로 특정 조건(여기서는 출처 파일)에 맞는 문서만 검색 대상으로 좁힐 수 있다. NLP 용어집에서만 검색한다.

```python
db.similarity_search(
    "TF IDF에 대하여 알려줘", filter={"source": "data/nlp-keywords.txt"}, k=2
)
```

출력:

```txt
[Document(id='4822232c-3076-4e28-a65d-911560e36c2a', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: TF-IDF는 문서 내에서 단어의 중요도를 평가하는 데 사용되는 통계적 척도입니다. 이는 문서 내 단어의 빈도와 전체 문서 집합에서 그 단어의 희소성을 고려합니다.\n예시: 많은 문서에서 자주 등장하지 않는 단어는 높은 TF-IDF 값을 가집니다.\n연관키워드: 자연어 처리, 정보 검색, 데이터 마이닝\n\nDeep Learning\n\n정의: 딥러닝은 인공신경망을 이용하여 복잡한 문제를 해결하는 머신러닝의 한 분야입니다. 이는 데이터에서 고수준의 표현을 학습하는 데 중점을 둡니다.\n예시: 이미지 인식, 음성 인식, 자연어 처리 등에서 딥러닝 모델이 활용됩니다.\n연관키워드: 인공신경망, 머신러닝, 데이터 분석\n\nSchema\n\n정의: 스키마는 데이터베이스나 파일의 구조를 정의하는 것으로, 데이터가 어떻게 저장되고 조직되는지에 대한 청사진을 제공합니다.\n예시: 관계형 데이터베이스의 테이블 스키마는 열 이름, 데이터 타입, 키 제약 조건 등을 정
... (일부 생략)
```

이번엔 반대로 금융 용어집에서만 검색한다. "TF-IDF"는 NLP 개념이라 금융 문서 안에서는 관련 있는 내용이 나오지 않거나 결과가 비어 있을 수 있다.

```python
db.similarity_search(
    "TF IDF에 대하여 알려줘", filter={"source": "data/finance-keywords.txt"}, k=2
)
```

출력:

```txt
[]
```

## 6. 문서 추가·조회·삭제(CRUD)

`add_documents()`로 `Document` 객체를 추가할 수 있다. `id`를 직접 지정하면 나중에 그 ID로 조회·삭제·덮어쓰기가 가능하다.

```python
from langchain_core.documents import Document

db.add_documents(
    [
        Document(
            page_content="안녕하세요! 이번엔 문서를 새로 추가해볼게요.",
            metadata={"source": "mydata.txt"},
            id="1"
        )
    ]
)
```

출력:

```txt
['1']
```

방금 추가한 문서를 ID로 조회한다.

```python
db.get("1")
```

출력:

```txt
{'ids': ['1'],
 'embeddings': None,
 'documents': ['안녕하세요! 이번엔 문서를 새로 추가해볼게요.'],
 'uris': None,
 'included': ['metadatas', 'documents'],
 'data': None,
 'metadatas': [{'source': 'mydata.txt'}]}
```

`add_texts()`에 이미 존재하는 ID(`"1"`)를 다시 지정하면, 새 문서를 추가하는 게 아니라 기존 문서를 덮어쓴다(upsert). 여기서는 `"1"`을 덮어쓰고 `"2"`는 새로 추가한다.

```python
db.add_texts(
    ["이전에 추가한 Document를 덮어쓰겠습니다.", "덮어 쓴 결과가 어떤가요?"],
    metadatas=[{"source": "mydata.txt"}, {"source": "mydata.txt"}],
    ids=["1", "2"],
)
```

출력:

```txt
['1', '2']
```

`"1"`의 내용이 덮어쓰기 된 것을 확인한다.

```python
db.get(["1"])
```

출력:

```txt
{'ids': ['1'],
 'embeddings': None,
 'documents': ['이전에 추가한 Document를 덮어쓰겠습니다.'],
 'uris': None,
 'included': ['metadatas', 'documents'],
 'data': None,
 'metadatas': [{'source': 'mydata.txt'}]}
```

`delete(ids=...)`로 특정 ID의 문서를 삭제한다.

```python
db.delete(ids=["1"])
```

`"1"`은 삭제되어 결과에서 빠지고, `"2"`만 남아있는 것을 확인한다.

```python
db.get(["1", "2"])
```

출력:

```txt
{'ids': ['2'],
 'embeddings': None,
 'documents': ['덮어 쓴 결과가 어떤가요?'],
 'uris': None,
 'included': ['metadatas', 'documents'],
 'data': None,
 'metadatas': [{'source': 'mydata.txt'}]}
```

`get(where=...)`로 metadata 조건에 맞는 문서를 조회할 수도 있다(ID 대신 metadata 기준 검색).

```python
db.get(where={"source": "mydata.txt"})
```

출력:

```txt
{'ids': ['2'],
 'embeddings': None,
 'documents': ['덮어 쓴 결과가 어떤가요?'],
 'uris': None,
 'included': ['metadatas', 'documents'],
 'data': None,
 'metadatas': [{'source': 'mydata.txt'}]}
```

`reset_collection()`으로 컬렉션 안의 데이터를 전부 초기화한다.

```python
db.reset_collection()
```

초기화되어 빈 상태인지 확인한다.

```python
db.get()
```

출력:

```txt
{'ids': [],
 'embeddings': None,
 'documents': [],
 'uris': None,
 'included': ['metadatas', 'documents'],
 'data': None,
 'metadatas': []}
```

## 7. Retriever로 변환해서 검색하기

이번엔 NLP·금융 용어집 문서를 모두 합쳐서 새 컬렉션(`nlp`)을 만든다.

```python
db = Chroma.from_documents(
    documents=split_doc1 + split_doc2,
    embedding=OpenAIEmbeddings(),
    collection_name="nlp",
)
```

`as_retriever()`로 벡터 스토어를 LangChain의 `Retriever` 인터페이스로 변환하면, 체인(Chain)에 곧바로 연결해서 쓸 수 있다. 기본 설정은 `similarity_search`와 동일하게 동작한다.

```python
retriever = db.as_retriever()
retriever.invoke("Word2Vec에 대하여 알려줘")
```

출력:

```txt
[Document(id='2de213b6-e0ad-4115-9a19-4b50505ce1fb', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

`search_type="mmr"`(Maximal Marginal Relevance)은 검색 결과가 서로 너무 비슷한 내용으로만 채워지지 않도록, 관련성과 다양성을 함께 고려해서 문서를 고른다.

- `fetch_k`: 먼저 넉넉하게 후보를 몇 개 가져올지.
- `k`: 그중 최종적으로 몇 개를 고를지.
- `lambda_mult`: 관련성(1에 가까울수록 중시) vs 다양성(0에 가까울수록 중시) 비율.

```python
retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "lambda_mult": 0.25, "fetch_k": 10}
)

retriever.invoke("Word2Vec에 대하여 알려줘")
```

출력:

```txt
[Document(id='2de213b6-e0ad-4115-9a19-4b50505ce1fb', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

같은 컬렉션을 다시 생성해서 아래 검색 실습들을 이어간다.

```python
db = Chroma.from_documents(
    documents=split_doc1 + split_doc2,
    embedding=OpenAIEmbeddings(),
    collection_name="nlp",
)
```

기본 retriever로 다시 검색한다.

```python
retriever = db.as_retriever()
retriever.invoke("Word2Vec에 대해 알려줘")
```

출력:

```txt
[Document(id='2de213b6-e0ad-4115-9a19-4b50505ce1fb', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

MMR 검색도 다시 확인한다.

```python
retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={"k":6, "lambda_mult":0.25, "fetch_k":10},
)

retriever.invoke("Word2Vec에 대해 알려줘")
```

출력:

```txt
[Document(id='2de213b6-e0ad-4115-9a19-4b50505ce1fb', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

`lambda_mult` 없이(기본값 사용) `k=2`로 더 적은 수의 결과만 MMR로 뽑아본다.

```python
retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={"k":2,
                   "fetch_k":10}
)

retriever.invoke("Word2Vec에 대하여 알려줘")
```

출력:

```txt
[Document(id='2de213b6-e0ad-4115-9a19-4b50505ce1fb', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

`k=1`로 가장 관련도 높은 문서 하나만 받아본다.

```python
retriever = db.as_retriever(search_kwargs={"k":1})

retriever.invoke("Word2Vec에 대하여 알려줘")
```

출력:

```txt
[Document(id='bf251dbb-0dc9-4d12-a65d-cf5659de23c3', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

retriever에도 `filter`를 지정해서 특정 출처 문서로 검색 범위를 좁힐 수 있다. 금융 용어집에서 "ESG"를 검색한다.

```python
retriever = db.as_retriever(
    search_kwargs={"filter": {"source":"data/finance-keywords.txt"}, "k":2}
)

retriever.invoke("ESG에 대하여 알려줘")
```

출력:

```txt
[Document(id='83888341-8165-41ee-a551-f870dcbb83a6', metadata={'source': 'data/finance-keywords.txt'}, page_content='정의: ESG는 기업의 환경, 사회, 지배구조 측면을 고려하는 투자 접근 방식입니다.\n예시: S&P 500 ESG 지수는 우수한 ESG 성과를 보이는 기업들로 구성된 지수입니다.\n연관키워드: 지속가능 투자, 기업의 사회적 책임, 윤리 경영\n\nStock Buyback\n\n정의: 자사주 매입은 기업이 자사의 주식을 시장에서 다시 사들이는 것을 말합니다.\n예시: 애플은 S&P 500 기업 중 가장 큰 규모의 자사주 매입 프로그램을 운영하고 있습니다.\n연관키워드: 주주 가치, 자본 관리, 주가 부양\n\nCyclical Stocks\n\n정의: 경기순환주는 경제 상황에 따라 실적이 크게 변동하는 기업의 주식을 말합니다.\n예시: 포드, 제너럴 모터스와 같은 자동차 기업들은 S&P 500에 포함된 대표적인 경기순환주입니다.\n연관키워드: 경제 사이클, 섹터 분석, 투자 타이밍\n\nDefensive Stocks\n\n정의: 방어주는 경기 변동에 상관
... (일부 생략)
```

## 8. 멀티모달(이미지) 검색 준비: 이미지 데이터셋 다운로드

여기서부터는 텍스트가 아니라 "이미지"를 검색 대상으로 다루는 멀티모달 벡터 검색을 실습한다. HuggingFace의 COCO 데이터셋(`detection-datasets/coco`)에서 이미지 20장을 스트리밍으로 내려받아 `tmp` 폴더에 저장하고, 각 이미지와 라벨(사물 종류)을 그리드로 미리 확인한다.

```python
import os
from datasets import load_dataset
from matplotlib import pyplot as plt

dataset = load_dataset(
    path="detection-datasets/coco", name="default", split="train", streaming=True
)

IMAGE_FOLDER = "tmp"
N_IMAGES = 20

plot_cols = 5
plot_rows = N_IMAGES // plot_cols
fig, axes = plt.subplots(plot_rows, plot_cols, figsize=(plot_rows * 2, plot_cols * 2))
axes = axes.flatten()

dataset_iter = iter(dataset)
os.makedirs(IMAGE_FOLDER, exist_ok=True)
for i in range(N_IMAGES):
    data = next(dataset_iter)
    image = data["image"]
    label = data["objects"]["category"][0]

    axes[i].imshow(image)
    axes[i].set_title(label, fontsize=8)
    axes[i].axis("off")

    image.save(f"{IMAGE_FOLDER}/{i}.jpg")

plt.tight_layout()
plt.show()
```

출력:

```txt
Resolving data files:   0%|          | 0/40 [00:00<?, ?it/s]
<Figure size 800x1000 with 20 Axes>
```

## 9. OpenCLIP 임베딩 모델 준비

이미지와 텍스트를 "같은 벡터 공간"에 임베딩할 수 있는 CLIP 계열 모델을 사용한다. `open_clip.list_pretrained()`로 어떤 사전학습 모델(model_name, checkpoint) 조합을 쓸 수 있는지 먼저 확인한다.

```python
import open_clip
import pandas as pd

pd.DataFrame(open_clip.list_pretrained(), columns=["model_name", "checkpoint"]).head(10)
```

출력:

```txt
model_name     checkpoint
0       RN50         openai
1       RN50        yfcc15m
2       RN50          cc12m
3      RN101         openai
4      RN101        yfcc15m
5     RN50x4         openai
6    RN50x16         openai
7    RN50x64         openai
8   ViT-B-32         openai
9   ViT-B-32  laion400m_e31
```

`OpenCLIPEmbeddings`로 이미지·텍스트 겸용 임베딩 함수를 준비한다. 이 임베딩 함수는 이미지(`embed_image`)와 텍스트(`embed_documents`) 양쪽 모두를 벡터로 변환할 수 있어서, 서로 다른 두 종류의 데이터를 같은 잣대로 비교할 수 있다.

```python
from langchain_experimental.open_clip import OpenCLIPEmbeddings

image_embedding_function = OpenCLIPEmbeddings(
    model_name="ViT-H-14-378-quickgelu", checkpoint="dfn5b"
)
```

출력:

```txt
C:\Users\user\AppData\Local\Temp\ipykernel_8300\365069730.py:1: DeprecationWarning: `langchain-experimental` is being sunset and is no longer actively maintained. See https://github.com/langchain-ai/langchain-experimental/issues/87 for details.
  from langchain_experimental.open_clip import OpenCLIPEmbeddings
```

앞서 저장한 이미지 파일들의 경로를 리스트로 모은다.

```python
# 이미지의 경로를 리스트로 저장
image_uris = sorted(
    [
        os.path.join("tmp", image_name)
        for image_name in os.listdir("tmp")
        if image_name.endswith(".jpg")
    ]
)

image_uris
```

출력:

```txt
['tmp\\0.jpg',
 'tmp\\1.jpg',
 'tmp\\10.jpg',
 'tmp\\11.jpg',
 'tmp\\12.jpg',
 'tmp\\13.jpg',
 'tmp\\14.jpg',
 'tmp\\15.jpg',
 'tmp\\16.jpg',
 'tmp\\17.jpg',
 'tmp\\18.jpg',
 'tmp\\19.jpg',
 'tmp\\2.jpg',
 'tmp\\3.jpg',
 'tmp\\4.jpg',
 'tmp\\5.jpg',
 'tmp\\6.jpg',
 'tmp\\7.jpg',
 'tmp\\8.jpg',
 'tmp\\9.jpg']
```

`SimpleMultiModal`은 `langchain_teddynote.models.MultiModal`을 대체하기 위해 직접 만든 클래스다. 이미지 파일을 열어서 base64로 인코딩한 뒤, 시스템 프롬프트·유저 프롬프트와 함께 `image_url` 콘텐츠 블록으로 감싸 멀티모달 메시지를 만들고 `llm.invoke()`로 호출한다. `invoke(image_path, display_image=...)` 인터페이스는 기존과 동일하게 유지해서, 아래 코드는 고칠 필요가 없다.

```python
import base64

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from IPython.display import Image as IPImage, display


class SimpleMultiModal:
    """langchain_teddynote.models.MultiModal을 대체하는 최소 구현체.
    이미지를 base64로 인코딩해서 시스템/유저 프롬프트와 함께 멀티모달 메시지로 LLM에 전달한다."""

    def __init__(self, model, system_prompt=None, user_prompt=None):
        self.model = model
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt

    def encode_image(self, image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def invoke(self, image_path, system_prompt=None, user_prompt=None, display_image=True):
        system_prompt = system_prompt or self.system_prompt
        user_prompt = user_prompt or self.user_prompt

        if display_image:
            display(IPImage(filename=image_path))

        image_b64 = self.encode_image(image_path)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=[
                    {"type": "text", "text": user_prompt},
                    {
               
# ... (일부 생략)
```

첫 번째 이미지로 잘 동작하는지 테스트해본다.

```python
# 이미지 설명 생성
model.invoke(image_uris[0])
```

출력:

```txt
<IPython.core.display.Image object>
'Colorful lunchboxes hold fruit, bread, meat, and broccoli.'
```

20장 전체 이미지에 대해 설명을 생성해서 `descriptions` 딕셔너리(이미지 경로 → 설명 텍스트)에 저장한다. `display_image=False`로 매번 이미지를 화면에 띄우지 않도록 한다.

```python
# 이미지 설명
descriptions = dict()

for image_uri in image_uris:
    descriptions[image_uri] = model.invoke(image_uri, display_image=False)

# 생성된 결과물 출력
descriptions
```

출력:

```txt
{'tmp\\0.jpg': 'Colorful lunchboxes hold fruit, bread, broccoli, and meat.',
 'tmp\\1.jpg': 'Two giraffes stand among trees in a sunny enclosure.',
 'tmp\\10.jpg': 'Two giraffes stand together among leafy trees.',
 'tmp\\11.jpg': 'Vintage motorcycle parked outdoors.',
 'tmp\\12.jpg': 'A puppy rests beside a bicycle on a cobblestone street.',
 'tmp\\13.jpg': 'Skateboarders perform tricks in a graffiti-covered park.',
 'tmp\\14.jpg': 'An owl candleholder beside an ornate mantel clock.',
 'tmp\\15.jpg': 'Two airplanes fly closely together in a cloudy sky.',
 'tmp\\16.jpg': 'A man rides a vintage 
... (일부 생략)
```

20장의 원본 이미지와 각각에 대해 생성된 설명을 4x5 그리드로 함께 시각화해서 결과를 한눈에 확인한다.

```python
import os
from PIL import Image
import matplotlib.pyplot as plt

# 원본 이미지, 처리된 이미지, 텍스트 설명을 저장할 리스트 초기화
original_images = []
images = []
texts = []

# 그래프 크기 설정 (20x10 인치)
plt.figure(figsize=(20, 10))

# 'tmp' 디렉토리에 저장된 이미지 파일들을 처리
for i, image_uri in enumerate(image_uris):
    # 이미지 파일 열기 및 RGB 모드로 변환
    image = Image.open(image_uri).convert("RGB")

    # 4x5 그리드의 서브플롯 생성
    plt.subplot(4, 5, i + 1)

    # 이미지 표시
    plt.imshow(image)

    # 이미지 파일명과 설명을 제목으로 설정
    plt.title(f"{os.path.basename(image_uri)}\n{descriptions[image_uri]}", fontsize=8)

    # x축과 y축의 눈금 제거
    plt.xticks([])
    plt.yticks([])

    # 원본 이미지, 처리된 이미지, 텍스트 설명을 각 리스트에 추가
    original_images.append(image)
    images.append(image)
    texts.append(descriptions[image_uri])

# 서브플롯 간 간격 조정
plt.tight_layout()
```

출력:

```txt
<Figure size 2000x1000 with 20 Axes>
```

## 11. 이미지-텍스트 임베딩 유사도 확인

방금 만든 이미지 설명 텍스트와, 원본 이미지를 각각 OpenCLIP으로 임베딩한 뒤, 두 벡터 집합 사이의 코사인 유사도(행렬 곱)를 계산한다. "이미지에 대해 생성된 설명이 실제로 그 이미지와 얼마나 잘 맞는지"를 벡터 공간에서 정량적으로 확인해볼 수 있다.

```python
import numpy as np

# 이미지와 텍스트 임베딩
# 이미지 URI를 사용하여 이미지 특징 추출
img_features = image_embedding_function.embed_image(image_uris)
# 텍스트 설명에 "This is" 접두사를 추가하고 텍스트 특징 추출
text_features = image_embedding_function.embed_documents(
    ["This is " + desc for desc in texts]
)

# 행렬 연산을 위해 리스트를 numpy 배열로 변환
img_features_np = np.array(img_features)
text_features_np = np.array(text_features)

# 유사도 계산
# 텍스트와 이미지 특징 간의 코사인 유사도를 계산
similarity = np.matmul(text_features_np, img_features_np.T)
```

유사도 행렬을 히트맵으로 시각화한다. 대각선(자기 자신의 이미지-설명 쌍)에서 유사도가 가장 높게 나온다면, 임베딩이 이미지와 그 설명을 잘 짝지어 이해하고 있다는 뜻이다.

```python
# 유사도 행렬을 시각화하기 위한 플롯 생성
count = len(descriptions)
plt.figure(figsize=(20, 14))

# 유사도 행렬을 히트맵으로 표시
plt.imshow(similarity, vmin=0.1, vmax=0.3, cmap="coolwarm")
plt.colorbar()  # 컬러바 추가

# y축에 텍스트 설명 표시
plt.yticks(range(count), texts, fontsize=18)
plt.xticks([])  # x축 눈금 제거

# 원본 이미지를 x축 아래에 표시
for i, image in enumerate(original_images):
    plt.imshow(image, extent=(i - 0.5, i + 0.5, -1.6, -0.6), origin="lower")

# 유사도 값을 히트맵 위에 텍스트로 표시
for x in range(similarity.shape[1]):
    for y in range(similarity.shape[0]):
        plt.text(x, y, f"{similarity[y, x]:.2f}", ha="center", va="center", size=12)

# 플롯 테두리 제거
for side in ["left", "top", "right", "bottom"]:
    plt.gca().spines[side].set_visible(False)

# 플롯 범위 설정
plt.xlim([-0.5, count - 0.5])
plt.ylim([count + 0.5, -2])

# 제목 추가
plt.title("Cosine Similarity", size=20)
```

출력:

```txt
Text(0.5, 1.0, 'Cosine Similarity')
<Figure size 2000x1400 with 2 Axes>
```

## 12. Chroma에 이미지 저장 및 이미지 검색

`Chroma`는 `add_images()`로 이미지 자체를 컬렉션에 저장할 수 있다(내부적으로 OpenCLIP 임베딩 함수가 이미지를 벡터로 변환해서 저장한다).

```python
# DB 생성
image_db = Chroma(
    collection_name="multimodal",
    embedding_function=image_embedding_function,
)

# 이미지 추가
image_db.add_images(uris=image_uris)
```

출력:

```txt
['33f198ec-e95e-47b0-9b94-461c1704b1c3',
 '399abf4b-b9aa-4a72-8435-be9ac27ccff9',
 '5252e6d1-1ea3-4edc-8c97-6aafff1a784c',
 '2cbd1372-4c2a-4679-82b7-2469335dabfe',
 '8c7a5d26-f049-49d4-a2a5-775b022e5d59',
 '43a3ef19-73fa-4c3b-adad-7f9d7db39bdb',
 '79978ad2-ba57-45ad-a635-6b114be9d4b8',
 'a43bd251-67b5-4d07-8dfd-f107304ca1fe',
 'b3fd68fd-d5de-453f-b6d2-e9a248e6c2df',
 '3c723468-8e28-489f-88ec-a4ee06748755',
 '6884c399-f881-4603-9175-b42a90fcdc98',
 '5ce1f927-0ef1-4bec-b036-bf4ac7d8c8d4',
 '36597883-36ca-4387-b537-cb4a30b2862f',
 '84f5a258-97ee-4b96-9103-390a67e058b8',
 '15edcb80-6850-4743-b1db-
... (일부 생략)
```

검색된 이미지를 노트북에 바로 표시해주는 `ImageRetriever` 헬퍼 클래스를 정의한다. 내부적으로 검색 결과의 `page_content`(base64로 인코딩된 이미지 문자열)를 HTML `<img>` 태그로 감싸서 표시한다.

```python
import base64
import io
from PIL import Image
from IPython.display import HTML, display
from langchain_core.documents import Document


class ImageRetriever:
    def __init__(self, retriever):
        """
        이미지 검색기를 초기화합니다.

        인자:
        retriever: LangChain의 retriever 객체
        """
        self.retriever = retriever

    def invoke(self, query):
        """
        쿼리를 사용하여 이미지를 검색하고 표시합니다.

        인자:
        query (str): 검색 쿼리
        """
        docs = self.retriever.invoke(query)
        if docs and isinstance(docs[0], Document):
            self.plt_img_base64(docs[0].page_content)
        else:
            print("검색된 이미지가 없습니다.")
        return docs

    @staticmethod
    def resize_base64_image(base64_string, size=(224, 224)):
        """
        Base64 문자열로 인코딩된 이미지의 크기를 조정합니다.

        인자:
        base64_string (str): 원본 이미지의 Base64 문자열.
        size (tuple): (너비, 높이)로 표현된 원하는 이미지 크기.

        반환:
        str: 크기가 조정된 이미지의 Base64 문자열.
        """
        img_data = base64.b64decode(base64_string)
        img = Image.open(io.BytesIO(img_data))
        resized_img = img.resize(size, Image.LANCZOS)
        buffered = io.BytesIO()
        resized_img.save(buffe
# ... (일부 생략)
```

이미지 DB를 retriever로 변환하고, 방금 만든 `ImageRetriever`로 감싼다(`k=3`: 상위 3개 이미지를 찾는다).

```python
# Image Retriever 생성
retriever = image_db.as_retriever(search_kwargs={"k": 3})
image_retriever = ImageRetriever(retriever)
```

텍스트 질의("A Dog on the street")로 이미지를 검색한다. 질의 텍스트가 OpenCLIP 임베딩 공간에서 이미지 벡터와 직접 비교되어, 가장 관련 있는 이미지가 화면에 표시된다.

```python
# 이미지 조회
result = image_retriever.invoke("A Dog on the street")
```

출력:

```txt
<IPython.core.display.HTML object>
```

다른 질의("Motorcycle with a man")로도 검색해본다.

```python
# 이미지 조회
result = image_retriever.invoke("Motorcycle with a man")
```

출력:

```txt
<IPython.core.display.HTML object>
```

## 정리

| 기능 | 메서드 |
|---|---|
| 생성(인메모리) | `Chroma.from_documents()` / `Chroma.from_texts()` |
| 생성(영구 저장) | `Chroma.from_documents(..., persist_directory=...)` |
| 다시 불러오기 | `Chroma(persist_directory=..., collection_name=...)` |
| 조회 | `get()`, `get(ids)`, `get(where=filter)` |
| 추가 | `add_documents()`, `add_texts()`, `add_images()` |
| 수정 | 같은 `id`로 `add_texts()`/`add_documents()`를 다시 호출(upsert) |
| 삭제 | `delete(ids=...)`, `reset_collection()`(전체 초기화) |
| 검색 | `similarity_search()`, `as_retriever()`(`search_type="mmr"` 등) |

후반부에서는 텍스트뿐 아니라 이미지도 같은 벡터 공간에 임베딩할 수 있는 OpenCLIP을 이용해, 이미지에 대한 설명을 자동 생성하고(멀티모달 LLM), 이미지 자체를 Chroma에 저장한 뒤 텍스트 질의로 이미지를 검색하는 멀티모달 RAG의 기본 흐름까지 실습했다.
