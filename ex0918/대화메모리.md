# 대화 메모리(Conversation Memory) 실습

LLM은 기본적으로 호출할 때마다 "이전에 무슨 대화를 했는지"를 기억하지 못한다. 그래서 채팅 기록을 직접 저장해뒀다가, 다음 호출을 할 때 그 기록을 프롬프트에 함께 넣어줘야 "이전 대화를 기억하는 것처럼" 동작하게 만들 수 있다. 대화 기록을 저장하는 방법부터, 체인에 자동으로 연결해서 대화가 이어지도록 만드는 방법까지 실습했다.

> [teddynote 교재의 ConversationBufferMemory 예제](https://github.com/teddylee777/langchain-kr/blob/main/05-Memory/01-ConversationBufferMemory.ipynb)는 `ConversationBufferMemory`, `ConversationChain`을 쓰는데, 이 두 클래스는 현재 LangChain 문서에서 deprecated(사용 중단)로 표시되어 있다. 여기서는 같은 개념을 현재 권장되는 `InMemoryChatMessageHistory` + `RunnableWithMessageHistory` 조합으로 실습했다.

## 1. 대화 기록 객체 만들기

```python
from langchain_core.chat_history import InMemoryChatMessageHistory

history = InMemoryChatMessageHistory()
```

`InMemoryChatMessageHistory`는 대화 메시지들을 순서대로 저장해두는 가장 기본적인 대화 기록 저장소다. 메모리(프로세스가 실행되는 동안)에만 저장되고, 프로그램을 재시작하면 사라진다.

## 2. 대화 저장하기 & 조회하기

```python
history.add_user_message("안녕하세요, 은행에서 계좌를 개설하고 싶습니다.")
history.add_ai_message(
    "안녕하세요! 계좌 개설을 도와드리겠습니다. 먼저 신분증을 준비해 주시겠어요?"
)

for message in history.messages:
    print(f"[{message.type}] {message.content}")
```

`add_user_message()` / `add_ai_message()`로 사용자 발화와 AI 응답을 순서대로 저장한다. `history.messages`는 저장된 메시지들을 `HumanMessage`, `AIMessage` 객체 리스트로 반환한다.

여러 턴을 이어서 저장하면 대화가 계속 쌓인다:

```python
history.add_user_message("신분증 사진을 업로드했습니다.")
history.add_ai_message("확인했습니다. 본인 인증을 위해 휴대폰 인증을 진행해 주세요.")

history.add_user_message("휴대폰 인증을 완료했습니다.")
history.add_ai_message("인증이 완료되었습니다. 이제 계좌 종류를 선택해 주세요.")
```

## 3. 체인에 자동으로 연결하기: RunnableWithMessageHistory

매번 메시지를 수동으로 저장/조회하는 대신, 체인 자체가 "호출할 때마다 자동으로 기록을 읽고 새 대화를 저장"하도록 만들 수 있다. `RunnableWithMessageHistory`가 그 역할을 한다.

먼저 대화 기록을 프롬프트에 끼워 넣을 수 있는 `ChatPromptTemplate`을 만든다. `MessagesPlaceholder("history")` 자리에 이전 대화 기록이 통째로 삽입된다.

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-5.6-luna")

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "당신은 친절한 은행 상담원입니다."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)

chain = prompt | llm
```

## 4. 세션(대화)별 기록 저장소 준비하기

한 프로그램 안에서 여러 사용자가 동시에 대화할 수도 있으므로, `session_id`별로 서로 다른 대화 기록을 관리해야 한다.

```python
store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]
```

`session_id`를 넣으면 해당 세션의 `InMemoryChatMessageHistory`를 반환하는(없으면 새로 만드는) 함수다.

## 5. RunnableWithMessageHistory로 감싸기

```python
from langchain_core.runnables.history import RunnableWithMessageHistory

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)
```

- `input_messages_key="input"` : 사용자 입력이 담긴 변수 이름
- `history_messages_key="history"` : 대화 기록이 채워질 `MessagesPlaceholder`의 변수 이름

이렇게 감싸면, 호출할 때마다 `get_session_history`로 해당 세션의 기록을 자동으로 불러와 `history` 자리에 채워주고, 호출이 끝나면 이번 대화(사용자 입력 + AI 응답)를 그 기록에 자동으로 저장해준다.

## 6. 대화 진행 및 기억 확인

```python
config = {"configurable": {"session_id": "moon"}}

response = chain_with_history.invoke(
    {"input": "안녕하세요, 저는 문선웅입니다. 계좌를 개설하고 싶어요."},
    config=config,
)
print(response.content)

# 같은 session_id로 다시 호출 -> 방금 나눈 대화를 기억하고 있어야 한다.
response2 = chain_with_history.invoke(
    {"input": "제 이름이 뭐라고 했는지 기억하시나요?"},
    config=config,
)
print(response2.content)
```

`config`에 `session_id`를 지정해서 호출한다. 같은 `session_id`로 다시 호출하면, 방금 나눈 대화가 `history`에 자동으로 반영되어 있어서 이름을 다시 알려주지 않아도 기억한다.

다른 `session_id`("guest")로 같은 질문을 하면, `"moon"` 세션과는 완전히 별개의 대화 기록이라 이름을 모른다고 답한다:

```python
response3 = chain_with_history.invoke(
    {"input": "제 이름이 뭐라고 했는지 기억하시나요?"},
    config={"configurable": {"session_id": "guest"}},
)
print(response3.content)
```

## 정리

- `InMemoryChatMessageHistory` : 대화 메시지를 순서대로 저장하는 기본 저장소 (`add_user_message`/`add_ai_message`로 저장, `.messages`로 조회)
- `RunnableWithMessageHistory` : 체인을 감싸서, 호출할 때마다 `session_id`에 해당하는 대화 기록을 자동으로 읽고 저장해준다
- `session_id`를 다르게 주면 완전히 독립된 대화로 관리된다

이 세 가지를 조합하면, 매번 직접 기록을 챙기지 않아도 "이전 대화를 기억하는" 챗봇 체인을 만들 수 있다.
