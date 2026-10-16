# 도구를 쓰는 AI 에이전트를 FastAPI 서버로 만들기

> **한눈에 보기**
> - 10/12의 "LLM + 도구 + 에이전트 루프"를 **REST API 서버**(`POST /chat`)로 만들고 Streamlit 채팅 화면을 붙였다
> - `session_id`별 대화 기록을 서버에 보관해 대화를 이어 간다
> - `MAX_STEPS = 5`로 도구 호출 무한 반복 방지
> - 계산 도구는 `eval()` 대신 `ast`로 허용한 연산만 + **결과 크기 제한** (직접 찾아 고친 부분)

10/12에 노트북에서 만든 "LLM + 도구 + 에이전트 루프"를 **REST API 서버**로 만들고, Streamlit으로 채팅 화면을 붙였다. 에이전트 '유니코'는 시간 조회, 계산, 주사위, 점심 메뉴 추천 도구 4개를 쓰고, `session_id`로 대화를 이어 간다.

- 코드: [`fastapiedu/exam19.py`](fastapiedu/exam19.py) (서버), [`fastapiedu/exam19_client.py`](fastapiedu/exam19_client.py) (Streamlit 화면)
- 실행: `uvicorn exam19:app --reload` → 다른 터미널에서 `streamlit run exam19_client.py`
- 2절의 표는 OpenAI 호출만 정해진 응답을 돌려주는 가짜로 바꿔서 루프의 각 경우를 확인한 결과이고, 5절은 실제 OpenAI API로 실행한 결과다.

## 1. 구조

```
Streamlit 화면 ──POST /chat {"message", "session_id"}──▶ FastAPI
                                                          └─ run_agent(): LLM 호출 → 도구 실행 → 결과 전달 → … → 최종 답변
◀── {"session_id", "answer", "tool_calls": [사용한 도구 기록]} ──
```

| 메서드 | 주소 | 기능 |
|---|---|---|
| GET | `/` | 서버 상태 `{"status":"ok","model":"gpt-4o-mini","agent":"유니코"}` |
| GET | `/tools` | 도구 목록 (화면 사이드바에 표시) |
| POST | `/chat` | 에이전트와 대화. `response_model=ChatResponse` |
| GET | `/sessions/{session_id}` | 대화 기록 (user, assistant 메시지만) |
| DELETE | `/sessions/{session_id}` | 대화 기록 삭제 ("새 대화 시작" 버튼) |

## 2. 에이전트 루프

```python
for _ in range(MAX_STEPS):                       # 최대 5번 (무한 반복 방지)
    res = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
    msg = res.choices[0].message
    messages.append(msg.model_dump(exclude_none=True))
    if not msg.tool_calls:                       # 도구 호출이 없으면 최종 답변
        return msg.content, tool_logs
    for call in msg.tool_calls:                  # 있으면 실행하고 결과를 role="tool"로 추가
        result = TOOL_FUNCS[call.function.name](**json.loads(call.function.arguments or "{}"))
        messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False)})
return "생각이 너무 길어져서 멈췄어요. ...", tool_logs
```

10/12 노트북은 Responses API(`function_call_output`)였고, 이번 서버는 **Chat Completions API**(`role: "tool"` + `tool_call_id`)로 같은 루프를 만들었다. 도구 명세 형식도 `{"type": "function", "function": {...}}`로 한 단계 더 감싸는 점이 다르다.

| 확인한 경우 | 결과 |
|---|---|
| "(123 + 456) * 3 계산해줘" → `calculate` 호출 후 답변 | `{"session_id":"...","answer":"1737이에요!","tool_calls":[{"tool":"calculate","args":{"expression":"(123 + 456) * 3"},"result":{...,"result":1737}}]}` |
| 같은 `session_id`로 기록 조회 | user, assistant 메시지 2개 (도구 메시지는 빠짐) |
| 기록 삭제 후 다시 조회 | 404 |
| LLM이 계속 도구만 부름 | 5번 실행 후 "생각이 너무 길어져서 멈췄어요" |
| LLM이 없는 인자를 넣음 (`roll_dice`에 `color`) | `TypeError` → **500** "에이전트 실행 오류: ... unexpected keyword argument 'color'" |

## 3. 도구들

- `get_current_time(timezone)`: `zoneinfo`로 타임존별 현재 시각. 없는 타임존은 `{"error": "알 수 없는 타임존: Mars/Base"}`
- `calculate(expression)`: `eval()` 대신 `ast`로 수식을 해석해서 숫자와 사칙연산·거듭제곱·나머지만 계산한다. `"__import__('os')"` 같은 코드는 "지원하지 않는 수식입니다."로 거부된다.
- `roll_dice(sides, count)`: 개수는 1 ~ 10, 면은 2 ~ 1000으로 잘라서 받는다(`count=50` → 10개).
- `recommend_lunch(mood)`: 우울/피곤/신남/보통별 메뉴 중 하나. 목록에 없는 기분은 "보통" 메뉴에서 고른다.

도구 결과는 딕셔너리로 돌려주고, `json.dumps(..., ensure_ascii=False)`로 한글이 깨지지 않게 LLM에 전달한다.

## 4. 확인하고 고친 점

**계산기 도구로 서버를 멈출 수 있었다.** `ast`로 코드 실행은 막았지만 거듭제곱 크기는 제한이 없었다. `9**9**7`은 계산에 2초가 걸렸고, `9**9**8`은 20초가 지나도 끝나지 않았다. 이 도구는 사용자 문장을 보고 LLM이 호출하는 API라서, 누구든 이런 계산을 시켜 서버를 붙잡아 둘 수 있다.

→ 거듭제곱을 계산하기 전에 결과의 크기(비트 수 ≈ 지수 × 밑의 비트 수)를 어림해서 10,000비트(약 3천 자리)를 넘으면 오류를 돌려주도록 고쳤다. 지수만 제한하면 `((10**1000)**1000)**1000`처럼 나눠서 키울 수 있어서 결과 크기로 막았다. 고친 뒤 `9**9**8`, `((10**1000)**1000)**1000`은 바로 "거듭제곱 결과가 너무 큽니다."가 나오고, `2**100`, `999**999`, `2**-3`, `(-2)**3` 같은 일반 계산은 그대로 된다.

그 밖에 확인한 점:

- 도구 인자가 맞지 않으면 대화 전체가 500으로 끝난다. 도구 실행을 `try/except`로 감싸서 오류 내용을 도구 결과로 LLM에 돌려주면, LLM이 다시 시도하거나 사용자에게 설명할 수 있다.
- 대화 기록(`sessions`)은 서버 메모리에 쌓여서 재시작하면 사라지고, 지우지 않으면 계속 늘어난다.
- 파일 맨 위 설명에 실행 명령이 `uvicorn main:app`으로 되어 있어서 파일 이름에 맞게 `exam19:app`으로 고쳤다.

## 5. 실제 실행 결과

같은 `session_id`로 다섯 가지를 차례로 물었다. (계산기를 고친 정리본으로 실행)

| 질문 | 사용한 도구 | 답변 |
|---|---|---|
| 지금 서울이랑 뉴욕 시간 알려줘 | `get_current_time(Asia/Seoul)`, `get_current_time(America/New_York)` | 서울 10월 16일 오전 9시 25분, 뉴욕 10월 15일 저녁 8시 25분 |
| 방금 알려 준 것 중에 뉴욕 시간만 다시 말해 줘 | 없음 | 뉴욕 10월 15일 저녁 8시 25분 |
| 주사위 2개 굴려서 나온 합에 7을 곱해줘 | `roll_dice(6, 2)` → [4, 1] 합 5, 이어서 `calculate("5 * 7")` → 35 | 합은 5, 7을 곱하면 35 |
| 오늘 너무 피곤한데 점심 뭐 먹을까? | `recommend_lunch("피곤")` → 장어덮밥 | 피곤할 땐 장어덮밥 |
| 9**9**8 계산해줘 | `calculate("9**9**8")` → "거듭제곱 결과가 너무 큽니다." | 너무 커서 계산할 수 없다며 다른 계산을 제안 |

- **한 응답에 도구 두 개**: 서울과 뉴욕 시간을 한 번에 요청했다.
- **도구를 차례로 이어서 사용**: 주사위 결과(5)를 받은 다음 그 값으로 계산기를 불렀다. 에이전트 루프가 결과를 대화에 붙여 다시 LLM을 부르기 때문에 가능하다.
- **대화 기억**: 두 번째 질문은 도구 없이 앞 대화 기록(같은 `session_id`)만 보고 답했다.
- **고친 계산기**: 큰 거듭제곱은 서버가 멈추지 않고 바로 오류를 돌려줬고, LLM이 그 오류를 사용자에게 자연스럽게 설명했다.
- 다섯 번의 대화가 약 11초 걸렸다(도구를 쓰는 질문은 LLM을 두 번 이상 호출한다).

## 6. Streamlit 화면 (exam19_client.py)

- 사이드바: 서버 주소 입력, `/`와 `/tools`로 연결 상태와 도구 목록 표시, 예시 질문 버튼, "새 대화 시작"(서버의 기록도 `DELETE`)
- 대화: `st.chat_input` / `st.chat_message`로 채팅 UI, 응답의 `tool_calls`는 접이식 영역에 "사용한 도구"로 표시
- Streamlit은 입력할 때마다 스크립트를 처음부터 다시 실행해서, 대화 목록과 `session_id`를 `st.session_state`에 보관한다.

## 정리

| 배운 것 | 코드 |
|---|---|
| 에이전트를 API로 | `POST /chat` → `run_agent()` → `ChatResponse(session_id, answer, tool_calls)` |
| 대화 이어 가기 | `session_id`별 메시지 리스트를 서버에 보관 |
| 무한 루프 방지 | `MAX_STEPS = 5` |
| 안전한 계산 | `eval()` 대신 `ast` + 허용 연산자 목록 + 결과 크기 제한 |
| 화면 분리 | Streamlit이 `requests`로 API 호출 |

## 🔁 복습 질문

<details>
<summary>1. 계산 도구에서 <code>eval()</code>을 쓰면 안 되는 이유는?</summary>

사용자 입력(또는 LLM이 만든 식)이 임의의 파이썬 코드로 실행될 수 있다.
</details>

<details>
<summary>2. 지수 크기만 제한하던 방식의 문제와 고친 방법은?</summary>

`((10**1000)**1000)**1000`처럼 거듭제곱을 겹치면 우회됐다. 결과 크기를 미리 추정해(`지수 × 밑의 비트 수`) 한도를 넘으면 막았다.
</details>

<details>
<summary>3. 세션별 대화 기록을 메모리 dict에 두면 생기는 한계는?</summary>

서버를 재시작하면 사라지고, 서버를 여러 대 두면 공유되지 않는다. 실제 서비스는 DB나 Redis에 둔다.
</details>
