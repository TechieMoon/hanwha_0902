# 다양한 방법으로 LLM 연동하기

> **한눈에 보기**
> - 같은 일을 여러 LLM·여러 방식으로 호출해 비교: **Ollama**(로컬) / **Gemini** / **OpenAI**
> - OpenAI 호환 엔드포인트(`base_url`)를 쓰면 다른 모델도 같은 코드 모양으로 호출할 수 있다
> - `chat.completions` vs `responses`: responses는 `output_text`, `instructions`, 서버 측 대화 기억(`previous_response_id`)
> - 이미지 분석·생성, 임베딩과 코사인 유사도, 프롬프트 기법(시스템 / Few-shot / CoT)

10월 12일부터 강사님이 직접 만든 자료로 수업이 진행됐다. 첫 시간에는 같은 일을 여러 LLM과 여러 방식으로 호출해 보면서 차이를 비교했다. 로컬 모델(Ollama), Gemini, OpenAI를 써 봤고, OpenAI로는 대화 기억, temperature, 이미지 분석·생성, 스트리밍, 임베딩, 프롬프트 기법까지 실습했다.

- 코드: [`exam1.ipynb`](exam1.ipynb) (강의 슬라이드 이미지는 빼고, 실행 결과를 보고 정리한 **📝 정리** 셀을 추가한 사본)
- 실행 환경: 강사님이 준 `requirements.txt`로 만든 가상환경(`eduvenv`, Python 3.12.10)
- API 키: 코드에 직접 쓰지 않고 환경변수(`OPENAI_API_KEY`, `GEMINI_API_KEY`)에서 읽는다.

## 1. Ollama: 내 컴퓨터에서 돌리는 무료 모델

Ollama는 LLM을 로컬(내 컴퓨터)에서 실행해 주는 오픈소스 도구다. 같은 모델을 세 가지 방법으로 호출했다.

| 방법 | 코드 | 특징 |
|---|---|---|
| REST API 직접 호출 | `requests.post("http://localhost:11434/api/generate", json={...})` | 라이브러리 없이 HTTP 요청만으로 호출 |
| OpenAI 호환 엔드포인트 | `OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")` | `openai` 코드를 그대로 쓰고 `base_url`만 바꿈. `api_key`는 형식상 아무 값 |
| `ollama` 라이브러리 | `ollama.chat(model=..., messages=[...], format='json')` | `format='json'`으로 JSON 출력 강제 가능 |

같은 프롬프트(영문·한글 Zero-shot, Few-shot, Chain of Thought)를 `llama3.1`과 `exaone3.5`에 보냈더니 둘 다 감정 분류와 사과 계산(5 − 2 + 4 − 1 = **6개**)을 맞혔다. 한국어 설명은 LG가 만든 `exaone3.5`가 더 자연스러웠다. 자기소개를 시켜 보면 차이가 더 컸다.

```txt
llama3.1  : 안녕하세요! 제가 뭘 해오고 있나요? 제가 하는 일은 자연어처리 AI를 포함한 기술을 연구 개발하고 있습니다.
exaone3.5 : 안녕하세요! 저는 LG AI Research에서 개발된 EXAONE 3.5입니다. 한국어 명령을 이해하고 실행하는 데 특화된 초거대 언어 모델로서, ...
```

`format='json'`과 함께 시스템 프롬프트로 스키마(`recipe_name`, `ingredients`, `steps`)를 알려 주니, 김치찌개 레시피를 그 키 그대로 JSON으로만 답했다.

## 2. Gemini: 두 가지 연동 방법

```python
# ① OpenAI 호환 엔드포인트 + openai 라이브러리
client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# ② 구글 공식 SDK (google-genai)
client = genai.Client()   # 환경변수의 키를 자동으로 읽음
response = client.models.generate_content(
    model='gemini-3.5-flash-lite',
    contents="Agentic AI 가 뭐야?",
    config=types.GenerateContentConfig(system_instruction="...", temperature=0.7, max_output_tokens=500),
)
```

①처럼 OpenAI 호환 엔드포인트를 쓰면 Ollama, Gemini, OpenAI를 같은 코드 모양으로 바꿔 가며 쓸 수 있다. ②를 실행하면 첫 줄에 `Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY.`라는 경고가 나온다. 환경변수에 두 키가 다 있어서 `GOOGLE_API_KEY`를 골랐다는 뜻이고, 키 값은 출력되지 않는다. 답변이 `**'자율`에서 끊긴 건 `max_output_tokens=500`에 걸렸기 때문이다.

## 3. OpenAI: chat.completions와 responses

OpenAI 라이브러리에는 텍스트를 생성하는 API가 두 가지 있다.

| | `client.chat.completions.create()` | `client.responses.create()` |
|---|---|---|
| 입력 | `messages=[{"role": "system", ...}, {"role": "user", ...}]` | `input="질문"` (문자열 또는 리스트), 시스템 지시는 `instructions=` |
| 출력 꺼내기 | `response.choices[0].message.content` | `response.output_text` |
| 길이 제한 | `max_tokens` | `max_output_tokens` |
| 대화 기억 | 내가 `messages`에 지난 대화를 계속 붙여서 보냄 | 서버가 기억하게 할 수 있음 (`previous_response_id`, `conversation`) |

### 3-1. 대화 기억

```python
# 따로 보내면 두 번째 요청은 첫 번째 요청을 모른다
response1 = client.responses.create(model="gpt-4o-mini", input="내 이름은 둘리야. 아기 공룡이야...")
response2 = client.responses.create(model="gpt-4o-mini", input="내 이름 뭐라고 했지?")

# previous_response_id로 이어 주면 기억한다 (예시: "내 이름은 유니코야. 직업은 IT 강사지" 다음에 질문)
response2 = client.responses.create(model="gpt-4o-mini", previous_response_id=response1.id, input="내 이름과 직업이 뭐라고 했지?")

# 대화방(conversation)을 만들어 같은 ID로 묶어도 기억한다
conv_id = client.conversations.create().id
client.responses.create(model="gpt-4o-mini", conversation=conv_id, input="...")
```

```txt
(따로 보냄)                  죄송하지만, 당신의 이름을 알지 못합니다. ...
(previous_response_id)       당신의 이름은 유니코이고, 직업은 IT 강사라고 하셨습니다. 맞나요?
(conversation)               김정현님이라고 하셨고, 좋아하는 음식은 떡볶이라고 하셨습니다!
```

`previous_response_id`는 직전 응답에 꼬리를 무는 방식이라 특정 시점에서 대화를 갈래로 나누기 좋고, `conversation`은 채팅방 하나를 계속 유지하는 방식이다. 둘 다 대화 기록을 내 코드가 아니라 **OpenAI 서버가 보관**한다.

### 3-2. temperature

같은 질문("우주를 한 문장으로 설명해줘")을 temperature만 바꿔서 보냈다.

```txt
0.0 : 우주는 모든 물질과 에너지가 존재하는 무한한 공간으로, 별, 행성, 은하, 그리고 다양한 천체들이 포함된 복잡한 구조입니다.
1   : 우주는 시간과 공간이 무한히 펼쳐진 곳으로, 수많은 별, 행성, 은하, 그리고 다양한 물질과 에너지가 존재하는 신비로운 세계입니다.
2.0 : 우주는 시간과 공간에 물질과 에너지가 배열된 본련에 유해과하며, 태양계와 격렬 홍 ┕ сх 충분шир lì fruits öldêtsiş ... (생략)
```

`2.0`에서는 확률이 낮은 토큰까지 마구 뽑혀서 여러 언어가 뒤섞인 의미 없는 글이 길게 나왔다. 정확한 답이 필요하면 낮게, 다양한 표현이 필요하면 조금 높게 쓴다.

### 3-3. 이미지 분석, 이미지 생성, 스트리밍

- **이미지 분석**: 이미지를 base64로 인코딩해 `{"type": "input_image", "image_url": "data:image/jpeg;base64,..."}`로 보낸다. 고양이·푸들·코기·고양이가 분홍 배경 앞에 앉은 사진을 왼쪽부터 순서대로 정확히 설명했다. (사진 파일은 출처를 몰라 저장소에 넣지 않았다)
- **이미지 생성**: `gpt-4o-mini`는 이미지를 이해할 수는 있지만 만들 수는 없어서, 이미지 생성 전용 모델 `gpt-image-2`를 `client.images.generate()`로 호출했다. 결과는 base64로 오고, 디코딩해서 파일로 저장한다.

  ![gpt-image-2로 생성한 이미지](output/spring_watercolor.png)

  프롬프트: "밝고 따스한 봄을 느낄 수 있는 수채화 같은 이미지"

- **스트리밍**: `stream=True`로 호출하고, 이벤트 중 `event.type == "response.output_text.delta"`인 것만 골라 `event.delta`를 출력하면 글자가 나오는 대로 찍힌다.

## 4. 임베딩

임베딩은 텍스트를 의미가 담긴 숫자 벡터로 바꾸는 것이다. `text-embedding-3-small`은 1,536차원 벡터를 만든다. 두 벡터가 얼마나 같은 방향인지 **코사인 유사도** `(A·B) / (‖A‖ × ‖B‖)`로 비교한다.

```txt
강아지 vs 강아지: 1.0000
강아지 vs 개: 0.2904
강아지 vs 애견: 0.2935
강아지 vs 고양이: 0.3361
강아지 vs 사과: 0.2071
강아지 vs 비행기: 0.2407
```

'강아지'와 가장 비슷할 것 같은 '개'·'애견'보다 '고양이'가 더 높게 나왔다. 단어 하나만 넣으면 문맥이 없어서 생기는 일이다. 특히 '개'는 '사과 5개'의 '개'처럼 뜻이 여러 개다. 임베딩 유사도는 문장 단위에서 더 잘 맞는다.

**단어 벡터 연산**도 해 봤다. `king − man + woman`과 가장 가까운 단어를 찾으면 `queen`(0.62)이 1위였다. 한국어 `왕 − 남자 + 여자`도 `여왕`(0.58)이 1위였지만, `자동차`(0.21)·`사과`(0.21)가 `황제`(0.20)·`공주`(0.19)보다 위에 올라왔다. 이 모델의 한국어 단어 임베딩은 영어보다 의미 구조가 덜 뚜렷했다.

## 5. 프롬프트 기법

| 기법 | 방법 | 결과 |
|---|---|---|
| 시스템 프롬프트 | `instructions="당신은 Python 시니어 개발자입니다. ..."` | 버그 → 성능 → 가독성 순서대로 코드 리뷰 |
| Few-shot | `input`에 user/assistant 예시 대화 3쌍을 넣고 마지막에 분류할 리뷰 | "색상은 사진과 달랐지만 품질은 좋았어요" → `긍정` |
| Chain of Thought + JSON | "단계적으로 생각한 후 JSON으로만 출력" + 스키마 제시 → `json.loads()` | 평균 1,340만원, 최대 4월, 최소 2월, 추세 상승 (계산 맞음) |

CoT 예제는 모델 출력 문자열을 `json.loads()`로 바로 파싱한다. 모델이 JSON 앞뒤에 설명을 붙이면 파싱이 실패하므로, 실제로는 구조화 출력 기능을 쓰는 게 안전하다.

## API 키 관리

- 모든 코드가 키를 코드에 쓰지 않고 환경변수에서 읽는다. (`OpenAI()`, `genai.Client()`는 인자가 없으면 환경변수를 자동으로 읽는다)
- 원래 자료에는 `print(os.environ.get("OPENAI_API_KEY"))`처럼 **키 전체를 출력하는 셀**이 두 개 있었다(실행 결과는 비어 있었음). 이 셀을 실행하고 저장하면 키가 노트북 출력에 남아 깃허브에 그대로 올라가므로, 저장소 사본에서는 설정 여부와 앞 7글자만 출력하도록 바꿨다.
- 코드에 보이는 `api_key="ollama"`는 Ollama용 형식상의 값이고, `#api_key="sk-...")`는 주석 처리된 예시라 실제 키가 아니다.

## 정리

| 대상 | 호출 방법 | 핵심 |
|---|---|---|
| Ollama | REST / OpenAI 호환(`base_url`) / `ollama` 라이브러리 | 로컬에서 무료로 실행. `exaone3.5`가 한국어에 강함 |
| Gemini | OpenAI 호환 / `google-genai` SDK | OpenAI 호환 엔드포인트로 같은 코드 모양 유지 |
| OpenAI 텍스트 | `chat.completions` / `responses` | `responses`는 `output_text`, `instructions`, 서버 측 대화 기억 |
| 대화 기억 | `previous_response_id` / `conversation` | 대화 기록을 서버가 보관 |
| 이미지 | `input_image`(분석), `images.generate`(생성) | 분석은 `gpt-4o-mini`, 생성은 `gpt-image-2` |
| 임베딩 | `embeddings.create` + 코사인 유사도 | 단어 하나보다 문장 단위에서 더 정확 |
| 프롬프트 | 시스템 / Few-shot / CoT | 역할·예시·단계를 주면 답의 형식과 품질이 안정된다 |

## 🔁 복습 질문

<details>
<summary>1. OpenAI 호환 엔드포인트를 쓰면 좋은 점은?</summary>

`OpenAI(base_url=..., api_key=...)`만 바꿔서 Ollama·Gemini 같은 다른 모델을 같은 코드로 호출할 수 있다.
</details>

<details>
<summary>2. <code>responses</code> API에서 이전 대화를 이어 가는 방법은?</summary>

`previous_response_id`에 앞 응답의 id를 넣거나 `conversation`을 써서, 대화 기록을 서버가 보관하게 한다.
</details>

<details>
<summary>3. Ollama 같은 로컬 모델의 장단점은?</summary>

무료이고 데이터가 밖으로 나가지 않지만, 내 컴퓨터 사양에 따라 느리고 큰 모델은 돌리기 어렵다.
</details>

<details>
<summary>4. Few-shot과 CoT 프롬프트는 각각 무엇인가?</summary>

Few-shot은 원하는 답의 예시를 몇 개 보여 주는 것, CoT는 단계별로 생각하며 풀게 하는 것이다 (→ [ex0916 퓨샷](../ex0916/퓨샷프롬프트.md)).
</details>
