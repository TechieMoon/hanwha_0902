# 한화내일아카데미 AI 에이전트 과정 학습 기록

> **한화내일아카데미 ICT부문** · 2026.09.01 ~ 2026.11.13 (400시간)
> LLM 오케스트레이션부터 RAG, 멀티 에이전트 배포까지 배운 내용을 날짜별로 기록한 저장소입니다.
> 실습 코드에는 주석을 달고, 직접 실행한 결과를 보고 확인한 점을 문서로 정리했습니다.

**사용 기술** · Python · LangChain · LangGraph · OpenAI API · FastAPI · Streamlit · Chroma · FAISS · pgvector(PostgreSQL) · Docker · Selenium

책 『만들면서 배우는 AI 에이전트 개발 입문+실전』 실습은 책 목차 순서로 [agent 저장소](https://github.com/TechieMoon/agent)에도 정리했습니다.

## 주제별로 보기

| 주제 | 배운 내용 | 기억할 것 | 대표 정리 문서 |
|---|---|---|---|
| 개발 환경 | VS Code, 가상환경, GitHub, API 키 관리, 도커 | API 키는 코드가 아니라 환경변수·`.env`에 두고, `.env`는 `.gitignore`에 넣는다 | [가상환경](ex0902/가상환경가이드.md) · [깃 충돌 해결](ex0907/깃충돌해결법.md) · [실습 환경 구축](ex1012/실습환경구축.md) |
| 파이썬과 데이터 | 기본 문법, Pydantic, 예외 처리, NumPy, Pandas | 타입 힌트와 Pydantic 모델이 곧 검증 규칙이다 (FastAPI도 같은 원리) | [Pydantic](ex0907/Pydantic.md) · [판다스 기초](ex0916/판다스기초.md) |
| LLM 호출과 프롬프트 | LangChain, LCEL·Runnable(병렬·분기·라우팅), 프롬프트 템플릿, Few-shot, 출력 파서, 구조화 출력(LangChain·OpenAI SDK·Ollama), 캐싱, 대화 메모리, Gemini·Ollama 연동 | 프롬프트는 템플릿으로 분리하고, 결과는 구조화 출력으로 받아야 코드에서 다루기 쉽다 | [LangChain](ex0914/랭체인.md) · [프롬프트 템플릿](ex0915/프롬프트템플릿.md) · [구조화된 출력](ex0916/구조화된출력.md) · [LLM 연동하기](ex1012/LLM연동하기.md) · [구조화된 출력(SDK)](ex1016/구조화된출력.md) · [LangChain 입문](ex1019/LangChain입문.md) · [LCEL과 Runnable](ex1019/LCEL과Runnable.md) |
| 문서 처리와 벡터 DB | 문서 로더, 텍스트 분할, 임베딩, Chroma, FAISS, pgvector | 청크 크기·겹침과 임베딩 모델이 검색 품질을 정한다. 저장과 검색은 같은 모델로 | [재귀 텍스트 분할](ex0921/재귀문자텍스트분할.md) · [OpenAI 임베딩](ex0922/OpenAI임베딩.md) · [Chroma](ex0922/크로마벡터스토어.md) · [임베딩과 벡터 DB](ex1015/임베딩과벡터DB.md) |
| 검색과 RAG | 리트리버(MMR, 앙상블, 문맥 압축, 부모 문서), 리랭커, RAG 파이프라인, RAGAS 평가 데이터 | 답이 틀리면 검색부터 의심한다: 검색 개수(k) → 임계값 → 청크 → 리랭커 순서로 확인 | [리랭커 RAG](ex0928/RAG실습.md) · [RAG 기본 파이프라인](ex0929/RAG기본파이프라인.md) · [RAG 실습 2](ex0930/RAG실습.md) · [RAG](ex1015/RAG.md) · [LangChain으로 RAG](ex1020/LangChain으로RAG.md) |
| 도구 호출과 에이전트 | 챗봇과 에이전트의 차이, 하네스, 에이전트 설계 과정, 멀티 에이전트 오케스트레이션 패턴, LangGraph(상태·노드·엣지), 웹 검색·코딩·RAG 에이전트, create_agent 미들웨어(요약·사람 승인·호출 제한·재시도·대체 모델·개인정보 가리기), 단기·장기 메모리(PostgreSQL 영구 저장), Function·빌트인·MCP 도구, 다중 LLM, ReAct, Human-in-the-loop | LLM은 무엇을 할지 결정하고, 실행은 내 코드가 한다. 모든 반복에는 횟수 상한 | [랭그래프 기본](ex1001/랭그래프기본개념.md) · [웹 검색 에이전트](ex1006/웹검색에이전트.md) · [RAG 에이전트](ex1008/RAG에이전트그래프.md) · [빌트인 툴과 MCP](ex1013/빌트인툴과MCP.md) · [다중 LLM과 ReAct](ex1016/다중LLM과ReAct.md) · [AI 에이전트 이론](ex1019/AI에이전트이론.md) · [도구 호출과 MCP](ex1019/도구호출과MCP.md) · [다중 LLM·ReAct (LangChain)](ex1020/다중LLM과ReAct_LangChain.md) · [단기·장기 메모리](ex1021/단기장기메모리.md) · [미들웨어](ex1021/미들웨어.md) |
| 웹 서비스 | FastAPI(라우팅, 검증, 템플릿, 파일 업로드), Streamlit, 에이전트·RAG를 REST API로 서비스 | 입력 검증은 타입 힌트로, 외부에서 온 값(파일 이름 등)은 그대로 믿지 않는다 | [FastAPI와 Streamlit](ex0910/streamlit_fastapi.md) · [요청 본문과 검증](ex1014/요청본문과검증.md) · [AI 에이전트 서버](ex1015/FastAPI_AI에이전트서버.md) |
| 웹 데이터 수집 | requests·BeautifulSoup, 공공·네이버 Open API, Selenium | HTML에 내용이 있으면 requests, 자바스크립트가 그리면 Selenium. 수집한 남의 글과 키는 공개 주의 | [정적 수집](ex1013/정적웹수집.md) · [오픈 API 수집](ex1013/오픈API수집.md) · [동적 수집](ex1013/동적웹수집.md) |

## 실습하며 얻은 교훈

실행해 보며 직접 부딪힌 문제에서 얻은, 다음에 만들 때 기억할 것들입니다.

**에이전트**
- 에이전트의 **모든 반복에 횟수 상한**을 둔다. 재검색만 막고 답변 재생성을 안 막았더니 `GraphRecursionError`가 났다. ([10/08](ex1008/RAG에이전트그래프.md))
- 상태에 쌓는 횟수는 **새 질문마다 초기화**한다. 같은 대화에서 앞 질문의 재시도 횟수가 다음 질문으로 이어졌다. ([10/08](ex1008/RAG에이전트그래프.md))
- 원문이 그대로 필요한 단계(검색 결과 정리 등)는 **LLM에 맡기지 말고 코드로** 처리한다. LLM이 원문을 고쳐 써서 출처 쪽 번호가 틀렸다. ([10/08](ex1008/RAG에이전트그래프.md))
- 여러 LLM의 답을 합칠 때는 **각 호출이 성공했는지 먼저 확인**한다. 없는 메서드를 불러 생긴 에러 문자열을 종합 모델이 답변으로 평가했다. ([10/16](ex1016/다중LLM과ReAct.md))
- 에이전트가 도구를 다 불러도 **마지막 판단은 틀릴 수 있다.** 예산 초과 장소를 1순위로 추천했다. 숫자 조건은 코드로 다시 검사한다. ([10/16](ex1016/다중LLM과ReAct.md), LangChain으로 바꾼 [10/20](ex1020/다중LLM과ReAct_LangChain.md)에도 똑같이)
- 작은 로컬 모델은 **지시(언어·형식)를 무시하고 `<think>` 추론을 답에 섞는다.** "파이썬 코드만" 달라고 했는데 TypeScript 명세서가 왔고, 검증 모델도 이 점을 놓쳤다. 다음 단계로 넘기기 전에 형식은 코드로 검사한다. ([10/20](ex1020/다중LLM과ReAct_LangChain.md))
- "도구로 확인해줘"라고 해도 도구가 실패하면 모델이 **스스로 계산해 답할 수 있다.** 도구 결과가 꼭 필요한 값은 실제로 쓰였는지 확인한다. ([10/20](ex1020/다중LLM과ReAct_LangChain.md))
- 대화 요약은 **원래 단어를 바꿀 수 있다.** 요약 미들웨어의 기본 프롬프트가 영어라 "등산"이 요약을 거치며 "하이킹"이 됐다. 한국어 서비스는 요약 프롬프트도 한국어로, 고유명사는 그대로 두라고 지시한다. ([10/21](ex1021/미들웨어.md))
- 장기 메모리를 시험할 때는 **처음 쓰는 대화방**으로 묻는다. 이미 대화가 쌓인 방에서는 모델이 단기 메모리만 보고 답해서 장기 메모리 조회가 일어나지 않았다. ([10/21](ex1021/단기장기메모리.md))
- 구조화 출력은 **형식만 보장한다.** 스키마 검증을 통과해도 값이 맞는지는 도구 결과와 따로 비교한다. ([10/19](ex1019/도구호출과MCP.md))
- LLM이 호출하는 도구는 **입력 크기와 실행 시간에 상한**을 둔다. 계산기 도구에 큰 거듭제곱을 넣자 서버가 멈췄다. ([10/15](ex1015/FastAPI_AI에이전트서버.md))

**RAG와 검색**
- 검색 임계값은 강의 자료의 숫자를 믿지 말고 **내 데이터로 유사도를 먼저 찍어 보고** 정한다. 정답도 0.3 ~ 0.5대였다. ([10/15](ex1015/RAG.md))
- **단어 하나끼리의 임베딩 유사도는 믿기 어렵다.** '강아지-반려견'이 '강아지-자동차'보다 낮게 나왔다. 문장으로 비교한다. ([10/15](ex1015/임베딩과벡터DB.md))
- 같은 문서를 다시 넣으면 그대로 **중복 저장**된다. 저장 전에 중복을 확인한다. ([10/08](ex1008/벡터DB저장과검색.md), [10/15](ex1015/RAG.md))
- **모델이 모르는 최신 용어는 그럴듯하게 지어낸다.** GPT·EXAONE·Llama 모두 "LCEL"을 매번 다른 약자로 설명했고, 설명 문서를 context로 넣은 RAG 체인만 맞게 답했다. ([10/19](ex1019/LCEL과Runnable.md))
- 웹 검색 도구를 붙여도 **"오늘" 같은 날짜 조건은 느슨하게 처리된다.** 오늘 소식을 물었는데 몇 달 전 기사가 섞였다. 출처 날짜를 확인한다. ([10/19](ex1019/도구호출과MCP.md))
- "문서에 없는 답"은 임계값만이 아니라 **시스템 프롬프트로도** 막는다. ([09/28](ex0928/RAG실습.md))

**웹 서비스와 보안**
- 업로드 파일 이름처럼 **외부에서 온 값은 그대로 경로에 쓰지 않는다.** `../`로 저장 폴더 밖에 파일이 써졌다. ([10/14](ex1014/폼과파일업로드.md))
- API 키는 **코드뿐 아니라 실행 결과(출력)에도** 남는다. 노트북은 출력까지 확인하고 올린다. ([10/13](ex1013/오픈API수집.md))
- 자료의 코드가 안 돌면 **라이브러리 버전부터** 확인한다. 같은 함수도 버전에 따라 호출 방식이 달랐다. ([10/14](ex1014/템플릿과AJAX.md))

## 날짜별 기록

10월 12일부터는 책 대신 강사님이 직접 만든 자료로 수업이 진행됐습니다.

<details open>
<summary><b>2026년 10월</b></summary>

### 2026-10-21
- **[단기·장기 메모리](ex1021/단기장기메모리.md)** — `thread_id`별 대화 기록(checkpointer)과 사용자별 메모장(store), 메모리 없음/단기/단기+장기 비교, PostgreSQL로 재시작 후에도 유지 · [코드](ex1021/exam6.ipynb)
- **[미들웨어](ex1021/미들웨어.md)** — 훅 6가지의 실행 순서, 요약·사람 승인·호출 제한·재시도·대체 모델·개인정보 가리기·할 일 목록, 배송 상담·쇼핑 주문 응용 · [코드](ex1021/exam7.ipynb)

### 2026-10-20
- **[LangChain으로 RAG](ex1020/LangChain으로RAG.md)** — `PGVectorStore`(pgvector)에 `add_documents`로 저장, retriever 검색, LCEL 없이 vs LCEL RAG 비교, PDF 적재, `batch` · [코드](ex1020/exam4.ipynb)
- **[다중 LLM과 ReAct (LangChain)](ex1020/다중LLM과ReAct_LangChain.md)** — `RunnableParallel` 병렬 종합, `assign` 순차 파이프라인, `bind_tools` 루프와 `create_agent` ReAct, 실행 결과에서 본 모델의 실수 · [코드](ex1020/exam5.ipynb)

### 2026-10-19
- **[AI 에이전트 이론](ex1019/AI에이전트이론.md)** — 챗봇 vs 에이전트, 하네스 구성 요소, 에이전트 설계 8단계, LangChain vs LangGraph, 멀티 에이전트 오케스트레이션 4패턴
- **[LangChain 입문](ex1019/LangChain입문.md)** — OpenAI SDK vs LangChain, `ChatOpenAI`·`ChatOllama`, 메시지 역할, 프롬프트 템플릿, `prompt | llm | parser` · [코드](ex1019/exam1.ipynb)
- **[LCEL과 Runnable](ex1019/LCEL과Runnable.md)** — Runnable·병렬·assign·분기·동적 라우팅, fake retriever RAG, "LCEL"을 지어낸 모델들과 RAG로 바로잡기 · [코드](ex1019/exam2.ipynb)
- **[도구 호출과 MCP](ex1019/도구호출과MCP.md)** — `@tool`, `create_agent` 실행 루프, `response_format` 구조화 출력, 내장 웹 검색, 원격 MCP 서버 도구 · [코드](ex1019/exam3.ipynb)

### 2026-10-16
- **[다중 LLM과 ReAct](ex1016/다중LLM과ReAct.md)** — GPT·Gemini·EXAONE 병렬 종합과 순차 파이프라인(설계→구현→검증), ReAct 루프, 재시도, Human-in-the-loop · [코드](ex1016/exam4.ipynb)
- **[구조화된 출력: OpenAI SDK와 Ollama](ex1016/구조화된출력.md)** — `json_object`→strict 스키마→Pydantic `.parse()`, Enum·Optional·refusal, 로컬 모델 검증-재시도 · [코드](ex1016/exam5.ipynb)

### 2026-10-15
- **[임베딩과 벡터 DB](ex1015/임베딩과벡터DB.md)** — 임베딩·코사인 유사도, 도커 pgvector에 저장하고 SQL로 유사도 검색, 실제 유사도 값과 임계값 실험 · [코드](ex1015/exam3.ipynb)
- **[RAG](ex1015/RAG.md)** — 검색·증강·생성 3단계, 청크 적재, 벡터 DB REST API와 항공 가이드 RAG 챗봇, 중복 저장·임계값 문제 확인 · [코드](ex1015/fastapiedu/exam21.py)
- **[도구를 쓰는 AI 에이전트 서버](ex1015/FastAPI_AI에이전트서버.md)** — FastAPI + Streamlit, 세션별 대화 유지, 계산기 도구 DoS 수정 · [코드](ex1015/fastapiedu/exam19.py)

### 2026-10-14
- **[FastAPI 라우팅과 파라미터](ex1014/라우팅과파라미터.md)** — 경로·쿼리 파라미터, 타입 검증과 422 응답, REST API 개념 · [코드](ex1014/exam3.py)
- **[템플릿과 AJAX](ex1014/템플릿과AJAX.md)** — Jinja2, `url_for`, 폼 제출과 AJAX 비교, 버전에 따른 호출 방식 오류 수정 · [코드](ex1014/exam9_1.py)
- **[요청 본문과 검증](ex1014/요청본문과검증.md)** — Pydantic 본문, `Query`·`Path` 검증, `HTTPException`, `response_model` · [코드](ex1014/exam14.py)
- **[폼과 파일 업로드](ex1014/폼과파일업로드.md)** — `Form`, lifespan, 파일 업로드·저장, 경로 조작 문제 수정, CORS · [코드](ex1014/exam18.py)

### 2026-10-13
- **[빌트인 툴과 MCP](ex1013/빌트인툴과MCP.md)** — Tool Schema 작성 원칙, `web_search`, 외부 MCP 서버 연결 · [코드](ex1013/exam2.ipynb)
- **[정적 웹 수집](ex1013/정적웹수집.md)** — urllib·requests·BeautifulSoup, YES24 도서 240권 수집, AI가 짠 수집 코드 비교 · [코드](ex1013/dataexam/exam1.ipynb)
- **[오픈 API 수집](ex1013/오픈API수집.md)** — 서울시·네이버 API(XML·JSON), API 키 정리 · [코드](ex1013/dataexam/exam2.ipynb)
- **[동적 웹 수집](ex1013/동적웹수집.md)** — Selenium, 명시적 대기, 정적·동적 수집 비교 · [코드](ex1013/dataexam/exam3.ipynb)

### 2026-10-12
- **[실습 환경 구축](ex1012/실습환경구축.md)** — API 키 환경변수, Ollama, 가상환경과 노트북 커널
- **[다양한 방법으로 LLM 연동하기](ex1012/LLM연동하기.md)** — Ollama·Gemini·OpenAI 호출 비교, 서버 측 대화 기억, 이미지 분석·생성, 임베딩 · [코드](ex1012/exam1.ipynb)
- **[LLM에 도구 연결하기](ex1012/도구호출.md)** — 함수 + JSON Schema 도구, 에이전트 루프, 실시간 날씨 도구 · [코드](ex1012/exam2.ipynb)

### 2026-10-08
- **[create_agent 미들웨어](ex1008/create_agent미들웨어.md)** — 모델 교체, 금지어 차단, 동적 프롬프트, 구조화 출력 · [코드](ex1008/create_agent/middleware.py)
- **[벡터 DB 저장과 검색](ex1008/벡터DB저장과검색.md)** — 264쪽 PDF를 청크 510개로 나눠 Chroma에 저장하고 검색 · [코드](ex1008/rag_agent/vector_retriever.ipynb)
- **[검색 도구 만들기](ex1008/검색도구만들기.md)** — `create_retriever_tool`, 검색 결과와 DB 경로 문제 확인 · [코드](ex1008/rag_agent/retriever.py)
- **[랭그래프로 RAG 에이전트 만들기](ex1008/RAG에이전트그래프.md)** — 관련성·환각 평가로 재검색·재생성, 찾은 문제 수정과 재실행 비교 · [코드](ex1008/rag_agent/agent.py)

### 2026-10-07
- **[코딩 에이전트](ex1007/코딩에이전트.md)** — 도구 설명서 비교, 코드 실행·파일 저장 도구, `create_agent` · [코드](ex1007/coding_agent/agent.py) · [도구](ex1007/coding_agent/tools.py) · [사용자 정의 도구](ex1007/coding_agent/custom_tools.ipynb)

### 2026-10-06
- **[웹 검색 에이전트](ex1006/웹검색에이전트.md)** — 도구 노드와 라우팅, 실행 방법 비교, `langgraph dev`와 LangSmith Studio · [코드](ex1006/web_agent.py)

### 2026-10-02
- **[랭그래프 에이전트 구현](ex1002/랭그래프에이전트구현.md)** — 입력·출력 상태 분리, 가드레일 노드와 조건부 엣지 · [코드](ex1002/design_agent.ipynb)
- **[타빌리 검색과 도구 호출](ex1002/타빌리검색도구호출.md)** — `TavilySearch`, `bind_tools`, 도구 설명서만큼 늘어나는 토큰 · [코드](ex1002/tavily_search.ipynb)

### 2026-10-01
- **[ChatOpenAI 번역](ex1001/ChatOpenAI번역.md)** — 첫 LLM 호출로 개발 환경 확인 · [코드](ex1001/translation.py)
- **[랭그래프 기본 개념](ex1001/랭그래프기본개념.md)** — 상태(TypedDict·Pydantic), 리듀서, 노드·엣지·조건부 엣지 · [코드](ex1001/try_langgraph.ipynb)

</details>

<details>
<summary><b>2026년 9월</b></summary>

### 2026-09-30
- **[RAG 실습 2: 생성형 AI 윤리 가이드북 QA](ex0930/RAG실습.md)** — 9/28 파이프라인을 30쪽 가이드북에 적용, 검색 후보·리랭커 개수 조정, 3문제 정답 확인 · [코드](ex0930/RAG.ipynb)

### 2026-09-29
- **[RAG 기본 파이프라인](ex0929/RAG기본파이프라인.md)** — 로드 → 분할 → 임베딩 → FAISS → 리트리버 → 프롬프트 → LLM → 체인 · [코드](ex0929/rag-basic-pdf.ipynb)
- **[문서 요약](ex0929/문서요약.md)** — Stuff, Map-Reduce, Map-Refine, Chain of Density 비교 · [코드](ex0929/summary.ipynb)
- **[RAGAS 테스트 데이터셋](ex0929/RAGAS테스트데이터셋.md)** — PDF로 평가용 질문·정답·근거 자동 생성 · [코드](ex0929/ragas_test_dataset.ipynb)
- **[RunnablePassthrough](ex0929/RunnablePassthrough.md)** — 입력 전달과 `.assign()`, RAG 체인 구성 · [코드](ex0929/runnable_passthrough.ipynb)

### 2026-09-28
- **[RAG 실습: 리랭커 기반 사내 문서 QA](ex0928/RAG실습.md)** — FAISS + Cross Encoder 리랭커, 임계값 대신 시스템 프롬프트로 "문서에 없는 답" 판별 · [코드 1(직접 작성)](ex0928/rag_01_0928.ipynb) · [코드 2(보강)](ex0928/rag_02_0928.ipynb)

### 2026-09-23
- **[VectorStore 리트리버](ex0923/벡터스토어리트리버.md)** — 기본·MMR·점수 임계값 검색, `ConfigurableField` · [코드](ex0923/vectorstore_retriever.ipynb)
- **[문맥 압축 리트리버](ex0923/문맥압축리트리버.md)** — 추출·필터·임베딩 필터, 압축 파이프라인 · [코드](ex0923/contextual_compression_retriever.ipynb)
- **[앙상블 리트리버](ex0923/앙상블리트리버.md)** — BM25(키워드) + FAISS(의미) 가중치 조합 · [코드](ex0923/ensemble_retriever.ipynb)
- **[Cross Encoder 리랭커](ex0923/크로스인코더리랭커.md)** — 1차 검색 후 재정렬(retrieve-then-rerank) · [코드](ex0923/cross_encoder_reranker.ipynb)
- **[Cohere 리랭커](ex0923/코히어리랭커.md)** — Cohere rerank API로 재정렬 · [코드](ex0923/cohere-reranker.ipynb)
- **[웹페이지 로더](ex0923/웹페이지로더.md)** — `WebBaseLoader`, 특정 영역만 파싱, 비동기 로드 · [코드](ex0923/web_base_loader.ipynb)
- **[부모 문서 리트리버](ex0923/부모문서리트리버.md)** — 작은 조각으로 검색하고 큰 부모 단위로 반환 · [코드](ex0923/parent_document_retriever.ipynb)

### 2026-09-22
- **[OpenAI 임베딩](ex0922/OpenAI임베딩.md)** — 문장 벡터화, 차원 축소, 코사인 유사도 · [코드](ex0922/openai_embeddings.ipynb)
- **[HuggingFace 임베딩](ex0922/허깅페이스임베딩.md)** — 원격·로컬 비교, bge-m3의 dense·sparse·ColBERT · [코드](ex0922/huggingface_embeddings.ipynb)
- **[Chroma 벡터 스토어](ex0922/크로마벡터스토어.md)** — 저장·검색·필터·CRUD·MMR, 이미지-텍스트 멀티모달 검색 · [코드](ex0922/chroma.ipynb)
- **[FAISS 벡터 스토어](ex0922/FAISS벡터스토어.md)** — 인덱스 구성, 저장·불러오기, 병합, 검색 전략 비교 · [코드](ex0922/FAISS.ipynb)

### 2026-09-21
- **[문자 텍스트 분할](ex0921/문자텍스트분할.md)** — `CharacterTextSplitter`, 문서별 metadata · [코드](ex0921/character_text_splitter.ipynb)
- **[재귀 문자 텍스트 분할](ex0921/재귀문자텍스트분할.md)** — 여러 구분자를 차례로 시도, `chunk_overlap` · [코드](ex0921/recursive_character_text_splitter.ipynb)
- **[토큰·문장 텍스트 분할](ex0921/토큰문장텍스트분할.md)** — tiktoken·`TokenTextSplitter`, spaCy 문장 분할 · [코드](ex0921/token_text_splitter.ipynb)
- **[HTML 헤더 텍스트 분할](ex0921/HTML헤더텍스트분할.md)** — 제목 태그 기준 분할, 실제 웹페이지에서 한계 확인 · [코드](ex0921/HTML_Header_text_splitter.ipynb)

### 2026-09-18
- **[대화 메모리](ex0918/대화메모리.md)** — `RunnableWithMessageHistory`로 세션별 대화 기록 · [코드](ex0918/conversation_memory.ipynb)
- **[문서 로더](ex0918/문서로더.md)** — PDF 로더 비교, 청크 분할, load/lazy_load/aload 비교 · [코드](ex0918/document_loader.ipynb)

### 2026-09-17
- **[LLM 응답 캐싱](ex0917/캐싱.md)** — InMemoryCache·SQLiteCache 속도 비교 · [코드](ex0917/cache.ipynb)
- **[체인 직렬화](ex0917/모델직렬화.md)** — dumpd·dumps, pickle·JSON 저장과 불러오기 · [코드](ex0917/model_serialization.ipynb)
- **[Google Gemini](ex0917/구글제미나이.md)** — 호출, 체인 재사용, 안전 설정, 멀티모달 · [코드](ex0917/google_generative.ipynb)
- **[토큰 사용량](ex0917/토큰사용량.md)** — 콜백으로 토큰 사용량 추적·합산 · [코드](ex0917/token_usage.ipynb)

### 2026-09-16
- **[Few-shot 프롬프트](ex0916/퓨샷프롬프트.md)** — Self-Ask 예시로 단계적 추론, `FewShotPromptTemplate` · [코드](ex0916/fewshot.ipynb)
- **[출력 파서](ex0916/아웃풋파서.md)** — `PydanticOutputParser`와 `with_structured_output()` 비교 · [코드](ex0916/output_parser.ipynb)
- **[판다스 기초](ex0916/판다스기초.md)** — Series·DataFrame, Titanic 데이터 필터링, loc·iloc · [코드](ex0916/csv.ipynb)
- **[쉼표 구분 리스트 파서](ex0916/쉼표구분리스트파서.md)** — 답변을 파이썬 리스트로, invoke·stream 비교 · [코드](ex0916/commaseparatedlist.ipynb)
- **[구조화된 출력](ex0916/구조화된출력.md)** — 답변과 출처를 객체로 받기 · [코드](ex0916/structured_output_parser.ipynb)

### 2026-09-15
- **[프롬프트 템플릿](ex0915/프롬프트템플릿.md)** — PromptTemplate·ChatPromptTemplate, `partial_variables`, yaml로 프롬프트 관리 · [코드](ex0915/ch05.ipynb)
- 멀티모달(이미지 입력) LLM 호출과 스트리밍 · [정리 문서](ex0915/프롬프트템플릿.md) · [코드](ex0915/multimodal.ipynb)

### 2026-09-14
- `.env`로 OpenAI API 키 관리 · [코드](ex0914/ch03.ipynb)
- **[LangChain으로 ChatOpenAI 호출](ex0914/랭체인.md)** — 응답 메타데이터, 토큰 사용량, logprobs, 스트리밍 · [코드](ex0914/ch04.ipynb)
- LangSmith 연동과 LangChain 에이전트(도구 호출) · [정리 문서](ex0914/랭체인.md) · [코드](ex0914/ch04_langsmith.ipynb)

### 2026-09-11
- **[OpenAI API 키 사용](ex0911/OpenAI가이드.md)** · [코드](ex0911/apikey_test.py)
- LangChain 프레임워크 연습 · [코드](ex0911/page92.ipynb)

### 2026-09-10
- 파이썬 제어문 · [딕셔너리](ex0910/dictionary.ipynb) · [if…else](ex0910/if_else.ipynb) · [match…case](ex0910/match_case.ipynb) · [while](ex0910/while.ipynb) · [for](ex0910/for.ipynb)
- **[FastAPI와 Streamlit 연결](ex0910/streamlit_fastapi.md)** · [FastAPI 코드](ex0910/proj_fastapi/main.py) · [Streamlit 코드](ex0910/proj_streamlit/app.py)

### 2026-09-09
- **[FastAPI GET·POST·PUT·DELETE](ex0909/FastAPI연습.md)** · [연습 코드](ex0909/main.py) · [최종 코드](ex0909_2/main.py)

### 2026-09-08
- **[FastAPI 기초](ex0908/fastapi_guide.md)** · [get](ex0908/main.py) · [put](ex0908/get_put.py) · [path parameters](ex0908/path_parameters.py) · [query parameters](ex0908/query_parameters.py)

### 2026-09-07
- **[Pydantic](ex0907/Pydantic.md)** · [코드 1](ex0907/pydantic.ipynb) · [코드 2](ex0907/day4_pydantic01.py) · [코드 3](ex0907/day4_pydantic02.py) · [코드 4](ex0907/day4_pydantic03.py)
- [try…except 예외 처리](ex0907/try_except.ipynb)
- [깃허브 충돌 해결 방법](ex0907/깃충돌해결법.md)

### 2026-09-04
- GitHub 사용법
- [GitHub Desktop 사용법](ex0904/깃허브데스크탑가이드.md)
- [문자열, 클래스, 딕셔너리, NumPy](ex0904/0904.ipynb)

### 2026-09-03
- [파이썬 함수와 클래스](ex0903/0903.ipynb)
- **[Streamlit](ex0903/streamlit가이드.md)** · [테스트 코드](ex0903/test.py)

### 2026-09-02
- [VS Code 설치](ex0902/VSCode설치가이드.md) · [Python 설치](ex0902/Python설치가이드.md) · [가상환경 세팅](ex0902/가상환경가이드.md)
- [파이썬 기초](ex0902/0902.ipynb)

### 2026-09-01
- 한화빌딩 기업 탐방(오리엔테이션)

</details>
