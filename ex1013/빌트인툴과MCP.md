# OpenAI 도구 3가지: Function, 빌트인, MCP

10월 12일에는 직접 만든 파이썬 함수를 도구(function tool)로 연결하고 에이전트 루프를 짰다. 이날은 그 뒷부분으로, 좋은 도구 명세(Tool Schema)를 쓰는 원칙과 OpenAI가 제공하는 나머지 두 종류의 도구인 **빌트인 툴**과 **MCP 툴**을 실습했다.

- 코드: [`exam2.ipynb`](exam2.ipynb) (강사님 자료 `exam2.ipynb`의 뒷부분만 정리. 앞부분은 [`../ex1012/exam2.ipynb`](../ex1012/exam2.ipynb), 정리 문서는 [`../ex1012/도구호출.md`](../ex1012/도구호출.md))

## 1. 다시 보는 역할 분담

| 단계 | 누가 | 하는 일 |
|---|---|---|
| 1 | 개발자 → LLM | 질문과 사용할 수 있는 도구 목록(JSON Schema)을 보낸다 |
| 2 | LLM → 애플리케이션 | "이 함수를 이 인자로 실행해 줘"라는 호출 요청(`function_call`)을 돌려준다 |
| 3 | 애플리케이션 | 실제 파이썬 함수를 실행한다 |
| 4 | 애플리케이션 → LLM | 실행 결과를 돌려주면 LLM이 사람이 읽을 답을 만든다 |

LLM은 **결정**, 내 코드는 **실행**을 맡는다. 함수 도구에서는 2~4단계를 내가 루프로 짜야 했다.

## 2. Tool Schema 작성 원칙

좋은 스키마의 핵심은 **모델이 추측하지 않아도 되게** 쓰는 것이다. 수업에서 본 템플릿:

```python
{
    "type": "function",
    "name": "verb_noun",
    "description": (
        "One-sentence purpose. "
        "Use this when ... "
        "Do not use this when ..."
    ),
    "strict": True,
    "parameters": {
        "type": "object",
        "properties": {
            "arg1": {"type": "string", "description": "Exact meaning, expected format, and example."},
            "arg2": {"type": ["string", "null"], "description": "Optional value. Use null if not specified."},
        },
        "required": ["arg1", "arg2"],
        "additionalProperties": False,
    },
}
```

- `name`은 `동사_명사` 형태로 짓는다(예: `get_current_weather`).
- `description`에는 목적과 함께 **언제 쓰고 언제 쓰면 안 되는지**를 적는다. 모델은 함수 코드를 보지 못하고 이 설명만 보고 판단한다.
- 인자마다 의미, 형식, 예시를 적는다. 10/12 날씨 도구에서 `location` 설명에 "영문 도시명 (예: 'Seoul')"이라고 적었더니, 한국어로 "서울"이라고 물어도 모델이 `Seoul`로 바꿔서 넘겼다.
- `"strict": True`를 켜면 모델이 스키마를 정확히 지켜서 인자를 만든다. 대신 모든 속성을 `required`에 넣고 `additionalProperties: False`를 줘야 해서, 선택 인자는 빼는 대신 `["string", "null"]`처럼 null을 허용해서 표현한다(위 `arg2`).

## 3. 빌트인 툴: `web_search`

OpenAI가 미리 만들어 둔 도구는 `type`만 적으면 바로 쓸 수 있다.

```python
response = client.responses.create(
    model="gpt-4o-mini",
    input="2026년 10월 1일 발표된 중요한 AI 뉴스 알려줘",
    tools=[{"type": "web_search"}],
)
print(response.output_text)
```

실행 결과(요약): 2026년 10월 1일의 AI 관련 뉴스 3건을 출처 링크(`newspim.com`, `yna.co.kr` 등)와 함께 답했다.

- 함수 도구와 달리 검색을 **OpenAI 서버가 직접 실행**하고 결과까지 반영해서 답을 준다. 그래서 `function_call`을 받아 실행하고 결과를 돌려주는 루프가 필요 없다.
- 모델이 학습 이후의 날짜에 대한 질문에도 답할 수 있게 됐다. 링크마다 `utm_source=openai`가 붙어 있어서 웹 검색 결과를 인용했다는 걸 알 수 있다.
- 뉴스 내용 자체가 맞는지는 따로 확인하지 않았다. 검색 결과를 요약한 답이라 출처 링크를 열어 확인하는 습관이 필요하다.

## 4. MCP 툴

**MCP(Model Context Protocol)**는 외부 서버가 제공하는 도구를 표준 방식으로 연결하는 프로토콜이다. 함수 도구가 "내 앱 코드 안에 직접 등록한 함수"라면, MCP 툴은 "다른 곳에서 돌아가는 MCP 서버의 도구들"을 가져다 쓰는 것이다.

```python
response = client.responses.create(
    model="gpt-4o-mini",
    input="서울의 현재 기온, 습도를 알려줘.",
    tools=[{
        "type": "mcp",
        "server_label": "open_meteo",
        "server_url": "https://open-meteo.caseyjhand.com/mcp",
        "require_approval": "never",
        "allowed_tools": ["openmeteo_search_locations", "openmeteo_get_forecast"],
    }],
)
print(response.output_text)
```

```txt
현재 서울의 기온은 **16.5°C**이며, 습도는 **86%**입니다.
```

| 설정 | 의미 |
|---|---|
| `server_label` | 이 MCP 서버를 부를 이름 |
| `server_url` | MCP 서버 주소. OpenAI 서버가 여기에 접속해 도구 목록을 받고 호출한다 |
| `allowed_tools` | 서버의 도구 중 쓸 것만 허용. 여기서는 위치 검색(서울 → 좌표)과 예보 조회 두 개 |
| `require_approval` | 도구를 호출할 때마다 승인을 받을지. `"never"`면 승인 없이 바로 호출 |

확인한 점:

- 날씨 함수를 직접 짜지 않았고, 에이전트 루프도 없이 **요청 한 번**으로 답을 받았다. 빌트인 툴처럼 도구 호출을 OpenAI 쪽에서 처리하기 때문이다.
- 같은 날 아침 10/12에 만든 `wttr.in` 함수 도구로 조회한 서울 날씨는 17°C, 습도 84%였다. MCP 결과(16.5°C, 86%)와 비슷하지만 조회 시각과 데이터 출처(Open-Meteo)가 달라서 숫자가 조금 다르다.
- `require_approval: "never"`는 외부 서버를 그대로 믿는 설정이다. 남이 운영하는 서버라면 어떤 도구를 부르는지 확인할 수 있게 승인을 켜거나, `allowed_tools`로 쓸 도구를 좁혀 두는 게 안전하다.

## 정리

| 종류 | 설정 | 실행 주체 | 내가 할 일 |
|---|---|---|---|
| Function tool | `{"type": "function", "name", "description", "parameters"}` | **내 코드** | 함수 작성 + `function_call` 실행 루프 |
| 빌트인 툴 | `{"type": "web_search"}` 등 | OpenAI 서버 | `type`만 지정 |
| MCP 툴 | `{"type": "mcp", "server_url", "allowed_tools", ...}` | 외부 MCP 서버 (OpenAI가 호출) | 서버 주소와 허용할 도구만 지정 |

내 서비스만의 기능(우리 DB 조회 등)은 함수 도구로, 웹 검색처럼 흔한 기능은 빌트인 툴로, 이미 누군가 MCP 서버로 만들어 둔 기능은 MCP 툴로 붙이면 된다.
