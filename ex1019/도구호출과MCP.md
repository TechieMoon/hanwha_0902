# 도구 호출과 MCP: @tool, create_agent, 구조화 출력, 웹 검색, 원격 MCP

> **한눈에 보기**
> - **LLM은 함수를 직접 실행하지 않는다.** 모델은 "이 도구를 이 인자로" **결정**하고, 실행은 **애플리케이션(코드)** 이 한다
> - `@tool`: 타입 힌트 + docstring → 도구 이름·설명·인자 스키마. 설명이 곧 모델이 읽는 사용 설명서다
> - `bind_tools()`는 도구를 **알려 주기만** 하고(`AIMessage.tool_calls`), `create_agent()`는 **실행 루프까지** 돌린다 (결과는 LangGraph `CompiledStateGraph`)
> - `response_format=Pydantic모델` → `result["structured_response"]`에 검증된 객체. 단, **형식만 보장하고 사실은 보장하지 않는다**
> - MCP: 외부 서버가 공개한 도구를 `MultiServerMCPClient.get_tools()`로 가져와 같은 에이전트에 꽂는다

- 코드: [`exam3.ipynb`](exam3.ipynb) (강사님 자료 `fwedu/exam3.ipynb` 사본, 강의 슬라이드 이미지 포함, 📝 정리 셀 추가)
- 실행 환경: langchain 1.4.6, langchain-core 1.6.12, langchain-openai 1.7.2, langchain-mcp-adapters 0.3.2, pydantic 2.14.1
- 10/12~10/16에 OpenAI SDK로 직접 짰던 도구 호출 루프([도구 호출](../ex1012/도구호출.md), [ReAct](../ex1016/다중LLM과ReAct.md))를 LangChain이 대신 돌려 주는 버전이다.

## 1. 도구가 없으면 "지금 몇 시야?"도 못 한다

```python
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm.invoke("지금 몇 시야? 그리고 오늘 날짜도 알려줘.").content
# '죄송하지만, 현재 시간을 확인하거나 날짜를 알려드릴 수는 없습니다. ...'
```

모델은 학습한 지식만 가지고 있어서 현재 시각·날씨처럼 **지금 바뀌는 값**은 모른다. 이런 값은 믿을 수 있는 외부 데이터(도구)에서 가져와야 한다.

## 2. `@tool`로 함수를 도구로 만들기

```python
@tool
def get_current_time() -> str:
    """현재 한국 표준시(Asia/Seoul)의 날짜와 시각을 반환합니다."""
    return datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S %Z")

get_current_time.name         # 'get_current_time'
get_current_time.description  # docstring
get_current_time.args         # {}  (인자 없음)
get_current_time.invoke({})   # '2026-10-19 14:15:32 KST'
```

- 함수 이름 → 도구 이름, docstring → 설명, 타입 힌트 → 인자 스키마.
- 좋은 도구 설명에는 **언제 쓰는지, 인자에 허용되는 값, 반환 데이터, 실패 조건**이 들어간다. 목표는 "모델이 추측하지 않아도 되게" 만드는 것.
- 날씨 도구 `get_current_weather(location: str)`는 docstring에 "영문 도시명. 예: Seoul, Tokyo, London, Suwon"을 적어 두었다. 그래서 "경기도 수원"이라고 물어도 모델이 `Suwon`으로 바꿔 넘겼다.
- 외부 API(wttr.in)가 실패하면 예외를 던지지 않고 `{"error": "날씨 API 조회 실패: ..."}` JSON을 돌려준다. 모델이 오류를 날씨 정보처럼 말하지 않도록 프롬프트에도 적어 두는 것이 좋다.

## 3. `create_agent()`: 도구 실행 루프 자동화

```python
agent = create_agent(
    model=ChatOpenAI(model="gpt-4o-mini"),
    tools=[get_current_time],
    system_prompt="당신은 친절한 어시스턴트입니다. 필요하다면 제공된 도구를 적극적으로 사용하세요.",
)
result = agent.invoke({"messages": [{"role": "user", "content": "지금 몇 시야?"}]})
result["messages"][-1].content    # 최종 답변
type(agent)                       # langgraph.graph.state.CompiledStateGraph
```

실행 중 오간 메시지:

```
[HumanMessage] 지금 몇 시야? 그리고 오늘 날짜도 알려줘.
[AIMessage]    (내용 없음) -> tool_calls: get_current_time {}
[ToolMessage]  2026-10-19 14:19:11 KST
[AIMessage]    현재 시각은 2026년 10월 19일 오후 2시 19분입니다.
```

- 결과는 문자열이 아니라 **상태 dict**다. 최종 답은 `result["messages"][-1].content`.
- `create_agent`는 LangChain v1에서 LangGraph의 `create_react_agent`를 대신하는 함수다. `type(agent)`가 LangGraph 그래프로 나오는 것으로 **내부가 LangGraph**라는 것을 확인했다.
- 미들웨어(로깅·재시도·보안 검사), 체크포인터(메모리), Human-in-the-loop를 붙일 수 있다.

### 여러 도구를 한 번에 부르기

"경기도 수원 날씨 알려줘 그리고 현재 시간도 알려줘"에 대해 첫 `AIMessage`가 `get_current_weather({"location": "Suwon"})`와 `get_current_time({})` **두 개를 동시에** 요청했고, `ToolMessage` 두 개가 돌아온 뒤 한 번에 답했다. "서울과 런던 날씨"도 두 도시 값을 모두 도구에서 가져와 답했다(서울 19°C 흐림, 런던 10°C 맑음). 다만 호출 횟수와 순서는 보장되지 않는다.

## 4. 구조화 출력: `response_format`

```python
class DateTimeResponse(BaseModel):
    current_year: int = Field(description="연도")
    current_month: int = Field(description="월 (1~12)", ge=1, le=12)
    ...
agent = create_agent(model=..., tools=[get_current_time],
                     system_prompt="날짜/시간 답변 전에는 반드시 get_current_time 도구를 사용하세요.",
                     response_format=DateTimeResponse)
structured = agent.invoke(...)["structured_response"]   # DateTimeResponse 객체
# {'current_year': 2026, 'current_month': 10, 'current_date': 19, 'current_hour': 15, ...}
```

- 마지막 메시지 `content`를 JSON이라고 가정해 직접 파싱하지 않는다. `structured_response`에 Pydantic 검증을 통과한 객체가 들어 있다.
- 10/16에 OpenAI SDK의 `.parse()`로 했던 것([구조화된 출력](../ex1016/구조화된출력.md))을 에이전트 단계에서 하는 방법이다.
- **스키마가 맞아도 값이 틀릴 수 있다.** `ge=0, le=23` 같은 범위는 막아 주지만, 시각이 도구 결과와 같은지는 따로 확인해야 한다.

## 5. `bind_tools()` vs `create_agent()`

| API | 하는 일 | 결과 |
|---|---|---|
| `@tool` | 파이썬 함수를 도구로 선언 | 스키마를 가진 Tool 객체 |
| `llm.bind_tools([...])` | 모델에 쓸 수 있는 도구를 알려 줌 | **호출 제안**(`AIMessage.tool_calls`)만. 실행·재호출은 직접 짜야 함 |
| `create_agent(...)` | 도구 선택 → 실행 → 결과 전달 → 재호출 자동 | 메시지 목록이 든 상태 dict |
| `response_format=모델` | 최종 결과 스키마 지정 | `result["structured_response"]` |
| `MultiServerMCPClient.get_tools()` | 외부 MCP 서버의 도구 가져오기 | LangChain 도구 리스트 |
| `agent.ainvoke(...)` | 비동기 실행 (MCP는 async) | 상태 dict |

## 6. 내장 도구(web_search)는 다른 종류의 도구다

```python
web_model = ChatOpenAI(model="gpt-4o-mini", use_responses_api=True)
web_model = web_model.bind_tools([{"type": "web_search_preview"}])
response = web_model.invoke("오늘 AI 분야의 중요한 소식을 출처와 함께 요약해줘.")
type(response.content)   # list  ([web_search_call 블록, text 블록(+출처 annotations)])
```

- `@tool`은 **내 파이썬 프로그램**이 실행하고, `web_search` 같은 내장 도구는 **OpenAI 서버**가 실행한다. 지원 모델·요금·사용 조건이 따로 있다.
- Responses API를 쓰면 `content`가 문자열이 아니라 **블록 리스트**다. `content[1]["text"]` 같은 고정 인덱스로 꺼내지 않는다.
- 실행 결과를 보면 "오늘 소식"을 물었는데 출처 날짜가 3월·6월·9월 기사였고, AI와 상관없는 대기업 채용 소식도 섞였다. **검색 도구를 붙여도 날짜·주제 조건은 모델이 느슨하게 처리한다.** 최신성이 중요하면 날짜를 질문에 명시하고 출처 날짜를 확인해야 한다.

## 7. MCP (Model Context Protocol)

```python
client = MultiServerMCPClient({
    "weather": {"url": "https://open-meteo.caseyjhand.com/mcp", "transport": "streamable_http"}
})
tools = await client.get_tools()     # 서버가 공개한 도구 목록
agent = create_agent(model=..., tools=tools)
await agent.ainvoke({"messages": [...]})
```

- `@tool`은 **내 프로그램 안의 함수**, MCP는 **외부 서버가 표준 프로토콜로 공개한 도구**다. 에이전트 입장에서는 둘 다 똑같은 도구 리스트다.
- 공개 Open-Meteo MCP 서버(API 키 불필요)에서 `openmeteo_search_locations`, `openmeteo_get_forecast`, `openmeteo_get_air_quality` 등 **11개 도구**를 받아 왔고, 에이전트가 서울을 검색해 현재 17.4°C 맑음이라고 답했다.
- 같은 시각에 wttr.in 도구는 서울 19°C 흐림이라고 했다. **데이터 출처가 다르면 값도 다르다** → 답변에 출처를 남기는 것이 좋다.
- MCP 사용 전 확인할 것: 전송 방식(`streamable_http` / `stdio`), **신뢰할 수 있는 서버인지**, 도구 이름·설명, 그리고 개인정보나 API 키를 도구 인자로 보내지 않기. 공개 서버는 언제든 종료·변경될 수 있다.

## 🔁 복습 질문

<details>
<summary>1. 도구 호출에서 LLM과 애플리케이션은 각각 무엇을 하나?</summary>

LLM은 어떤 도구를 어떤 인자로 부를지 결정(`tool_calls`)하고, 애플리케이션(또는 에이전트 런타임)이 실제 파이썬 함수를 실행해 결과를 `ToolMessage`로 돌려준다.
</details>

<details>
<summary>2. <code>@tool</code>이 도구 스키마를 만들 때 쓰는 정보 세 가지는?</summary>

함수 이름(도구 이름), docstring(설명), 타입 힌트(인자 스키마).
</details>

<details>
<summary>3. <code>bind_tools()</code>만 쓰면 무엇을 직접 구현해야 하나?</summary>

`tool_calls`를 읽어 함수를 실행하고, 결과를 `ToolMessage`로 붙여 모델을 다시 부르는 루프. `create_agent()`는 이 루프를 대신 돌린다.
</details>

<details>
<summary>4. <code>agent.invoke()</code>의 결과에서 최종 답과 구조화 결과는 어디에 있나?</summary>

최종 답은 `result["messages"][-1].content`, `response_format`을 지정했다면 검증된 객체는 `result["structured_response"]`.
</details>

<details>
<summary>5. 구조화 출력이 검증을 통과하면 내용도 믿어도 되나?</summary>

아니다. 형식(필드·타입·범위)만 보장한다. 값이 도구 결과와 일치하는지는 따로 확인해야 한다.
</details>

<details>
<summary>6. <code>@tool</code> 도구와 OpenAI 내장 <code>web_search</code> 도구의 차이는?</summary>

`@tool`은 내 프로그램이 실행하고, 내장 도구는 OpenAI 서버에서 실행된다. 내장 도구는 지원 모델·요금이 따로 있고 Responses API의 블록 리스트로 결과가 온다.
</details>

<details>
<summary>7. 원격 MCP 서버를 연결하기 전에 확인할 것은?</summary>

서버가 신뢰할 수 있는지, 전송 방식, 제공하는 도구 목록과 설명, 그리고 개인정보·API 키를 도구 인자로 보내지 않는지.
</details>
