# 벡터 데이터베이스에 문서 저장하고 검색하기

RAG 에이전트를 만들기 위한 첫 단계로, PDF 문서를 잘게 나눠 **Chroma 벡터 데이터베이스**에 저장하고 의미가 비슷한 내용을 검색한다(교재 6.5.2). 문서는 국립국어원의 「한글 맞춤법, 표준어 규정 해설」(264쪽)이다.

`PDF 불러오기 → 청크로 나누기 → 임베딩해서 Chroma에 저장 → 유사도 검색` 순서로 진행한다. 다음 단계(6.5.3~)에서는 이 검색 기능을 에이전트의 도구로 만든다.

- 코드: [`rag_agent/vector_retriever.ipynb`](rag_agent/vector_retriever.ipynb)
- 문서: `rag_agent/datasets/한글맞춤법 표준어규정 해설.pdf` (국립국어원, 264쪽)

> 긴 출력은 줄였다. 전체 출력은 노트북에 그대로 남아 있다.

## 1. PDF 불러오기

`PyPDFLoader`는 PDF를 **페이지 하나당 `Document` 하나**로 읽는다. `alazy_load()`는 페이지를 한 번에 다 읽지 않고 하나씩 비동기로 넘겨주는 메서드다. 주피터 노트북은 이미 이벤트 루프가 돌고 있어서 셀에서 `async for`를 바로 쓸 수 있다. (일반 `.py` 파일에서는 `async def` 함수 안에서 `asyncio.run()`으로 실행해야 한다.)

실행하면 `langchain-community` 패키지가 더 이상 적극적으로 관리되지 않는다는 `DeprecationWarning`이 나온다. 경고일 뿐이라 동작에는 문제가 없다.

```python
from dotenv import load_dotenv 
from langchain_community.document_loaders import PyPDFLoader 

# .env의 OPENAI_API_KEY를 환경변수로 불러온다. (임베딩에 필요)
load_dotenv()

# 노트북 위치 기준 상대 경로
file_path = "datasets/한글맞춤법 표준어규정 해설.pdf" 

# PDF를 페이지 단위 Document로 읽는 로더
loader = PyPDFLoader(file_path)
pages = []

# alazy_load(): 페이지를 하나씩 비동기로 읽어 온다. 노트북에서는 셀에서 바로 async for를 쓸 수 있다.
async for page in loader.alazy_load():
    pages.append(page)
```

출력:

```txt
C:\Users\user\AppData\Local\Temp\ipykernel_5900\3270393923.py:2: DeprecationWarning: `langchain-community` is being sunset and is no longer actively maintained. See https://github.com/langchain-ai/langchain-community/issues/674 for details and migration guidance toward standalone integration packages.
  from langchain_community.document_loaders import PyPDFLoader
```

페이지 수와 첫 페이지를 확인한다. `metadata`의 `page`는 0부터 세는 번호이고, `page_label`은 PDF에 실제로 찍힌 쪽 번호다. `source`(파일 경로)도 함께 들어 있어서, 나중에 검색 결과가 어느 문서·몇 쪽에서 나왔는지 알 수 있다.

```python
# 264쪽 PDF -> Document 264개
print("페이지 수:",  len(pages))
# 첫 페이지(표지)의 내용과 메타데이터
print("첫 번째 페이지 정보:", pages[0])
```

출력:

```txt
페이지 수: 264
첫 번째 페이지 정보: page_content='국립국어원 2018-01-08
발간 등록 번호
11-1371028-000712-01
한글 맞춤법
표준어 규정
해설' metadata={'producer': 'Acrobat Distiller 9.0.0 (Windows)', 'creator': 'PScript5.dll Version 5.2.2', 'creationdate': '2018-12-20T09:36:29+09:00', 'author': 'admin', 'moddate': '2018-12-20T09:38:09+09:00', 'title': '<C6ED2DBEEEB9AEB1D4B9FCC7D8BCB35FB1B9BEEEBFF8C3D6C1BE5F76657232302DBCF6C1A4BABB2E687770>', 'source': 'datasets/한글맞춤법 표준어규정 해설.pdf', 'total_pages': 264, 'page': 0, 'page_label': '1'}
```

## 2. 청크로 나누기

한 페이지는 검색 단위로 쓰기에 너무 길어서, `RecursiveCharacterTextSplitter`로 500자 단위 청크로 나눈다. 문단 → 줄 → 단어 순으로 자연스러운 경계를 찾아 자르고, 청크 사이에 50자를 겹치게 해서 경계에서 문장이 끊겨도 앞뒤 맥락이 조금은 남게 한다. 각 청크는 원래 페이지의 메타데이터를 그대로 물려받는다.

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter 

# 최대 500자 단위로 자르고, 이웃한 청크끼리 50자씩 겹치게 한다.
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
# 페이지 Document 목록 -> 청크 Document 목록 (메타데이터는 그대로 유지)
docs = text_splitter.split_documents(pages)
```

청크 수와 길이를 확인한다. 264쪽이 **510개 청크**가 됐다. 대부분 500자 가까이 채워지지만, 페이지 끝에 남은 짧은 조각(11자, 19자 등)도 있다. 페이지 단위로 먼저 나뉜 상태에서 자르기 때문이다.

처음에는 510개 청크를 전부 출력했는데, 출력만 약 45만 자라 노트북 파일이 800KB가 넘었다. 깃허브에서 보기 편하도록 `docs[:3]`으로 **앞쪽 3개 청크만** 출력하게 바꿨다. 첫 청크는 1쪽 표지(63자)이고, 두세 번째 청크는 3쪽 머리말을 나눈 것이다.

```python
print(f"총 {len(docs)}개의 청크 생성완료")
# 청크마다 글자 수
print("각 청크의 길이:", [len(i.page_content) for i in docs])

# 앞쪽 3개 청크만 메타데이터와 내용을 출력 (510개를 전부 출력하면 노트북이 800KB 넘게 커진다)
for i in docs[:3]:
    print("[메타데이터]", i.metadata)
    print("[내용]", i.page_content)
    print("=" * 100)
```

출력:

```txt
총 510개의 청크 생성완료
각 청크의 길이: [63, 467, 367, 472, 96, 473, 110, 343, 458, 471, 499, 129, 484, 456, 461, 124, 11, 420, 448, 448, 466, 463, 220, 489, 486, 484, 466, 54, 454, 476, 288 ... (510개)
[메타데이터] {'producer': 'Acrobat Distiller 9.0.0 (Windows)', 'creator': 'PScript5.dll Version 5.2.2', 'creationdate': '2018-12-20T09:36:29+09:00', 'author': 'admin', 'moddate': '2018-12-20T09:38:09+09:00', 'title': '<C6ED2DBEEEB9AEB1D4B9FCC7D8BCB35FB1B9BEEEBFF8C3D6C1BE5F76657232302DBCF6C1A4BABB2E687770>', 'source': 'datasets/한글맞춤법 표준어규정 해설.pdf', 'total_pages': 264, 'page': 0, 'page_label': '1'}
[내용] 국립국어원 2018-01-08
발간 등록 번호
11-1371028-000712-01
한글 맞춤법
표준어 규정
해설
====================================================================================================
[메타데이터] {'producer': 'Acrobat Distiller 9.0.0 (Windows)', 'creator': 'PScript5.dll Version 5.2.2', 'creationdate': '2018-12-20T09:36:29+09:00', 'author': 'admin', 'moddate': '2018-12-20T09:38:09+09:00', 'title': '<C6ED2DBEEEB9AEB1D4B9FCC7D8BCB35FB1B9BEEEBFF8C3D6C1BE5F76657232302DBCF6C1A4BABB2E687770>', 'source': 'datasets/한글맞춤법 표준어규정 해설.pdf', 'total_pages': 264, 'page': 2, 'page_label': '3'}
[내용] 1988년 ‘한글 맞춤법’과 ‘표준어 규정’이 개정되면서, 국립국어원의 전신이라 
할 수 있는 국어연구소에서는 ‘한글 맞춤법 해설’, ‘표준어 규정 해설’(이하 ‘해
설’)을 함께 내놓았습니다. ‘해설’은 ‘한글 맞춤법’이나 ‘표준어 규정’의 내용을 
알기 쉽게 설명하면서, 동시에 규정 본문에서는 상세히 다루기 어려웠던 부분
을 보완하는 역할도 함께하였습니다. 또한 규정의 역사적 배경이나 관련 사항 
등도 담아 규정을 이해하는 데에 도움을 주고자 하였습니다. 실제로 많은 사람
이 ‘해설’과 규정을 거의 동등한 지위에 있는 것으로 인식할 만큼 지난 30년간 
‘해설’은 중요하게 다루어져 왔습니다.
그러나 시간이 지나 말이 변하면서 ‘해설’의 내용도 변할 수밖에 없는 부분이 
생겨났습니다. 먼저 1999년 “표준국어대사전”을 발간하면서 규정에는 명시되지 
않았던 맞춤법이나 표준어 관련 세부 사항을 사전 항목으로 담았습니다. 이는
====================================================================================================
[메타데이터] {'producer': 'Acrobat Distiller 9.0.0 (Windows)', 'creator': 'PScript5.dll Version 5.2.2', 'creationdate': '2018-12-20T09:36:29+09:00', 'author': 'admin', 'moddate': '2018-12-20T09:38:09+09:00', 'title': '<C6ED2DBEEEB9AEB1D4B9FCC7D8BCB35FB1B9BEEEBFF8C3D6C1BE5F76657232302DBCF6C1A4BABB2E687770>', 'source': 'datasets/한글맞춤법 표준어규정 해설.pdf', 'total_pages': 264, 'page': 2, 'page_label': '3'}
[내용] 않았던 맞춤법이나 표준어 관련 세부 사항을 사전 항목으로 담았습니다. 이는 
실질적으로 규정을 확장한 것으로 볼 수 있는데 이 과정에서 기존 ‘해설’과는 
달리 처리한 부분도 생겨났습니다. 또한 2011년 이후 국민의 언어생활 편의 증
진을 위해 많이 사용하는 비표준어나 방언을 국어심의회에서 표준어로 인정함
에 따라 기존 규정과 다른 부분이 생겼습니다. 이러한 내용을 담아 2017년에 
‘한글 맞춤법’과 ‘표준어 규정’을 일부 개정하였는데, 비록 규정의 방향이나 내
용은 크게 달라지지 않았지만 수정된 내용을 해설에 반영해야 하는 상황이 되
었습니다. 이에 국어연구소에서 펴낸 기존 ‘해설’을 보완하여 ‘국립국어원 해설’
을 발간하게 되었습니다.
머리말
====================================================================================================
```

## 3. Chroma 벡터 DB에 저장하기

`Chroma.from_documents()`는 청크마다 `OpenAIEmbeddings(text-embedding-3-small)`로 임베딩(숫자 벡터)을 만들어 저장한다. `persist_directory`를 주면 메모리가 아니라 **디스크(`./chroma_db` 폴더)에 저장**되어, 노트북을 다시 켜도 임베딩을 다시 만들 필요 없이 불러올 수 있다. `collection_name`은 DB 안에서 이 문서 묶음을 구분하는 이름이다.

**주의:** 이 셀을 다시 실행하면 같은 컬렉션에 510개가 **또 추가**된다. 문서마다 새 ID가 붙기 때문이다. 같은 버전(langchain-chroma 1.1.0)으로 문서 5개를 두 번 저장해 보니 개수가 5 → 10이 됐다. 지금 `chroma_db`에는 510개가 들어 있어 중복은 없었다. 다시 만들 때는 `chroma_db` 폴더를 지우고 실행하거나, 이미 있으면 `Chroma(persist_directory=..., collection_name=..., embedding_function=...)`로 불러와서 써야 한다.

`chroma_db` 폴더(약 9MB)는 `.gitignore`에 들어 있어서 깃허브에는 올라가지 않는다.

```python
from langchain_chroma import Chroma 
from langchain_openai import OpenAIEmbeddings 

# 벡터 DB를 저장할 폴더 (.gitignore에 등록되어 깃허브에는 안 올라감)
DB_PATH = "./chroma_db"

# 청크마다 임베딩을 만들어 Chroma에 저장. 다시 실행하면 같은 내용이 중복으로 추가된다.
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
    # 디스크에 저장 -> 다음에 다시 불러올 수 있다.
    persist_directory=DB_PATH,
    # DB 안에서 이 문서 묶음을 구분하는 이름
    collection_name="korean_pdf",
)

```

## 4. 유사도 검색

검색어도 같은 임베딩 모델로 벡터로 바꾼 뒤, 저장된 청크 중 가장 가까운(의미가 비슷한) 3개를 돌려준다.

`"구개음화"`로 검색하니 세 결과 모두 구개음화를 직접 다루는 청크였다. 24쪽(`곧이[고지]`와 `곧이어[고디어]`의 차이로 구개음화가 일어나는 조건 설명), 245쪽(조사·접미사 '이', '히' 앞의 구개음화), 240쪽(구개음화 때문에 연음이 되지 않는 경우)이다. 결과마다 `page_label`과 `source`가 있어서 근거 위치를 바로 알 수 있다.

세 번째 결과 첫 줄의 `\x13\x14\x19` 같은 문자는 PDF 머리말(책 제목 옆 쪽 번호 자리)이 텍스트로 제대로 추출되지 않아 생긴 깨진 글자로 보인다. PDF 텍스트 추출에서 흔히 생기는 잡음이다.

```python
# "구개음화"와 의미가 가장 가까운 청크 3개 검색
vectorstore.similarity_search("구개음화", k=3)
```

출력:

```txt
[Document(id='9df8de4c-822f-428a-8d33-a32446f29536', metadata={..., 'page_label': '24', ...}, page_content='는 부사 파생 접미사가 결합하여 부사가 되었으므로 구개음화가 실현되었지만, ‘곧이\n어’는 형식 형태소가 아닌 실질 형태소 부사가 결합한 말이므로 구개음화가 실현되지 \n않는다. \n곧이[고지]: 곧-(어근)+-이(부사 파생 접미사)\n곧이어[고디어]: 곧(부사)+이어(부사)\n현재 표준어에서 구개음화는 형태소와 형태소가 결합할 때 일어나는 현상이다. 그러\n므로 ‘마디, 견디다’와 같이 하나의 형태소 내부에서는 구개음화가 일어나지 않는다.'),
 Document(id='90aa941d-9da6-4b6d-ae67-965b0bbd1be6', metadata={..., 'page_label': '245', ...}, page_content='이 현상은 주격 조사 ‘이’ 앞에서도 일어나고 접미사 ‘-이’ 앞에서도 일어난다.\n[붙임]에서는 ‘ㄷ’으로 끝나는 말 뒤에 ‘이’가 아닌 ‘히’가 결합할 때에도 구개음화가 \n일어난다고 규정했다. 이 경우 먼저 ‘ㄷ’과 ‘히’의 ‘ㅎ’이 [ㅌ]으로 축약되는데, 이는 ‘ㅌ’ \n뒤에 ‘ㅣ’가 결합하는 것과 비슷하기 때문에 구개음화가 적용되어 [ㅊ]이 된다.'),
 Document(id='bfb045d6-7355-4f85-ba17-d7debda49ad5', metadata={..., 'page_label': '240', ...}, page_content='‘한글 맞춤법’, ‘표준어 규정’ 해설\x13\x14\x19\n결합할 때에도 연음이 되지 않는다. 연음이 되려면 ‘ㄷ, ㅌ’이 그대로 초성으로 발음되\n어야 하는데, 구개음화(표준 발음법 제17항 참조)가 적용되어 ‘ㅈ, ㅊ’으로 바뀌기 때\n문이다. 이 외에도 연음의 예외는 좀 더 있지만 그 비율은 높지 않다. 그런 점에서 연\n음은 국어의 중요한 발음 원칙이라고 할 수 있다.\n한편 현실 발음에서는 연음이 되어야만 하는 환경에서 연음이 되지 않아, 아래와 \n같이 잘못된 발음이 나타나기도 한다.\n부엌이[부어기], 부엌을[부어글], 꽃이[꼬시], 꽃을[꼬슬] (×)\n이러한 경우는 모두 연음을 적용하여 발음하는 것이 타당하므로 다음과 같이 발음\n하는 것이 옳다.\n부엌이[부어키], 부엌을[부어클], 꽃이[꼬치], 꽃을[꼬츨] (○)\n제14항\n겹받침이 모음으로 시작된 조사나 어미, 접미사와 결합되는 경우에는, 뒤엣것만을 뒤 음절 \n첫소리로 옮겨 발음한다.(이 경우, ‘ㅅ’은 된소리로 발음함.)')]
```

## 정리

| 단계 | 코드 | 결과 |
|---|---|---|
| PDF 불러오기 | `PyPDFLoader(file_path)` + `async for ... in loader.alazy_load()` | 264쪽 -> `Document` 264개 (`page`, `page_label`, `source` 메타데이터) |
| 청크 나누기 | `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)` | 510개 청크 |
| 벡터 DB 저장 | `Chroma.from_documents(..., persist_directory="./chroma_db", collection_name="korean_pdf")` | 임베딩 510개를 디스크에 저장. 다시 실행하면 중복 추가 |
| 유사도 검색 | `vectorstore.similarity_search("구개음화", k=3)` | 구개음화를 다루는 청크 3개 (24쪽, 245쪽, 240쪽) |

다음 단계는 이 검색을 `@tool`로 감싸서, 에이전트가 필요할 때 스스로 문서를 검색하고 그 내용으로 답하게 만드는 것이다.
