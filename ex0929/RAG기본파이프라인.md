# PDF 문서 기반 RAG 기본 파이프라인

RAG(Retrieval-Augmented Generation)의 기본 흐름을 **문서 로드 → 분할 → 임베딩 → 벡터 DB 저장 → 검색기 생성 → 프롬프트 → LLM → 체인** 8단계로 나눠서 하나씩 실행해보고, 마지막에 전체 과정을 한 셀로 합쳐본다. 대상 문서는 소프트웨어정책연구소(SPRi)의 `SPRI_AI_Brief_2023년12월호_F.pdf`다.

## 1. 환경변수 로드

`.env`에서 OpenAI/LangSmith 키를 읽고, 이번 실습의 LangSmith 추적 프로젝트 이름을 `RAG-PIPELINE`으로 지정한다.

```python
from dotenv import load_dotenv
import os 

# .env에 저장한 API 키(OPENAI_API_KEY, LANGSMITH_API_KEY 등)를 환경변수로 불러온다.
load_dotenv()
# LangSmith에서 이번 실습의 실행 기록을 따로 모아보기 위한 프로젝트 이름
os.environ["LANGSMITH_PROJECT"] = "RAG-PIPELINE"
```

## 2. 사용할 도구 임포트

파이프라인 각 단계에서 쓸 클래스를 한 번에 불러온다.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 2단계: 문서 분할
from langchain_community.document_loaders import PyMuPDFLoader  # 1단계: PDF 로드
from langchain_community.vectorstores import FAISS  # 4단계: 벡터 DB
from langchain_core.output_parsers import StrOutputParser  # LLM 응답을 문자열로 변환
from langchain_core.runnables import RunnablePassthrough  # 질문을 그대로 다음 단계로 전달
from langchain_core.prompts import PromptTemplate  # 6단계: 프롬프트
from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # 7단계: LLM, 3단계: 임베딩
```

## 3. 단계 1: 문서 로드 (Load Documents)

`PyMuPDFLoader`로 PDF를 읽으면 **페이지 하나가 `Document` 하나**가 된다. 총 23페이지라서 `Document` 23개가 만들어진다.

```python
# PDF 파일을 페이지 단위 Document 리스트로 불러온다.
loader = PyMuPDFLoader("data/SPRI_AI_Brief_2023년12월호_F.pdf")
docs = loader.load() 
print(f"문서의 페이지수: {len(docs)}")
```

출력:

```txt
문서의 페이지수: 23
```

11번째 페이지(`docs[10]`)의 본문을 확인해본다.

```python
# page_content: 페이지에서 추출된 텍스트
print(docs[10].page_content)
```

출력:

```txt
SPRi AI Brief |  
2023-12월호
8
코히어, 데이터 투명성 확보를 위한 데이터 출처 탐색기 공개
n 코히어와 12개 기관이  광범위한 데이터셋에 대한 감사를 통해 원본 데이터 출처, 재라이선스 상태, 
작성자 등 다양한 정보를 제공하는 ‘데이터 출처 탐색기’ 플랫폼을 출시
n 대화형 플랫폼을 통해 개발자는 데이터셋의 라이선스 상태를 쉽게 파악할 수 있으며 데이터셋의 
구성과 계보도 추적 가능
KEY Contents
£ 데이터 출처 탐색기, 광범위한 데이터셋 정보 제공을 통해 데이터 투명성 향상
n AI 기업 코히어(Cohere)가 매사추세츠 공과⼤(MIT), 하버드⼤ 로스쿨, 카네기멜론⼤ 등 12개 기관과 
함께 2023년 10월 25일 ‘데이터 출처 탐색기(Data Provenance Explorer)’ 플랫폼을 공개
∙AI 모델 훈련에 사용되는 데이터셋의 불분명한 출처로 인해 데이터 투명성이 확보되지 않아 다양한 
법적·윤리적 문제가 발생
∙이에 연구진은 가장 널리 사용되는 2,000여 개의 미세조정 데이터셋을 감사 및 추적하여 데이터셋에 
원본 데이터소스에 대한 태그, 재라이선스(Relicensing) 상태, 작성자, 기타 데이터 속성을 지정하고 
이러한 정보에 접근할 수 있는 플랫폼을 출시
∙대화형 플랫폼 형태의 데이터 출처 탐색기를 통해 데이터셋의 라이선스 상태를 쉽게 파악할 수 있으며, 
주요 데이터셋의 구성과 데이터 계보도 추적 가능
n 연구진은 오픈소스 데이터셋에 대한 광범위한 감사를 통해 데이터 투명성에 영향을 미치는 주요 
...
```

`__dict__`로 `Document` 객체 전체를 보면, `page_content` 외에 `metadata`에 파일 경로, 전체 페이지 수, 페이지 번호 같은 정보가 함께 들어 있다.

```python
# Document 객체의 모든 속성(id, metadata, page_content 등)을 딕셔너리로 확인
docs[10].__dict__
```

출력:

```txt
{'id': None,
 'metadata': {'producer': 'Hancom PDF 1.3.0.542',
  'creator': 'Hwp 2018 10.0.0.13462',
  'creationdate': '2023-12-08T13:28:38+09:00',
  'source': 'data/SPRI_AI_Brief_2023년12월호_F.pdf',
  'file_path': 'data/SPRI_AI_Brief_2023년12월호_F.pdf',
  'total_pages': 23,
  'format': 'PDF 1.4',
  'title': '',
  'author': 'dj',
  'subject': '',
  'keywords': '',
  'moddate': '2023-12-08T13:28:38+09:00',
  'trapped': '',
  'modDate': "D:20231208132838+09'00'",
  'creationDate': "D:20231208132838+09'00'",
  'page': 10},
 'page_content': 'SPRi AI Brief |  \n2023-12월호\n8\n코히어, 데이터 투명성 확보를 위한 데이터 출처 탐색기 공개\nn 코히어와 12개 기관이  광범위한 데이터셋에 대한 감사를 통해 원본 데이터 출처, 재라이선스 상태, \n작성자 등 다양한 정보를 제공하는 ‘데이터 출처 탐색기’ 플랫폼을 출시\nn 대화형 플랫폼을 통해 개발자는 데이터셋의 라이선스 상태를 쉽게 파악할 수 있으며 데이터셋의 \n구성과 계보도 추적 가능\nKEY Contents\n£ 데이터 출처 탐색기, 광범위한 데이터셋 정보 제공 ...
 'type': 'Document'}
```

## 4. 단계 2: 문서 분할 (Split Documents)

페이지 통째로는 너무 길어서 검색 정확도가 떨어지므로, `RecursiveCharacterTextSplitter`로 500자 단위(겹침 50자)로 잘게 나눈다. 23페이지가 72개 청크(chunk)로 나뉜다.

```python
# chunk_size: 청크 하나의 최대 글자 수, chunk_overlap: 앞뒤 청크가 겹치는 글자 수(문맥이 끊기지 않게)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
split_documents = text_splitter.split_documents(docs) 
print(f"분할된 청크 수: {len(split_documents)}")
```

출력:

```txt
분할된 청크 수: 72
```

## 5. 단계 3: 임베딩 (Embedding)

각 청크를 벡터로 바꿀 임베딩 모델을 준비한다.

```python
# OpenAI 임베딩 모델 (텍스트 -> 숫자 벡터)
embeddings = OpenAIEmbeddings()
```

## 6. 단계 4: 벡터 DB 생성 (Create DB)

분할된 청크를 임베딩해서 FAISS 벡터 스토어에 저장한다.

```python
# 청크 72개를 모두 임베딩해서 FAISS 인덱스에 저장
vectorstore = FAISS.from_documents(documents=split_documents, embedding=embeddings)
```

저장이 잘 됐는지 "구글"로 유사도 검색을 해본다. 구글이 언급된 청크들이 검색된다.

```python
# 질의와 의미가 가장 가까운 청크(기본 4개)를 찾아서 출력
for doc in vectorstore.similarity_search("구글"):
    print(doc.page_content)
```

출력:

```txt
저해상도 이미지의 고해상도 전환도 지원
n IT 전문지 테크리퍼블릭(TechRepublic)은 온디바이스 AI가 주요 기술 트렌드로 부상했다며, 
2024년부터 가우스를 탑재한 삼성 스마트폰이 메타의 라마(Llama)2를 탑재한 퀄컴 기기 및 구글 
어시스턴트를 적용한 구글 픽셀(Pixel)과 경쟁할 것으로 예상
☞ 출처 : 삼성전자, ‘삼성 AI 포럼’서 자체 개발 생성형 AI ‘삼성 가우스’ 공개, 2023.11.08.
삼성전자, ‘삼성 개발자 콘퍼런스 코리아 2023’ 개최, 2023.11.14.
TechRepublic, Samsung Gauss: Samsung Research Reveals Generative AI, 2023.11.08.
1. 정책/법제  
2. 기업/산업 
3. 기술/연구 
 4. 인력/교육
구글, 앤스로픽에 20억 달러 투자로 생성 AI 협력 강화 
n 구글이 앤스로픽에 최대 20억 달러 투자에 합의하고 5억 달러를 우선 투자했으며, 앤스로픽은 
구글과 클라우드 서비스 사용 계약도 체결
n 3대 클라우드 사업자인 구글, 마이크로소프트, 아마존은 차세대 AI 모델의 대표 기업인 
앤스로픽 및 오픈AI와 협력을 확대하는 추세
KEY Contents
£ 구글, 앤스로픽에 최대 20억 달러 투자 합의 및 클라우드 서비스 제공
n 구글이 2023년 10월 27일 앤스로픽에 최대 20억 달러를 투자하기로 합의했으며, 이 중 5억 
달러를 우선 투자하고 향후 15억 달러를 추가로 투자할 방침
...
```

## 7. 단계 5: 검색기 생성 (Create Retriever)

벡터 스토어를 체인에 연결할 수 있도록 `as_retriever()`로 retriever로 바꾼다.

```python
# 벡터 스토어 -> retriever (invoke(질문)으로 관련 문서 리스트를 반환)
retriever = vectorstore.as_retriever()
```

```python
# 질문과 관련된 청크 4개가 Document 리스트로 반환된다.
retriever.invoke("삼성전자가 자체 개발한 AI의 이름은?")
```

출력:

```txt
[Document(id='17b8e478-2f90-451d-ae6d-9f0ebfa14a74', metadata={'producer': 'Hancom PDF 1.3.0.542', 'creator': 'Hwp 2018 10.0.0.13462', 'creationdate': '2023-12-08T13:28:38+09:00', 'source': 'data/SPRI_AI_Brief_2023년12월호_F.pdf', 'file_path': 'data/SPRI_AI_Brief_2023년12월호_F.pdf', 'total_pages': 23, 'f ...
 Document(id='fd7d8dca-2015-464e-b068-59c2fdbe9723', metadata={'producer': 'Hancom PDF 1.3.0.542', 'creator': 'Hwp 2018 10.0.0.13462', 'creationdate': '2023-12-08T13:28:38+09:00', 'source': 'data/SPRI_AI_Brief_2023년12월호_F.pdf', 'file_path': 'data/SPRI_AI_Brief_2023년12월호_F.pdf', 'total_pages': 23, 'f ...
 Document(id='0e6615bd-c716-4df5-bc09-fead0e05fdc3', metadata={'producer': 'Hancom PDF 1.3.0.542', 'creator': 'Hwp 2018 10.0.0.13462', 'creationdate': '2023-12-08T13:28:38+09:00', 'source': 'data/SPRI_AI_Brief_2023년12월호_F.pdf', 'file_path': 'data/SPRI_AI_Brief_2023년12월호_F.pdf', 'total_pages': 23, 'f ...
 Document(id='2c1adc5c-4bf7-40dd-b7cb-c6ad64bcc021', metadata={'producer': 'Hancom PDF 1.3.0.542', 'creator': 'Hwp 2018 10.0.0.13462', 'creationdate': '2023-12-08T13:28:38+09:00', 'source': 'data/SPRI_AI_Brief_2023년12월호_F.pdf', 'file_path': 'data/SPRI_AI_Brief_2023년12월호_F.pdf', 'total_pages': 23, 'f ...
```

## 8. 단계 6: 프롬프트 생성 (Create Prompt)

검색된 문서(`{context}`)와 질문(`{question}`)을 넣을 자리를 만든다. 모르면 모른다고 답하고, 한국어로 답하도록 지시한다.

```python
prompt = PromptTemplate.from_template(
    """You are an assistant for question-answering tasks. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. 
Answer in Korean.

#Context: 
{context}

#Question:
{question}

#Answer:"""
)
```

## 9. 단계 7: 언어모델 생성 (Create LLM)

```python
# temperature=0: 같은 질문에 최대한 같은 답을 하도록(무작위성 최소화)
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
```

## 10. 단계 8: 체인 생성 (Create Chain)

LCEL 파이프(`|`)로 전체 흐름을 연결한다. 체인에 질문 문자열 하나를 넣으면

- `"context"`: retriever가 질문으로 검색한 문서들이 들어가고
- `"question"`: `RunnablePassthrough()`가 질문을 그대로 넘긴다.

이 딕셔너리가 프롬프트를 채우고 → LLM이 답하고 → `StrOutputParser`가 문자열로 꺼낸다.

```python
chain = (
    # 질문 하나로 context(검색 결과)와 question(원래 질문)을 동시에 만든다.
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt 
    | llm 
    | StrOutputParser()
)
```

## 11. 체인 실행

PDF에 있는 "삼성 가우스" 내용을 근거로 정확하게 답한다.

```python
question = "삼성전자가 자체 개발한 AI의 이름은?"
# 검색 -> 프롬프트 -> LLM -> 문자열 파싱이 한 번에 실행된다.
response = chain.invoke(question)
print(response)
```

출력:

```txt
삼성전자가 자체 개발한 AI의 이름은 '삼성 가우스'입니다.
```

## 12. 전체 과정을 하나의 코드로

지금까지 나눠서 실행한 8단계를 한 셀로 모았다. 실제로 RAG를 만들 때는 이 형태를 뼈대로 두고 단계별 부품(로더, 분할기, 임베딩, 벡터 DB, 프롬프트, 모델)만 바꿔 끼우면 된다. 여기서는 `chunk_size`를 1000으로 늘려봤다.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# 단계 1: 문서 로드(Load Documents)
loader = PyMuPDFLoader("data/SPRI_AI_Brief_2023년12월호_F.pdf")
docs = loader.load()

# 단계 2: 문서 분할(Split Documents)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
split_documents = text_splitter.split_documents(docs)

# 단계 3: 임베딩(Embedding) 생성
embeddings = OpenAIEmbeddings()

# 단계 4: DB 생성(Create DB) 및 저장
# 벡터스토어를 생성합니다.
vectorstore = FAISS.from_documents(documents=split_documents, embedding=embeddings)

# 단계 5: 검색기(Retriever) 생성
# 문서에 포함되어 있는 정보를 검색하고 생성합니다.
retriever = vectorstore.as_retriever()

# 단계 6: 프롬프트 생성(Create Prompt)
# 프롬프트를 생성합니다.
prompt = PromptTemplate.from_template(
    """You are an assistant for question-answering tasks. 
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. 
Answer in Korean.

#Context: 
{context}

#Question:
{question}

#Answer:"""
)

# 단계 7: 언어모델(LLM) 생성
# 모델(LLM) 을 생성합니다.
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

# 단계 8: 체인(Chain) 생성
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

```python
# 체인 실행(Run Chain)
# 문서에 대한 질의를 입력하고, 답변을 출력합니다.
question = "삼성전자가 자체 개발한 AI 의 이름은?"
response = chain.invoke(question)
print(response)
```

출력:

```txt
삼성전자가 자체 개발한 AI의 이름은 '삼성 가우스'입니다.
```

## 정리

| 단계 | 사용한 도구 | 역할 |
|---|---|---|
| 1. 문서 로드 | `PyMuPDFLoader` | PDF를 페이지 단위 `Document`로 읽기 |
| 2. 문서 분할 | `RecursiveCharacterTextSplitter` | 검색하기 좋은 크기의 청크로 나누기 |
| 3. 임베딩 | `OpenAIEmbeddings` | 청크를 벡터로 변환 |
| 4. 벡터 DB | `FAISS.from_documents()` | 벡터를 저장하고 유사도 검색 |
| 5. 검색기 | `vectorstore.as_retriever()` | 질문과 관련된 청크 찾기 |
| 6. 프롬프트 | `PromptTemplate` | 검색 결과와 질문을 LLM 입력으로 조립 |
| 7. LLM | `ChatOpenAI` | 답변 생성 |
| 8. 체인 | LCEL (`\|`) + `RunnablePassthrough` | 전체 과정을 하나의 실행 흐름으로 연결 |
