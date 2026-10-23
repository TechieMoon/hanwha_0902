# LangGraph 기본: State · Node · Edge, 첫 그래프, 상태 갱신, State 스키마

> **한눈에 보기**
> - **LangGraph** = 상태(State)를 가진 작업 흐름을 **그래프(노드 + 엣지)**로 설계하고 실행하는 라이브러리. LangChain이 부품 상자라면 LangGraph는 부품을 **어떤 순서·조건으로** 움직일지 정하는 설계도 + 실행 엔진
> - 비유: **State** = 모두가 보는 화이트보드, **Node** = 화이트보드를 읽고 **바뀐 칸만 적는** 직원(함수), **Edge** = 다음에 누가 일할지 정하는 화살표
> - 만드는 4단계: State 정의 → Node 함수 → `StateGraph`에 `add_node`/`add_edge` → `compile()` 후 `invoke()`
> - 노드는 **바뀐 필드만 dict로 반환**한다. 반환하지 않은 필드는 그대로, 반환한 필드는 덮어쓰기(리듀서가 없을 때)
> - State 스키마는 `TypedDict`(가장 흔함) / `dataclass`(기본값) / `Pydantic`(입력 검증). `input_schema`/`output_schema`로 밖에 보여 줄 필드만 고를 수 있다

- 코드: [`exam8.ipynb`](exam8.ipynb) (강사님 자료 `fwedu/exam8.ipynb` 사본, 강의 슬라이드 이미지 포함, 📝 정리 셀 추가) — 노트북 로드맵의 1~4장
- 실행 환경: Python 3.12, langgraph 1.2.16, langchain 1.4.6 (이 노트북은 LLM 없이 실행)
- 10/01에 책으로 배운 [랭그래프 기본 개념](../ex1001/랭그래프기본개념.md)을 강사님 자료로 다시, 더 자세히 배웠다. 10/19~21에 쓴 `create_agent()`의 결과도 `CompiledStateGraph`였다.

## 1. LangChain(LCEL)과 LangGraph

| 기능 | LCEL | LangGraph |
|---|---|---|
| 순차 실행 | `RunnableSequence` / `\|` | `add_edge()` |
| 조건 분기 | `RunnableBranch` | `add_conditional_edges()` |
| 반복 | 파이썬 반복문 | 순환 Edge |
| 병렬 | `RunnableParallel` | 병렬 노드(fan-out) |
| 대화 기록 | `RunnableWithMessageHistory` | State + Checkpointer |
| 중단·재개 | 직접 구현 | `interrupt()` + Checkpointer |

순차·병렬·조건부 처리 정도의 **파이프라인은 LCEL**, 상태를 공유하며 분기·반복하고 **중단·재개까지 관리**해야 하면 LangGraph.

### 슈퍼스텝(super-step)

LangGraph는 구글의 대규모 그래프 처리 모델 **Pregel**에서 따온 방식으로 실행한다. **슈퍼스텝** = 실행할 수 있는 노드들을 실행하고, 결과(업데이트)를 State에 반영한 뒤 다음 단계로 넘어가는 기본 단위다. 같은 슈퍼스텝의 노드들은 **동시에** 실행되고, 모두 끝나야 State에 한꺼번에 반영된다(→ [8장 병렬 실행](LangGraph흐름제어.md#8장-병렬-실행-fan-out--fan-in)).

## 2. 첫 번째 그래프: START → 노드 → END

```python
class GreetState(TypedDict):
    name: str          # 입력
    greeting: str      # 노드가 채울 값

def make_greeting(state: GreetState) -> dict:
    return {"greeting": f"안녕하세요, {state['name']}님! 👋"}      # 바뀐 칸만 반환

builder = StateGraph(GreetState)
builder.add_node("make_greeting", make_greeting)
builder.add_edge(START, "make_greeting")
builder.add_edge("make_greeting", END)
graph = builder.compile()                     # CompiledStateGraph
graph.invoke({"name": "유니코"})              # {'name': '유니코', 'greeting': '안녕하세요, 유니코님! 👋'}
```

- `invoke` 결과는 **최종 State(dict)**. `name`은 노드가 반환하지 않았지만 그대로 남는다. 입력 때 모든 칸을 채울 필요는 없다.
- 컴파일된 그래프는 Runnable이라 `batch([{"name": "둘리"}, {"name": "고길동"}])`, `stream`, `ainvoke`를 그대로 쓴다.
- `graph.get_graph().draw_mermaid_png()`로 그래프 그림을 그린다(인터넷 필요, 실패하면 `draw_mermaid()` 텍스트를 mermaid.live에 붙여 넣기).
- **자주 하는 실수**: 아직 채워지지 않은 필드를 `state["b"]`로 읽으면 `KeyError: 'b'`. 입력으로 주거나 앞 노드에서 채우고, 없을 수도 있는 필드는 `state.get()`. 노드가 dict가 아닌 값을 반환하거나 State에 없는 필드를 반환하면 `InvalidUpdateError`. `START`에서 연결을 빠뜨리면 컴파일 오류.

## 3. 노드 여러 개 순차 실행

`raw → clean → cleaned → count_words → word_count → make_summary → summary`처럼 노드마다 **자기 칸 하나**만 채웠다. `"  LangGraph   IS   Fun  "` → `cleaned='langgraph is fun'`, `word_count=3`, `summary="총 3단어 → 'langgraph is fun'"`. 아무도 안 바꾼 `raw`는 원본 그대로 남았다.

```python
for u in text_graph.stream({"raw": "  Hello   World  "}, stream_mode="updates"): print(u)
# {'clean': {'cleaned': 'hello world'}} → {'count_words': {'word_count': 2}} → {'make_summary': {...}}
for s in text_graph.stream({"raw": "  Hello   World  "}, stream_mode="values"): print(s)
# 슈퍼스텝마다 전체 State: {'raw': ...} → {'raw', 'cleaned'} → {..., 'word_count'} → {..., 'summary'}
```

- `updates` = 노드별 **바뀐 부분**, `values` = 단계별 **전체 State**. 디버깅할 때 어느 노드가 무엇을 바꿨는지 보기 좋다.
- 일직선이면 `builder.add_sequence([clean, count_words, make_summary])`로 노드 등록과 연결을 한 번에(노드 이름 = 함수 이름). START/END 연결은 직접.
- 이름 습관: 노드는 동사(`clean`), 필드는 명사(`cleaned`).

## 4. State 스키마

| 방식 | 노드에서 읽기 | 기본값 | 입력 검증 | 실행 결과 |
|---|---|:-:|:-:|---|
| `TypedDict` | `state["count"]` | ❌ | ❌ | `{'count': 1}` → `{'count': 2}` |
| `dataclass` | `state.count` | ✅ | ❌ | `{}`만 넣어도 기본값 100 → `{'count': 101}` |
| `Pydantic` | `state.count` | ✅ | ✅ | `{"count": "abc"}` → `ValidationError` (valid integer 아님) |

어떤 방식이든 **노드의 반환값과 `invoke` 결과는 dict**다.

### 입력·출력 스키마 분리

```python
class InputSchema(TypedDict):  question: str
class OutputSchema(TypedDict): answer: str
class FullState(InputSchema, OutputSchema): scratch: str     # 내부 작업용

StateGraph(FullState)                                                          # → question, answer, scratch 모두 반환
StateGraph(FullState, input_schema=InputSchema, output_schema=OutputSchema)    # → {'answer': ...}만 반환
```

내부 메모(`scratch`)가 밖으로 새지 않는다. API로 그래프를 서비스할 때 응답 모양을 고정하는 데 쓴다.

## 정리

| 단계 | 코드 |
|---|---|
| State 정의 | `class State(TypedDict): ...` |
| 노드 | `def node(state) -> dict: return {"바뀐필드": 값}` |
| 조립 | `builder = StateGraph(State)`, `add_node`, `add_edge(START, ...)`, `add_edge(..., END)` / `add_sequence([...])` |
| 실행 | `graph = builder.compile()`, `invoke` / `batch` / `stream(stream_mode="updates"\|"values")` |
| 스키마 | `TypedDict` / `dataclass` / `Pydantic`, `input_schema` · `output_schema` |

## 🔁 복습 질문

<details>
<summary>1. 노드 함수가 State를 직접 고치지 않고 dict를 반환하는 이유는?</summary>

엔진이 반환값을 받아 State에 반영(필요하면 리듀서로 합치기)하기 때문이다. "누가 무엇을 바꿨는지"가 분명해지고, 병렬 실행 때도 안전하게 합칠 수 있다.
</details>

<details>
<summary>2. 노드가 반환하지 않은 필드는 어떻게 되나?</summary>

그대로 유지된다. 반환한 필드는 리듀서가 없으면 덮어쓴다.
</details>

<details>
<summary>3. <code>stream_mode="updates"</code>와 <code>"values"</code>의 차이는?</summary>

updates는 노드가 끝날 때마다 그 노드가 바꾼 부분만, values는 슈퍼스텝마다 전체 State를 보여 준다.
</details>

<details>
<summary>4. 슈퍼스텝이란?</summary>

실행할 수 있는 노드들을 (동시에) 실행하고 그 결과를 State에 반영하는 한 단계. 같은 슈퍼스텝의 노드는 서로의 결과를 보지 못한다.
</details>

<details>
<summary>5. Pydantic State를 쓰면 무엇이 좋아지나?</summary>

입력 타입을 검증해서 `{"count": "abc"}` 같은 잘못된 입력을 그래프 실행 전에 `ValidationError`로 막는다. 기본값도 줄 수 있다.
</details>

<details>
<summary>6. <code>output_schema</code>를 지정하면 결과가 어떻게 달라지나?</summary>

전체 State가 아니라 출력 스키마에 정의한 필드(예: `answer`)만 돌려준다. 내부 작업용 필드는 숨겨진다.
</details>
