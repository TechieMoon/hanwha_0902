# LangGraph 오케스트레이션 패턴 4가지와 LangSmith

> **한눈에 보기**
> - **오케스트레이션** = 여러 에이전트의 실행 순서·분기·반복·협업을 설계하는 것. 순차형 / 슈퍼바이저형 / 피드백 루프형 / 계층형 4가지를 같은 공통 코드(`ask()`, `show_graph()`)로 구현했다
> - 모든 패턴은 같은 4단계: **State 정의 → 노드 함수 → 엣지 연결 → `compile()`**. 다른 것은 "다음 순서를 누가 정하나"뿐이다(코드 / 관리자 LLM / 조건 함수 / 총괄 LLM + 팀)
> - 보너스: `create_agent()`로 만든 전문가 에이전트를 **통역사 함수**로 감싸 LangGraph 노드로 넣는 법 (주말 나들이 플래너)
> - **LangSmith**: 에이전트 실행의 블랙박스. 환경변수 3개로 켜고, `tracing_context(enabled=False)`로 잠시 끈다
> - 실행 결과에서 본 것: 슈퍼바이저가 **한 번도 FINISH를 고르지 않고** 상한(5번)까지 같은 담당자를 반복 호출, budget_agent가 **총액을 틀리게 계산**해 예산 초과 계획이 "예산 안"으로 통과

- 코드: [`exam14.ipynb`](exam14.ipynb) (강사님 자료 `fwedu/exam14.ipynb` 사본, 강의 슬라이드 이미지 포함, 📝 정리 셀 추가)
- 같은 날: [멀티 에이전트 설계 패턴 5가지](멀티에이전트패턴.md)

## 공통 준비

| 모델 | 맡는 역할 |
|---|---|
| `gpt-4o-mini` | 판단·평가·정리 (슈퍼바이저, 리뷰어, 편집자) |
| `gemini-3.5-flash-lite` | 글쓰기·아이디어 (작가, 기술 담당) |

코드 주석에 `[LangChain]`(모델 호출·구조화 출력)과 `[LangGraph]`(State·엣지·서브그래프)를 붙여 누가 무엇을 하는지 구분했다.

## ① 순차형 — 정해진 순서대로

`researcher(gpt) → writer(gemini) → editor(gpt)`. 각 노드가 `notes → draft → final` 칸을 차례로 채운다.

- 실행 순서는 몇 번을 돌려도 같다. 가장 예측 가능하고 LLM 호출이 가장 적다.
- 주제 "LangGraph로 멀티 에이전트를 만드는 이유"의 최종 글이 "LangGraph는 **자연어 처리와 그래프 기반 데이터 구조를 결합**해…"로 시작했다. 10/23 exam10에서 본 것과 같은 **틀린 설명**이다. 리서처에게 자료(문서·검색)를 주지 않으면 세 단계를 거쳐도 틀린 내용이 다듬어질 뿐이다.

## ② 슈퍼바이저형 — 관리자가 다음 담당자를 지목

```python
class Route(BaseModel):
    next: Literal["billing_agent", "tech_agent", "FINISH"]
    reason: str

def supervisor(state):
    steps = state.get("steps", 0) + 1
    if steps > MAX_STEPS:                       # MAX_STEPS = 5, 안전장치
        return {"next": "FINISH", "steps": steps}
    route = supervisor_llm.invoke([SystemMessage("…모두 처리됐으면 FINISH."),
                                   HumanMessage(f"문의: {state['request']}\n\n지금까지의 보고:\n{done}")])
    return {"next": route.next, "steps": steps}

def route_from_supervisor(state) -> str:
    return "responder" if state["next"] == "FINISH" else state["next"]

builder.add_conditional_edges("supervisor", route_from_supervisor,
                              ["billing_agent", "tech_agent", "responder"])
builder.add_edge("billing_agent", "supervisor")                      # 처리 후 복귀
builder.add_edge("tech_agent", "supervisor")
```

`reports`는 `operator.add` 리듀서로 담당자 보고를 쌓는다.

| 문의 | 실행 결과 |
|---|---|
| 환불 문의 | billing_agent를 **5번 연속** 지목 ("추가 처리가 필요합니다") → 상한으로 종료 |
| 앱 화면이 하얗게 멈춤 | tech_agent를 **5번 연속** 지목 |
| 로그인 안 됨 + 환불 | tech → tech → billing → billing → tech → 상한으로 종료 |

- 세 번 모두 **FINISH를 한 번도 고르지 않았다.** 최종 답변은 `MAX_STEPS` 안전장치 덕분에 나왔고, 담당자 호출 4번은 낭비였다(같은 보고가 쌓인다).
- 같은 날 ④ 계층형의 총괄 관리자는 3번 만에 FINISH를 골랐다. 차이는 입력이다. 계층형은 "조사 결과: 있음/없음, 기획서: 있음/없음"처럼 **완료 여부를 짧게 정리한 상태**를 받았고, 슈퍼바이저형은 긴 보고 원문만 받았다. 완료 판단은 LLM에게 맡기기보다 코드가 **처리한 항목을 표시**해서 넘기는 것이 안전하다.

## ③ 피드백 루프형 — 작성 → 검토 → 다시 작성

```python
PASS_SCORE = 8; MAX_ROUNDS = 3

def continue_or_end(state) -> str:
    if state["score"] >= PASS_SCORE or state["round"] >= MAX_ROUNDS:
        return END
    return "writer"
```

- 주제 "직장인을 위한 6시간 'AI 에이전트 입문' 주말 강좌" 홍보 문구 → 1회차에 **8점으로 바로 통과**했다. 점수에 따라 반복 횟수가 실행마다 달라진다.
- 리뷰어 결과는 `Review(score: int = Field(ge=1, le=10), feedback: str)` 구조화 출력으로 받아 조건 함수가 숫자로 비교한다.

## ④ 계층형 — 총괄 관리자 → 팀장 → 팀원

| 그래프 | 내부 방식 | State |
|---|---|---|
| 조사팀 `research_team` | 팀 안은 슈퍼바이저형 (team_lead → market/tech_researcher) | `ResearchState(task, findings, next)` |
| 작성팀 `writing_team` | 팀 안은 순차형 (planner → doc_writer) | `WritingState(task, materials, outline, document)` |
| 상위 `hierarchical_app` | 총괄 관리자가 팀을 지목 | `TopState(request, research, document, next, steps)` |

```python
def call_research_team(state: TopState) -> dict:        # 상위 ↔ 하위 State를 바꿔 주는 연결자(wrapper)
    out = research_team.invoke({"task": state["request"], "findings": []})
    return {"research": "\n\n".join(out["findings"])}   # 결과만 상위 State에
```

- 팀(서브그래프)마다 State 모양이 달라 노드로 바로 넣지 않고 wrapper 함수로 감쌌다. `show_graph(hierarchical_app, xray=True)`로 팀 내부까지 그릴 수 있다.
- 실행: 총괄 #1 → research_team(시장 → 기술 조사) → #2 writing_team → #3 FINISH.
- 다만 시장 조사원의 결과가 시장 조사가 아니라 **"교육과정 기획서" 전체**였다. 역할 프롬프트가 짧으면 팀원이 최종 요청(기획서 작성)을 그대로 수행해 버린다.

### 네 가지 패턴 비교

| | ① 순차형 | ② 슈퍼바이저형 | ③ 피드백 루프형 | ④ 계층형 |
|---|---|---|---|---|
| 다음 순서를 정하는 주체 | 코드 (`add_edge`) | 관리자 LLM | 조건 함수 (점수·횟수) | 총괄 LLM + 팀별 방식 |
| 핵심 기능 | `add_edge` | 조건부 엣지 + 복귀 엣지 | 조건부 엣지 루프 | 서브그래프 |
| LLM 호출 수 | 가장 적음 | 판단 호출 추가 | 반복할수록 증가 | 가장 많음 |
| 안전장치 | 필요 없음 | `MAX_STEPS` | `MAX_ROUNDS` | 단계별 상한 |

가장 단순한 패턴부터 시작하고, 필요할 때 섞는다(계층형 안에 슈퍼바이저형과 순차형이 들어 있었던 것처럼).

## 보너스: `create_agent` 에이전트를 LangGraph 노드로

`create_agent()`는 "혼자 일하는 전문가(모델 + 도구)", LangGraph는 "누가, 어떤 순서로, 몇 번 일할지 정하는 조직도"다. 에이전트는 `{"messages": [...]}`를 주고받으므로 큰 그래프의 State와 모양이 다르다. 그래서 **통역사 함수**가 ① State에서 질문을 꺼내고 ② 에이전트를 호출해 ③ `messages[-1]`을 State 칸에 넣는다.

주말 나들이 플래너: `weather(gemini) → place(gpt) → budget(gpt)`, 예산 초과면 place로 되돌림(`MAX_TRIES=2`).

```python
budget_agent = create_agent(model=gpt, tools=[get_price],
    system_prompt="각 장소의 1인 가격을 get_price로 조회하고, 1인 식사비 15000원을 더해 인원수만큼 곱한 총액을 계산한다.",
    response_format=ToolStrategy(Budget))              # Budget(total: int, detail: str)

def budget_node(state):
    b = budget_agent.invoke(...)["structured_response"]
    within = b.total <= state["limit"]                 # 예산 비교는 LLM이 아니라 코드로
```

- 비 오는 토요일 → 실내 2곳(국립중앙박물관, 코엑스 아쿠아리움) 선택까지는 맞았다.
- budget_agent: **78,000원 / 예산 안** (내역: 0 + 33,000 + 30,000). 지시대로라면 (0 + 33,000 + 15,000) × 2명 = **96,000원**으로 예산 80,000원을 넘는다. 입장료에 인원수를 곱하지 않았다.
- 비교(`<=`)는 코드가 했지만 **비교할 숫자를 LLM이 만들었기 때문에** 안전장치가 통하지 않았다. 합계처럼 정해진 계산은 도구 결과를 받아 코드에서 더해야 한다(`Budget`에는 장소별 가격만 받기).

## LangSmith — 에이전트의 블랙박스

어떤 단계를 거쳤는지, LLM에 무엇을 묻고 무엇을 받았는지, 시간과 토큰이 얼마나 들었는지 기록해 웹 화면으로 보여 준다. 코드 변경 없이 환경변수만 설정하면 LangChain·LangGraph 실행이 자동 기록된다.

```
pip install -U langsmith
setx LANGSMITH_TRACING "true"
setx LANGSMITH_API_KEY "lsv2_..."      ← 실제 키는 코드·노트북에 쓰지 않는다
setx LANGSMITH_PROJECT "exam14"
```

수업 순서(강사님 LangSmith 사용 자료): 회원가입 → Settings > API Keys > Create API Key(Personal Access Token) → 키 복사 → 환경변수 설정 후 VS Code 재시작 → 노트북 실행 → 왼쪽 **Tracing** 메뉴에서 프로젝트(exam14)의 실행 기록 확인. 실행 하나(`app.invoke()` 1번)가 트레이스 1건이고, 안에서 노드·LLM 호출이 트리로 펼쳐진다.

기록을 잠시 끄는 방법:

```python
from langsmith import tracing_context

with tracing_context(enabled=False):     # 이 블록 안의 실행만 기록 안 됨 (커널 재시작 불필요)
    result = app.invoke({...})
```

또는 `setx LANGSMITH_TRACING "false"` 후 VS Code 재시작. 프롬프트·답변 원문이 외부 서비스에 저장되므로 **개인정보나 회사 데이터가 들어가는 실행은 끄고** 돌린다.

> LangChain으로 만들고, LangGraph로 연결하고, LangSmith로 들여다본다.

## 🔁 복습 질문

<details>
<summary>1. 슈퍼바이저형에서 <code>MAX_STEPS</code>가 없었다면 이번 실행은 어떻게 됐을까?</summary>

슈퍼바이저가 FINISH를 고르지 않아 같은 담당자를 계속 부르다 LangGraph의 `recursion_limit`(기본 25)에 걸려 예외로 끝났을 것이다. 고객에게 줄 답변도 만들어지지 않는다.
</details>

<details>
<summary>2. 계층형에서 하위 팀을 상위 그래프 노드로 바로 넣지 않고 wrapper 함수로 감싼 이유는?</summary>

팀마다 State 키가 달라서다. wrapper가 상위 State(`request`)를 하위 입력(`task`)으로 바꿔 서브그래프를 실행하고, 결과(`findings`)를 상위 칸(`research`)으로 돌려준다.
</details>

<details>
<summary>3. budget_node가 "예산 비교는 코드로" 했는데도 틀린 이유와 해결책은?</summary>

비교할 총액을 LLM이 계산했기 때문이다. 장소별 가격은 도구로 받고, `(입장료 합 + 식사비) × 인원`은 파이썬 코드에서 계산해 비교한다.
</details>

<details>
<summary>4. 피드백 루프형이 순차형보다 LLM 호출이 많아지는 경우는?</summary>

리뷰 점수가 `PASS_SCORE` 미만일 때마다 작성·검토가 한 번씩 더 돈다. `MAX_ROUNDS`가 최대 호출 수를 정한다.
</details>

<details>
<summary>5. LangSmith 트레이싱을 특정 실행에서만 끄려면?</summary>

`with tracing_context(enabled=False):` 블록 안에서 실행한다. 블록 밖의 실행은 다시 기록된다.
</details>
