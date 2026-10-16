# 다중 LLM 활용과 ReAct 에이전트

> **한눈에 보기**
> - 다중 LLM 두 가지 패턴: **병렬**(같은 질문을 GPT·Gemini·EXAONE에 동시에 → GPT가 종합)과 **순차**(Gemini 설계 → EXAONE 구현 → GPT 검증)
> - **ReAct**: Thought(생각) → Action(도구 호출) → Observation(결과)을 반복하면서 답을 찾는 에이전트 패턴
> - 실패한 Observation을 보고 다른 행동을 고르는 **재시도 루프**, 돈이 나가는 행동만 사람이 승인하는 **Human-in-the-loop**
> - 실행해 보니 모델은 도구를 건너뛰고 값을 지어내거나, 도구 결과와 맞지 않는 결론을 내기도 했다 → 중요한 조건은 코드로 다시 검사한다

- 코드: [`exam4.ipynb`](exam4.ipynb) (강사님 자료 `basicedu/exam4.ipynb` 사본. 강의 슬라이드 이미지는 빼고 자리만 표시, 실행 결과를 보고 쓴 **📝 정리** 셀 추가)
- 강사님이 함께 준 `실행결과.pdf`(순차 파이프라인을 미리 돌린 결과)는 저장소에 넣지 않고 3절에 요약했다.

## 1. 클라이언트 세 개 준비

```python
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))     # gpt-4o-mini
google_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))  # gemini (google-genai SDK)
ollama_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")  # 로컬 EXAONE 3.5
```

Ollama는 OpenAI와 같은 형식의 엔드포인트를 주기 때문에 `openai` 클라이언트에 `base_url`만 바꿔 재사용한다 (→ [10/12 LLM 연동하기](../ex1012/LLM연동하기.md)).

## 2. 병렬 패턴: 같은 질문을 동시에 묻고 종합하기

질문: "초보 개발자의 첫 웹 백엔드 스택으로 Python FastAPI와 Java Spring Boot 중 무엇을 더 추천하나요?"

```python
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        "GPT": executor.submit(ask_gpt, user_question),
        "Gemini": executor.submit(ask_gemini, user_question),
        "Ollama": executor.submit(ask_ollama, user_question),
    }
    gpt_answer = futures["GPT"].result()   # 끝날 때까지 기다렸다가 결과를 받는다
    ...
final_report = ask_gpt(synthesis_prompt)    # 세 답을 프롬프트에 넣고 GPT가 종합
```

- LLM 호출은 대부분 **응답을 기다리는 시간**이라, 스레드 3개로 동시에 보내면 하나씩 보낼 때보다 전체 시간이 짧아진다.
- 결과: 종합 리포트는 "초보자에게는 FastAPI, Spring Boot는 경험을 쌓은 뒤"로 정리했다.

**확인한 문제**: 종합 리포트가 Gemini를 "기술적 오류로 인해 미비함"이라고 평가했다. `ask_gemini`가 `google_client.models.send_message(...)`를 부르는데, google-genai의 `client.models`에는 이 메서드가 없다(`send_message`는 `client.chats.create(...)`로 만든 채팅 객체에 있다). 그래서 매번 `except`로 빠져 `"Gemini 에러: ..."` **문자열**을 돌려줬고, 종합하는 GPT는 그 에러 문자열을 Gemini의 "답변"으로 받아 평가했다. 올바른 호출은 순차 패턴 코드처럼 `models.generate_content(model=..., contents=...)`다.

> 여러 모델의 답을 합칠 때는 **각 호출이 성공했는지 먼저 확인**하고, 실패한 답은 종합에서 빼야 한다. 에러를 문자열로 돌려주면 다음 단계가 에러인지 알 수 없다.

## 3. 순차 패턴: 역할을 나눈 파이프라인

| 단계 | 모델 | 역할 | 넘겨주는 것 |
|---|---|---|---|
| 1 | Gemini | 시스템 아키텍트 | 기능 명세서 (함수 목록, 입출력 타입, 예외 기준) |
| 2 | EXAONE 3.5 (로컬) | 풀스택 개발자 | 명세를 반영한 파이썬 코드 |
| 3 | GPT-4o-mini | 시니어 QA 리뷰어 | 명세 대비 교차 검증 + Pass/Fail |

요청: "회원가입할 때 비밀번호를 SHA-256으로 해싱하고 솔트를 추가해 검증까지 하는 보안 모듈"

같은 파이프라인을 두 번 실행한 결과가 달랐다.

| | 강사님 실행 (`실행결과.pdf`) | 내 실행 (`exam4.ipynb`) |
|---|---|---|
| 솔트 | `os.urandom(16)` → Base64 | `os.urandom(16)` → Base64 (명세는 Hex) |
| 해시 비교 | `hmac.compare_digest` (상수 시간 비교) | `==` 직접 비교 |
| 리뷰 판정 | **Pass** (단, SHA-256 단독 사용은 PBKDF2·bcrypt·Argon2 같은 KDF로 개선 권고) | **Fail** (인코딩 불일치, 타이밍 공격 취약, 키 스트레칭 없음) |

- 같은 코드라도 LLM의 결과물은 **매번 달라진다**. 그래서 마지막 검증 단계(리뷰어)가 있어야 한다.
- 두 리뷰 모두 "SHA-256 한 번만으로 비밀번호를 저장하는 것은 약하다"고 짚었다. 실제 비밀번호 저장에는 느리게 만든 KDF(bcrypt, Argon2 등)를 쓴다.
- `hmac.compare_digest`는 문자열을 끝까지 같은 시간에 비교해서, 응답 시간 차이로 정답을 추측하는 **타이밍 공격**을 막는다.

## 4. ReAct: 생각하고, 행동하고, 관찰하기

**ReAct**(Reasoning + Acting, ICLR 2023 논문)는 LLM이 **Thought → Action → Observation**을 번갈아 하면서 답을 찾는 방식이다.

| 방식 | 하는 일 | 약점 |
|---|---|---|
| Chain-of-Thought | 추론만 한다 | 외부 확인이 없어 틀린 가정을 못 고친다(환각) |
| Act-only | 바로 도구만 부른다 | 왜 그 도구인지 설명이 없고 복잡한 문제에서 길을 잃는다 |
| Plan-and-Execute | 처음 세운 계획대로 밀고 간다 | 중간에 예상 못한 결과가 나와도 계획을 못 바꾼다 |
| **ReAct** | 매 단계 결과를 보고 다음 행동을 정한다 | 호출이 많아 느리고, 반복 상한이 필요하다 |

### 4-1. 최소 예제: 불안정한 계산기

```python
def calculator(expression: str) -> str:
    return str(eval(expression)) if random.randint(1, 3) == 1 else ""   # 3번에 1번만 성공
```

- 일부러 실패하는 도구다. "153 곱하기 27"에서 첫 호출이 빈 결과를 받자, 모델이 같은 식으로 다시 호출해 4131을 얻었다. **관찰을 보고 다시 행동**하는 것이 ReAct의 핵심이다.
- 반복 횟수 `count`는 실패한 호출에서만 늘어서, 실패를 최대 5번까지 허용한다.
- `eval()`은 학습용이다. LLM이 만든 식을 그대로 실행하므로 실제로는 [10/15 에이전트 서버](../ex1015/FastAPI_AI에이전트서버.md)처럼 `ast`로 허용한 연산만 계산한다.

### 4-2. 주말 나들이 추천 에이전트

도구 3개(`get_weather`, `search_places`, `estimate_total_cost`)와 작은 가짜 DB, 그리고 지시문(날씨가 영향을 주면 먼저 확인, 도구는 한 번에 하나, 호출 전에 `Thought:` 한 줄)으로 만든 에이전트다. `parallel_tool_calls=False`로 도구를 하나씩 부르게 해 흐름을 보기 쉽게 했다.

| 질문 | 도구 호출 | 결과 | 판정 |
|---|---|---|---|
| 토요일, 비 오면 실내, 6만원 이하, 문화 선호 | 날씨 → 장소(실내·문화) → 비용 | 국립중앙박물관(0원) | 조건에 맞음 |
| 일요일, 2명 | 날씨만 | 한강공원, "자전거 대여 약 5,000원" | **값을 지어냄**: 장소·비용 도구를 건너뛰었고, DB의 한강공원은 1인 10,000원 |
| 일요일, 2명, 1만원 이하 | 날씨 → 장소 → 비용 | 한강공원(20,000원), "예산 초과" | **결론이 틀림**: 대안으로 적은 서울숲(0원)이 조건에 맞는데 1순위로 고르지 않음 |

- 지시문에 "추측하지 말고 도구로 확인"이라고 써도 모델이 건너뛸 수 있다.
- 도구를 다 불렀어도 **마지막 판단이 틀릴 수 있다**. 예산처럼 숫자로 확인할 수 있는 조건은 코드로 다시 검사하는 편이 안전하다.
- Responses API에서 도구 호출과 함께 온 글자(`output_text`)가 그 턴의 Thought다. 첫 질문 출력에는 Thought가 없고 두 번째부터 보인다.

### 4-3. 재시도 루프: 회의실 예약

"7명 회의, 먼저 Alpha로 시도하고 안 되면 다른 곳으로" → `reserve_room("Alpha")` 실패(이미 예약됨) → `search_available_rooms` → Beta(8명)·Delta(12명) 후보 → `reserve_room("Beta")` 성공. 실패 결과를 보고 **다른 행동을 고르는** 것까지 확인했다. 도구 명세에 `"strict": True`와 `"additionalProperties": False`를 줘서 인자 형식을 강제했다.

### 4-4. Human-in-the-loop: 야식 주문 에이전트

```python
NEEDS_APPROVAL = {"order_food"}          # 돈이 나가는 도구만 승인 대상

def ask_human(name, args):
    answer = input("승인 = Enter / 거부·수정 지시 = 하고 싶은 말 입력 > ").strip()
    return answer == "", answer           # 빈 입력만 승인
```

- 조회 도구(`search_menu`, `check_budget`)는 자동 실행, 주문(`order_food`)만 사람에게 묻는다.
- **Enter만 승인**이고 무엇이든 입력하면 거부로 처리된다. "불닭볶음면 좋아요"라고 입력했더니 거부로 처리되어, 에이전트가 같은 주문을 한 번 더 요청했다. 승인 UI는 "예/아니오"를 분명히 받는 게 좋다.
- "고기 먹고싶다"에서 '소고기' 검색 결과가 없자 `search_menu`가 전체 메뉴를 돌려줬고(`found or MENU`), 에이전트는 떡볶이를 "고기 맛"이라며 추천했다. 검색 결과가 없을 때는 "없음"을 그대로 알려 주는 편이 모델이 덜 헷갈린다.
- `run_agent`를 부를 때마다 대화 기록은 새로 시작하지만 잔액(`wallet`)은 이어져서, 앞에서 냉면을 주문한 것을 모르고 다시 냉면을 제안했다.

## 정리

| 패턴 | 코드 | 핵심 |
|---|---|---|
| 병렬 다중 LLM | `ThreadPoolExecutor` + 종합 프롬프트 | 기다리는 시간을 겹쳐 빠르게. 합치기 전에 실패한 응답을 걸러야 한다 |
| 순차 다중 LLM | 설계 → 구현 → 검증 | 모델마다 잘하는 역할을 맡기고, 결과물은 리뷰어가 검증 |
| ReAct | Thought → Action → Observation 반복 | 결과를 보고 다음 행동을 정한다. 반복 상한 필수 |
| 재시도 | 실패 Observation → 다른 도구 | 실패를 숨기지 말고 이유와 함께 돌려준다 |
| Human-in-the-loop | 위험한 도구만 승인 | 돈·삭제·전송 같은 되돌릴 수 없는 행동 앞에서 멈춘다 |

LangGraph로 만든 [웹 검색 에이전트](../ex1006/웹검색에이전트.md)와 [RAG 에이전트](../ex1008/RAG에이전트그래프.md)도 같은 구조(생각 → 도구 → 결과 → 다시 생각)를 그래프로 표현한 것이다.

## 🔁 복습 질문

<details>
<summary>1. 병렬 패턴에서 <code>ThreadPoolExecutor</code>를 쓰면 빨라지는 이유는?</summary>

LLM 호출 시간 대부분은 서버 응답을 기다리는 시간이다. 세 요청을 동시에 보내면 기다리는 시간이 겹쳐서 전체 시간이 가장 느린 하나 정도로 줄어든다.
</details>

<details>
<summary>2. 종합 리포트가 Gemini를 "기술적 오류"라고 평가한 원인과 고치는 방법은?</summary>

`client.models`에 없는 `send_message`를 불러 매번 에러 문자열이 답변 자리에 들어갔다. `models.generate_content(model=..., contents=...)`로 고치고, 합치기 전에 실패한 응답은 빼야 한다.
</details>

<details>
<summary>3. 같은 순차 파이프라인인데 강사님 결과는 Pass, 내 결과는 Fail이 나온 이유는?</summary>

LLM이 만드는 명세와 코드는 실행할 때마다 달라진다. 내 실행에서는 해시를 `==`로 비교하고 명세와 다른 인코딩을 써서 리뷰어가 Fail을 줬다. 그래서 검증 단계가 필요하다.
</details>

<details>
<summary>4. ReAct의 세 단계와, Chain-of-Thought만 쓸 때의 약점은?</summary>

Thought(무엇을 할지 생각) → Action(도구 호출) → Observation(결과 확인)을 반복한다. CoT는 추론만 하고 외부에서 확인하지 않아 틀린 가정을 고치지 못한다.
</details>

<details>
<summary>5. 나들이 에이전트가 "자전거 대여 약 5,000원"이라고 답한 것은 무엇이 문제인가?</summary>

비용 도구를 부르지 않고 값을 지어냈다(DB의 한강공원은 1인 10,000원). 지시문이 있어도 모델이 도구를 건너뛸 수 있으므로, 중요한 수치는 도구 결과로만 쓰게 하거나 코드로 검사한다.
</details>

<details>
<summary>6. Human-in-the-loop에서 "불닭볶음면 좋아요"를 입력했는데 주문이 안 된 이유는?</summary>

`ask_human`은 빈 입력(Enter)만 승인으로 보고, 글자를 입력하면 모두 거부로 처리한다.
</details>

<details>
<summary>7. 사람 승인을 받아야 하는 도구는 어떤 것인가?</summary>

결제·삭제·메일 전송처럼 되돌릴 수 없거나 비용이 드는 행동. 조회만 하는 도구는 자동으로 실행해도 된다.
</details>
