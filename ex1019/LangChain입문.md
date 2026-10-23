# LangChain 입문: 모델 호출, 메시지, 프롬프트 템플릿, LCEL 첫걸음

> **한눈에 보기**
> - LangChain은 모델이 아니라 **LLM 앱의 부품(모델·프롬프트·파서·도구)을 연결하는 프레임워크**
> - `ChatOpenAI`(OpenAI)와 `ChatOllama`(로컬 EXAONE)를 **같은 `invoke()`** 로 호출하고, 결과는 `AIMessage`(`.content`에 답)
> - `SystemMessage`(역할·규칙) / `HumanMessage`(사용자 질문) / `AIMessage`(모델 답)로 역할을 나눠 보낸다
> - `PromptTemplate`(문자열 하나)과 `ChatPromptTemplate`(역할별 메시지)으로 프롬프트를 재사용
> - `prompt | llm | StrOutputParser()` — 모델만 바꿔 끼워도 같은 체인을 재사용할 수 있다

- 코드: [`exam1.ipynb`](exam1.ipynb) (강사님 자료 `fwedu/exam1.ipynb` 사본, 강의 슬라이드 이미지 포함, 📝 정리 셀 추가)
- 실행 환경: langchain 1.4.6, langchain-core 1.6.12, langchain-openai 1.7.2, langchain-ollama 1.1.0
- 9월에 책으로 배운 내용([LangChain](../ex0914/랭체인.md), [프롬프트 템플릿](../ex0915/프롬프트템플릿.md))을 강사님 자료로 다시 정리한 날이다.

## 1. OpenAI SDK vs LangChain

```python
# OpenAI SDK 직접 호출 (10/12에 배운 방식)
client = OpenAI()
response = client.responses.create(model="gpt-4o-mini", input="LangChain이란 무엇인가요?")
print(response.output_text)

# LangChain
llm = ChatOpenAI(model="gpt-4o-mini")
aim = llm.invoke("LangChain이란 무엇인가요?")
print(aim.content)
```

SDK는 회사마다 호출 방법이 다르지만, LangChain은 모델이 달라도 `invoke()` / `stream()` / `batch()`로 똑같이 부른다. 프롬프트, 파서, 도구, 검색기를 같은 방식으로 이어 붙일 수 있는 것이 장점이다.

## 2. 같은 코드로 두 모델 부르기

```python
llm_openai = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
llm_exaone = ChatOllama(model="exaone3.5", temperature=0.7)   # 로컬 Ollama
```

모델 객체를 만들 때는 API를 호출하지 않는다. `invoke()`할 때 비로소 호출한다. "LangChain이 뭔지 한 문장으로" 질문에 두 모델 모두 비슷한 한 문장으로 답했다.

- 문자열을 `invoke()`에 넘기면 내부에서 `HumanMessage`로 감싸서 보낸다.
- `gpt-4o-mini` 같은 채팅 모델에는 `ChatOpenAI`를 쓴다. 문장을 이어 쓰던 옛 Completion용 `OpenAI` 클래스는 쓰지 않는다.

## 3. 메시지로 역할 나누기

```python
messages = [
    SystemMessage(content="너는 20년차 파이썬 강사야. 답변은 항상 한국어로, 예시 코드를 곁들여 설명해."),
    HumanMessage(content="리스트 컴프리헨션이 뭐야?"),
]
llm_openai.invoke(messages)
llm_exaone.invoke(messages)   # 같은 messages를 그대로 재사용
```

`SystemMessage`는 사용자에게 보이지 않는 지시문(역할·말투·제약), `HumanMessage`는 사용자 질문, `AIMessage`는 모델의 답이다.

## 4. 프롬프트 템플릿

| | `PromptTemplate` | `ChatPromptTemplate` |
|---|---|---|
| 다루는 것 | 문자열 하나 | system / human / ai 메시지 여러 개 |
| `invoke({...})` 결과 | `StringPromptValue` | `ChatPromptValue` (메시지 리스트) |
| 예 | `"다음 단어의 뜻을 초등학생도 이해할 수 있게 설명해줘: {word}"` | `("system", "너는 {role} 분야 전문가야"), ("human", "{question}")` |

템플릿은 모델과 무관해서, 같은 `word_template`을 GPT와 EXAONE에 그대로 넣어 "재귀함수" 설명을 받았다.

## 5. LCEL 첫걸음: 프롬프트 → 모델 → 문자열 파서

```python
recipe_chain = recipe_prompt | llm_openai | StrOutputParser()
answer = recipe_chain.invoke({"food": "비빔밥"})

local_recipe_chain = recipe_prompt | llm_exaone | StrOutputParser()   # 모델만 교체
```

- `prompt | llm`만 쓰면 결과가 `AIMessage`, 뒤에 `StrOutputParser()`를 붙이면 바로 문자열이다.
- 실행 결과 `type(answer)`가 `str`이 아니라 `TextAccessor`로 나왔다. 확인해 보니 `TextAccessor`는 **`str`을 상속한 클래스**라 문자열처럼 그대로 쓰면 된다 (langchain-core 1.x에서 `.text()` 메서드 방식과 `.text` 속성 방식을 둘 다 지원하려고 만든 타입).
- 단순한 체인은 LCEL로, 상태 관리와 반복이 필요한 흐름은 LangGraph로 만드는 것이 공식 가이드의 권장이다.

## 정리

| API | import | 역할 | 반환 |
|---|---|---|---|
| `ChatOpenAI` | `langchain_openai` | OpenAI 채팅 모델 | `invoke()` → `AIMessage` |
| `ChatOllama` | `langchain_ollama` | 로컬 Ollama 모델 | `invoke()` → `AIMessage` |
| `SystemMessage`, `HumanMessage` | `langchain_core.messages` | 역할이 있는 메시지 | |
| `PromptTemplate` | `langchain_core.prompts` | 문자열 템플릿 | `StringPromptValue` |
| `ChatPromptTemplate` | `langchain_core.prompts` | 역할별 메시지 템플릿 | `ChatPromptValue` |
| `StrOutputParser` | `langchain_core.output_parsers` | `AIMessage` → 문자열 | `str`(TextAccessor) |

## 🔁 복습 질문

<details>
<summary>1. LangChain을 쓰면 OpenAI SDK를 직접 쓸 때보다 무엇이 좋아지나?</summary>

모델 회사가 달라도 같은 `invoke()`로 부르고, 프롬프트·파서·도구를 같은 방식으로 연결할 수 있다. 모델만 바꿔 끼워 같은 체인을 재사용한다.
</details>

<details>
<summary>2. <code>llm.invoke("질문")</code>처럼 문자열만 넘기면 내부에서 어떻게 되나?</summary>

`HumanMessage`로 감싸서 보낸다. 결과는 `AIMessage`이고 답 글자는 `.content`에 있다.
</details>

<details>
<summary>3. <code>SystemMessage</code>에는 무엇을 넣나?</summary>

모델의 역할, 말투, 답변 규칙 같은 지시. 사용자 화면에는 보이지 않는다.
</details>

<details>
<summary>4. <code>PromptTemplate</code>과 <code>ChatPromptTemplate</code>의 차이는?</summary>

`PromptTemplate`은 문자열 하나를 채우고, `ChatPromptTemplate`은 system·human 등 역할이 있는 메시지 여러 개를 한 번에 채운다.
</details>

<details>
<summary>5. 체인 결과의 타입이 <code>TextAccessor</code>로 나왔는데 문자열로 써도 되나?</summary>

된다. `TextAccessor`는 `str`을 상속한 클래스라 문자열 메서드와 연산을 그대로 쓸 수 있다.
</details>
