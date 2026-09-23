# ParentDocumentRetriever (부모 문서 리트리버)

검색은 잘게 쪼갠 조각(child) 단위로 정밀하게 하되, 실제로 반환하는 내용은 더 큰 단위(parent)로 돌려주는 `ParentDocumentRetriever`를 실습한다. 부모 문서를 원본 그대로 두는 구성과, 부모 문서도 적당한 크기로 나누는 구성 두 가지를 비교한다.

```python
from dotenv import load_dotenv

load_dotenv()
```

출력:

```txt
True
```

환경 변수를 불러오고, LangSmith에서 이 실습의 추적 로그를 구분할 수 있도록 프로젝트 이름을 지정한다.

```python
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["LANGSMITH_PROJECT"] = "CH10-Retriever"
```

## 1. ParentDocumentRetriever란

`ParentDocumentRetriever`는 검색은 작은 조각(child)으로 정밀하게 하되, 실제로 반환하는 내용은 더 큰 단위(parent)로 돌려주는 retriever다. 문서를 아주 잘게 쪼개면 검색 정확도는 높아지지만 반환된 조각만으로는 맥락이 부족하고, 문서를 크게 쪼개면 맥락은 풍부하지만 검색 정확도가 떨어지는 딜레마를 해결하기 위한 방법이다.

```python
from langchain_core.stores import InMemoryStore
from langchain_community.document_loaders import TextLoader 
from langchain_chroma import Chroma 
from langchain_openai import OpenAIEmbeddings 
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_classic.retrievers import ParentDocumentRetriever
```

한글 용어집 텍스트 파일을 로드한다(아직 분할은 하지 않는다 — 분할은 retriever 내부에서 처리된다).

```python
loaders = [
    TextLoader("./data/appendix-keywords.txt", encoding="utf-8"),
]

docs = []
for loader in loaders:
    docs.extend(loader.load())
```

## 2. 부모 문서는 그대로, 자식 문서만 분할하는 구성

`child_splitter`(200자 단위)만 지정하고 `parent_splitter`는 지정하지 않으면, 원본 문서 전체가 "부모"가 되고 그것을 잘게 쪼갠 조각들이 "자식"이 된다. `vectorstore`(Chroma, 검색용 자식 벡터 저장)와 `docstore`(InMemoryStore, 부모 문서 원문 저장)를 각각 지정해서 `ParentDocumentRetriever`를 만든다.

```python
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200)

vectorstore = Chroma(
    collection_name="full_documents", embedding_function=OpenAIEmbeddings()
)

store = InMemoryStore() 

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
)
```

`add_documents()`로 문서를 추가하면, 내부적으로 각 문서를 `child_splitter`로 쪼개 벡터 스토어에 임베딩하고, 원본 문서는 `docstore`에 그대로 저장한다.

```python
retriever.add_documents(docs, ids=None, add_to_docstore=True)
```

`store.yield_keys()`로 `docstore`에 저장된 부모 문서들의 ID를 확인한다. 문서를 통째로 하나만 넣었으므로 ID가 1개다.

```python
list(store.yield_keys())
```

출력:

```txt
['27e1f935-2bc7-4cdd-add2-87c093752733']
```

## 3. 검색은 자식 단위로, 반환은 부모 단위로

`vectorstore.similarity_search()`로 벡터 스토어(자식 조각들)에서 직접 검색해본다 — 이건 `ParentDocumentRetriever`를 거치지 않은, 순수 자식 조각 검색 결과다.

```python
sub_docs = vectorstore.similarity_search("Word2Vec")
```

자식 조각 검색 결과를 출력한다. 200자 단위로 잘린 짧은 조각이다.

```python
print(sub_docs[0].page_content)
```

출력:

```txt
정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.
예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.
연관키워드: 자연어 처리, 임베딩, 의미론적 유사성
```

이번엔 `retriever.invoke()`로 `ParentDocumentRetriever`를 통해 검색한다.

```python
retrieved_docs = retriever.invoke("Word2Vec")
```

결과 문서의 길이를 확인해보면, 자식 조각(200자)이 아니라 그 조각이 속한 원본 문서 전체(부모, 훨씬 김)가 반환된 것을 알 수 있다.

```python
print(
    f"문서의 길이: {len(retrieved_docs[0].page_content)}",
    end="\n\n============================\n\n",
)

print(retrieved_docs[0].page_content[2000:2500])
```

출력:

```txt
문서의 길이: 5733

============================

 컴퓨팅을 도입하여 데이터 저장과 처리를 혁신하는 것은 디지털 변환의 예입니다.
연관키워드: 혁신, 기술, 비즈니스 모델

Crawling

정의: 크롤링은 자동화된 방식으로 웹 페이지를 방문하여 데이터를 수집하는 과정입니다. 이는 검색 엔진 최적화나 데이터 분석에 자주 사용됩니다.
예시: 구글 검색 엔진이 인터넷 상의 웹사이트를 방문하여 콘텐츠를 수집하고 인덱싱하는 것이 크롤링입니다.
연관키워드: 데이터 수집, 웹 스크래핑, 검색 엔진

Word2Vec

정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.
예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.
연관키워드: 자연어 처리, 임베딩, 의미론적 유사성
LLM (Large Language Model)

정의: LLM은 대규모의 텍스트 데이터로 훈련된 큰 규모의 언어 모델을
```

## 4. 부모 문서도 적당히 나누는 구성

원본 문서가 너무 크면 부모 전체를 반환해도 여전히 맥락이 과하게 넘칠 수 있다. 이번엔 `parent_splitter`(1000자 단위)와 `child_splitter`(200자 단위)를 모두 지정해서, 원본 문서를 먼저 1000자 단위의 "부모 조각"들로 나누고, 그 각각을 다시 200자 단위의 "자식 조각"으로 나누는 2단계 분할 구조를 만든다.

```python
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200)
vectorstore = Chroma(
    collection_name="split_parents", embedding_function=OpenAIEmbeddings()
)

store = InMemoryStore()
```

`parent_splitter`와 `child_splitter`를 모두 지정해서 retriever를 생성한다.

```python
retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)
```

문서를 추가한다. 이번엔 원본 문서 자체가 아니라, `parent_splitter`로 나뉜 여러 개의 부모 조각이 각각 `docstore`에 저장된다.

```python
retriever.add_documents(docs)
```

`docstore`에 저장된 부모 조각의 개수를 센다. 원본 문서 하나가 1000자 단위로 여러 조각(부모)으로 나뉘었기 때문에 앞서(1개)보다 개수가 늘어난다.

```python
len(list(store.yield_keys()))
```

출력:

```txt
7
```

자식 조각 단위로 직접 검색해본다.

```python
sub_docs = vectorstore.similarity_search("Word2Vec")
print(sub_docs[0].page_content)
```

출력:

```txt
정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.
예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.
연관키워드: 자연어 처리, 임베딩, 의미론적 유사성
```

`retriever.invoke()`로 검색하면, 이번엔 원본 문서 전체가 아니라 1000자 단위로 나뉜 부모 조각이 반환된다 — 원본 문서보다는 짧지만 자식 조각보다는 맥락이 풍부하다.

```python
retrieved_docs = retriever.invoke("Word2Vec")
print(retrieved_docs[0].page_content)
```

출력:

```txt
정의: 트랜스포머는 자연어 처리에서 사용되는 딥러닝 모델의 한 유형으로, 주로 번역, 요약, 텍스트 생성 등에 사용됩니다. 이는 Attention 메커니즘을 기반으로 합니다.
예시: 구글 번역기는 트랜스포머 모델을 사용하여 다양한 언어 간의 번역을 수행합니다.
연관키워드: 딥러닝, 자연어 처리, Attention

HuggingFace

정의: HuggingFace는 자연어 처리를 위한 다양한 사전 훈련된 모델과 도구를 제공하는 라이브러리입니다. 이는 연구자와 개발자들이 쉽게 NLP 작업을 수행할 수 있도록 돕습니다.
예시: HuggingFace의 Transformers 라이브러리를 사용하여 감정 분석, 텍스트 생성 등의 작업을 수행할 수 있습니다.
연관키워드: 자연어 처리, 딥러닝, 라이브러리

Digital Transformation

정의: 디지털 변환은 기술을 활용하여 기업의 서비스, 문화, 운영을 혁신하는 과정입니다. 이는 비즈니스 모델을 개선하고 디지털 기술을 통해 경쟁력을 높이는 데 중점을 둡니다.
예시: 기업이 클라우드 컴퓨팅을 도입하여 데이터 저장과 처리를 혁신하는 것은 디지털 변환의 예입니다.
연관키워드: 혁신, 기술, 비즈니스 모델

Crawling

정의: 크롤링은 자동화된 방식으로 웹 페이지를 방문하여 데이터를 수집하는 과정입니다. 이는 검색 엔진 최적화나 데이터 분석에 자주 사용됩니다.
예시: 구글 검색 엔진이 인터넷 상의 웹사이트를 방문하여 콘텐츠를 수집하고 인덱싱하는 것이 크롤링입니다.
연관키워드: 데이터 수집, 웹 스크래핑, 검색 엔진

Word2Vec

정의: Word2Vec은
... (일부 생략)
```

여러 자식 조각들의 검색 결과를 순서대로 출력해서 비교한다.

```python
for sub_doc in sub_docs:
    print(sub_doc.page_content)
    print("=" * 20)
```

출력:

```txt
정의: Word2Vec은 단어를 벡터 공간에 매핑하여 단어 간의 의미적 관계를 나타내는 자연어 처리 기술입니다. 이는 단어의 문맥적 유사성을 기반으로 벡터를 생성합니다.
예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.
연관키워드: 자연어 처리, 임베딩, 의미론적 유사성
====================
예시: Word2Vec 모델에서 "왕"과 "여왕"은 서로 가까운 위치에 벡터로 표현됩니다.
연관키워드: 자연어 처리, 임베딩, 의미론적 유사성
LLM (Large Language Model)
====================
Crawling

정의: 크롤링은 자동화된 방식으로 웹 페이지를 방문하여 데이터를 수집하는 과정입니다. 이는 검색 엔진 최적화나 데이터 분석에 자주 사용됩니다.
예시: 구글 검색 엔진이 인터넷 상의 웹사이트를 방문하여 콘텐츠를 수집하고 인덱싱하는 것이 크롤링입니다.
연관키워드: 데이터 수집, 웹 스크래핑, 검색 엔진

Word2Vec
====================
TF-IDF (Term Frequency-Inverse Document Frequency)
====================
```

## 정리

| 구성 | parent_splitter | 검색 단위 | 반환 단위 |
|---|---|---|---|
| 원본 그대로 부모 | 지정 안 함 | 200자 자식 조각 | 원본 문서 전체 |
| 부모도 분할 | 1000자 단위 | 200자 자식 조각 | 1000자 부모 조각 |

| 구성 요소 | 역할 |
|---|---|
| `vectorstore` | 자식 조각을 임베딩해서 저장 — 실제 유사도 검색이 일어나는 곳 |
| `docstore` (`InMemoryStore`) | 부모 문서(또는 부모 조각)의 원문을 저장 |
| `child_splitter` | 검색 정밀도를 위해 문서를 잘게 쪼개는 분할기 |
| `parent_splitter` (선택) | 부모 단위 자체도 적당한 크기로 미리 나누는 분할기 |

"검색은 작게, 반환은 크게"가 `ParentDocumentRetriever`의 핵심 아이디어다. `parent_splitter`를 생략하면 맥락이 가장 풍부하지만(원본 전체) 문서가 길면 비효율적이고, `parent_splitter`를 지정하면 검색 정밀도와 반환 맥락 사이의 균형을 세밀하게 조절할 수 있다.
