# LangChain으로 RAG: pgvector 저장·검색, LCEL 없이 vs LCEL로

> **한눈에 보기**
> - 10/15에 OpenAI SDK + SQL로 직접 짰던 RAG를 **LangChain 부품**으로 다시 만들었다: `OpenAIEmbeddings` + `PGEngine`/`PGVectorStore`(pgvector) + `as_retriever()` + `ChatPromptTemplate` + `ChatOpenAI`
> - `add_documents()` 한 줄이 **임베딩 계산 + INSERT**를, `similarity_search()`가 `ORDER BY embedding <=> ... LIMIT k`를 대신한다
> - **A. LCEL 없이**(검색 → 포맷 → 프롬프트 → 모델을 하나씩 `invoke`) vs **B. LCEL로**(`{"context": retriever | format_docs, "question": RunnablePassthrough()} | prompt | llm | parser`) — 결과는 같다
> - LCEL은 조립을 쉽게 할 뿐 **검색 정확도나 사실성을 올려 주지 않는다**
> - 같은 체인으로 항공 가이드(15건), ERP PDF(28쪽)까지 문서 집합만 바꿔 재사용, `batch()`로 질문 여러 개를 한 번에 처리

- 코드: [`exam4.ipynb`](exam4.ipynb) (강사님 자료 `fwedu/exam4.ipynb` 사본, 슬라이드 이미지는 자리만 표시, 📝 정리 셀 추가)
- 실행 환경: langchain 1.4.6, langchain-postgres 0.0.19, PostgreSQL + pgvector(도커 `edupgvector`), `text-embedding-3-small`(1536차원), `gpt-4o-mini`
- 이전 방식: [10/15 RAG](../ex1015/RAG.md) · [임베딩과 벡터 DB](../ex1015/임베딩과벡터DB.md) · [10/19 LCEL과 Runnable](../ex1019/LCEL과Runnable.md)
- 샘플 문서 중 강사님 개인 정보(이름·별명·사는 곳)가 들어 있던 문장은 사본에서 **가상의 값(홍길동 등)으로 바꿨다.** 유사도 점수는 원래 문장으로 계산된 값이다.

## 1. 직접 SQL vs LangChain

| 단계 | OpenAI SDK + 직접 SQL (10/15) | LangChain (10/20) |
|---|---|---|
| 임베딩 | `client.embeddings.create(...)` | `OpenAIEmbeddings(...)` — VectorStore가 알아서 호출 |
| 테이블 | `CREATE TABLE ... vector(1536)` | `engine.init_vectorstore_table(table_name, vector_size, overwrite_existing=True)` |
| 저장 | 임베딩 계산 + `INSERT` | `store.add_documents([Document(...)])` |
| 검색 | `ORDER BY embedding <=> :q LIMIT k` | `store.similarity_search(q, k)` / `retriever.invoke(q)` |
| 생성 | 메시지 조립 + `responses.create` | `prompt \| llm \| StrOutputParser()` |

```python
engine = PGEngine.from_connection_string(url="postgresql+psycopg://edu:1234@localhost:5432/edudb")
engine.init_vectorstore_table(table_name="fwmydoc1", vector_size=1536, overwrite_existing=True)
store = PGVectorStore.create_sync(engine=engine, table_name="fwmydoc1", embedding_service=embeddings)
store.add_documents([Document(page_content=text, metadata={"topic": topic}) for topic, text in SAMPLE_DOCS])
```

- `overwrite_existing=True`는 **테이블을 지우고 다시 만든다.** 실습용 테이블에서만 쓴다. (10/15에 같은 문서를 다시 넣으면 중복 저장되던 문제를 이 방식으로 피했다.)
- Windows에서 psycopg 비동기 연결을 쓰려면 `asyncio.WindowsSelectorEventLoopPolicy()`로 이벤트 루프를 바꿔 줘야 했다.
- 이미 저장된 테이블은 `PGVectorStore.create_sync(..., table_name=기존테이블)`로 **다시 연결만** 하면 된다(다시 임베딩하지 않음). 단, 저장할 때와 **같은 임베딩 모델**을 써야 한다.

## 2. 검색만 먼저 (LLM 없이)

```python
store.similarity_search("강사님에게 어떤 음식을 사 가면 좋을까?", k=2)   # Document 리스트
store.as_retriever(search_kwargs={"k": 2}).invoke(question)               # Retriever 표준 인터페이스
```

두 방식 모두 같은 결과(강사 문서 → RAG 문서)였다. `retriever`는 Runnable이라 LCEL 체인에 바로 넣을 수 있다.

`similarity_search_with_score("떡볶이")`의 점수는 **거리**라서 코드에서 `1 - score`로 바꿔 출력했다(라벨은 raw score였지만 실제로는 코사인 유사도). 정답 문서도 **0.24** 정도였고, 나머지는 0.07~0.09였다. 10/15에 확인한 것처럼 **단어 하나짜리 질문은 유사도가 낮게 나온다** → 절대값보다 순위를 본다.

## 3. A. LCEL 없이 vs B. LCEL로

```python
# A. 한 단계씩 (디버깅이 쉽다)
def ask_rag_without_lcel(question):
    docs = retriever.invoke(question)                                  # 1. 검색
    context = format_docs(docs)                                        # 2. 문서 → 문자열
    messages = prompt.invoke({"context": context, "question": question})  # 3. 프롬프트
    return llm.invoke(messages).content                                # 4. 모델

# B. LCEL (조립·교체·batch/stream이 쉽다)
rag_with_lcel = (
    {"context": retriever | RunnableLambda(format_docs),
     "question": RunnablePassthrough()}
    | prompt | llm | StrOutputParser()
)
```

- `retriever | prompt`만 이으면 안 된다. 프롬프트는 `{context, question}` dict를 기대하는데 retriever는 Document 리스트를 내놓기 때문이다 → 위처럼 **입력 매핑 dict**가 필요하다.
- 질문 4개를 두 방식에 똑같이 넣었더니 답이 글자까지 같았다(temperature=0).

| 질문 | 검색된 문서 | 답 |
|---|---|---|
| AX 전환이 무슨 뜻이야? | AX, Embedding | 문서 내용대로 답함 ✅ |
| 강사님이 좋아하는 음식은? | 강사, RAG | 떡볶이 ✅ |
| RAG는 왜 사용하나요? | RAG, Docker | 문서 내용대로 답함 ✅ |
| 강사님의 전화번호는? | 강사, RAG | "제공된 자료에서 확인할 수 없습니다" ✅ |

- k=2라서 관련 없는 문서도 항상 하나씩 같이 들어왔다. 그래도 시스템 프롬프트("근거에 기반해서만, 없으면 확인할 수 없다고")가 있어 **없는 정보(전화번호)를 지어내지 않았다.**

## 4. 문서 집합만 바꿔 재사용

- **항공 이용 가이드 15건**(10/15 데이터)을 `fwmydoc3` 테이블에 넣고 같은 체인 구조로 질문했다. "배가 고픈데, 비행기에 타면 식사는 언제 나오나요?" → 1위 "기내 식사 서비스"를 찾아 장거리 2회/중거리 1회/단거리 간식으로 정확히 답했다. 2·3위(항공권 변경, 공항 도착 시간)는 관련이 없었다 — k개는 관련이 있든 없든 채워진다.
- **PDF**: `PdfReader`로 쪽마다 `Document` → `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)` → `fwmydoc4`에 저장. 28쪽이 28청크가 됐다(쪽 수와 청크 수가 같다 = 대부분 쪽이 1000자 안쪽). 스캔 PDF는 OCR이 필요하다. (실습 PDF는 다른 회사 자료라 저장소에 넣지 않았다.)

## 5. 질문 여러 개 한 번에: batch

```python
# 단계별 batch
docs_batch = retriever.batch(questions)
messages_batch = prompt.batch([{"context": format_docs(d), "question": q} for q, d in zip(questions, docs_batch)])
responses = llm.batch(messages_batch)

# 체인 통째로 batch
answers = rag_chain.batch(questions, config={"max_concurrency": 3})
```

ERP 질문 3개(제약 GMP, 의료기기 원가, 화장품 3PL 연동)를 두 방법으로 돌렸고 답이 거의 같았다. 체인으로 묶어 두면 `batch` 한 줄로 끝나고, `max_concurrency`로 동시에 보내는 요청 수를 제한할 수 있다.

## 정리

| 관점 | A. LCEL 없이 | B. LCEL로 |
|---|---|---|
| 읽는 방식 | 위에서 아래로 함수 호출 | `\|`로 데이터 흐름 선언 |
| 검색 | `retriever.invoke()` | `retriever` 자체를 체인 부품으로 |
| 문맥 가공 | `format_docs(docs)` | `RunnableLambda(format_docs)` |
| 장점 | 단계별 디버깅, 처음 배울 때 직관적 | 조립·교체, `batch`/`stream` 활용 |

## 🔁 복습 질문

<details>
<summary>1. <code>store.add_documents()</code>가 내부에서 하는 두 가지 일은?</summary>

각 문서의 임베딩을 계산하고(`OpenAIEmbeddings` 호출), 본문·메타데이터·벡터를 PostgreSQL 테이블에 INSERT한다.
</details>

<details>
<summary>2. <code>similarity_search()</code>와 <code>as_retriever().invoke()</code>의 차이는?</summary>

검색 결과(Document 리스트)는 같다. retriever는 Runnable 표준 인터페이스라 LCEL 체인에 부품으로 넣거나 `batch`할 수 있다.
</details>

<details>
<summary>3. <code>retriever | prompt</code>로 바로 이으면 왜 안 되나?</summary>

retriever는 Document 리스트를 내놓는데 프롬프트는 `{context, question}` dict를 기대한다. `{"context": retriever | format_docs, "question": RunnablePassthrough()}`로 입력을 만들어 줘야 한다.
</details>

<details>
<summary>4. LCEL로 바꾸면 RAG 답변이 더 정확해지나?</summary>

아니다. 같은 단계를 다르게 조립할 뿐이라 결과가 같았다. 정확도는 검색(청크, k, 임베딩)과 프롬프트가 정한다.
</details>

<details>
<summary>5. 문서에 없는 "전화번호"를 지어내지 않은 이유는?</summary>

시스템 프롬프트에 "참고 문서에 근거해서만 답하고, 없으면 확인할 수 없다고 답하라"고 적었기 때문이다.
</details>

<details>
<summary>6. 이미 저장된 pgvector 테이블을 다시 쓸 때 주의할 점은?</summary>

다시 임베딩할 필요 없이 테이블에 연결만 하면 되지만, 질문도 저장할 때와 같은 임베딩 모델로 벡터화해야 한다. `overwrite_existing=True`로 초기화하면 저장된 데이터가 지워진다.
</details>
