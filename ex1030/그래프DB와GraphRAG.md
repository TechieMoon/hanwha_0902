# Neo4j 그래프 DB와 GraphRAG

> **한눈에 보기**
> - 벡터 RAG(pgvector)는 "비슷한 문장"은 잘 찾지만 **여러 문서에 흩어진 사실 잇기(멀티홉)**, **"모두"·"몇 명" 같은 정확한 집계**에 약하다. 관계 자체를 데이터로 저장하는 그래프 DB(Neo4j)로 이를 보완한다
> - **1부 Cypher**: 노드·관계·속성, `CREATE` vs `MERGE`, 유일성 제약, 패턴 매칭, 멀티홉, 경로 탐색(`shortestPath`), 집계·추천·영향 분석, 유연한 스키마, 인덱스와 `PROFILE`
> - **2부 GraphRAG**: `SimpleKGPipeline`으로 LLM이 문서 10개를 지식 그래프로 변환 → 벡터 인덱스 + `SEARCH` 절 → 벡터로 찾고 그래프로 넓히는 `VectorCypherRetriever` → 개수·목록은 `Text2CypherRetriever` → 에이전트가 두 검색을 골라 씀
> - 같은 질문 4개로 비교: 멀티홉·목록은 GraphRAG만 답했지만, GraphRAG도 **근거에 있는 사람을 빠뜨리거나**, 벡터 RAG가 **없는 관계를 "근거 경로"로 지어내는** 경우가 있었다

- 코드: [`exam15.ipynb`](exam15.ipynb) (강사님 자료 `fwedu/exam15.ipynb` 사본, 강의 슬라이드 이미지 포함, 📝 정리 셀 추가)
- 이어지는 수업: [11/2 지식 자산화 GraphRAG 에이전트](../ex1102/지식자산화GraphRAG에이전트.md)
- 실습 데이터의 인물 이름(유니코·도우너·둘리 등)과 회사(넥스트AI·클라우드웨이)는 교안의 가상 예제다.

## 0. 실습 환경

```yaml
# docker-compose.yml (강사님 제공, 교안 3.3절)
services:
  neo4j:
    image: neo4j:2026.09.0          # Community Edition
    container_name: neo4j-edu
    ports:
      - "7474:7474"                 # Neo4j Browser (웹 화면)
      - "7687:7687"                 # Bolt (Python 드라이버 접속)
    environment:
      NEO4J_AUTH: neo4j/<로컬 실습용 비밀번호>
      NEO4J_PLUGINS: '["apoc"]'     # APOC 플러그인 (Text2Cypher 자동 스키마 등에 사용)
    volumes:
      - neo4j_data:/data            # 컨테이너를 지워도 데이터 유지
volumes:
  neo4j_data:
```

- `docker compose up -d` → `http://localhost:7474`에서 Neo4j Browser 접속(`neo4j://localhost:7687`).
- 환경변수 `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `OPENAI_API_KEY`를 `setx`로 등록. 라이브러리: `neo4j==6.4.1`, `neo4j-graphrag[openai]==1.22.0`.
- 공통 함수 `run(query, **params)`는 Cypher 결과를 DataFrame으로, `draw()`는 networkx로 그래프를 그린다.

## 1부. 그래프 DB 기초 — Cypher

### 1단계. 노드·관계·속성

| 구성 요소 | Cypher 표기 | 예 |
|---|---|---|
| 노드 | `( )` | `(u:Person {name:'유니코'})` |
| 관계 (방향 + 타입) | `-[ ]->` | `-[:WORKS_AT {since: 2023}]->` |
| 속성 | `{키: 값}` | `{role: '데이터 엔지니어'}` |
| 라벨 | `:이름` | `:Person` — 테이블이 아니라 노드에 붙이는 **이름표**(여러 개 가능) |

```cypher
CREATE (u:Person {name: '유니코', role: '데이터 엔지니어'})-[:WORKS_AT {since: 2023}]->(c:Company {name: '넥스트AI'})
MATCH (p:Person)-[r:WORKS_AT]->(c:Company) RETURN p.name, p.role, r.since, c.name
```

`SET`은 미리 정의하지 않은 속성도 바로 추가한다(ALTER TABLE이 필요 없음). 노드를 지울 때는 관계까지 `DETACH DELETE`.

### 2단계. `CREATE`와 `MERGE` — 중복의 함정

| | 같은 명령 두 번 실행 |
|---|---|
| `CREATE (:Person {name:'둘리'})` | **2개** 생김 (중복) |
| `MERGE (:Person {name:'둘리'})` | **1개** 그대로 (있으면 찾고, 없으면 만든다) |

실무 규칙: 데이터를 쌓을 때는 **`MERGE` + 유일성 제약조건**(`CREATE CONSTRAINT … REQUIRE n.name IS UNIQUE`)을 기본으로 쓰고, `MERGE`에는 고유 키만 넣고 나머지 속성은 `SET`으로 붙인다.

### 3단계. 실습 데이터

사람 4명(유니코·도우너·둘리·또치), 회사 2개, 프로젝트 2개(스마트상담봇·문서검색엔진), 기술 4개 → **노드 12개, 관계 20개**. 같은 셀을 다시 실행해도 `MERGE`라서 늘어나지 않는다.

### 4~7단계. 그래프가 잘하는 질문

| 질문 | Cypher 핵심 | 결과 |
|---|---|---|
| 넥스트AI 직원 | `(p:Person)-[r:WORKS_AT]->(:Company {name:'넥스트AI'})` | 유니코(2023), 도우너(2024) |
| 서로 아는 사이 | `(a)-[:KNOWS]-(b)` (방향 무시) | |
| **멀티홉** 유니코 회사의 프로젝트가 쓰는 기술 | `(:Person)-[:WORKS_AT]->(c)-[:DEVELOPS]->(p)-[:USES]->(t)` | 스마트상담봇: LangGraph, Neo4j — SQL이면 JOIN 6개 |
| 친구의 친구 | `(me)-[:KNOWS]-{2}(fof)` | 둘리 |
| 최단 경로 유니코 → PostgreSQL | `allShortestPaths((a)-[*..6]-(b))` | 3홉 경로 **2개** |
| 소개 경로 (사람 관계 + 기술 보유만) | `shortestPath((a)-[:KNOWS\|HAS_SKILL*..6]-(b))` | 유니코 → 도우너 → 둘리 → PostgreSQL |
| 집계: 기술별 보유 인원 | `count(p)`, `collect(p.name)` | |
| 추천: 동료가 가진 기술 중 나에게 없는 것 | `WHERE NOT (me)-[:HAS_SKILL]->(t)` | LangGraph (도우너) |
| 영향 분석: PostgreSQL 장애 | 기술 ← 프로젝트 ← 참여자 | 문서검색엔진 [또치, 둘리] |
| `WITH`로 단계 나누기 | 직원 2명 이상인 회사의 프로젝트 | |

> 벡터 RAG는 Top-k 청크만 보기 때문에 "모두", "몇 명"에 약하다. 그래프는 관계를 끝까지 따라가 **빠짐없이** 센다.

### 8~9단계. 유연한 스키마, 인덱스

- `UNWIND $rows AS row MERGE …`로 여러 건을 한 번에 적재(배치).
- 처음 보는 라벨(`Certificate`)과 관계(`MENTORS`, `HOLDS`)를 테이블 변경 없이 바로 추가 → "Neo4j를 다룰 줄 아는 사람과 멘토" 질문이 바로 가능.
- `PROFILE`로 실행 계획을 보면 유일성 제약이 만든 인덱스로 시작 노드를 찾는 **`NodeUniqueIndexSeek`**가 보인다. 그래프 탐색은 "시작 노드 하나를 빨리 찾고 → 관계를 따라가기"이므로 시작점 속성에 인덱스가 중요하다.

## 2부. GraphRAG — 문서를 지식 그래프로

### 10~11단계. 문서 10개 → 지식 그래프 (`SimpleKGPipeline`)

```python
SCHEMA = {
    "node_types": [
        {"label": "Person", "description": "사람. 이름은 문서에 쓰인 그대로 (예: '희동이는' → '희동이')",
         "properties": [{"name": "name", "type": "STRING"}, {"name": "role", "type": "STRING"}]},
        {"label": "Technology", "description": "… 이름은 제품명만 짧게 (예: 'Neo4j 그래프 데이터베이스' → 'Neo4j')"},
        ...
    ],
    "relationship_types": [
        {"label": "USES", "description": "프로젝트가 쓰는 기술. 주어가 사람이면 USES가 아니라 HAS_SKILL"}, ...
    ],
    "patterns": [("Person", "WORKS_AT", "Company"), ("Project", "USES", "Technology"), ...],
}
kg_builder = SimpleKGPipeline(llm=extract_llm, driver=driver, embedder=embedder, schema=SCHEMA,
                              text_splitter=FixedSizeSplitter(chunk_size=300, chunk_overlap=30))
await kg_builder.run_async(text=doc)    # .py 파일에서는 asyncio.run(...)
```

- 결과는 두 층: **어휘 그래프**(Document 10, Chunk 10 + 임베딩) + **지식 그래프**(Person 6, Technology 6, Project 2, Company 2). 엔티티는 `FROM_CHUNK`로 원문 청크와 연결돼 근거를 추적할 수 있다.
- 스키마 설명에 "이름은 그대로", "사람이면 HAS_SKILL"처럼 **헷갈리는 경우를 예시로** 적어 추출 품질을 맞췄다.
- 품질 점검에서 발견: 스키마에 넣은 `role` 속성이 **6명 모두 None**이었다(문서에는 "데이터 엔지니어" 등이 있음). 도우너·또치는 보유 기술이 빈 목록이었다. GraphRAG는 그래프에 있는 사실을 그대로 믿으므로 **추출 결과를 먼저 확인**해야 한다.

### 12단계. 벡터 인덱스와 `SEARCH` 절

```cypher
CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS FOR (c:Chunk) ON (c.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}

CYPHER 25
MATCH (c:Chunk)
  SEARCH c IN (VECTOR INDEX chunk_embedding FOR $qv LIMIT $k) SCORE AS score
RETURN round(score, 3) AS 유사도, c.text AS 청크
```

- "상담 이력은 어디에 저장하나요?" → 유사도 0.723으로 스마트상담봇 청크.
- 예전 방식 `CALL db.index.vector.queryNodes(...)`도 같은 결과지만 이제 **deprecated 경고**가 나온다(SEARCH로 대체).
- Neo4j 벡터 검색의 장점: 찾은 청크에서 **같은 쿼리 안에서** `<-[:FROM_CHUNK]-(e)-[r]-(nb)`로 그래프를 이어 갈 수 있다. pgvector라면 SQL을 따로 짜야 한다.

### 13단계. 벡터 RAG vs GraphRAG — 같은 질문, 다른 근거

GraphRAG 검색 쿼리(`VectorCypherRetriever`의 `retrieval_query`): 벡터로 찾은 청크 → 그 청크의 엔티티 → **1~2홉 이웃 관계**까지 모아 `[문서] + [관계 사실]`로 LLM에 넘긴다.

```cypher
WITH node AS chunk, score
OPTIONAL MATCH (chunk)<-[:FROM_CHUNK]-(e:__Entity__)
OPTIONAL MATCH path = (e)-[r WHERE type(r) <> 'FROM_CHUNK']-{1,2}(nb:__Entity__)
...
RETURN chunk.text AS text, [x IN rels | startNode(x).name + ' -[' + type(x) + ']-> ' + endNode(x).name] AS facts, score
```

| 질문 | 벡터 RAG (`top_k=2`) | GraphRAG |
|---|---|---|
| ① 스마트상담봇은 상담 이력을 어디에 저장? (한 문서) | 정답. 그런데 답에 붙인 "근거 경로"가 `-[SAVES_DATA_IN]->` — **그래프에 없는 관계**를 지어냈다 | 정답 (`스마트상담봇 -[USES]-> Neo4j`) |
| ② 유니코 회사의 대표 제품은 어떤 DB? (멀티홉) | "근거에서 찾을 수 없습니다" | 정답: 유니코 → 넥스트AI → 스마트상담봇 → Neo4j |
| ③ 넥스트AI 직원 모두 (목록) | 찾을 수 없음 | 4명 |
| ④ PostgreSQL 장애 시 영향받는 사람 | 둘리만. 경로 `PostgreSQL -[PARTICIPATES_IN]->` 같은 **틀린 경로** | **둘리만** — 근거의 관계 사실에 `또치 -[PARTICIPATES_IN]-> 문서검색엔진`이 있었는데도 빠뜨림. 경로 방향도 반대로 씀 |

- 1부의 직접 Cypher는 ④를 [또치, 둘리]로 정확히 답했다. GraphRAG는 근거를 잘 모아도 **답을 만드는 LLM이 근거를 다 읽고 쓰지 않을 수 있다.** 근거가 길면(관계 사실 수십 줄) 더 심하다.
- 디버깅 순서(13-1): ① 추출된 그래프에 사실이 있나 → ② 검색 결과(context)에 들어갔나 → ③ LLM이 그걸 썼나. 답보다 **근거(context)를 먼저** 본다.

### 14단계. Text2Cypher — "몇 명", "모두"에 정확히

LLM이 질문을 Cypher로 **번역**하고, 실행 결과 행을 근거로 답한다.

```python
EXAMPLES = [
    "USER INPUT: 클라우드웨이 직원은 몇 명이야? "
    "QUERY: MATCH (p:Person)-[:WORKS_AT]->(c:Company {name:'클라우드웨이'}) RETURN count(p) AS 인원",
    ...   # few-shot: '대표 제품' = 회사가 DEVELOPS 한 Project
]
t2c_retriever = Text2CypherRetriever(driver=driver, llm=answer_llm, examples=EXAMPLES,
                                     result_formatter=format_row)   # neo4j_schema를 생략하면 APOC로 자동 조회
```

| 질문 | 생성된 Cypher | 답 |
|---|---|---|
| 넥스트AI 직원은 모두 몇 명? | `MATCH (p:Person)-[:WORKS_AT]->(c:Company {name:'넥스트AI'}) RETURN count(p)` | 4명 |
| Neo4j를 다룰 줄 아는 사람은? | `…-[:HAS_SKILL]->(:Technology {name:'Neo4j'})` | 유니코, 희동이 |
| PostgreSQL 프로젝트 참여자는? | `…-[:PARTICIPATES_IN]->(proj)-[:USES]->(…)` | 둘리, 또치 |

- 같은 개수 질문을 `compare()`로 하면 벡터 RAG도 GraphRAG도 "찾을 수 없습니다". 청크 2개로는 4명을 셀 수 없다.
- **스키마**: 자동 스키마는 처음 한 번만 읽고, `Chunk`·`FROM_CHUNK`·`embedding` 같은 내부 구조까지 섞인다. 자동 스키마를 초안으로 출력해 필요한 부분만 남기고 **값 예시**("이름은 띄어쓰기 없이 '넥스트AI'")를 주석으로 붙이면 정확도가 오른다.
- **보안**: LLM이 만든 쿼리가 `DETACH DELETE`일 수도 있다. 읽기 전용 계정, `routing_=RoutingControl.READ`, `CREATE`/`MERGE`/`DELETE`/`SET` 포함 쿼리 차단.

| 비교 | VectorCypherRetriever | Text2CypherRetriever |
|---|---|---|
| 출발점 | 질문과 의미가 비슷한 청크 | 질문에 나온 조건 그대로 |
| 잘하는 질문 | 설명, 맥락, 멀티홉 관계 | 개수, 목록, 조건 필터 |
| 약한 질문 | "모두", "몇 명" | 설명형·요약형 |
| 결과 안정성 | 쿼리가 고정이라 예측 가능 | LLM이 매번 쿼리를 써서 변동 가능 |

### 15단계. 에이전트가 검색을 고르기

```python
@tool
def search_documents(question: str) -> str:
    "문서의 설명·맥락, 그리고 여러 단계로 이어진 관계가 필요할 때 사용한다."   # → VectorCypherRetriever
@tool
def query_graph(question: str) -> str:
    "개수, 목록, 조건 필터처럼 정확한 값이 필요할 때 사용한다."               # → Text2CypherRetriever (실패하면 '조회 실패' 문자열)

agent = create_agent(model=ChatOpenAI(model="gpt-4o-mini", temperature=0),
                     tools=[search_documents, query_graph], system_prompt=SYSTEM_PROMPT)
```

- "넥스트AI 직원은 몇 명이고, 대표 제품은 어떤 기술을 쓰나요?" → `query_graph`(4명)와 `search_documents`(스마트상담봇: LangGraph, Neo4j)를 **둘 다** 골라 요청별로 답하고 출처를 붙였다.
- "PostgreSQL을 쓰는 프로젝트에는 누가 참여하고, 어느 회사가 개발?" → 둘리·또치(query_graph), 클라우드웨이.

## 마무리

| 장점 | 벡터 RAG (pgvector) | 그래프 DB / GraphRAG |
|---|---|---|
| 비슷한 문장 찾기 | ✅ | ✅ (벡터 인덱스) |
| 멀티홉 관계 | 청크가 우연히 다 걸려야 함 | 관계를 따라감 |
| 정확한 개수·목록 | ❌ Top-k 한계 | ✅ Cypher 집계 |
| 근거 설명 | 문장 | 문장 + 관계 경로 |
| 준비 비용 | 낮음 | 추출·스키마·품질 점검 필요 |

## 🔁 복습 질문

<details>
<summary>1. 같은 데이터 적재 셀을 두 번 실행해도 노드가 늘지 않게 하려면?</summary>

`CREATE` 대신 `MERGE`를 쓰고, 고유 키에 유일성 제약조건을 건다. MERGE에는 고유 키만 넣고 나머지 속성은 `SET`으로.
</details>

<details>
<summary>2. "유니코가 일하는 회사의 대표 제품이 쓰는 DB"를 벡터 RAG가 못 찾은 이유는?</summary>

필요한 사실이 서로 다른 문서 3개(유니코→넥스트AI, 넥스트AI→스마트상담봇, 스마트상담봇→Neo4j)에 흩어져 있어 Top-2 청크에 다 들어오지 않았다. GraphRAG는 찾은 청크의 엔티티에서 관계를 따라가 이었다.
</details>

<details>
<summary>3. GraphRAG가 "PostgreSQL 장애 시 영향받는 사람"에서 또치를 빠뜨렸다. 어디부터 확인하나?</summary>

① 그래프에 `또치-PARTICIPATES_IN->문서검색엔진`이 있는지 → ② 검색 context에 그 사실이 들어갔는지 → ③ 답변 LLM이 사용했는지. 이번에는 ②까지 있었으므로 ③ 문제다. 목록 질문은 Text2Cypher로 보내는 것이 맞다.
</details>

<details>
<summary>4. Text2Cypher에 직접 작성한 스키마를 주는 이유는?</summary>

자동 스키마는 처음 한 번만 읽고 내부 구조(Chunk, embedding)까지 섞여 LLM이 헷갈린다. 필요한 라벨·관계와 값 예시만 주면 쿼리가 정확해진다.
</details>

<details>
<summary>5. Text2Cypher를 운영에 쓸 때 꼭 해야 할 보안 조치는?</summary>

읽기 전용 계정과 읽기 트랜잭션(`RoutingControl.READ`)으로 실행하고, 쓰기 키워드(`CREATE`, `MERGE`, `DELETE`, `SET`)가 들어간 쿼리는 실행 전에 차단한다.
</details>
