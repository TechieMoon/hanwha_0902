# OpenAI API 시작하기

> **한눈에 보기**
> - OpenAI API를 쓰려면 OpenAI Platform에서 발급한 **API 키**가 필요하다. 키는 비밀번호처럼 다룬다.
> - 키는 코드에 쓰지 않고 **`OPENAI_API_KEY` 환경변수**나 **`.env` 파일**에 둔다. `OpenAI()`가 이 이름을 알아서 찾는다.
> - `.env`를 쓰면 반드시 `.gitignore`에 넣어 깃허브에 올라가지 않게 한다.
> - `client.responses.create(model=..., input=...)`로 요청하고 `response.output_text`로 답 글자만 꺼낸다.
> - LangChain의 `ChatOpenAI`로도 같은 일을 할 수 있다: `invoke`(한 번에 받기), `stream`(조각씩 받기), `response_metadata`(토큰 사용량) → 아래 'LangChain으로 호출하기'

| 코드 | 내용 |
|---|---|
| [apikey_test.py](apikey_test.py) | 키가 잘 설정됐는지 확인 |
| [page90.ipynb](page90.ipynb) | OpenAI SDK로 첫 호출, 응답 객체 구조 |
| [page92.ipynb](page92.ipynb) | LangChain `ChatOpenAI`: invoke, 메타데이터, logprobs, stream |
| [requirements.txt](requirements.txt) | 이날 가상환경의 패키지 목록 |

## OpenAI API key 테스트

```python
import os
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6-luna",
    input="안녕하세요라고 한마디만 해줘."
)

print(response.output_text)
```

윈도우의 환경변수에 들어가서 변수명은 `OPENAI_API_KEY`로 넣고, 변수 값은 OpenAI Platform에서 발급 받은 api key로 넣는다.

OpenAI 라이브러리가 `OPENAI_API_KEY` 변수명을 알아서 찾기 때문에 코드에서 api key를 입력할 필요가 없다.

---

`.env`로도 가능하다.

`.env`에 다음과 같이 저장한다.

```env
OPENAI_API_KEY=sk-*****************************
```

코드 상단에 다음 내용을 추가한다.

```python
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
```

그러면 운영체제 환경변수처럼 똑같이 작동한다.

> `load_dotenv()`는 같은 폴더(또는 상위 폴더)의 `.env`를 읽어 환경변수로 등록한다. `python-dotenv` 패키지가 필요하다 (`pip install python-dotenv`).

## LangChain으로 호출하기 ([page92.ipynb](page92.ipynb))

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(temperature=0.1, model="gpt-5.6-luna")
response = llm.invoke("대한민국의 수도는 어디인가요?")
```

| 꺼내는 것 | 결과 |
|---|---|
| `response` | `AIMessage(content=..., response_metadata=..., ...)` 객체 |
| `response.content` | 답 글자만: `'대한민국의 수도는 서울특별시입니다.'` |
| `response.response_metadata["token_usage"]` | 토큰 사용량 (이 질문은 입력 15 + 출력 14 = 29토큰) |

- **temperature**: 0에 가까울수록 같은 질문에 비슷한 답, 높을수록 다양한 답.
- **`.bind(logprobs=True)`**: 답의 각 토큰을 모델이 얼마나 확신했는지(로그 확률)를 메타데이터에 함께 받는다. 실행 결과에서 `' 서울'` 토큰의 logprob은 약 -0.0002로, 0에 가까울수록 확신이 크다는 뜻이다.
- **`llm.stream(...)`**: 답을 다 만들 때까지 기다리지 않고 조각(chunk)마다 받는다. `print(token.content, end="", flush=True)`로 이어 찍으면 채팅처럼 글자가 흘러나온다. 조각을 `+=`로 모으면 전체 답이 된다.
- stream을 두 번 실행한 결과를 보면 관광지 목록이 서로 다르다. 같은 질문이어도 매번 답이 조금씩 달라질 수 있다.

## 🔁 복습 질문

<details>
<summary>1. API 키를 코드에 직접 쓰면 안 되는 이유는?</summary>

코드가 깃허브 등에 올라가면 키가 공개되어 다른 사람이 내 돈으로 API를 쓸 수 있다. 환경변수나 `.env`(+ `.gitignore`)에 둔다.
</details>

<details>
<summary>2. <code>OpenAI()</code>에 키를 넣지 않았는데 어떻게 동작하나?</summary>

`OPENAI_API_KEY`라는 환경변수를 자동으로 찾아 쓴다. `.env`를 쓸 때는 `load_dotenv()`가 그 값을 환경변수로 등록해 준다.
</details>

<details>
<summary>3. OpenAI SDK 응답에서 답 글자만 꺼내려면? LangChain에서는?</summary>

OpenAI SDK의 Responses API는 `response.output_text`, LangChain은 `response.content`.
</details>

<details>
<summary>4. <code>invoke</code>와 <code>stream</code>의 차이는?</summary>

`invoke`는 답이 다 만들어진 뒤 한 번에 받고, `stream`은 만들어지는 대로 조각씩 받는다. 사용자에게 바로바로 보여 줄 때 stream을 쓴다.
</details>

<details>
<summary>5. 요청 한 번에 토큰을 얼마나 썼는지 확인하려면?</summary>

LangChain 응답의 `response.response_metadata["token_usage"]`에서 `prompt_tokens`(입력), `completion_tokens`(출력), `total_tokens`(합계)를 본다.
</details>