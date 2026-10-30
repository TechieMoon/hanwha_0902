# LangGraph 에이전트와 운영 기능: LLM 노드, 라우터, ReAct, 메모리, 스트리밍, 사람 승인, 재시도, 서브그래프

> **한눈에 보기**
> - **LLM 노드**에 새 문법은 없다: 노드 함수 안에서 `llm.invoke(state["messages"])`를 부르고 `{"messages": [응답]}`을 반환. 대화용 State는 `MessagesState`(`add_messages` 내장)
> - **라우터**: LLM이 `with_structured_output(Literal[...])`로 의도를 분류 → 조건부 엣지로 전문 노드에 보낸다
> - **ReAct 에이전트** = `llm.bind_tools` + `ToolNode` + `tools_condition` + `add_edge("tools", "agent")` 사이클. `create_agent`가 이 구조를 한 줄로 만든다
> - **운영 기능**: 체크포인터 + `thread_id`(메모리), `stream_mode` 5가지, `interrupt()` + `Command(resume=)`(사람 승인 — **재개 시 노드가 처음부터 다시 실행**), `RetryPolicy`(노드 재시도), 서브그래프
> - 종합 실습: 사람 피드백을 받아 다시 쓰는 **글쓰기 에이전트** (루프 + interrupt + 수정 횟수 상한)

- 코드: [`exam10.ipynb`](exam10.ipynb) (강사님 자료 `fwedu/exam10.ipynb` 사본, 강의 슬라이드 이미지 포함, 📝 정리 셀 추가) — 노트북 로드맵의 12~21장
- 앞 내용: [LangGraph 기본](LangGraph기본.md)(1~4장) · [LangGraph 흐름 제어](LangGraph흐름제어.md)(5~11장)

## 12장. LLM 노드: 가장 단순한 챗봇

```python
def chatbot(state: MessagesState) -> dict:
    system = SystemMessage("당신은 친절한 IT 강사입니다. 한국어로 두 문장 이내로 답하세요.")
    return {"messages": [llm.invoke([system] + state["messages"])]}   # 시스템 프롬프트는 호출 때만 붙임
```

- 결과의 `messages`에는 사용자 메시지 + AI 응답 2개. 노드는 응답 하나만 반환했지만 `add_messages`가 이어 붙였다.
- 시스템 프롬프트를 State에 넣지 않고 호출 때만 붙여 대화 기록이 깔끔하다.
- "LangGraph가 뭐야?"에 gpt-4o-mini는 "**NLP와 그래프 기반 데이터 구조를 결합해 텍스트 관계를 시각화**하는 도구"라고 **틀리게** 답했다. 10/19 "LCEL", 10/21 "RAG"처럼 모델은 학습 시점 이후의 라이브러리 이름을 지어낸다.
- "내 이름은 도우너야" 다음 호출에서 "내 이름이 뭐였지?" → 모름. **`invoke`는 호출마다 State를 새로 시작**한다(→ 15장).

## 13장. LLM 라우팅: 구조화된 출력 + 조건부 엣지

```python
class Route(BaseModel):
    intent: Literal["translate", "summarize", "chat"]
router_llm = llm.with_structured_output(Route)

def route_by_intent(state) -> Literal["translate", "summarize", "chat"]:
    return state["intent"]              # LLM이 분류한 값이 곧 다음 노드 이름
```

| 입력 | 분류 | 답 |
|---|---|---|
| "'오늘 날씨가 정말 좋네요'를 영어로 번역해줘" | translate | "The weather is really nice today." |
| "다음 글을 요약해줘: 랭그래프는 …" | summarize | 한 문장 요약 |
| "오늘 점심 뭐 먹을까?" | chat | "김밥 어때?" |

`classify`는 분류만 하고 분기는 라우팅 함수가 한다. 출력을 `Literal` 세 값으로 강제해서 "번역이요" 같은 엉뚱한 값으로 라우팅이 깨질 일이 없다. 고객 문의 분류, 부서 배정에 쓰는 **라우터 워크플로**다. (10/19에는 키워드 `RunnableBranch`로 라우팅했었다.)

## 14장. 도구 에이전트 (ReAct)

```python
b.add_node("agent", agent)                          # llm_with_tools = llm.bind_tools(tools)
b.add_node("tools", ToolNode(tools))                # tool_calls를 실행하고 ToolMessage 추가
b.add_edge(START, "agent")
b.add_conditional_edges("agent", tools_condition)   # tool_calls 있으면 "tools", 없으면 END
b.add_edge("tools", "agent")                        # 사이클
```

- "서울 날씨 알려줘" → `AI(tool_calls: get_weather(서울))` → `Tool: 맑음, 18도` → "서울의 날씨는 맑고, 기온은 18도입니다."
- "12 곱하기 7은?" → `multiply(12, 7)` → 84.
- 실수 두 가지: 노드에서 `bind_tools` 안 한 `llm`을 부르면 도구 호출 요청이 안 나온다. `add_edge("tools", "agent")`를 빼면 도구 결과를 받은 뒤 최종 답 없이 끝난다.
- 10/16에 `for` 루프로 짠 ReAct가 그래프 사이클 하나가 됐다. 10/19의 `create_agent`가 바로 이 구조다.

## 15장. 메모리: 체크포인터와 thread_id

```python
memory_agent = build_agent(checkpointer=InMemorySaver())          # 그래프 코드는 그대로
memory_agent.invoke({"messages": [HumanMessage("내 이름은 유니코야")]}, {"configurable": {"thread_id": "unico-1"}})
```

같은 thread에서는 "유니코님이세요!", 다른 thread에서는 "알 수 없습니다". 새 메시지만 넘기면 체크포인터가 이전 State에서 이어 준다. 2번째 턴의 입력 토큰이 135 → 169로 늘어난 것도 이전 대화가 함께 전달된다는 증거다.

`get_state_history`를 보니 체크포인트가 **6개**였다: 턴마다 `('__start__',)`(입력 직후) → `('agent',)`(agent 실행 차례) → `()`(끝) 세 개씩. `next`가 비어 있지 않으면 그래프가 중간에 멈춰 있다는 뜻이다(→ 17장). 과거 체크포인트에서 다시 실행(replay)하거나 분기(fork)할 수도 있다. `get_state()`는 최신 스냅샷 하나, `get_state_history()`는 최신 → 과거 순서의 이터레이터다.

## 16장. 스트리밍: stream_mode 5가지

| 모드 | 흘려보내는 것 | 실행 결과 (`heavy_job` 예) |
|---|---|---|
| `values` | 단계별 전체 State | `[{'total': 0}, {'total': 6}]` |
| `updates` | 노드가 바꾼 부분 | `[{'heavy_job': {'total': 6}}]` |
| `custom` | 노드 안에서 `get_stream_writer()`로 보낸 값 | `{'progress': '1/3 단계 완료'}` … 3개 |
| `messages` | LLM 토큰 + 메타데이터 | `부@산@의@ 현재@ 날@씨@는@ …` |
| `debug` | 모든 세부 이벤트 | 심층 디버깅 |

- 리스트로 여러 모드를 요청하면 `("custom", {...})`, `("updates", {...})`처럼 이름표가 붙는다. `custom`은 노드가 **실행되는 도중** 보낸 값이라 진행률 표시에 맞다.
- `messages` 모드는 `meta["langgraph_node"] == "agent"`로 걸러야 도구 결과 같은 다른 노드의 출력이 섞이지 않는다. 도구 호출 단계는 텍스트 토큰이 없어 조용히 지나가고 최종 답만 글자 단위로 나왔다.

## 17장. Human-in-the-loop: interrupt와 Command(resume=)

```python
def approval(state) -> Command[Literal["execute", "cancel"]]:
    print("[approval] 노드 시작")
    approved = interrupt({"question": f"{state['to']}님께 {state['amount']:,}원을 송금할까요?"})   # 여기서 멈춤
    return Command(goto="execute" if approved else "cancel")

graph.invoke({...}, config)                       # → result["__interrupt__"][0].value = 질문, next=('approval',)
graph.invoke(Command(resume=True), config)        # 같은 thread_id로 재개 → approved=True
```

- **`[approval] 노드 시작`이 두 번 출력됐다.** 재개하면 노드가 **처음부터 다시 실행**되고, 이번에는 `interrupt()`가 멈추지 않고 사람의 답(`True`)을 반환한다. 그래서 `interrupt()` **앞에는 여러 번 실행돼도 안전한 코드만** 둔다. 송금처럼 위험한 일은 뒤의 별도 노드(`execute`)에 둔다. 앞 노드 `prepare`는 다시 실행되지 않았다.
- 거부 시나리오(`resume=False`)도 approval이 두 번 실행된 뒤 `cancel`로 갔다.
- 체크포인터와 `thread_id`가 필수다(멈춘 State를 저장해야 하므로).
- 정적 중단점: `compile(interrupt_before=["times_ten"])` → `{'x': 2}`에서 멈춤, `invoke(None, cfg)`로 재개 → `{'x': 20}`. 값을 주고받을 수 없고 항상 멈추므로 디버깅용, 실무는 `interrupt()`.
- 10/21 `HumanInTheLoopMiddleware`가 내부에서 이 `interrupt`를 쓴다.

## 18장. 에러 처리: RetryPolicy

```python
builder.add_node("flaky_api", flaky_api,
                 retry_policy=RetryPolicy(max_attempts=3, initial_interval=0.1, retry_on=ConnectionError))
```

처음 두 번 `ConnectionError` → 3번째 성공(호출하는 쪽은 `invoke` 한 번). 계속 실패하면 3번 시도 후 **마지막 예외가 그대로** 올라온다 → 호출자가 `try/except`. `max_attempts`는 첫 시도 포함, `retry_on`을 안 주면 `ValueError`·`TypeError` 같은 코드 버그 성격의 예외는 재시도하지 않는다. 미들웨어의 재시도(10/21)는 에이전트의 모델·도구 호출에, `RetryPolicy`는 **그래프의 노드 하나**에 붙인다.

## 19장. 서브그래프

| 연결 방식 | 조건 | 방법 | 실행 결과 |
|---|---|---|---|
| 노드로 직접 추가 | 부모와 State 키가 겹칠 때 | `pb.add_node("cleaner", cleaner)` | `"  LangGRAPH  "` → `{'text': 'langgraph', 'length': 9}` |
| 함수로 감싸기 | State 모양이 다를 때 | 노드 안에서 `cleaner.invoke(변환한 입력)` 후 결과 변환 | `{'raw': '   Wrapped   ', 'clean_len': 7}` |

- 서브그래프만 따로 `invoke`해 테스트할 수 있다(`"  HeLLo  "` → `'hello'`). 재사용, 팀 분업, 멀티 에이전트의 기초.
- `get_graph(xray=True)`로 서브그래프 내부 노드까지 그린다. `stream(..., subgraphs=True)`로 내부 진행(`'  ABC  '` → `'ABC'` → `'abc'`)까지 본다.

## 20장. 종합 실습: 사람 피드백을 반영하는 글쓰기 에이전트

```python
def review(state) -> Command[Literal["write", "__end__"]]:
    decision = interrupt({"draft": state["draft"], "revisions": state["revisions"]})   # 앞에 부작용 없음
    if decision["approved"]:                return Command(goto=END)
    if state["revisions"] >= MAX_REVISIONS: return Command(goto=END)                  # 안전장치
    return Command(goto="write", update={"feedback": decision["feedback"]})
```

`write`(LLM 초안·수정) → `review`(interrupt로 멈춤) → 승인이면 종료, 피드백이면 `write`로 돌아가는 루프. 수정 횟수 `revisions`를 State에 두고 `MAX_REVISIONS=3`으로 끊어 비용이 새지 않게 했다. 실행에서는 "AI 시대에 개발자가 배워야 할 것" 1차 초안에 `y`로 바로 승인해 루프는 돌지 않았다.

`while` + `input()`으로 짜면 웹 서비스로 옮길 때 구조를 갈아엎어야 하지만, LangGraph는 `__interrupt__`를 API 응답으로 내려보내고 사용자의 답이 오면 같은 `thread_id`로 `Command(resume=...)`만 부르면 된다.

## 꼭 기억할 원칙 (21장)

1. 노드는 **바뀐 것만** dict로 반환한다
2. **어떻게 합칠지는 리듀서**가 정한다 (병렬·메시지 누적)
3. 같은 슈퍼스텝의 노드는 서로의 결과를 못 본다
4. fan-in은 리스트로 `add_edge([a, b], "join")`
5. 루프에는 종료 조건 + 상한(`recursion_limit` 또는 카운터)
6. `interrupt()` 재개 시 노드가 처음부터 다시 실행된다 → **앞쪽에 부작용 금지**
7. State = 흐르며 바뀌는 데이터, Context = 바뀌지 않는 실행 설정

## 🔁 복습 질문

<details>
<summary>1. <code>MessagesState</code>를 쓰면 노드가 응답 하나만 반환해도 대화가 쌓이는 이유는?</summary>

`messages` 필드에 `add_messages` 리듀서가 붙어 있어서 반환한 메시지를 기존 목록 뒤에 이어 붙인다.
</details>

<details>
<summary>2. 라우터에서 LLM 출력을 <code>Literal</code>로 강제하는 이유는?</summary>

라우팅 함수가 그 값을 그대로 노드 이름으로 쓰기 때문이다. 자유 텍스트면 등록되지 않은 이름이 나와 실행 중 에러가 난다.
</details>

<details>
<summary>3. ReAct 그래프에서 <code>add_edge("tools", "agent")</code>를 빼면?</summary>

도구를 실행한 뒤 모델에게 돌아가지 않아 최종 답변 없이 그래프가 끝난다.
</details>

<details>
<summary>4. 체크포인터를 붙인 뒤 두 번째 호출에는 무엇만 넘기면 되나?</summary>

새 메시지와 같은 `thread_id`. 이전 State는 체크포인터가 불러와 이어 준다.
</details>

<details>
<summary>5. <code>interrupt()</code> 앞에 결제 코드를 두면 왜 위험한가?</summary>

재개하면 노드가 처음부터 다시 실행되어 결제가 두 번 일어난다. 위험한 동작은 interrupt 뒤나 별도 노드에 둔다.
</details>

<details>
<summary>6. <code>stream_mode="custom"</code>은 언제 쓰나?</summary>

노드가 실행되는 도중에 `get_stream_writer()`로 진행률 같은 값을 실시간으로 보낼 때.
</details>

<details>
<summary>7. 서브그래프를 노드로 바로 넣을 수 없는 경우와 해결법은?</summary>

부모와 State 키가 다를 때. 노드 함수 안에서 입력을 서브그래프 모양으로 바꿔 `invoke`하고, 결과를 부모 모양으로 바꿔 반환한다.
</details>
