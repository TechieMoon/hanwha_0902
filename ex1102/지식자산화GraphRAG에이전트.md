# GraphRAG 응용: 프로젝트 산출물 지식 자산화 에이전트

> **한눈에 보기**
> - 문제: 프로젝트가 끝나면 설계서·결과보고서·이슈 목록이 **저장만 되고 재활용되지 않아** 비슷한 프로젝트에서 같은 시행착오가 반복된다
> - 해결: 산출물(Word·Excel)에서 **지식 카드**(적용기술 / 문제해결 / 교훈)를 뽑아 Neo4j에 쌓고, 도구 5개를 가진 에이전트가 **검색·출처 있는 Q&A·신규 프로젝트 추천**을 한다. Gradio 채팅 화면까지
> - "심플한 GraphRAG" 설계: LLM은 **정해진 칸(카드)만 채우고** 그래프는 코드(`MERGE`)가 만든다. Cypher는 개발자가 검증한 **고정 쿼리**를 쓰고 LLM은 도구와 파라미터만 고른다(Text2Cypher 대신)
> - 구조화된 Excel 이슈는 LLM 없이 코드로 카드 변환(정확·무료), 자유 문장인 Word만 LLM. 기술명은 사전으로 정규화(`카프카` → `Kafka`)
> - 실행 결과에서 본 것: 설계서에서 LLM이 **실제로 일어나지 않은 "문제해결" 카드와 내용 없는 "교훈" 카드**를 만들었고, 에이전트가 그 카드를 출처까지 붙여 답했다. 사람 확인 단계가 왜 필요한지 보여 준 사례

- 코드: [`exam15_1.ipynb`](exam15_1.ipynb) (강사님 자료 `fwedu/exam15_1.ipynb` 사본, 강의 슬라이드 이미지 포함, 📝 정리 셀 추가)
- 앞 내용: [10/30 Neo4j 그래프 DB와 GraphRAG](../ex1030/그래프DB와GraphRAG.md)
- 노트북이 만드는 실습 파일(`project_outputs/P001~P003/*.docx·xlsx`, `knowledge_cards_review.xlsx`)은 노트북 코드로 다시 만들 수 있어 저장소에 넣지 않았다.

## 전체 흐름

```
① 도큐먼트: 설계서.docx · 결과보고서.docx · 이슈목록.xlsx → 파싱 → 청크 → 임베딩
② 지식 카드: Excel 이슈 → 코드로 변환 / Word 보고서 → LLM이 칸 채우기  (+ 기술명 정규화, 사람 확인 엑셀)
③ 그래프: Project · Document · Chunk(벡터) · Card · Technology  ← UNWIND + MERGE
④ 에이전트: create_agent + 도구 5개 (벡터 검색 1, 고정 Cypher 3, LLM + 그래프 추천 1) + 대화 기억
⑤ 웹 데모: Gradio ChatInterface
```

**사용자 질문 → LLM 판단 → 도구 호출 → 결과 확인 → 필요하면 추가 도구 호출 → 최종 답변** (Tool-based Agentic RAG)

| | Chunk (15개) | Card (29개) |
|---|---|---|
| 저장하는 것 | 원문 + 임베딩 | 원문에서 뽑은 구조화된 지식 (유형·제목·요약·문제·해결·기술·태그) |
| 검색 방식 | 벡터 유사도 (VectorRAG) | 기술·유형·키워드 필터, 관계 탐색 (GraphRAG) |

## 1. 가상 프로젝트 산출물 (3개 프로젝트 × 3종 = 9개 파일)

| ID | 프로젝트 | 분야 | 주요 기술 |
|---|---|---|---|
| P001 | 스마트팩토리 설비 모니터링 | 제조 | Kafka, InfluxDB, Grafana, MQTT, FastAPI |
| P002 | 사내 문서 RAG 챗봇 | 사무 | LangChain, pgvector, PostgreSQL, BM25, Redis, FastAPI |
| P003 | 쇼핑몰 상품 추천 시스템 | 커머스 | Kafka, Spark, Redis, FastAPI |

Kafka·Redis·FastAPI를 일부러 여러 프로젝트에 겹치게 했다. 이 겹침이 그래프에서 "비슷한 프로젝트"를 찾는 연결 고리다. 프로젝트 기본 정보는 PMS의 구조화 데이터라고 가정하고 딕셔너리로 둔다. `python-docx`로 Word를, `pandas`로 Excel을 만든다.

## 2. 파싱 → 청크 → 임베딩

```python
def parse_docx(path) -> str:            # 문단을 읽고 제목 스타일이면 "## " 표시
    ...
def parse_xlsx(path) -> list[dict]:     # 행 = 딕셔너리
    return pd.read_excel(path).fillna("").to_dict("records")

splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50, separators=["\n## ", "\n", ". ", " "])
```

| 형식 | 파싱 | 청크 |
|---|---|---|
| Word | `python-docx` 문단, 제목은 `## ` | 글자 수 기준 분할 |
| Excel | `pandas` 행 | **이슈 1건 = 청크 1개** (이미 잘 나뉘어 있음) |

결과는 모두 `{"project_id", "file", "doc_type", "text"}` 모양으로 통일 → 청크 15개 × 1536차원(`text-embedding-3-small`). PDF·PPT는 `parse_pdf`(pypdf), `parse_pptx`(python-pptx) 파서만 추가하면 뒤 과정은 그대로다.

## 3. 지식 카드 추출

| 원천 | 추출 방법 | 이유 |
|---|---|---|
| 이슈 목록 (Excel) | **코드로 바로** 카드 변환 → 9개, LLM 호출 0회 | 이미 칸(현상·원인·해결·관련기술)이 나뉜 구조화 데이터 |
| 설계서·결과보고서 (Word) | LLM이 카드 칸 채우기 (`with_structured_output(CardList)`) → 20개 | 자유 문장이라 LLM이 필요. 단, **형식은 코드가 고정** |

```python
class Card(BaseModel):
    card_type: Literal["적용기술", "문제해결", "교훈"]
    title: str = Field(description="30자 이내 한 줄 제목")
    summary: str
    problem: str | None = None          # 문제해결 카드만
    solution: str | None = None
    technologies: list[str] = []
    tags: list[str] = []

# 기술명 정규화: 같은 기술이 다른 이름으로 들어오는 것을 막는다 (가장 쉬운 엔티티 해소)
ALIASES = {"카프카": "Kafka", "레디스": "Redis", "postgres": "PostgreSQL", "k8s": "Kubernetes", ...}
normalize_techs(["kafka", "레디스", "Fast API", "fastapi", "Spark"])   # ['FastAPI', 'Kafka', 'Redis', 'Spark']

make_card_id = lambda pid, title: "C-" + hashlib.md5(f"{pid}|{title}".encode()).hexdigest()[:8]   # 다시 실행해도 같은 ID
```

전체 카드 29개(문제해결 15, 적용기술 7, 교훈 7). 카드를 `knowledge_cards_review.xlsx`로 저장해 **사람이 확인한 뒤** 그래프에 넣는 것이 안전하다고 노트북도 안내한다.

### 실제로 나온 잘못된 카드

추출 프롬프트에 "글에 없는 내용은 만들지 마라. 단순 개요나 수치 보고만 있으면 카드를 만들지 마라."라고 적었지만, **설계서**(개요·아키텍처·기술 선정 이유만 있음)에서 이런 카드가 나왔다.

| 카드 | 원문 | 문제 |
|---|---|---|
| [문제해결] 데이터 수집 지연 문제 (P001 설계서) | "비기능 요구사항: 수집 지연 2초 이내" | 요구사항을 문제로 바꾸고, 해결책 "MQTT와 Kafka로 경로를 최적화해 지연을 최소화했다"를 **지어냈다** |
| [교훈] 쇼핑몰 상품 추천 시스템 교훈 (P003 설계서) | 설계서에 교훈 항목 없음 | 요약이 "다음 프로젝트에서 기억해야 할 점." 한 줄뿐인 **빈 카드** |
| [교훈] 다음 프로젝트에서 기억할 점 (P001) · 챗봇 구축 시 데이터베이스 선택의 중요성 (P002) | 기술 선정 이유 ("PostgreSQL 운영 경험이 많아 pgvector 선택" 등) | 기술 선정 이유를 "DB 선택이 중요하다" 같은 일반론 교훈으로 부풀림 |

그리고 이 카드들이 그대로 답변에 쓰였다(아래 6장). 카드 품질 문제는 그래프와 에이전트가 아무리 좋아도 고칠 수 없다. 개선 방법: 문서 유형별로 만들 수 있는 카드 유형을 제한(설계서 → 적용기술만), "요약이 원문 문장을 포함하는지" 같은 코드 검사, 사람 확인 엑셀에서 삭제 후 적재.

## 4. 그래프 구축 (Neo4j)

| 노드 | 고유 키 | 관계 | 의미 |
|---|---|---|---|
| `Project` | `id` | `(Project)-[:HAS_DOCUMENT]->(Document)-[:HAS_CHUNK]->(Chunk)` | 어휘 그래프 (원문 위치) |
| `Document` | `id` | `(Project)-[:HAS_CARD]->(Card)` | 프로젝트의 지식 카드 |
| `Chunk` | `id` (+ 벡터 인덱스) | `(Card)-[:FROM_CHUNK]->(Chunk)` | **출처** |
| `Card` | `id` | `(Card)-[:ABOUT]->(Technology)` | 카드의 관련 기술 |
| `Technology` | `name` | `(Project)-[:USES]->(Technology)` | 유사 프로젝트 찾기의 핵심 |

```cypher
CREATE CONSTRAINT card_id IF NOT EXISTS FOR (n:Card) REQUIRE n.id IS UNIQUE      -- 라벨마다
CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS FOR (c:Chunk) ON c.embedding
  OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}

UNWIND $rows AS row
MERGE (c:Card {id: row.card_id}) SET c.card_type = row.card_type, ...
```

- 적재 결과: Project 3, Document 9, Chunk 15, Card 29, Technology 12 (Neo4j Browser: 노드 68, 관계 139).
- 확인 쿼리: 기술을 공유하는 프로젝트 쌍 → RAG 챗봇 ↔ 추천 시스템 [Redis, FastAPI], 스마트팩토리 ↔ 추천 시스템 [Kafka].
- 임베딩 확인(Cypher 25): `size(c.embedding)`, `c.embedding[0..5]`, `count(c.embedding)`(null은 안 셈), `SHOW VECTOR INDEXES`, `vector.similarity.cosine(a.embedding, b.embedding)`, 그리고 `SEARCH` 절로 비슷한 청크 찾기.

## 5. 에이전트 도구 5개

| 도구 | 검색 방식 | 이런 질문에 |
|---|---|---|
| `search_documents(query)` | **벡터** (상위 4 청크 + 프로젝트·파일명) | "RAG 챗봇은 검색 정확도를 어떻게 올렸어?" |
| `search_knowledge_cards(technology, card_type, keyword)` | 그래프 필터 (조건은 필요한 것만, 기술명 정규화) | "Kafka 문제 해결 사례", "교훈만 모아줘" |
| `get_project_overview(project_name)` | 그래프 (이름 일부로 검색) | "추천 시스템 프로젝트 개요" |
| `find_related_by_technology(technology)` | 그래프 **2홉** (기술 → 프로젝트 → 다른 기술) | "Redis 쓴 프로젝트와 같이 쓴 기술은?" |
| `recommend_for_new_project(description)` | LLM이 기술 추출 + 공유 기술 수로 상위 3개 프로젝트와 카드 | "새 프로젝트를 시작하는데 참고할 것은?" |

```python
@tool
def search_knowledge_cards(technology: str | None = None,
                           card_type: Literal["적용기술", "문제해결", "교훈"] | None = None,
                           keyword: str | None = None) -> list[dict]:
    "지식 카드를 기술명·카드 유형·키워드로 찾는다. 조건은 필요한 것만 넣는다."
    return run('''
        MATCH (p:Project)-[:HAS_CARD]->(c:Card)-[:FROM_CHUNK]->(:Chunk)<-[:HAS_CHUNK]-(d:Document)
        WHERE ($card_type IS NULL OR c.card_type = $card_type)
          AND ($keyword IS NULL OR c.title CONTAINS $keyword OR c.summary CONTAINS $keyword)
        OPTIONAL MATCH (c)-[:ABOUT]->(t:Technology)
        WITH p, d, c, collect(t.name) AS techs
        WHERE $technology IS NULL OR $technology IN techs
        RETURN p.name AS project, d.file AS file, c.card_type AS card_type, c.title AS title, ...
        LIMIT 10''', technology=normalize_tech(technology) if technology else None, ...)
```

- `$x IS NULL OR …` 패턴으로 **선택 조건**을 Cypher 하나에 담았다. 모든 결과에 프로젝트명·파일명이 들어 있어 에이전트가 출처를 붙일 수 있다.
- 에이전트에 넣기 전에 **도구를 하나씩 먼저 테스트**했다. 문제가 생겼을 때 도구 문제인지 에이전트 판단 문제인지 구분하기 쉽다(`카프카` → Kafka 정규화도 여기서 확인).
- `search_documents`는 아직 `db.index.vector.queryNodes`를 써서 실행할 때마다 deprecated 경고가 나온다. 같은 노트북 4장에서 소개한 `SEARCH` 절로 바꿀 수 있다.

## 6. 지식 자산화 에이전트

```python
SYSTEM_PROMPT = '''너는 회사의 '기술 지식 자산화 도우미'다.
[도구 선택] 특정 기술의 문제 해결 사례·교훈 → search_knowledge_cards / 구체적 설명·수치 → search_documents / ...
[답변 규칙] 반드시 도구 결과에 있는 내용만 쓴다. 없으면 "지식 베이스에서 찾지 못했습니다".
           사실마다 끝에 (출처: 프로젝트명 / 파일명). 문제 해결 사례는 '문제 → 원인 → 해결' 순서.'''

kb_agent = create_agent(model=llm, tools=TOOLS, system_prompt=SYSTEM_PROMPT,
                        middleware=[ModelCallLimitMiddleware(run_limit=8, exit_behavior="end")],   # 도구 무한 호출 방지
                        checkpointer=InMemorySaver())                                              # thread_id별 대화 기억
```

| 질문 | 고른 도구 | 결과 |
|---|---|---|
| Kafka 관련 문제와 해결 | `search_knowledge_cards` | 수집 지연(파티션 1 → 6, 컨슈머 3대), 이벤트 유실(acks=1 → all) 등 3건. 그런데 2번째 사례가 **설계서에서 지어낸 "데이터 수집 지연 문제" 카드**였고, 원인을 "비기능 요구사항"이라고 적었다 |
| RAG 챗봇 검색 정확도와 수치 | `search_documents` | BM25 + 벡터 하이브리드 검색, 64% → 82% (출처: 결과보고서.docx) |
| Redis를 쓴 프로젝트와 같이 쓴 기술 | `find_related_by_technology` | 추천 시스템(FastAPI, Kafka, Spark), RAG 챗봇(OpenAI, BM25, FastAPI, PostgreSQL, pgvector, LangChain) |
| 모든 프로젝트의 교훈 | `search_knowledge_cards` | 부하 테스트·보관 정책, 평가셋 먼저, A/B 테스트 등. 빈 카드도 섞여 "**다음 프로젝트에서 기억해야 할 점이 있다**"가 교훈 항목으로 나왔다 |
| 물류센터 IoT(Kafka + FastAPI + Redis) 신규 프로젝트 | `recommend_for_new_project` → `find_related_by_technology` | 공유 기술 3개인 추천 시스템을 1순위로, 각 프로젝트의 문제해결·교훈 카드와 출처 |
| (같은 thread) 가장 먼저 챙길 한 가지는? | 도구 없음 | 앞 대화를 기억해 "Kafka 이벤트 유실 모니터링" |

- 고정 Cypher 도구라 **검색 동작은 매번 같고** 출처 표시 규칙도 잘 지켰다. 틀린 부분은 모두 **카드 자체**에서 왔다. 출처가 붙어 있으니 오히려 믿기 쉬워진다는 점이 더 위험하다.

## 7~8. 지식 카드 샘플과 Gradio 데모

- 카드를 `| 항목 | 내용 |` 마크다운 표(요약·문제·해결·기술·태그·출처)로 출력해 그대로 결과물로 쓸 수 있게 했다.
- `gr.ChatInterface(fn=chat, additional_inputs=[session])`로 채팅 화면을 띄우고, `gr.State(lambda: str(uuid.uuid4()))`로 **브라우저 탭마다 다른 `thread_id`**를 줘 대화 기억이 섞이지 않게 했다. `demo.launch()` → `http://127.0.0.1:7860`.

## 정리: 왜 "심플한 GraphRAG"인가

| 어려운 부분 | 피한 방법 |
|---|---|
| 문서에서 그래프 자유 추출 | LLM은 카드 칸 채우기만, 노드·관계 이름은 코드에 고정 |
| 엔티티 해소 | 합쳐야 할 대상은 기술명뿐 → 사전(`ALIASES`)으로 정규화 |
| Text2Cypher의 불안정성 | 검증된 고정 Cypher 도구 |
| 추출 결과 검증 | 카드를 엑셀로 저장해 사람이 확인 — **이번 실행에서 실제로 필요했다** |

| 질문 | 벡터 RAG | 이 그래프 |
|---|---|---|
| "Kafka 문제 해결 사례 **모두**" | 비슷한 청크 몇 개만 | `(Card)-[:ABOUT]->(Kafka)` 전부 |
| "Redis 쓴 프로젝트와 **같이 쓴 기술**" | 여러 문서를 이어야 해서 어려움 | 2홉 `Technology ← Project → Technology` |
| "새 프로젝트와 **기술이 겹치는** 과거 프로젝트" | 설명이 비슷한 문서 | 공유 기술 **개수로 순위** |
| "HR-204 규정은?" 같은 원문 질문 | ✅ | 벡터 도구를 함께 쓰므로 ✅ |

## 🔁 복습 질문

<details>
<summary>1. 이슈 목록(Excel)은 LLM 없이 카드로 바꾼 이유는?</summary>

이미 현상·원인·해결·관련기술 칸이 나뉜 구조화 데이터라 코드로 바로 옮기면 정확하고 비용이 없다. LLM은 자유 문장(Word)에만 쓴다.
</details>

<details>
<summary>2. 기술명 정규화를 하지 않으면 그래프에서 어떤 문제가 생기나?</summary>

`Kafka`와 `kafka`, `카프카`가 서로 다른 Technology 노드가 되어 같은 기술을 쓴 프로젝트가 연결되지 않는다. 유사 프로젝트 추천과 기술별 카드 검색이 빠진다.
</details>

<details>
<summary>3. 설계서에서 "문제해결" 카드가 만들어진 것을 막으려면?</summary>

문서 유형별로 허용할 카드 유형을 제한하고(설계서 → 적용기술), 사람 확인 엑셀에서 걸러 낸 뒤 적재한다. 프롬프트의 "지어내지 마라"만으로는 막지 못했다.
</details>

<details>
<summary>4. Text2Cypher 대신 고정 Cypher 도구를 쓴 장단점은?</summary>

장점: 검증된 쿼리라 결과가 안정적이고 쓰기 쿼리 위험이 없다. 단점: 도구가 다루지 않는 질문에는 답할 수 없다(확장 과제: 읽기 전용 Text2Cypher를 보조 도구로 추가).
</details>

<details>
<summary>5. Gradio 데모에서 탭마다 uuid로 thread_id를 만든 이유는?</summary>

같은 thread_id를 쓰면 서로 다른 사용자의 대화 기억이 섞인다. 접속마다 새 대화로 분리한다.
</details>
