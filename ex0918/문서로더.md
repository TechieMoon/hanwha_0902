# Document Loader 실습

PDF 같은 외부 파일을 LangChain의 `Document` 객체로 불러오는 방법을 실습했다. 먼저 `Document` 객체 자체의 구조를 살펴본 뒤, 실제 PDF 파일을 여러 방식으로 불러오고(loader), 불러온 문서를 작은 조각(chunk)으로 나눠보는 것(splitter)까지 다뤘다.

## 1. Document 객체의 구조

```python
from langchain_core.documents import Document

document = Document(page_content="안녕하세요? 이건 랭체인의 다큐먼트입니다.")
document.__dict__
```

출력:

```txt
{'id': None, 'metadata': {}, 'page_content': '안녕하세요? 이건 랭체인의 다큐먼트입니다.', 'type': 'Document'}
```

`Document`는 텍스트(`page_content`)와 부가정보(`metadata`)를 함께 담는 단순한 자료구조다. `id`(아직 지정 안 해서 `None`), `metadata`(빈 dict), `page_content`, `type`(`"Document"` 고정값) 네 가지로 이루어져 있다.

## 2. metadata 채워넣기

```python
document.metadata["source"] = "TeddyNote"
document.metadata["page"] = 1
document.metadata["author"] = "Teddy"
```

`metadata`는 평범한 파이썬 `dict`라서, 키를 추가하는 것만으로 원하는 부가정보(출처, 페이지 번호, 작성자 등)를 자유롭게 붙일 수 있다.

## 3. PyPDFLoader로 PDF 불러오기

```python
FILE_PATH = "./data/SPRI_AI_Brief_2023년12월호_F.pdf"

from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader(FILE_PATH)
docs = loader.load()

len(docs)  # 23
```

`PyPDFLoader`는 PDF를 페이지 단위로 읽어서 각 페이지를 하나의 `Document`로 만들어주는 가장 기본적인 PDF 로더다. `langchain_community` 소속이라 "sunset(지원 종료 예정)" 경고가 뜨지만, `langchain-community` 패키지 자체가 점차 별도 통합 패키지들로 옮겨가고 있어서 나오는 경고이고 기능은 정상 동작한다. PDF가 23페이지라서 `Document`도 23개(페이지당 1개)가 만들어진다.

```python
docs[5]
```

개별 문서(페이지)를 보면 `metadata`에 PDF 자체의 메타정보(`producer`, `creator`, `creationdate`, `author`, `total_pages`, `page`, `page_label` 등)가 자동으로 채워져 있고, `page_content`에는 그 페이지의 텍스트가 그대로 들어있다.

## 4. 다른 로더와 비교

**PyMuPDF4LLMLoader** — LLM이 다루기 좋은 마크다운 형태(제목에 `#`, 굵은 글씨에 `**` 등)로 변환해서 추출해준다.

```python
from langchain_pymupdf4llm import PyMuPDF4LLMLoader

future_loader = PyMuPDF4LLMLoader(FILE_PATH, use_layout=False)
future_docs = future_loader.load()
```

**PyPDFLoader의 레이아웃 보존 모드** — `extraction_mode="layout"`로 불러오면, 원본 PDF에 보이는 것과 비슷하게 띄어쓰기·정렬 등 시각적 레이아웃을 최대한 살려서 텍스트를 추출한다.

```python
layout_loader = PyPDFLoader(FILE_PATH, extraction_mode="layout")
layout_docs = layout_loader.load()
```

기본 모드보다 원본의 표/문단 구조를 짐작하기엔 좋지만, 그만큼 공백이 많이 섞여서 텍스트가 다소 지저분해 보일 수 있다.

## 5. 문서를 작은 조각(chunk)으로 나누기

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=0)

docs = loader.load()
split_docs = text_splitter.split_documents(docs)

print(f"문서의 길이: {len(split_docs)}")  # 173
```

`RecursiveCharacterTextSplitter`는 긴 문서를 지정한 글자 수 단위로 잘라서 여러 개의 작은 `Document`로 쪼개준다. 나중에 RAG(검색 기반 답변) 등에서 문서를 다룰 때, 문서 전체를 통째로 쓰기보다 이렇게 작은 조각 단위로 다루는 경우가 많다. `chunk_size=200`은 조각 하나의 최대 글자 수, `chunk_overlap=0`은 조각들 사이에 겹치는 부분이 없다는 뜻이다. 23개였던 문서(페이지)가 200자 단위로 쪼개지면서 173개의 조각으로 늘어났다.

## 6. load() vs lazy_load(), 동기 vs 비동기

```python
loader.lazy_load()  # 아직 아무 것도 읽지 않은 상태의 제너레이터 객체

for doc in loader.lazy_load():
    print(doc.metadata)  # 순회하는 시점에 한 페이지씩 실제로 로드된다

adocs = await loader.aload()  # load()의 비동기 버전

async for doc in loader.alazy_load():
    print(doc.metadata)  # lazy_load()의 비동기 버전
```

`load()`는 호출하는 즉시 전체 페이지를 한 번에 다 읽어서 리스트로 반환한다. 반면 `lazy_load()`는 호출해도 아직 아무 페이지도 읽지 않고 제너레이터 객체만 반환하며, 실제로 순회할 때마다 그제서야 페이지를 하나씩 읽어온다. 문서가 아주 많아서 한 번에 메모리에 다 올리기 부담스러울 때 유용하다.

## 정리

| 메서드 | 반환 방식 | 동기/비동기 |
|---|---|---|
| `load()` | 전체를 한 번에 리스트로 | 동기 |
| `lazy_load()` | 순회할 때마다 하나씩(제너레이터) | 동기 |
| `aload()` | 전체를 한 번에 리스트로 | 비동기 (`await`) |
| `alazy_load()` | 순회할 때마다 하나씩(비동기 제너레이터) | 비동기 (`async for`) |

로더 자체도 `PyPDFLoader`(기본/레이아웃 보존 모드), `PyMuPDF4LLMLoader`(마크다운 형태로 추출)처럼 여러 종류가 있어서, 이후 처리(요약, 검색 등) 목적에 맞는 형식으로 불러올 수 있다. 불러온 문서는 `RecursiveCharacterTextSplitter`로 원하는 크기의 조각으로 잘라서 활용한다.
