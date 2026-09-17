# LLM 응답 캐싱(Caching) 실습

같은 질문을 여러 번 물어볼 때마다 매번 LLM API를 호출하면 시간도 오래 걸리고 비용도 반복해서 든다. LangChain의 **캐시(cache)** 기능을 쓰면, 한 번 물어본 질문(정확히는 같은 프롬프트)에 대한 답을 저장해뒀다가, 똑같은 질문이 다시 들어오면 API를 다시 호출하지 않고 저장된 답을 즉시 돌려준다. `%%time` 매직 명령으로 각 호출에 실제로 걸린 시간을 측정해가며 캐시 적용 전/후 속도 차이를 직접 확인했다.

## 1. 캐시 없이 호출

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

llm = ChatOpenAI(model="gpt-5.6-luna")
prompt = PromptTemplate.from_template("{country}에 대해서 200자 내외로 요약해줘")
chain = prompt | llm

%%time
response = chain.invoke({"country": "한국"})
print(response.content)
```

캐시가 없으니 실제로 API를 호출한다. (Wall time 약 2.93초)

## 2. InMemoryCache: 메모리에 저장되는 캐시

```python
from langchain_core.globals import set_llm_cache
from langchain_core.caches import InMemoryCache

set_llm_cache(InMemoryCache())

response = chain.invoke({"country": "한국"})  # 캐시가 막 켜진 직후라 아직 저장된 답이 없음 -> API 호출
```

캐시를 켜는 시점부터 새로 캐시가 시작되므로, 켠 직후의 첫 호출은 여전히 API를 호출한다(약 3.23초). 하지만 이 호출 결과부터는 캐시에 저장된다.

```python
response = chain.invoke({"country": "한국"})  # 완전히 같은 입력 -> 캐시 적중
```

바로 같은 입력으로 다시 호출하면 캐시에서 즉시 꺼내온다. Wall time이 **3.22 밀리초**로, 앞의 3.23**초**보다 1000배 가까이 빨라진다. 답변 내용도 이전 캐시된 답과 완전히 동일하다.

`InMemoryCache`는 프로그램(커널)을 껐다 켜면 사라진다는 한계가 있다.

## 3. SQLiteCache: 디스크에 영구 저장되는 캐시

```python
import os
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache

if not os.path.exists("cache"):
    os.makedirs("cache")

set_llm_cache(SQLiteCache(database_path="cache/llm_cache.db"))
```

지정한 파일(`cache/llm_cache.db`)에 캐시를 저장해서, 노트북을 재시작해도 캐시가 그대로 남아있다. (`langchain_community`의 `SQLiteCache`를 쓰면 "sunset(지원 종료 예정)" 경고가 뜨는데, `langchain-community` 패키지 자체가 점차 별도 통합 패키지들로 옮겨가고 있어서 나오는 경고이고 기능은 정상 동작한다.)

`InMemoryCache`와는 별개의 새 캐시 저장소이므로, 여기서도 첫 호출은 캐시 미스라 API를 호출한다(약 2.86초). 완전히 같은 질문을 다시 호출하면 이번엔 SQLite 파일에서 바로 읽어와서 다시 밀리초 단위(6.11ms)로 빨라진다.

## 정리

| 캐시 종류 | 저장 위치 | 특징 |
|---|---|---|
| `InMemoryCache` | 프로세스 메모리 | 빠르지만 프로그램(커널)을 재시작하면 사라짐 |
| `SQLiteCache` | 지정한 파일(`.db`) | 노트북을 재시작해도 캐시가 유지됨 |

두 캐시 모두 "완전히 같은 입력으로 다시 호출하면 API 재호출 없이 저장된 답을 즉시 반환한다"는 동작 원리는 같고, 저장 위치(메모리 vs 파일)만 다르다.
