# 다중 LLM과 ReAct를 LangChain으로: RunnableParallel, assign 파이프라인, create_agent

> **한눈에 보기**
> - 10/16에 OpenAI·Google·Ollama SDK로 따로따로 짰던 [다중 LLM과 ReAct](../ex1016/다중LLM과ReAct.md)를 **LangChain 1.x로 다시 작성**했다
> - 세 모델 모두 `ChatOpenAI` / `ChatGoogleGenerativeAI` / `ChatOllama` → **같은 `invoke()`**. `prompt | llm | parser` 체인으로 통일
> - 병렬: `ThreadPoolExecutor` 대신 **`RunnableParallel`**, 순차: 함수 3개 대신 **`RunnablePassthrough.assign()`** 이 state dict에 `spec → code → review`를 한 칸씩 쌓는다
> - ReAct: `bind_tools` + `ToolMessage`로 루프를 직접 짜 보고, **`create_agent`** 로 같은 일을 맡김 (`stream_mode="updates"`로 Thought/Action/Observation 출력)
> - 실행 결과에서 본 문제: 작은 로컬 모델이 **`<think>` 추론을 답에 섞고 지시(파이썬 코드만)를 무시**, 에이전트가 **도구 결과 없이 스스로 계산**하거나 **예산 초과 장소를 1순위로 추천**

- 코드: [`exam5.ipynb`](exam5.ipynb) (강사님 자료 `fwedu/exam5.ipynb` 사본, 강의 슬라이드 이미지 포함, 📝 정리 셀 추가)
- 모델: `gpt-4o-mini`, `gemini-3.5-flash-lite`(langchain-google-genai 4.4.2), Ollama `exaone4.0`(EXAONE 4.0 1.2B)

## 1. SDK 직접 호출 → LangChain

| 구분 | 10/16 (SDK 직접) | 10/20 (LangChain) |
|---|---|---|
| 모델 객체 | `OpenAI()` / `genai.Client()` / `OpenAI(base_url=ollama)` | `ChatOpenAI` / `ChatGoogleGenerativeAI` / `ChatOllama` |
| 호출 | `responses.create` / `models.generate_content` / `chat.completions.create` | 모두 `invoke()` |
| 답 꺼내기 | `output_text` / `.text` / `choices[0].message.content` | `StrOutputParser()` 또는 `.text` |
| 병렬 | `ThreadPoolExecutor` + `submit` + `result()` | `RunnableParallel` |
| 순차 | 함수 3개를 차례로 호출 | `RunnablePassthrough.assign()` 체인 하나 |
| 도구 정의 | JSON 스키마를 손으로 (`strict`, `additionalProperties`) | `@tool(parse_docstring=True)` — docstring의 `Args:`가 인자 설명 |
| ReAct 루프 | `for step in range(max_steps)` | `create_agent(...)` (`recursion_limit` 초과 시 `GraphRecursionError`) |

```python
def build_chain(llm, system=None):
    messages = ([("system", system)] if system else []) + [("human", "{question}")]
    return ChatPromptTemplate.from_messages(messages) | llm | StrOutputParser()

def safe(chain, name):          # 한 모델이 실패해도 전체가 멈추지 않게 (10/16의 try/except)
    def _run(inputs, config):
        try:
            return chain.invoke(inputs, config)
        except Exception as e:
            return f"{name} 에러 (키/모델/서버 확인 필요): {e}"
    return RunnableLambda(_run)
```

- 10/16에는 Gemini 호출이 없는 메서드(`models.send_message`)를 불러 매번 에러였는데, 이번에는 `ChatGoogleGenerativeAI`로 바꾸니 **세 모델 모두 정상으로 답했다.** 다만 `safe()`도 에러를 문자열로 돌려주므로, 종합 전에 에러 여부를 확인해야 한다는 10/16 교훈은 그대로다(`with_fallbacks([...])`로 다른 체인에 넘기는 방법도 있다).
- 첫 호출에서 "Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY." 경고가 나왔다. 키 이름 두 개를 모두 인식하므로 하나만 두는 게 깔끔하다.
- Gemini 3.5 Flash-Lite는 **마지막 메시지가 AI 메시지인 요청을 지원하지 않는다**(항상 Human 메시지로 끝나게).

## 2. 병렬: 세 모델에 동시에 묻고 GPT가 종합

```python
parallel = RunnableParallel(gpt=ask_gpt, gemini=ask_gemini, ollama=ask_ollama)
answers = parallel.invoke({"question": user_question})        # 34.9초 (가장 느린 모델 기준)

report_chain = (
    RunnablePassthrough.assign(gpt_answer=ask_gpt, gemini_answer=ask_gemini, ollama_answer=ask_ollama)
    | synthesis_prompt | gpt | parser                          # 수집 + 종합을 체인 하나로
)
```

- 질문: "초보 개발자의 첫 웹 백엔드 스택으로 FastAPI와 Spring Boot 중 무엇을 추천?" GPT는 장단점 나열, Gemini는 **Spring Boot를 분명히 추천**, EXAONE은 생각 과정을 길게 적었다. 종합 리포트는 "빠른 개발이면 FastAPI, 취업·대규모면 Spring Boot"로 정리했다.
- `RunnableParallel`은 내부 스레드 풀로 실행한다. 동시 실행 수는 `config={"max_concurrency": 3}`, 비동기는 `await parallel.ainvoke(...)`.
- `runnable.get_graph().draw_mermaid_png()`로 체인 구조를 그림으로 볼 수 있다(mermaid.ink를 쓰므로 인터넷 필요, 실패하면 `draw_mermaid()` 코드를 출력).

## 3. 순차 파이프라인: 설계 → 구현 → 검증

```python
pipeline = (
    RunnablePassthrough.assign(spec=planner_chain)       # Gemini: 기능 명세서     {idea} → {idea, spec}
    | RunnablePassthrough.assign(code=developer_chain)   # EXAONE: 파이썬 코드     → {..., code}
    | RunnablePassthrough.assign(review=reviewer_chain)  # GPT: 검증, Pass/Fail    → {..., review}
)
result = pipeline.invoke({"idea": "비밀번호를 솔트 + SHA-256으로 해싱하고 검증하는 보안 모듈"})
```

- `assign`이 이전 결과를 지우지 않고 쌓으므로 `result["spec"]`, `result["code"]`, `result["review"]`를 모두 다시 볼 수 있다. 중간에 `RunnableLambda`로 **진행 상황을 출력하는 단계**(`log()`)를 끼워 넣었다.
- **실행 결과의 문제**: 개발자 역할의 EXAONE 4.0 1.2B는 "설명 없이 파이썬 코드만"이라는 지시를 무시하고, 영어 `<think>` 추론 + **TypeScript로 된 명세서**를 냈다. `generateSalt()`의 변환 코드도 동작하지 않는 코드였다.
- GPT 리뷰어는 **Fail**을 줬지만, 이유는 세부 로직(hex 변환, `timingSafeEqual` 사용법)이었고 **파이썬이 아니라는 점은 지적하지 않았다.** 검증 모델도 놓칠 수 있다 → 언어·형식처럼 코드로 확인할 수 있는 것은 코드로 먼저 검사한다(예: 코드 블록이 ```` ```python ````인지, `ast.parse`가 되는지).
- 추론(reasoning) 모델은 답에 `<think>...</think>`를 섞어 내보낼 수 있다. 다음 단계에 넘기기 전에 잘라 내야 한다.

## 4. ReAct 소스(1): 루프 직접 만들기

```python
llm_with_tools = gpt.bind_tools([calculator], parallel_tool_calls=False)
ai = llm_with_tools.invoke(messages)
if not ai.tool_calls:                    # 도구 요청 없음 = 최종 답변
    return ai.text
for call in ai.tool_calls:
    result = TOOLS_BY_NAME[call["name"]].invoke(call["args"])     # JSON 파싱 불필요
    messages.append(ToolMessage(content=result or "(빈 결과: ...)", tool_call_id=call["id"]))
```

계산기는 일부러 3번 중 2번 빈 결과를 돌려준다.

| 질문 | 도구 호출 | 최종 답 | 문제 |
|---|---|---|---|
| 153 × 27 | 1번, 빈 결과 | "계산 결과를 확인할 수 없네요. 직접 계산해보면 4131" | 재시도하지 않고 **스스로 계산**했다(이번엔 맞음) |
| (1+2) × 4 | 4번: `(1 + 2) * 4` 실패 ×2 → `1 + 2` = 3 → `3 * 4` 실패 | 12 | 식을 나눠 다시 시도한 건 좋았지만, **마지막 단계는 도구 결과 없이** 답했다 |

- 10/16 SDK 버전에서는 같은 상황에서 모델이 다시 호출해 4131을 얻었다. 같은 코드 구조라도 **재시도할지는 모델 마음**이다. "계산기로 정확히 확인해줘"가 반드시 지켜진다는 보장이 없으므로, 도구 결과가 필수인 값은 **답에 도구 결과가 쓰였는지 코드로 확인**해야 한다.

## 5. ReAct 소스(2): create_agent + Thought 출력

```python
agent = create_agent(model=ChatOpenAI(model="gpt-4o-mini", temperature=0.2),
                     tools=[get_weather, search_places, estimate_total_cost],
                     system_prompt=INSTRUCTIONS)            # "도구 호출 전에 Thought: 한 문장"
for chunk in agent.stream({"messages": [HumanMessage(q)]},
                          config={"recursion_limit": max_steps * 2 + 1},   # 1 step = model + tools 2칸
                          stream_mode="updates"):            # 노드가 끝날 때마다 새 메시지만
    ...   # ai 메시지: Thought(.text) + Action(tool_calls) / tool 메시지: Observation
```

`show_graph(agent)`로 그려 보니 `__start__ → model ⇄ tools → __end__`, 소스(1)의 while 루프와 같은 구조였다.

| 요청 | 도구 순서 | 추천 | 판정 |
|---|---|---|---|
| 토요일, 비 오면 실내, 2명 6만원 이하, 문화 선호 | 날씨(비) → 장소(실내·문화) → 비용 **3곳 동시에** | 국립중앙박물관 0원 | ✅ 답은 맞음. 다만 Thought 줄이 없었고, "도구는 한 번에 하나씩" 규칙도 어겼다 |
| 일요일, 2명 | 날씨(맑음) → 장소(산책) → 비용 | 한강공원 20,000원 | 예산을 말하지 않았는데 "예산 20,000원으로 충족"이라고 적음 |
| 일요일, 2명이 **10,000원** | 날씨 → 장소 → 비용 | **한강공원 20,000원**, "예산 초과로 충족되지 않습니다" | ❌ 스스로 초과라고 쓰고도 1순위 추천. 조건에 맞는 서울숲(0원)은 대안으로만 |

- 10/16과 **똑같은 실수**가 LangChain 버전에서도 나왔다. 프레임워크를 바꿔도 모델의 판단 실수는 그대로다 → 예산처럼 숫자로 확인할 수 있는 조건은 **코드로 다시 검사**하거나, 도구가 조건에 맞는 후보만 돌려주게 만든다.
- `bind_tools(parallel_tool_calls=False)`를 쓴 소스(1)과 달리 `create_agent`에는 그 설정이 없어서, 프롬프트의 "한 번에 하나씩"만으로는 동시 호출을 막지 못했다.
- Thought 문장 끝에 `functions.get_weather` 같은 내부 표기가 섞여 나왔다. Thought는 프롬프트로 부탁한 출력일 뿐이라 형식이 매번 같지는 않다.

## 6. ReAct 소스(3): 실패하면 다시 시도

"7명 회의, 먼저 Alpha로 시도, 안 되면 다른 방" → `reserve_room(Alpha)` **unavailable** → `search_available_rooms`(Beta 8명, Delta 12명) → `reserve_room(Beta)` **success** → "Beta 회의실이 예약되었습니다." 재시도 로직을 코드로 짜지 않아도, 실패 결과가 `ToolMessage`로 쌓이면 모델이 읽고 다음 행동을 바꾼다. 소스(2)의 `run_verbose()` 출력 함수를 그대로 재사용했다.

## 정리

| 원본(SDK) | LangChain | 얻는 것 |
|---|---|---|
| SDK 3종 | `ChatOpenAI` · `ChatGoogleGenerativeAI` · `ChatOllama` | 모델 교체 = 클래스 한 줄 |
| `ask_*()` 함수 | `prompt \| llm \| StrOutputParser()` | 부품처럼 조립 |
| `ThreadPoolExecutor` | `RunnableParallel`, `assign` | 병렬을 선언만으로, `ainvoke`로 비동기 |
| 순차 함수 호출 | `assign` 체인 | 중간 결과가 state dict에 남음 |
| JSON 스키마 + `call_tool()` | `@tool(parse_docstring=True)` | 스키마 자동 생성 |
| `for` 루프 ReAct | `create_agent` | 루프·종료·재귀 제한을 프레임워크가 관리 |

원리를 배울 때는 루프를 직접 짜 보고(소스 1), 실무에서는 `create_agent`처럼 검증된 부품을 쓴다. 흐름이 더 복잡해지면(분기, 사람 승인, 여러 에이전트) LangGraph로 직접 그래프를 설계한다.

## 🔁 복습 질문

<details>
<summary>1. <code>RunnableParallel(gpt=..., gemini=..., ollama=...)</code>의 결과와 걸리는 시간은?</summary>

`{"gpt": ..., "gemini": ..., "ollama": ...}` dict. 세 호출이 동시에 실행되므로 가장 느린 모델의 시간만큼 걸린다(이번 실행 34.9초).
</details>

<details>
<summary>2. 순차 파이프라인에서 <code>RunnablePassthrough.assign()</code>을 쓰는 이유는?</summary>

입력 dict를 유지한 채 새 키를 추가하므로 `idea → spec → code → review`가 한 dict에 쌓인다. 다음 단계는 이전 결과를 모두 쓸 수 있고, 끝난 뒤 중간 결과도 다시 볼 수 있다.
</details>

<details>
<summary>3. 개발자 역할 모델이 TypeScript 명세서를 냈는데 리뷰어가 그 점을 지적하지 않았다. 어떻게 막을까?</summary>

형식은 코드로 검사한다. 예를 들어 파이썬 코드 블록이 있는지, `ast.parse`가 통과하는지 확인하고, 실패하면 다음 단계로 넘기지 않고 다시 요청한다. 추론 모델의 `<think>` 부분도 잘라 낸다.
</details>

<details>
<summary>4. <code>bind_tools</code>로 루프를 직접 짤 때 도구 결과는 어떻게 모델에 돌려주나?</summary>

`ToolMessage(content=결과, tool_call_id=call["id"])`를 messages에 추가하고 모델을 다시 부른다. `tool_call_id`가 요청과 결과를 짝지어 준다.
</details>

<details>
<summary>5. <code>create_agent</code>의 <code>recursion_limit</code>을 <code>max_steps * 2 + 1</code>로 준 이유는?</summary>

한 step이 model 노드와 tools 노드 두 칸을 쓰고, 마지막 최종 답변에 model 노드 한 칸이 더 필요하기 때문이다. 넘으면 `GraphRecursionError`가 난다.
</details>

<details>
<summary>6. 에이전트가 "예산 초과"라고 적고도 그 장소를 추천했다. 이번에 배운 교훈은?</summary>

SDK든 LangChain이든 모델의 판단 실수는 그대로 나온다. 숫자 조건은 코드로 다시 검사하거나, 도구가 조건을 만족하는 후보만 돌려주게 한다.
</details>
