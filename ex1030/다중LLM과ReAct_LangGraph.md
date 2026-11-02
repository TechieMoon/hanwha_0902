# 다중 LLM과 ReAct를 LangGraph로 다시 만들기

> **한눈에 보기**
> - 10/20 exam5에서 LangChain으로 만든 **다중 LLM 비교·순차 파이프라인·ReAct 에이전트**를 LangGraph의 `StateGraph`로 옮겼다
> - **병렬(fan-out/fan-in)**: START에서 노드 3개로 엣지를 나누면 같은 슈퍼스텝에서 동시에 실행되고, 셋이 모두 끝나야 `synthesize`가 실행된다
> - **순차 + 되돌리기**: 리뷰어가 `Fail`이면 조건부 엣지로 개발자에게 돌아간다. `MAX_REVISIONS`로 반복 상한을 둔다
> - **ReAct = 노드 2개 + 순환 엣지**. `while` 루프를 `agent ⇄ tools` 그래프로 바꾸고, `ToolNode` + `tools_condition`으로 줄인 뒤 `create_agent` 한 줄과 비교
> - 도구 실패 처리 3가지: 모델에게 오류를 알려 다시 판단(`handle_tool_errors=True`), 실패 횟수로 라우팅, 노드 재시도(`RetryPolicy`)

- 코드: [`exam12.ipynb`](exam12.ipynb) (강사님 자료 `fwedu/exam12.ipynb` 사본, 강의 슬라이드 이미지 포함, 📝 정리 셀 추가)
- 앞 내용: [10/20 다중 LLM과 ReAct (LangChain 버전)](../ex1020/다중LLM과ReAct_LangChain.md) · [10/23 LangGraph 기본](../ex1023/LangGraph기본.md)

## 1. 왜 같은 예제를 LangGraph로 다시 만드나

| 구분 | exam5 (LangChain) | exam12 (LangGraph) |
|---|---|---|
| 병렬 실행 | `RunnableParallel` | START → 노드 3개 엣지 (fan-out) |
| 결과 전달 | 체인 출력 → 다음 체인 입력 | 공유 **State**의 칸에 쓰고 읽기 |
| 되돌리기(재작성) | 파이썬 `for`/`while` | **조건부 엣지 + 순환** |
| ReAct 루프 | `while`로 직접 관리 | `agent ⇄ tools` 그래프, 체크포인터로 대화 기억 |

노드 안의 모델 호출은 그대로 LangChain 체인(`prompt | llm | parser`)이다. LangGraph는 **누가, 어떤 순서로, 몇 번** 실행할지만 맡는다.

## 2. 병렬 다중 LLM + 종합

```python
class MultiLLMState(TypedDict, total=False):   # 처음엔 일부 칸이 비어 있어도 됨
    question: str
    gpt_answer: str
    gemini_answer: str
    ollama_answer: str
    report: str

def make_ask_node(chain, answer_key):           # 모델별 노드를 찍어내는 함수
    def node(state):
        return {answer_key: chain.invoke({"question": state["question"]})}
    return node

for name in ["ask_gpt", "ask_gemini", "ask_ollama"]:
    builder.add_edge(START, name)                # fan-out
builder.add_edge(["ask_gpt", "ask_gemini", "ask_ollama"], "synthesize")   # fan-in: 셋 다 끝나야 실행
```

- 각 노드는 **자기 칸 하나만** 반환한다. 칸이 겹치지 않아 리듀서가 필요 없다.
- 실행 결과(질문: FastAPI vs Spring Boot): gemini 7.8초, gpt 7.8초, **Ollama(exaone3.5) 51.4초**. 병렬이라 전체 시간은 가장 느린 노드에 맞춰진다. 내 PC의 Ollama는 GPU 없이 CPU로 돌기 때문이다(`ollama ps` → 100% CPU).
- `get_graph().draw_mermaid_png()`로 그래프 그림을 확인할 수 있다.

## 3. 순차 파이프라인과 Fail 되돌리기

planner(Gemini, 명세서) → developer(EXAONE, 코드) → reviewer(GPT, 리뷰)를 엣지로 이었다. 응용 버전은 리뷰어가 문장이 아니라 **구조화된 판정**을 낸다.

```python
class Verdict(BaseModel):
    verdict: Literal["Pass", "Fail"]
    feedback: str

def route_after_review(state) -> str:
    if state["verdict"] == "Pass" or state.get("revisions", 0) >= MAX_REVISIONS:
        return END                     # 통과했거나 고칠 기회가 없으면 종료
    return "developer"                 # 피드백을 들고 다시 작성 (순환)

loop_builder.add_conditional_edges("reviewer", route_after_review, ["developer", END])
```

- 이번 실행은 첫 코드가 바로 **Pass(수정 0회)**여서 되돌리기는 돌지 않았다. 그래프 그림에는 developer ↔ reviewer 점선(조건부 엣지)이 보인다.
- 상한(`MAX_REVISIONS`) 없이 순환을 만들면 LLM이 계속 Fail을 주는 경우 무한 반복된다(LangGraph 기본 `recursion_limit`에 걸려 예외).

## 4. ReAct 루프를 그래프로

| exam5 코드 | LangGraph |
|---|---|
| `for`/`while` 루프 | 순환 엣지 `tools → agent` |
| `if not ai.tool_calls: return` | 조건부 엣지 (`tools_condition`) |
| `messages.append(...)` | `MessagesState`의 `add_messages` 리듀서 |
| `count`, `max_steps` | State의 `failures` 필드 또는 `recursion_limit` |
| (없음) | 체크포인터로 대화 기억·재시작 |

### 도구가 실패할 때 3가지 방법 (계산기 `153*27`)

| 버전 | 방법 | 결과 |
|---|---|---|
| ① `create_agent` + 미들웨어 | 도구가 **빈 문자열 `""`**을 반환 | 도구 결과가 비었는데 모델이 **스스로 4,131**이라고 답했다. 실패가 오류로 보이지 않으면 모델은 지나간다 |
| ② `ToolNode(handle_tool_errors=True)` + 실패 횟수 라우팅 | `ToolException`을 `status="error"` ToolMessage로 바꿔 모델에 전달 | 실패를 본 모델이 지시대로 "**계산기로 확인할 수 없으므로 모른다**"고 답했다 |
| ③ `RetryPolicy(max_attempts=3)` on tools 노드 | `handle_tool_errors=False`로 예외를 **노드 밖으로** 던짐 | 1번 실패 → 노드 자동 재실행 → 4131. 모델 호출은 늘지 않는다 |

- ③에서 `handle_tool_errors=True`로 두면 예외가 ToolMessage로 바뀌어 **노드는 성공한 것**이 되므로 RetryPolicy가 동작하지 않는다.
- 교훈: 도구 실패는 `""` 같은 값이 아니라 **예외(`ToolException`)로** 알려야 한다. 그래야 모델이나 그래프가 실패를 처리할 수 있다.

## 5. 재사용 가능한 ReAct 그래프 (주말 나들이 추천)

```python
def build_react_graph(llm, tools, system_prompt, checkpointer=None):
    llm_with_tools = llm.bind_tools(tools)
    def agent(state: MessagesState):
        messages = [SystemMessage(system_prompt)] + state["messages"]   # 지침은 State에 저장하지 않음
        return {"messages": [llm_with_tools.invoke(messages)]}
    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)
```

도구: `get_weather`, `search_places`, `estimate_total_cost` (가짜 데이터).

| 질문 | 결과 |
|---|---|
| "일요일 서울에서 2명이 갈 만한 곳" | 모델이 **`Thought: … functions.get_weather`를 글자로만 쓰고** 실제 `tool_calls`를 만들지 않아 그래프가 1단계에서 끝났다. 프롬프트에 "Thought를 출력하라"고 하면 이런 일이 생긴다 |
| "둘이서 1만 원으로" | 날씨(맑음) → 장소 → 비용 계산까지 했지만 **2만 원짜리 한강공원을 추천**하고 "예산 초과"라고 적은 뒤 대안으로 서울숲(0원)을 제시 |
| 같은 질문을 `create_agent` 버전으로 | 같은 실수 반복. 10/20 exam5에서도 나왔으니 세 번째 |
| 체크포인터 + `thread_id="trip-1"` 후속 질문 "4명이면?" | 앞에서 추천한 국립중앙박물관을 기억하고 `estimate_total_cost(4명)` → 0원 |
| 다른 thread(`trip-2`)에서 "아까 그곳 비용은?" | 기억이 없고, 또 Thought만 쓰고 끝났다 |

- 예산 같은 **조건 검사**는 프롬프트에 맡기지 말고 도구나 코드(예: 비용 계산 도구가 `within_budget`을 돌려주기)로 확인해야 한다.

## 6. 정리

| 소스 | exam5 (LangChain) | exam12 (LangGraph) | 얻는 이점 |
|---|---|---|---|
| 다중 LLM | `RunnableParallel` | fan-out / fan-in 엣지 | 노드별 결과가 State에 남아 추적이 쉽다 |
| 순차 파이프라인 | 체인 연결 | 엣지 + 조건부 순환 | Fail이면 되돌리기를 엣지 하나로 |
| ReAct | `while` 루프 | `ToolNode` + `tools_condition` | 메모리·재시도·중단점 같은 운영 기능을 붙일 수 있다 |

## 🔁 복습 질문

<details>
<summary>1. 병렬 노드 3개가 같은 State 키에 쓰면 어떻게 되나? 이 예제는 왜 괜찮았나?</summary>

같은 슈퍼스텝에서 리듀서 없이 한 키를 여러 노드가 갱신하면 `InvalidUpdateError`가 난다. 이 예제는 노드마다 `gpt_answer`, `gemini_answer`, `ollama_answer`처럼 다른 칸에 썼다.
</details>

<details>
<summary>2. <code>RetryPolicy</code>를 tools 노드에 붙였는데 재시도가 안 된다면 무엇부터 확인하나?</summary>

`ToolNode(handle_tool_errors=True)`인지 확인한다. 그러면 예외가 ToolMessage로 바뀌어 노드가 성공으로 끝나므로 RetryPolicy가 동작하지 않는다. `False`로 바꿔 예외를 밖으로 던지게 한다.
</details>

<details>
<summary>3. 도구가 실패했을 때 빈 문자열을 돌려주면 생기는 문제는?</summary>

모델이 실패를 알아채지 못하고 스스로 답을 지어낸다(이번에는 계산은 맞았지만 검증 없이 답했다). `ToolException`으로 알려야 한다.
</details>

<details>
<summary>4. 에이전트가 "Thought: … functions.get_weather"라고만 쓰고 끝난 이유는?</summary>

도구를 부르는 문장을 **텍스트로** 썼을 뿐 `tool_calls`가 없어서 `tools_condition`이 END로 보냈다. ReAct 형식 출력을 강요하는 프롬프트가 원인이 될 수 있다.
</details>

<details>
<summary>5. 같은 그래프에서 대화를 기억하려면 무엇이 필요한가?</summary>

`compile(checkpointer=InMemorySaver())`와 호출마다 같은 `config={"configurable": {"thread_id": ...}}`.
</details>
