# LCEL과 Runnable: 체인 연결, 병렬, 분기, 라우팅, 그리고 환각

> **한눈에 보기**
> - **LCEL**: `A | B | C`처럼 LangChain 부품을 파이프로 잇는 문법. 앞 단계의 출력이 다음 단계의 입력이 된다
> - 모든 부품은 **Runnable** → 공통 실행 메서드 `invoke`(하나) / `batch`(여러 개) / `stream`(조각씩)
> - 일반 함수는 `RunnableLambda`, 동시에 여러 값 만들기는 `RunnableParallel`(dict), 입력 유지 + 키 추가는 `RunnablePassthrough.assign`, 조건 분기는 `RunnableBranch`
> - 체인을 만들 때 제일 많이 틀리는 것은 문법이 아니라 **단계 사이 입력·출력의 모양**(dict? 문자열?)
> - 이날 가장 큰 교훈: **모델이 모르는 최신 용어("LCEL")는 그럴듯하게 지어낸다.** 같은 질문도 context를 넣은 RAG 체인은 맞게 답했다

- 코드: [`exam2.ipynb`](exam2.ipynb) (강사님 자료 `fwedu/exam2.ipynb` 사본, 슬라이드 이미지는 자리만 표시, 📝 정리 셀 추가)
- 9월에 책으로 배운 [RunnablePassthrough](../ex0929/RunnablePassthrough.md)와 [RAG 기본 파이프라인](../ex0929/RAG기본파이프라인.md)을 다시 다뤘다.

## 1. Runnable과 LCEL (LLM 없이)

```python
strip_text = RunnableLambda(lambda x: x.strip())
to_lower   = RunnableLambda(lambda x: x.lower())
add_prefix = RunnableLambda(lambda x: f"정리된 입력: {x}")
chain = strip_text | to_lower | add_prefix      # RunnableSequence

chain.invoke("   HELLO LCEL     ")        # '정리된 입력: hello lcel'
chain.batch(["   HELLO   ", "   LCEL   "])  # 결과 리스트
for chunk in chain.stream("   STREAM TEST"): ...   # 문자열 처리라 한 번에 나옴
```

## 2. 단계별 입력·출력 모양

| 단계 | 입력 | 출력 |
|---|---|---|
| `ChatPromptTemplate` | `dict` | `ChatPromptValue` |
| `ChatOpenAI` / `ChatOllama` | `PromptValue` 또는 메시지 | `AIMessage` |
| `StrOutputParser` | `AIMessage` | 문자열 |
| `JsonOutputParser` | `AIMessage` | `dict` (Pydantic 객체가 아님) |
| `RunnableParallel` / dict | 입력 하나 | 키별 결과를 모은 `dict` |

- `JsonOutputParser`의 결과(dict)를 문자열 함수에 바로 넘기면 타입 오류가 난다. 후처리가 문자열을 받아야 하면 `StrOutputParser()` 뒤에 `RunnableLambda(clean_output)`를 붙인다.
- 프롬프트가 `{name}`을 기대하면 입력은 `{"name": "둘리"}`여야 한다. 체인을 만들 때마다 앞뒤 단계의 모양이 맞는지 확인한다.

## 3. 병렬과 입력 유지

```python
RunnableParallel({
    "original": RunnablePassthrough(),               # 입력 그대로
    "upper":    RunnableLambda(lambda x: x.upper()),
    "length":   RunnableLambda(lambda x: len(x)),
}).invoke("  hello lcel  ")
# {'original': '  hello lcel  ', 'upper': '  HELLO LCEL  ', 'length': 14}

RunnablePassthrough.assign(
    length=lambda x: len(x["text"]),
    preview=lambda x: x["text"][:10] + "...",
).invoke({"text": "LangChain LCEL은 체인을 조립하기 쉽게 해준다."})
# {'text': ..., 'length': 32, 'preview': 'LangChain ...'}  (원래 키 유지 + 새 키)
```

## 4. Fake Retriever로 RAG 구조 보기

벡터 DB 없이 키워드로 문서 4개 중 일부를 고르는 `fake_retriever`로 RAG의 뼈대만 만들었다.

```python
rag_input_chain = RunnableParallel({
    "context": RunnableLambda(fake_retriever) | RunnableLambda(augmanted_docs),
    "question": RunnablePassthrough(),
})
rag_chain = rag_input_chain | rag_prompt | model | StrOutputParser()
```

질문 하나를 넣으면 `{"context": 검색된 문서들, "question": 원래 질문}`이 만들어져 프롬프트로 들어간다. 실제 RAG에는 문서 수집·청킹·임베딩·벡터 DB·검색 평가가 더 필요하다 (→ [10/15 RAG](../ex1015/RAG.md)).

## 5. 실행 결과에서 본 환각: "LCEL"을 모르는 모델

| 체인 | 모델이 말한 LCEL | 판정 |
|---|---|---|
| 기본 체인 (gpt-4o-mini) | "Language Chain Execution Language의 약자" | ❌ 지어냄 |
| 후처리 체인 (gpt-4o-mini) | "Low-Carbon Energy Laboratory", 탄소 포집 기술 | ❌ 엉뚱한 분야 |
| 스트리밍 체인 (gpt-4o-mini) | "Low-Cost Energy Loss" | ❌ |
| batch (gpt-4o-mini) | "Learning Content Exchange Language" | ❌ |
| EXAONE 3.5 | "대화형 AI 모델의 실제 성능을 측정하는 방법" | ❌ |
| Llama 3.1 | "LangChain의 Core Library", 같은 문장 반복 | ❌ |
| **RAG 체인** (context 제공) | "LangChain 컴포넌트를 파이프처럼 연결하는 문법" | ✅ |

- LCEL은 **LangChain Expression Language**다. 모델이 학습하지 않았거나 드문 용어는 **실행할 때마다 다른 답을 그럴듯하게 지어낸다.**
- 같은 batch에서 "Runnable"은 **자바의 Runnable 인터페이스**로 답했다. 맥락 없이 단어만 주면 더 흔한 뜻으로 답한다.
- 문서를 context로 넣어 준 RAG 체인만 정확히 답했다. **모델이 모를 수 있는 내용은 근거를 넣어 주고, 근거 안에서만 답하게** 해야 한다.

## 6. 분기와 라우팅

```python
router_chain = RunnableBranch(
    (lambda x: "코드" in x["question"] or "파이썬" in x["question"], code_chain),
    (lambda x: "쿠버네티스" in x["question"] or "클라우드" in x["question"], cloud_chain),
    general_chain,                        # 마지막 인자 = else
)
```

- `RunnableBranch`: 조건을 위에서부터 검사해 처음 맞는 체인을 실행한다(if-elif-else).
- 동적 라우팅: `RunnableLambda`가 **체인 자체를 반환**하면 LangChain이 그 체인을 이어서 실행한다. 질문에 "ollama"가 있으면 EXAONE 체인, 아니면 GPT 체인을 고르게 했다.
- 키워드 라우팅은 의미를 이해하지 못한다. "ollama로 실행 중인 exaone3.5 모델의 특징"을 EXAONE에게 보냈더니 **자기 자신에 대한 정보도 모른다**고 답했다.

## 7. stream과 batch

- `stream()`: 조각마다 `@`를 붙여 출력해 보니 토큰 단위로 나뉘어 왔다(`LC@EL@(stream@)@은@...`). 채팅 화면에 바로바로 보여 줄 때 쓴다. 단, 모든 Runnable이 토큰 단위로 흘려보내는 것은 아니다.
- `batch()`: 입력 여러 개를 한 번에 처리해 리스트로 돌려준다. 반복문보다 간결하고 내부에서 병렬로 처리한다.

## 정리

| 패턴 | 코드 |
|---|---|
| 기본 LLM 체인 | `prompt \| model \| parser` |
| 전처리 후 호출 | `preprocess \| prompt \| model \| parser` |
| RAG | `{"context": retriever \| format_docs, "question": RunnablePassthrough()} \| prompt \| model \| parser` |
| 입력에 값 추가 | `RunnablePassthrough.assign(key=함수)` |
| 조건 분기 | `RunnableBranch((조건, 체인), ..., 기본체인)` |
| 동적 선택 | `RunnableLambda(체인을 반환하는 함수)` |

## 🔁 복습 질문

<details>
<summary>1. <code>chain = A | B | C</code>에서 데이터는 어떻게 흐르나?</summary>

입력이 A로 들어가고, A의 출력이 B의 입력, B의 출력이 C의 입력이 된다. C의 출력이 체인의 결과다.
</details>

<details>
<summary>2. <code>invoke</code>, <code>batch</code>, <code>stream</code>은 각각 언제 쓰나?</summary>

입력 하나는 `invoke`, 여러 입력을 한 번에는 `batch`, 답을 조각씩 바로 보여 줄 때는 `stream`.
</details>

<details>
<summary>3. <code>JsonOutputParser</code> 결과를 문자열 후처리 함수에 넣으면 왜 오류가 나나?</summary>

`JsonOutputParser`는 dict를 돌려주기 때문이다. 문자열이 필요하면 `StrOutputParser()` 뒤에 후처리를 붙인다.
</details>

<details>
<summary>4. <code>RunnablePassthrough()</code>와 <code>RunnablePassthrough.assign()</code>의 차이는?</summary>

`RunnablePassthrough()`는 입력을 그대로 넘기고, `.assign()`은 입력 dict를 유지한 채 새 키를 추가한다.
</details>

<details>
<summary>5. GPT가 "LCEL"을 매번 다른 뜻으로 설명한 이유와, RAG 체인은 맞게 답한 이유는?</summary>

모델이 모르는 최신·드문 용어라 그럴듯한 약자를 지어냈다(환각). RAG 체인은 정확한 설명이 담긴 문서를 context로 넣어 주고 그 안에서만 답하게 했기 때문이다.
</details>

<details>
<summary>6. <code>RunnableBranch</code>의 마지막 인자는 무엇인가?</summary>

어떤 조건에도 맞지 않을 때 실행할 기본 체인(else).
</details>

<details>
<summary>7. <code>RunnableLambda</code> 함수가 문자열이 아니라 체인을 반환하면 어떻게 되나?</summary>

LangChain이 반환된 체인(Runnable)을 같은 입력으로 이어서 실행한다. 입력에 따라 다른 모델·체인을 고르는 동적 라우팅에 쓴다.
</details>
