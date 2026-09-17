# 체인 직렬화(Serialization) 실습

LangChain의 프롬프트·모델·체인 객체를 **파일로 저장했다가 나중에 다시 불러와서 그대로 사용**하는 방법을 실습했다. 객체를 저장 가능한 형태(dict, JSON 문자열)로 바꾸는 것을 "직렬화(serialize)", 저장된 것을 다시 원래 객체로 복원하는 것을 "역직렬화(deserialize)"라고 부른다.

## 1. 직렬화 가능 여부 확인

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template("{fruit}의 색상이 무엇입니까?")

print(f"ChatOpenAI: {ChatOpenAI.is_lc_serializable()}")  # 클래스 자체에 대해 확인

llm = ChatOpenAI(model="gpt-5.6-luna", temperature=0)
print(f"ChatOpenAI: {llm.is_lc_serializable()}")  # 인스턴스에 대해 확인

chain = prompt | llm
chain.is_lc_serializable()  # 체인 전체에 대해 확인
```

`is_lc_serializable()`은 LangChain 객체가 직렬화를 지원하는지 알려주는 메서드다. 클래스, 인스턴스, 체인 전체 모두에 대해 호출할 수 있고, 체인은 구성 요소(prompt, llm)가 모두 직렬화 가능해야 전체도 `True`가 된다.

## 2. dumpd / dumps로 직렬화하기

```python
from langchain_core.load import dumpd, dumps

dumpd_chain = dumpd(chain)   # dict로 직렬화
type(dumpd_chain)            # dict

dumps_chain = dumps(chain)   # JSON 문자열로 직렬화
type(dumps_chain)            # str
```

- `dumpd()` : 체인을 파이썬 `dict`로 변환
- `dumps()` : 같은 내용을 JSON 문자열로 바로 변환

결과 dict를 들여다보면 `PromptTemplate`, `ChatOpenAI`의 설정값(템플릿 문자열, 모델명 등)이 그대로 들어있다. 중요한 점은 `openai_api_key` 값이 실제 키 문자열이 아니라 `{"lc": 1, "type": "secret", "id": ["OPENAI_API_KEY"]}`처럼 **"이 값은 OPENAI_API_KEY라는 환경변수에서 가져온 비밀값이다"라는 참조 정보만** 들어있다는 것이다. 덕분에 이 dict를 파일로 저장해도 API 키가 그대로 노출되지 않는다.

## 3. 파일로 저장하기

```python
import pickle
with open("fruit_chain.pkl", "wb") as f:
    pickle.dump(dumpd_chain, f)

import json
with open("fruit_chain.json", "w") as fp:
    json.dump(dumpd_chain, fp)
```

같은 dict를 `pickle`(바이너리, 파이썬 전용)과 `json`(텍스트, 범용) 두 형식으로 각각 저장해봤다. JSON은 사람이 읽을 수 있고 다른 언어/도구에서도 쉽게 읽을 수 있다는 장점이 있다.

## 4. 다시 불러와서 체인으로 복원하기

```python
with open("fruit_chain.pkl", "rb") as f:
    loaded_chain = pickle.load(f)  # 파일 -> dict

from langchain_core.load import load

chain_from_file = load(loaded_chain, allowed_objects="all")  # dict -> 실행 가능한 체인
print(chain_from_file.invoke({"fruit": "사과"}))
```

`load()`는 `dumpd()`의 반대 동작을 한다: dict를 다시 실제 LangChain 객체(`RunnableSequence` 체인)로 복원한다. `allowed_objects="all"`은 "신뢰할 수 있는 데이터이니 어떤 타입이든 복원해도 좋다"는 허용 옵션이다(신뢰할 수 없는 데이터를 역직렬화하면 임의 코드 실행 위험이 있을 수 있어서, LangChain이 기본적으로는 이를 제한한다).

`secrets_map`을 따로 넘기지 않아도 `load_dotenv()`로 환경변수에 올려둔 `OPENAI_API_KEY`를 LangChain이 알아서 참조해서 정상 동작한다. 필요하다면 아래처럼 명시적으로 지정할 수도 있다.

```python
load_chain = load(
    loaded_chain,
    secrets_map={"OPENAI_API_KEY": os.environ["OPENAI_API_KEY"]},
    allowed_objects="all",
)
print(load_chain.invoke({"fruit": "사과"}))
```

## 5. JSON 파일에서부터도 동일하게 복원

```python
with open("fruit_chain.json", "r") as fp:
    loaded_from_json_chain = json.load(fp)
    loads_chain = load(loaded_from_json_chain, allowed_objects="all")

print(loads_chain.invoke({"fruit": "사과"}))
```

pickle이든 JSON이든, `dumpd()`로 만든 dict를 저장해뒀다가 `load()`로 복원하면 원래와 동일하게 동작하는 체인을 다시 만들어낼 수 있다.

## 정리

| 함수 | 방향 | 결과 |
|---|---|---|
| `dumpd(chain)` | 직렬화 | `dict` |
| `dumps(chain)` | 직렬화 | JSON 문자열(`str`) |
| `load(dict, ...)` | 역직렬화 | 실행 가능한 체인 객체 |

API 키 같은 비밀값은 직렬화된 결과에 실제 값 대신 "참조"만 남기 때문에, 저장된 파일(pickle/JSON)을 다른 사람과 공유하거나 버전 관리에 올려도 키가 노출되지 않는다.
