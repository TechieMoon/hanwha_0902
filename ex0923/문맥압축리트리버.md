# 문맥 압축 리트리버 (Contextual Compression Retriever)

기본 retriever가 반환한 문서를 그대로 쓰지 않고, 질문과 관련된 부분만 골라내거나 관련 없는 문서를 걸러내는 압축(Compression) 기법을 실습한다. LLM으로 관련 부분만 추출하는 방식, 문서 단위로 거르는 방식, 임베딩 유사도로 빠르게 거르는 방식, 그리고 이들을 파이프라인으로 조합하는 방식까지 비교한다.

```python
from dotenv import load_dotenv 

load_dotenv()
```

출력:

```txt
True
```

## 1. 결과 출력 헬퍼 함수

검색된 문서 여러 개를 구분선과 함께 보기 좋게 출력하는 함수를 정의한다.

```python
def pretty_print_docs(docs):
    print(
        f"\n{'-' * 100}\n".join(
            [f"문서 {i+1}:\n\n" + d.page_content for i, d in enumerate(docs)]
        )
    )
```

## 2. 기본 Retriever 구축

한글 용어집을 분할해서 FAISS retriever를 만든다. 기본 retriever는 질의와 관련이 있든 없든, 유사도 상위 k개 문서를 통째로 반환한다 — 문서 안에서 실제로 질문과 관련된 부분이 일부뿐이어도 문서 전체를 그대로 돌려준다는 뜻이다.

```python
from langchain_community.document_loaders import TextLoader 
from langchain_community.vectorstores import FAISS 
from langchain_openai import OpenAIEmbeddings 
from langchain_text_splitters import CharacterTextSplitter

loader = TextLoader("./data/appendix-keywords.txt", encoding="utf-8")

text_splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=0)
texts = loader.load_and_split(text_splitter)

retriever = FAISS.from_documents(texts, OpenAIEmbeddings()).as_retriever()

docs = retriever.invoke("Semantic Search에 대해서 알려줘.")

pretty_print_docs(docs)
```

출력:

```txt
문서 1:

Semantic Search

정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.
예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.
연관키워드: 자연어 처리, 검색 알고리즘, 데이터 마이닝

Embedding
----------------------------------------------------------------------------------------------------
문서 2:

정의: 키워드 검색은 사용자가 입력한 키워드를 기반으로 정보를 찾는 과정입니다. 이는 대부분의 검색 엔진과 데이터베이스 시스템에서 기본적인 검색 방식으로 사용됩니다.
예시: 사용자가 "커피숍 서울"이라고 검색하면, 관련된 커피숍 목록을 반환합니다.
연관키워드: 검색 엔진, 데이터 검색, 정보 검색

Page Rank
----------------------------------------------------------------------------------------------------
문서 3:

정의: 크롤링은 자동화된 방식으로 웹 페이지를 방문하여 데이터를 수집하는 과정입니다. 이는 검색 엔진 최적화나 데이터 분석에 자주 사용됩니다.
예시: 구글 검색 엔진이 인터넷 상의 웹사이트를 방문하여 콘텐츠를 수집하고 인덱싱하는 것이 크롤링입니다.
연관키워드: 데이터 수집, 웹 스크래핑, 검색 엔진

Word2Vec
-----------------------
... (일부 생략)
```

## 3. ContextualCompressionRetriever + LLMChainExtractor

`ContextualCompressionRetriever`는 기본 retriever(`base_retriever`)가 찾아온 문서를, `base_compressor`로 한 번 더 가공해서 반환한다. `LLMChainExtractor`는 LLM에게 "이 문서에서 질문과 관련된 부분만 추출해줘"라고 요청하는 압축기다. 압축 전(원래 retriever 결과)과 압축 후 결과를 나란히 비교한다 — 압축 후에는 문서 전체가 아니라 질문과 관련된 문장만 남는다.

```python
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    temperature=0,
    model="gpt-4o-mini"
)

# LLM을 이용해 검색된 문서에서 질문과 관련된 부분만 추출
compressor = LLMChainExtractor.from_llm(llm)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever,
)

# 원래 Retriever 결과
docs = retriever.invoke("Semantic Search 에 대해서 알려줘.")
pretty_print_docs(docs)

print("=========================================================")
print("============== LLMChainExtractor 적용 후 ==================")

# 압축된 결과
compressed_docs = compression_retriever.invoke(
    "Semantic Search 에 대해서 알려줘."
)

pretty_print_docs(compressed_docs)
```

출력:

```txt
문서 1:

Semantic Search

정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.
예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.
연관키워드: 자연어 처리, 검색 알고리즘, 데이터 마이닝

Embedding
----------------------------------------------------------------------------------------------------
문서 2:

정의: 키워드 검색은 사용자가 입력한 키워드를 기반으로 정보를 찾는 과정입니다. 이는 대부분의 검색 엔진과 데이터베이스 시스템에서 기본적인 검색 방식으로 사용됩니다.
예시: 사용자가 "커피숍 서울"이라고 검색하면, 관련된 커피숍 목록을 반환합니다.
연관키워드: 검색 엔진, 데이터 검색, 정보 검색

Page Rank
----------------------------------------------------------------------------------------------------
문서 3:

정의: 크롤링은 자동화된 방식으로 웹 페이지를 방문하여 데이터를 수집하는 과정입니다. 이는 검색 엔진 최적화나 데이터 분석에 자주 사용됩니다.
예시: 구글 검색 엔진이 인터넷 상의 웹사이트를 방문하여 콘텐츠를 수집하고 인덱싱하는 것이 크롤링입니다.
연관키워드: 데이터 수집, 웹 스크래핑, 검색 엔진

Word2Vec
-----------------------
... (일부 생략)
```

## 4. LLMChainFilter: 문서 단위로 거르기

`LLMChainFilter`는 문서의 내용을 요약/추출하지 않고, LLM에게 "이 문서가 질문과 관련 있는지"만 판단시켜서 관련 없는 문서를 통째로 걸러낸다(문서 자체는 원문 그대로 유지).

```python
from langchain_classic.retrievers.document_compressors import LLMChainFilter 

_filter = LLMChainFilter.from_llm(llm) 

compression_retriever = ContextualCompressionRetriever(
    base_compressor=_filter,
    base_retriever=retriever,
)

compressed_docs = compression_retriever.invoke(
    "Semantic Search에 대하여 알려줘."
)

pretty_print_docs(compressed_docs)
```

출력:

```txt
문서 1:

Semantic Search

정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.
예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.
연관키워드: 자연어 처리, 검색 알고리즘, 데이터 마이닝

Embedding
```

## 5. EmbeddingsFilter: 임베딩 유사도로 빠르게 거르기

`EmbeddingsFilter`는 LLM 호출 없이, 질의와 문서의 임베딩 벡터 사이의 코사인 유사도가 `similarity_threshold`(여기서는 0.86) 이상인 문서만 남긴다. LLM을 매번 호출하는 `LLMChainFilter`보다 훨씬 빠르고 저렴하다.

```python
from langchain_classic.retrievers.document_compressors import EmbeddingsFilter
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

embeddings_filter = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.86)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=embeddings_filter,
    base_retriever=retriever,
)

compressed_docs = compression_retriever.invoke(
    "Semantic Search에 대하여 알려줘."
)

pretty_print_docs(compressed_docs)
```

출력:

```txt
문서 1:

Semantic Search

정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.
예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.
연관키워드: 자연어 처리, 검색 알고리즘, 데이터 마이닝

Embedding
```

## 6. DocumentCompressorPipeline: 여러 단계 조합하기

여러 압축/필터 단계를 순서대로 이어붙일 수 있다. 여기서는 (1) `CharacterTextSplitter`로 문서를 잘게 재분할 → (2) `EmbeddingsRedundantFilter`로 서로 내용이 겹치는 중복 문서 제거 → (3) `EmbeddingsFilter`로 관련성 낮은 문서 제거 → (4) `LLMChainExtractor`로 관련 부분만 추출, 순서로 파이프라인을 구성한다.

```python
from langchain_classic.retrievers.document_compressors import DocumentCompressorPipeline 
from langchain_community.document_transformers import EmbeddingsRedundantFilter 
from langchain_text_splitters import CharacterTextSplitter 

splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=0)

redundant_filter = EmbeddingsRedundantFilter(embeddings=embeddings)

relevant_filter = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.86)

pipeline_compressor = DocumentCompressorPipeline(
    transformers=[
        splitter,
        redundant_filter,
        relevant_filter,
        LLMChainExtractor.from_llm(llm),
    ]
)
```

구성한 파이프라인 압축기로 검색을 실행한다. 여러 단계를 거치면서 최종적으로는 질문과 진짜 관련 있는, 중복 없는 핵심 내용만 남는다.

```python
compression_retriever = ContextualCompressionRetriever(
    base_compressor=pipeline_compressor,
    base_retriever=retriever,
)

compressed_docs = compression_retriever.invoke(
    "Semantic Search에 대하여 알려줘."
)

pretty_print_docs(compressed_docs)
```

출력:

```txt
문서 1:

Semantic Search

정의: 의미론적 검색은 사용자의 질의를 단순한 키워드 매칭을 넘어서 그 의미를 파악하여 관련된 결과를 반환하는 검색 방식입니다.
예시: 사용자가 "태양계 행성"이라고 검색하면, "목성", "화성" 등과 같이 관련된 행성에 대한 정보를 반환합니다.
```

## 정리

| 압축기 | 동작 방식 | 특징 |
|---|---|---|
| `LLMChainExtractor` | LLM이 문서에서 질문과 관련된 부분만 추출 | 문서 내용이 가장 정교하게 압축됨, LLM 호출 비용 발생 |
| `LLMChainFilter` | LLM이 문서 전체의 관련 여부만 판단 | 문서 원문은 그대로 유지, LLM 호출 비용 발생 |
| `EmbeddingsFilter` | 임베딩 코사인 유사도로 필터링 | LLM 호출 없이 빠르고 저렴, 문서 내용은 그대로 유지 |
| `DocumentCompressorPipeline` | 여러 압축기를 순서대로 조합 | 재분할 → 중복 제거 → 관련성 필터 → 추출 등 단계별 조합 가능 |

`ContextualCompressionRetriever(base_compressor=..., base_retriever=...)`로 기본 retriever와 압축기를 조합하는 구조는 모든 방식에서 동일하다.
