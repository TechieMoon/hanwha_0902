# LangGraph 흐름 제어: 리듀서, 조건부 엣지, 반복, 병렬, Send, Command, 런타임 컨텍스트

> **한눈에 보기**
> - **리듀서** `Annotated[타입, 함수]`: 노드가 반환한 값을 덮어쓰지 않고 **합치는 규칙**. `operator.add`(이어붙이기), `add_messages`(대화 메시지), 직접 만든 함수(최댓값 유지 등)
> - **조건부 엣지** `add_conditional_edges(노드, 라우팅함수)`: State를 보고 다음 노드 이름을 반환. 목적지를 앞쪽으로 두면 **반복(루프)**, 상한은 `recursion_limit`
> - **병렬(fan-out/fan-in)**: 같은 슈퍼스텝의 노드는 동시에 실행. 같은 필드에 동시에 쓰려면 리듀서 필수, 모이는 곳은 `add_edge([A, B, C], "join")`
> - **`Send`**: 개수가 정해지지 않은 병렬(Map-Reduce), **`Command(update=, goto=)`**: 노드가 상태 갱신과 다음 목적지를 한 번에
> - **런타임 컨텍스트** `context_schema`: 사용자 이름·언어처럼 실행 내내 **변하지 않는 설정**은 State가 아니라 `context=`로

- 코드: [`exam9.ipynb`](exam9.ipynb) (강사님 자료 `fwedu/exam9.ipynb` 사본, 강의 슬라이드 이미지 포함, 📝 정리 셀 추가) — 노트북 로드맵의 5~11장, 모두 LLM 없이 실행
- 앞 내용: [LangGraph 기본](LangGraph기본.md) (1~4장)

## 5장. 리듀서: 덮어쓸까, 합칠까

```python
logs: list[str]                              # 덮어쓰기
logs: Annotated[list[str], operator.add]     # 이어붙이기
```

| State | `{"logs": ["시작"]}` → step1 → step2 결과 |
|---|---|
| 리듀서 없음 | `['step2 실행']` (앞의 값이 모두 사라짐) |
| `operator.add` | `['시작', 'step1 실행', 'step2 실행']` |
| 직접 만든 `keep_max(old, new)` | 70 → 95 → 80점을 차례로 기록해도 **95 유지** |

리듀서 = `(기존값, 새값) -> 합친값` 함수. `add_messages`는 대화 메시지 전용이다.

| `add_messages` 동작 | 결과 |
|---|---|
| 새 메시지 | 뒤에 추가 |
| **같은 `id`**의 메시지 | 이어붙이지 않고 **교체** ("안녕" → "안녕(수정됨)") |
| `("user", "질문")`, `{"role": "assistant", ...}` | `HumanMessage`, `AIMessage`로 자동 변환 |

에이전트의 `messages`는 계속 쌓여야 하고, 병렬 노드가 같은 필드에 쓰려면 반드시 리듀서가 있어야 해서 중요하다.

## 6장. 조건부 엣지

```python
def route_by_score(state) -> Literal["passed", "retake", "failed"]:
    if state["score"] >= 80: return "passed"
    if state["score"] >= 60: return "retake"
    return "failed"

builder.add_conditional_edges("receive_score", route_by_score)
```

- 95점 → 합격, 70점 → 재시험, 30점 → 불합격.
- 라우팅 함수는 **State를 읽기만** 하고 다음 노드 이름(또는 `END`)을 반환한다. 여기서 State를 고쳐도 반영되지 않는다. 바꾸는 일은 노드에서.
- 반환 타입을 `Literal[...]`로 적어 두면 그래프 그림에 갈림길이 정확히 그려진다.
- `path_map`: 라우팅 함수가 `"high"`/`"low"` 같은 **라벨**을 반환하고 `{"high": "passed", "low": "failed"}`로 노드에 연결한다. 노드 이름을 바꿔도 라우팅 함수는 그대로 둘 수 있다.
- 등록되지 않은 노드 이름을 반환하면 실행 중 에러 → `Literal`이나 `path_map`으로 목적지를 명시한다.

## 7장. 반복(사이클)과 recursion_limit

```python
def check_goal(state) -> Literal["save_money", "__end__"]:
    return END if state["balance"] >= state["goal"] else "save_money"    # 미달이면 자기 자신으로
builder.add_conditional_edges("save_money", check_goal)
```

매달 30만 원씩 모아 목표 100만 원 → 4개월째 120만 원에서 종료.

종료 조건이 없는 그래프(`add_edge("tick", "tick")`)를 `config={"recursion_limit": 6}`으로 실행하니 tick 0~5까지 **6번 실행**하고 `GraphRecursionError: Recursion limit of 6 reached without hitting a stop condition`으로 멈췄다.

- `recursion_limit`은 이 호출에서 허용하는 **최대 슈퍼스텝 수**(기본 25). 실행 엔진(Pregel)이 `config`에서 직접 읽는다.
- `config`에는 그 밖에 `configurable`(`thread_id` 등), `tags`, `run_name`(LangSmith 추적용)도 넣는다.
- LLM을 부르는 루프라면 상태에 반복 횟수를 두고 직접 제한하는 것도 좋다. 10/08에 재생성 루프 상한을 빠뜨려 `GraphRecursionError`를 겪었다([RAG 에이전트](../ex1008/RAG에이전트그래프.md)).

## 8장. 병렬 실행: fan-out / fan-in

```python
builder.add_edge(START, "count_chars")       # fan-out: START에서 세 노드로
builder.add_edge(START, "count_words")
builder.add_edge(START, "detect_mood")
builder.add_edge(["count_chars", "count_words", "detect_mood"], "make_report")   # fan-in: 셋 다 끝나야
```

- 0.5초씩 걸리는 노드 3개가 **0.51초**에 끝났다(순서대로면 1.5초). "배송도 빠르고 품질이 최고예요 정말 만족합니다" → 25자 / 6단어 / 긍정.
- `log: Annotated[list[str], operator.add]` 덕분에 세 노드의 로그가 모두 쌓였다.
- 리듀서 없는 필드에 두 노드가 동시에 쓰면 `InvalidUpdateError: At key 'value': Can receive only one value per step. Use an Annotated key to handle multiple values.`
- 규칙 3가지: ① 같은 슈퍼스텝 노드는 서로의 결과를 못 본다 ② 같은 필드에 동시에 쓰려면 리듀서 ③ 모이는 곳은 **리스트로** 연결(따로 연결하면 분기마다 단계 수가 다를 때 join이 여러 번 실행될 수 있다).

## 9장. Send: 개수가 정해지지 않은 병렬 (Map-Reduce)

```python
def fan_out(state) -> list[Send]:
    return [Send("lookup", {"city": c}) for c in state["cities"]]     # Map: 항목마다 Send

def lookup(payload: dict) -> dict:            # State 전체가 아니라 Send로 받은 dict만 받는다
    return {"temps": [(payload["city"], FAKE_TEMPS.get(payload["city"], 0))]}

builder.add_conditional_edges(START, fan_out, ["lookup"])
builder.add_edge("lookup", "report")          # temps(operator.add)에 모인 결과를 집계
```

같은 그래프에 도시 3개를 넣으면 `lookup`이 3번(평균 19.3°C), 5개를 넣으면 5번(19.0°C) 실행됐다. 그래프 구조는 그대로인데 **병렬 개수가 입력에 따라 바뀐다.** 문서 여러 개를 각각 요약해서 합치기, 검색어 여러 개를 동시에 검색하기에 쓴다.

## 10장. Command: 상태 갱신 + 이동을 한 번에

```python
def validate(state) -> Command[Literal["ship", "reject"]]:
    if state["stock"] >= state["qty"]:
        return Command(update={"status": "검증 통과 ✅"}, goto="ship")
    return Command(update={"status": f"재고 부족 ❌ ..."}, goto="reject")
```

- 재고 10 / 주문 3 → "검증 통과 → 배송 시작", 주문 30 → "재고 부족 … → 주문 취소".
- `validate → ship/reject` 엣지를 `add_edge`로 그리지 않았는데도 그림에 연결선이 나왔다. **반환 타입 힌트** `Command[Literal[...]]`를 보고 그린다 → 힌트를 꼭 적는다.
- 규칙이 단순하면 조건부 엣지(분기 로직이 노드와 분리), 노드 안에서 계산한 결과로 판단하거나 갱신과 이동이 한 덩어리면 `Command`. `Command(resume=...)`는 [10/21 사람 승인](../ex1021/미들웨어.md)에서 이미 썼다.

## 11장. 런타임 컨텍스트

| | State | Context |
|---|---|---|
| 성격 | 노드를 거치며 바뀌는 데이터 | 실행 내내 바뀌지 않는 설정 |
| 선언 | `StateGraph(State)` | `StateGraph(State, context_schema=AppContext)` |
| 전달 | `invoke({...})` | `invoke(..., context=AppContext(...))` |
| 노드에서 | `state["x"]` | `runtime.context.x` (두 번째 인자 `runtime: Runtime[AppContext]`) |
| 체크포인트 저장 | ✅ | ❌ |

같은 그래프에 `AppContext(user_name="둘리", lang="ko")` → "안녕하세요, 둘리님!", `lang="en"` → "Hello, …!". 사용자 ID, DB 연결, 모델 이름처럼 멀티 유저 서비스에서 호출마다 다른 설정을 넘길 때 쓴다. 10/21 장기 메모리의 `Context(user_id=...)`가 바로 이것이었다.

## 정리

| 하고 싶은 것 | LangGraph |
|---|---|
| 값을 쌓기 / 최댓값 유지 | `Annotated[..., operator.add]` / 직접 만든 리듀서 |
| 대화 메시지 누적 | `add_messages` |
| 조건 분기 | `add_conditional_edges(노드, 라우팅함수, path_map)` |
| 반복 | 조건부 엣지의 목적지를 앞 노드로 + `recursion_limit` |
| 정해진 개수 병렬 | 여러 `add_edge(START, ...)` + `add_edge([...], join)` |
| 개수가 바뀌는 병렬 | `Send("노드", 입력)` 리스트 |
| 갱신과 이동을 함께 | `Command(update=..., goto=...)` |
| 바뀌지 않는 실행 설정 | `context_schema` + `Runtime` |

## 🔁 복습 질문

<details>
<summary>1. 리듀서가 없는 <code>list</code> 필드에 두 노드가 차례로 값을 반환하면?</summary>

뒤 노드의 값으로 덮어써진다. 이어붙이려면 `Annotated[list[str], operator.add]`.
</details>

<details>
<summary>2. <code>add_messages</code>가 <code>operator.add</code>와 다른 점 두 가지는?</summary>

같은 `id`의 메시지는 추가하지 않고 교체한다. `("user", "...")` 같은 튜플·딕셔너리를 메시지 객체로 바꿔 준다.
</details>

<details>
<summary>3. 라우팅 함수에서 State를 고치면 반영되나?</summary>

아니다. 라우팅 함수는 다음 노드 이름만 정한다. State 변경은 노드의 반환값으로 한다.
</details>

<details>
<summary>4. 병렬 노드가 같은 필드에 리듀서 없이 쓰면 어떤 오류가 나나?</summary>

`InvalidUpdateError` (한 스텝에 값을 하나만 받을 수 있다). 리듀서를 지정해 합치는 방법을 알려 줘야 한다.
</details>

<details>
<summary>5. 일반 병렬 대신 <code>Send</code>를 쓰는 경우는?</summary>

처리할 항목의 개수가 실행 때마다 달라서, 노드를 몇 개 실행할지 미리 정할 수 없을 때(Map-Reduce).
</details>

<details>
<summary>6. <code>Command</code>를 반환하는 노드에 <code>Command[Literal[...]]</code> 타입 힌트가 필요한 이유는?</summary>

엣지를 따로 그리지 않으므로, 그래프가 갈 수 있는 목적지를 타입 힌트로 알아야 컴파일과 그림이 제대로 된다.
</details>

<details>
<summary>7. 사용자 언어 설정은 State와 Context 중 어디에 두나?</summary>

Context. 실행 중에 바뀌지 않고 체크포인트에 저장할 필요도 없는 설정이기 때문이다.
</details>
