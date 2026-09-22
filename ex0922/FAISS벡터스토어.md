# FAISS 벡터 스토어 실습

FAISS(Facebook AI Similarity Search)는 메타(구 페이스북)에서 만든 고속 벡터 유사도 검색 라이브러리다. Chroma와 마찬가지로 로컬에서 바로 쓸 수 있는 벡터 스토어이며, 문서 추가/삭제, 로컬 저장/불러오기, 두 인덱스 합치기(merge), 다양한 검색 전략(MMR, 점수 임계값 등)까지 실습한다.

```python
from dotenv import load_dotenv

load_dotenv()
```

출력:

```txt
True
```

## 1. 문서 로드 및 분할

Chroma 실습과 동일하게, NLP·금융 용어집 텍스트를 600자 단위로 분할해서 준비한다.

```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=0)

loader1 = TextLoader("data/nlp-keywords.txt", encoding="utf-8")
loader2 = TextLoader("data/finance-keywords.txt", encoding="utf-8")

split_doc1 = loader1.load_and_split(text_splitter)
split_doc2 = loader2.load_and_split(text_splitter)

len(split_doc1), len(split_doc2)
```

출력:

```txt
(11, 6)
```

## 2. 빈 FAISS 인덱스 직접 만들기

FAISS는 Chroma와 달리 "인덱스"(벡터를 저장하고 검색하는 자료구조) 자체를 직접 다뤄야 할 때가 있다. `faiss.IndexFlatL2(dimension)`은 유클리드 거리(L2)로 유사도를 계산하는 가장 단순한 인덱스이며, 임베딩 벡터의 차원 수를 먼저 알아야 만들 수 있다. 임베딩 모델에 문장 하나("hello world")를 넣어보면 그 결과 벡터의 길이로 차원 수를 확인할 수 있다.

```python
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

dimension_size = len(embeddings.embed_query("hello world"))
print(dimension_size)
```

출력:

```txt
1536
```

위에서 구한 차원 수로 빈 FAISS 벡터 스토어를 만든다. `docstore`는 실제 문서 내용을 저장하는 별도 저장소이고, `index_to_docstore_id`는 FAISS 인덱스 안의 위치(정수)와 문서 ID를 연결해주는 매핑이다. 아직 아무 문서도 넣지 않은 빈 상태다.

```python
db = FAISS(
    embedding_function=embeddings,
    index=faiss.IndexFlatL2(dimension_size),
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)
```

## 3. from_documents()로 바로 벡터 스토어 만들기

실무에서는 대부분 위처럼 빈 인덱스를 직접 만들기보다, `from_documents()`로 문서를 임베딩과 함께 한 번에 넣어 벡터 스토어를 생성한다.

```python
db = FAISS.from_documents(documents=split_doc1, embedding=OpenAIEmbeddings())
```

`index_to_docstore_id`로 FAISS 인덱스 위치와 문서 ID의 매핑을 확인한다.

```python
db.index_to_docstore_id
```

출력:

```txt
{0: '6da3b602-3539-438d-8edc-d06ad2abe97e',
 1: 'cfd3b839-7b8b-4a28-862a-f88b4559e8ed',
 2: '190a6fa1-900e-4809-9586-4ecbc01af2b5',
 3: '36b505e0-33ed-4890-926e-dfc6be21f8d5',
 4: 'c028312f-6995-4b5a-97a7-a26b39ce76d1',
 5: '25dd3c1a-c5f8-465c-9f38-e8571de460c7',
 6: 'f89f3f47-cf4a-4b1c-933d-184665754d99',
 7: 'c4f73d65-8b91-40f4-9225-91d6fd653509',
 8: 'ffb573ad-1a36-411b-bd12-aa0b64317bc9',
 9: '4bd588af-7fdd-4869-a7e0-9a60d600d4d9',
 10: 'd95deef5-399f-48cc-be63-1cc348bb0d61'}
```

`docstore._dict`로 실제 저장된 문서 내용(id → Document)을 확인한다.

```python
db.docstore._dict
```

출력:

```txt
{'6da3b602-3539-438d-8edc-d06ad2abe97e': Document(id='6da3b602-3539-438d-8edc-d06ad2abe97e', metadata={'source': 'data/nlp-keywords.txt'}, page_content='Semantic Search\n\n정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.\n예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.\n연관키워드: 자연어 처리, 검색 알고리즘, 데이터 마이닝\n\nEmbedding\n\n정의: 임베딩은 단어나 문장 같은 텍스트 데이터를 저차원의 연속적인 벡터로 변환하는 과정입니다. 이를 통해 컴퓨터가 텍스트를 이해하고 처리할 수 있게 합니다.\n예시: "사과"라는 단어를 [0.65, -0.23, 0.17]과 같은 벡터로 표현합니다.\n연관키워드: 자연어 처리, 벡터화, 딥러닝\n\nToken\n\n정의: 토큰은 텍스트를 더 작은 단위로 분할하는 것을 의미합니다. 이는 일반적으로 단어, 문장, 또는 구절일 수 
... (일부 생략)
```

## 4. from_texts(): 문자열 리스트 + 커스텀 ID로 생성

Chroma와 마찬가지로 문자열 리스트만으로도 바로 벡터 스토어를 만들 수 있고, `ids`로 원하는 ID를 직접 지정할 수 있다.

```python
db2 = FAISS.from_texts(
    ["안녕하세요. 정말 반갑습니다.", "제 이름은 알파고입니다."],
    embedding=OpenAIEmbeddings(),
    metadatas=[{"source": "텍스트문서"}, {"source": "텍스트문서"}],
    ids=["doc1", "doc2"]
)
```

저장된 내용을 확인한다.

```python
db2.docstore._dict
```

출력:

```txt
{'doc1': Document(id='doc1', metadata={'source': '텍스트문서'}, page_content='안녕하세요. 정말 반갑습니다.'),
 'doc2': Document(id='doc2', metadata={'source': '텍스트문서'}, page_content='제 이름은 알파고입니다.')}
```

## 5. 유사도 검색

Chroma와 동일한 인터페이스로 유사도 검색을 할 수 있다.

```python
db.similarity_search("TF IDF에 대하여 알려줘")
```

출력:

```txt
[Document(id='f89f3f47-cf4a-4b1c-933d-184665754d99', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: TF-IDF는 문서 내에서 단어의 중요도를 평가하는 데 사용되는 통계적 척도입니다. 이는 문서 내 단어의 빈도와 전체 문서 집합에서 그 단어의 희소성을 고려합니다.\n예시: 많은 문서에서 자주 등장하지 않는 단어는 높은 TF-IDF 값을 가집니다.\n연관키워드: 자연어 처리, 정보 검색, 데이터 마이닝\n\nDeep Learning\n\n정의: 딥러닝은 인공신경망을 이용하여 복잡한 문제를 해결하는 머신러닝의 한 분야입니다. 이는 데이터에서 고수준의 표현을 학습하는 데 중점을 둡니다.\n예시: 이미지 인식, 음성 인식, 자연어 처리 등에서 딥러닝 모델이 활용됩니다.\n연관키워드: 인공신경망, 머신러닝, 데이터 분석\n\nSchema\n\n정의: 스키마는 데이터베이스나 파일의 구조를 정의하는 것으로, 데이터가 어떻게 저장되고 조직되는지에 대한 청사진을 제공합니다.\n예시: 관계형 데이터베이스의 테이블 스키마는 열 이름, 데이터 타입, 키 제약 조건 등을 정
... (일부 생략)
```

`k`로 반환 개수를 지정한다.

```python
db.similarity_search("TF IDF에 대하여 알려줘", k=2)
```

출력:

```txt
[Document(id='f89f3f47-cf4a-4b1c-933d-184665754d99', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: TF-IDF는 문서 내에서 단어의 중요도를 평가하는 데 사용되는 통계적 척도입니다. 이는 문서 내 단어의 빈도와 전체 문서 집합에서 그 단어의 희소성을 고려합니다.\n예시: 많은 문서에서 자주 등장하지 않는 단어는 높은 TF-IDF 값을 가집니다.\n연관키워드: 자연어 처리, 정보 검색, 데이터 마이닝\n\nDeep Learning\n\n정의: 딥러닝은 인공신경망을 이용하여 복잡한 문제를 해결하는 머신러닝의 한 분야입니다. 이는 데이터에서 고수준의 표현을 학습하는 데 중점을 둡니다.\n예시: 이미지 인식, 음성 인식, 자연어 처리 등에서 딥러닝 모델이 활용됩니다.\n연관키워드: 인공신경망, 머신러닝, 데이터 분석\n\nSchema\n\n정의: 스키마는 데이터베이스나 파일의 구조를 정의하는 것으로, 데이터가 어떻게 저장되고 조직되는지에 대한 청사진을 제공합니다.\n예시: 관계형 데이터베이스의 테이블 스키마는 열 이름, 데이터 타입, 키 제약 조건 등을 정
... (일부 생략)
```

`filter`로 metadata 조건에 맞는 문서만 검색한다(NLP 용어집).

```python
db.similarity_search(
    "TF IDF 에 대하여 알려줘", filter={"source": "data/nlp-keywords.txt"}, k=2
)
```

출력:

```txt
[Document(id='f89f3f47-cf4a-4b1c-933d-184665754d99', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: TF-IDF는 문서 내에서 단어의 중요도를 평가하는 데 사용되는 통계적 척도입니다. 이는 문서 내 단어의 빈도와 전체 문서 집합에서 그 단어의 희소성을 고려합니다.\n예시: 많은 문서에서 자주 등장하지 않는 단어는 높은 TF-IDF 값을 가집니다.\n연관키워드: 자연어 처리, 정보 검색, 데이터 마이닝\n\nDeep Learning\n\n정의: 딥러닝은 인공신경망을 이용하여 복잡한 문제를 해결하는 머신러닝의 한 분야입니다. 이는 데이터에서 고수준의 표현을 학습하는 데 중점을 둡니다.\n예시: 이미지 인식, 음성 인식, 자연어 처리 등에서 딥러닝 모델이 활용됩니다.\n연관키워드: 인공신경망, 머신러닝, 데이터 분석\n\nSchema\n\n정의: 스키마는 데이터베이스나 파일의 구조를 정의하는 것으로, 데이터가 어떻게 저장되고 조직되는지에 대한 청사진을 제공합니다.\n예시: 관계형 데이터베이스의 테이블 스키마는 열 이름, 데이터 타입, 키 제약 조건 등을 정
... (일부 생략)
```

이번엔 금융 용어집으로 필터링한다.

```python
db.similarity_search(
    "TF IDF 에 대하여 알려줘", filter={"source": "data/finance-keywords.txt"}, k=2
)
```

출력:

```txt
[]
```

## 6. 문서 추가

`add_documents()`로 새 문서를 추가한다. ID를 직접 지정하려면 `ids` 인자를 쓴다.

```python
from langchain_core.documents import Document

db.add_documents(
    [
        Document(
            page_content="안녕하세요! 이번엔 문서를 새로 추가해볼게요.",
            metadata={"source": "mydata.txt"},
        )
    ],
    ids=["new_doc1"],
)
```

출력:

```txt
['new_doc1']
```

방금 추가한 문서가 검색되는지 확인한다.

```python
db.similarity_search("안녕하세요",k=1)
```

출력:

```txt
[Document(id='new_doc1', metadata={'source': 'mydata.txt'}, page_content='안녕하세요! 이번엔 문서를 새로 추가해볼게요.')]
```

`add_texts()`로 텍스트를 추가한다(이번엔 `ids` 인자를 올바르게 사용).

```python
db.add_texts(
    ["이번엔 텍스트 데이터 추가합니다.", "추가한 2번째 텍스트 데이터입니다."],
    metadatas=[{"source": "mydata.txt"}, {"source": "mydata.txt"}],
    ids=["new_doc2", "new_doc3"],
)
```

출력:

```txt
['new_doc2', 'new_doc3']
```

전체 매핑을 다시 확인한다.

```python
db.index_to_docstore_id
```

출력:

```txt
{0: '6da3b602-3539-438d-8edc-d06ad2abe97e',
 1: 'cfd3b839-7b8b-4a28-862a-f88b4559e8ed',
 2: '190a6fa1-900e-4809-9586-4ecbc01af2b5',
 3: '36b505e0-33ed-4890-926e-dfc6be21f8d5',
 4: 'c028312f-6995-4b5a-97a7-a26b39ce76d1',
 5: '25dd3c1a-c5f8-465c-9f38-e8571de460c7',
 6: 'f89f3f47-cf4a-4b1c-933d-184665754d99',
 7: 'c4f73d65-8b91-40f4-9225-91d6fd653509',
 8: 'ffb573ad-1a36-411b-bd12-aa0b64317bc9',
 9: '4bd588af-7fdd-4869-a7e0-9a60d600d4d9',
 10: 'd95deef5-399f-48cc-be63-1cc348bb0d61',
 11: 'new_doc1',
 12: 'new_doc2',
 13: 'new_doc3'}
```

## 7. 문서 삭제

삭제 실습을 위해 새 텍스트 2개를 추가하고, 반환된 ID를 저장해둔다.

```python
ids = db.add_texts(
    ["삭제용 데이터를 추가합니다.", "2번째 삭제용 데이터입니다."],
    metadatas=[{"source": "mydata.txt"}, {"source": "mydata.txt"}],
    ids = ["delete_doc1", "delete_doc2"],
)
```

추가된 ID를 확인한다.

```python
print(ids)
```

출력:

```txt
['delete_doc1', 'delete_doc2']
```

`delete(ids)`로 방금 추가한 문서들을 삭제한다.

```python
db.delete(ids)
```

출력:

```txt
True
```

삭제 후 매핑에서 해당 ID들이 빠졌는지 확인한다.

```python
db.index_to_docstore_id
```

출력:

```txt
{0: '6da3b602-3539-438d-8edc-d06ad2abe97e',
 1: 'cfd3b839-7b8b-4a28-862a-f88b4559e8ed',
 2: '190a6fa1-900e-4809-9586-4ecbc01af2b5',
 3: '36b505e0-33ed-4890-926e-dfc6be21f8d5',
 4: 'c028312f-6995-4b5a-97a7-a26b39ce76d1',
 5: '25dd3c1a-c5f8-465c-9f38-e8571de460c7',
 6: 'f89f3f47-cf4a-4b1c-933d-184665754d99',
 7: 'c4f73d65-8b91-40f4-9225-91d6fd653509',
 8: 'ffb573ad-1a36-411b-bd12-aa0b64317bc9',
 9: '4bd588af-7fdd-4869-a7e0-9a60d600d4d9',
 10: 'd95deef5-399f-48cc-be63-1cc348bb0d61',
 11: 'new_doc1',
 12: 'new_doc2',
 13: 'new_doc3'}
```

## 8. 로컬 저장 및 불러오기

`save_local()`로 FAISS 인덱스를 디스크에 저장한다. Chroma처럼 자동으로 영구 저장되는 게 아니라, 이렇게 명시적으로 저장해줘야 한다.

```python
db.save_local(folder_path="faiss_db", index_name="faiss_index")
```

`load_local()`로 저장된 인덱스를 다시 불러온다. `allow_dangerous_deserialization=True`는 FAISS 인덱스 로딩에 pickle 역직렬화가 쓰이기 때문에 필요한 안전장치용 플래그로, 신뢰할 수 있는(직접 저장한) 파일일 때만 켜야 한다.

```python
loaded_db = FAISS.load_local(
    folder_path="faiss_db",
    index_name="faiss_index",
    embeddings=embeddings,
    allow_dangerous_deserialization=True,
)
```

불러온 DB의 매핑을 확인해서 기존 데이터가 그대로 살아있는지 확인한다.

```python
loaded_db.index_to_docstore_id
```

출력:

```txt
{0: '6da3b602-3539-438d-8edc-d06ad2abe97e',
 1: 'cfd3b839-7b8b-4a28-862a-f88b4559e8ed',
 2: '190a6fa1-900e-4809-9586-4ecbc01af2b5',
 3: '36b505e0-33ed-4890-926e-dfc6be21f8d5',
 4: 'c028312f-6995-4b5a-97a7-a26b39ce76d1',
 5: '25dd3c1a-c5f8-465c-9f38-e8571de460c7',
 6: 'f89f3f47-cf4a-4b1c-933d-184665754d99',
 7: 'c4f73d65-8b91-40f4-9225-91d6fd653509',
 8: 'ffb573ad-1a36-411b-bd12-aa0b64317bc9',
 9: '4bd588af-7fdd-4869-a7e0-9a60d600d4d9',
 10: 'd95deef5-399f-48cc-be63-1cc348bb0d61',
 11: 'new_doc1',
 12: 'new_doc2',
 13: 'new_doc3'}
```

## 9. 두 인덱스 합치기(merge)

이후 실습을 위해 `db` 변수에 저장된 DB를 다시 불러온다.

```python
db = FAISS.load_local(
    folder_path="faiss_db",
    index_name="faiss_index",
    embeddings=embeddings,
    allow_dangerous_deserialization=True,
)
```

금융 용어집 문서(`split_doc2`)만으로 별도의 FAISS 인덱스(`db2`)를 새로 만든다.

```python
db2 = FAISS.from_documents(documents=split_doc2, embedding=OpenAIEmbeddings())
```

`db`(NLP 용어집 기반)의 현재 매핑을 확인한다.

```python
db.index_to_docstore_id
```

출력:

```txt
{0: '6da3b602-3539-438d-8edc-d06ad2abe97e',
 1: 'cfd3b839-7b8b-4a28-862a-f88b4559e8ed',
 2: '190a6fa1-900e-4809-9586-4ecbc01af2b5',
 3: '36b505e0-33ed-4890-926e-dfc6be21f8d5',
 4: 'c028312f-6995-4b5a-97a7-a26b39ce76d1',
 5: '25dd3c1a-c5f8-465c-9f38-e8571de460c7',
 6: 'f89f3f47-cf4a-4b1c-933d-184665754d99',
 7: 'c4f73d65-8b91-40f4-9225-91d6fd653509',
 8: 'ffb573ad-1a36-411b-bd12-aa0b64317bc9',
 9: '4bd588af-7fdd-4869-a7e0-9a60d600d4d9',
 10: 'd95deef5-399f-48cc-be63-1cc348bb0d61',
 11: 'new_doc1',
 12: 'new_doc2',
 13: 'new_doc3'}
```

`db2`(금융 용어집 기반)의 매핑도 확인한다. 서로 다른 두 인덱스라는 것을 알 수 있다.

```python
db2.index_to_docstore_id
```

출력:

```txt
{0: '6b43a3e1-fcf8-480b-bba9-a9e2b65356b1',
 1: '2e536893-5c37-43d8-8c59-16b97692c8c5',
 2: '23b2bd59-6148-4692-80bc-6dad0f3f2054',
 3: '2a6bce6d-569c-4384-b2a2-9c99313a67bb',
 4: '818e6188-8c31-45c8-a6b8-f0be65618611',
 5: 'bd0d7784-632f-4fb4-a291-c98f79ebe407'}
```

`merge_from()`으로 `db2`의 모든 벡터를 `db`에 합친다. 이렇게 하면 서로 다른 시점/출처에서 만든 인덱스를 하나로 통합할 수 있다.

```python
db.merge_from(db2)
```

합쳐진 후 매핑을 확인하면 `db2`에 있던 문서들의 ID까지 포함된 것을 볼 수 있다.

```python
db.index_to_docstore_id
```

출력:

```txt
{0: '6da3b602-3539-438d-8edc-d06ad2abe97e',
 1: 'cfd3b839-7b8b-4a28-862a-f88b4559e8ed',
 2: '190a6fa1-900e-4809-9586-4ecbc01af2b5',
 3: '36b505e0-33ed-4890-926e-dfc6be21f8d5',
 4: 'c028312f-6995-4b5a-97a7-a26b39ce76d1',
 5: '25dd3c1a-c5f8-465c-9f38-e8571de460c7',
 6: 'f89f3f47-cf4a-4b1c-933d-184665754d99',
 7: 'c4f73d65-8b91-40f4-9225-91d6fd653509',
 8: 'ffb573ad-1a36-411b-bd12-aa0b64317bc9',
 9: '4bd588af-7fdd-4869-a7e0-9a60d600d4d9',
 10: 'd95deef5-399f-48cc-be63-1cc348bb0d61',
 11: 'new_doc1',
 12: 'new_doc2',
 13: 'new_doc3',
 14: '6b43a3e1-fcf8-480b-bba9-a9e2b65356b1',
 15: '2e536893-5c37
... (일부 생략)
```

## 10. Retriever로 변환해서 검색하기

이후 검색 실습을 위해 NLP·금융 용어집을 모두 포함한 새 DB를 만든다.

```python
db = FAISS.from_documents(
    documents=split_doc1 + split_doc2, embedding=OpenAIEmbeddings()
)
```

기본 retriever로 검색한다.

```python
retriever = db.as_retriever()
retriever.invoke("Word2Vec에 대하여 알려줘.")
```

출력:

```txt
[Document(id='b8d67768-ef4c-4f39-bfe0-383ceb459207', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

MMR(관련성 + 다양성)로 검색한다.

```python
retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={"k":6, "lambda_mult":0.25, "fetch_k":10}
)

retriever.invoke("Word2Vec에 대하여 알려줘.")
```

출력:

```txt
[Document(id='b8d67768-ef4c-4f39-bfe0-383ceb459207', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

`lambda_mult` 없이(기본값) `k=2`로 더 적은 결과만 MMR로 뽑는다.

```python
retriever = db.as_retriever(
    search_type="mmr",
    search_kwargs={"k":2, "fetch_k":10}
)

retriever.invoke("Word2Vec에 대하여 알려줘.")
```

출력:

```txt
[Document(id='b8d67768-ef4c-4f39-bfe0-383ceb459207', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

`search_type="similarity_score_threshold"`는 유사도 점수가 `score_threshold`(여기서는 0.8) 이상인 문서만 반환한다. 개수(`k`) 기준이 아니라 "얼마나 관련 있는가" 기준으로 결과를 거르고 싶을 때 유용하다.

```python
retriever = db.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.8}
)

retriever.invoke("Word2Vec에 대하여 알려줘.")
```

출력:

```txt
[Document(id='b8d67768-ef4c-4f39-bfe0-383ceb459207', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

`k=1`로 가장 관련도 높은 문서 하나만 받는다.

```python
retriever = db.as_retriever(
    search_kwargs={"k": 1}
)

retriever.invoke("Word2Vec에 대하여 알려줘.")
```

출력:

```txt
[Document(id='b8d67768-ef4c-4f39-bfe0-383ceb459207', metadata={'source': 'data/nlp-keywords.txt'}, page_content='정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.\n예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.\n연관키워드: 자연어 처리, 임베딩, 의미론적 유사성\nLLM (Large Language Model)\n\n정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을 의미합니다. 이러한 모델은 다양한 자연어 이해 및 생성 작업에 사용됩니다.\n예시: OpenAI의 GPT 시리즈는 대표적인 대규모 언어 모델입니다.\n연관키워드: 자연어 처리, 딥러닝, 텍스트 생성\n\nFAISS (Facebook AI Similarity Search)\n\n정의: FAISS는 페이스북에서 개발한 고속 유사성 검색 라이브러리로, 특히 대규모 벡터 집합에서 유사 벡터를 효과적으로 검색할 수 있도록 설계되었습니
... (일부 생략)
```

retriever에도 `filter`를 지정해서 특정 출처(금융 용어집)로 검색 범위를 좁힌다.

```python
retriever = db.as_retriever(
    search_kwargs={"filter": {"source": "data/finance-keywords.txt"}, "k": 2}
)

retriever.invoke("ESG에 대하여 알려줘.")
```

출력:

```txt
[Document(id='625e3e0c-35c1-4b4b-a4eb-1c79533e1325', metadata={'source': 'data/finance-keywords.txt'}, page_content='정의: ESG는 기업의 환경, 사회, 지배구조 측면을 고려하는 투자 접근 방식입니다.\n예시: S&P 500 ESG 지수는 우수한 ESG 성과를 보이는 기업들로 구성된 지수입니다.\n연관키워드: 지속가능 투자, 기업의 사회적 책임, 윤리 경영\n\nStock Buyback\n\n정의: 자사주 매입은 기업이 자사의 주식을 시장에서 다시 사들이는 것을 말합니다.\n예시: 애플은 S&P 500 기업 중 가장 큰 규모의 자사주 매입 프로그램을 운영하고 있습니다.\n연관키워드: 주주 가치, 자본 관리, 주가 부양\n\nCyclical Stocks\n\n정의: 경기순환주는 경제 상황에 따라 실적이 크게 변동하는 기업의 주식을 말합니다.\n예시: 포드, 제너럴 모터스와 같은 자동차 기업들은 S&P 500에 포함된 대표적인 경기순환주입니다.\n연관키워드: 경제 사이클, 섹터 분석, 투자 타이밍\n\nDefensive Stocks\n\n정의: 방어주는 경기 변동에 상관
... (일부 생략)
```

## 정리

| 기능 | 메서드 |
|---|---|
| 생성(빈 인덱스) | `FAISS(embedding_function=..., index=faiss.IndexFlatL2(dim), docstore=..., index_to_docstore_id={})` |
| 생성(문서로부터) | `FAISS.from_documents()` / `FAISS.from_texts()` |
| 저장/불러오기 | `save_local()` / `load_local(..., allow_dangerous_deserialization=True)` |
| 추가 | `add_documents()`, `add_texts()` |
| 삭제 | `delete(ids)` |
| 합치기 | `merge_from(other_db)` |
| 검색 | `similarity_search()`, `as_retriever()`(`mmr`, `similarity_score_threshold` 등) |

Chroma와 인터페이스(`similarity_search`, `as_retriever`, `add_texts` 등)는 대부분 동일해서 코드를 거의 그대로 옮겨 쓸 수 있다. 다만 FAISS는 저장을 `save_local()`/`load_local()`로 명시적으로 해줘야 하고, 서로 다른 인덱스를 `merge_from()`으로 합칠 수 있다는 점, 그리고 인덱스 구조(`index`, `docstore`, `index_to_docstore_id`)를 직접 다룰 수도 있다는 점이 Chroma와 다르다.
