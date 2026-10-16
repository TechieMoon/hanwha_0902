# FastAPI 기초

> **한눈에 보기**
> - FastAPI는 함수 위에 `@app.get("/주소")` 같은 데코레이터를 붙여 **주소(경로)와 함수를 연결**하는 웹 프레임워크다.
> - **경로 매개변수**: `/items/{item_id}`의 `{item_id}`가 함수의 `item_id` 인자로 들어간다.
> - **쿼리 매개변수**: 경로에 없는 함수 인자는 `?q=google&skip=1`처럼 주소 뒤에서 받는다. 기본값이 있으면 선택, 없으면 필수.
> - 타입 힌트(`int`, `bool`, `Enum`)대로 값을 변환·검사하고, 맞지 않으면 **422 오류**를 돌려준다.
> - 요청 본문(JSON)은 Pydantic 모델로 받는다 (→ [Pydantic](../ex0907/Pydantic.md)).
> - `http://127.0.0.1:8000/docs`에서 만든 API를 바로 눌러 보며 테스트할 수 있다.

| 코드 | 내용 |
|---|---|
| [main.py](main.py) | 첫 GET 예제 |
| [path_parameters.py](path_parameters.py) | Enum으로 경로 값 제한 |
| [query_parameters.py](query_parameters.py) | 쿼리 매개변수 (기본값, 선택, bool) |
| [get_put.py](get_put.py) | PUT + 요청 본문 |
| [request_body.py](request_body.py) | POST + 요청 본문 |

# FastAPI 설치

```cmd
pip install "fastapi[standard]"
```

# FastAPI 실행

main.py를 생성하고

```cmd
fastapi dev main.py
```

아니면

```cmd
uvicorn main:app --reload
```

를 실행하면 `http://127.0.0.1:8000` 주소에서 결과를 볼 수 있다.

- `main:app`은 "main.py 파일 안의 `app` 객체"라는 뜻이다. 파일 이름이 다르면 `uvicorn path_parameters:app --reload`처럼 바꾼다.
- `--reload`는 코드를 저장하면 서버를 자동으로 다시 띄워 준다 (개발할 때만 사용).

# Get

```python
from fastapi import FastAPI 

app = FastAPI()

@app.get("/")
def read_root():
    return{"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id:int, q:str | None=None):
    return {"item_id":item_id, "q": q}
```

`http://127.0.0.1:8000`에 접속하면 {"Hello": "World"} 반환

`http://127.0.0.1:8000/items/12`에 접속하면 {"item_id":12,"q":null} 반환

`http://127.0.0.1:8000/items/12?q=google`에 접속하면 {"item_id":12,"q":"google"} 반환

@app.get() 괄호 안의 중괄호에 값을 넣은 채로 주소를 만들어 접속하면 그 이름에 해당하는 변수에 값이 대입된다.

주소 마지막에 ?q=google를 붙이면 q라는 변수에 "google"을 대입한다.

> `item_id: int`로 선언했으므로 `/items/abc`처럼 숫자가 아닌 값을 넣으면 422 오류가 난다. 함수가 dict를 돌려주면 FastAPI가 JSON으로 바꿔 응답한다 (`None` → `null`).

# Get 실행 순서

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/users")
async def read_users():
    return ["Rick", "Morty"]


@app.get("/users")
async def read_users2():
    return ["Bean", "Elfo"]
```

항상 ["Rick","Morty"]을 반환한다. 주소가 같으면 맨 처음 함수만 실행된다.

> 같은 이유로 `/users/me`처럼 고정된 주소는 `/users/{user_id}`보다 **위에** 적어야 한다. 아래에 두면 `me`가 `user_id`로 먼저 잡힌다.

# 경로 매개변수 

```python
from enum import Enum

from fastapi import FastAPI


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


app = FastAPI()


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}
```

Enum으로 선택지를 강제로 제어할 수 있다.

ModelName 속성을 제외한 문자열이 전달되면 에러(422)를 발생시킨다. `/docs`에서도 세 값 중 하나를 고르는 목록으로 보인다.

# 쿼리 매개변수 

```python
from fastapi import FastAPI

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

`http://127.0.0.1:8000/items/` 결과는 [{"item_name":"Foo"},{"item_name":"Bar"},{"item_name":"Baz"}] 입니다.

skip과 limit에 값을 대입하지 않았으므로 fake_items_db[0:10]을 반환하기 때문입니다.

`http://127.0.0.1:8000/items/?skip=1&limit=2` 결과는 [{"item_name":"Bar"},{"item_name":"Baz"}] 입니다.

skip=1, limit=2이므로 fake_items_db[1:3]을 반환하기 때문입니다.

> skip/limit은 목록을 여러 페이지로 나눠 보여 줄 때(페이지네이션) 쓰는 대표적인 쿼리 매개변수다.

# 매개변수 선택

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None):
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
```

조건문을 넣어서 q가 존재하면 출력, 존재하지 않으면 출력하지 않음으로 매개변수를 선택할 수 있게 된다.

# 매개변수 타입

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item
```

조건문 `if not short`를 통해 `item.update`를 실행하게 된다. 전달 받을 값을 타입 상관없이 마음껏 추가할 수 있다.

short는 bool 타입이고, (1, True, true, on, yes와 같은 방법으로 값을 받을 수 있다.)

예: `http://127.0.0.1:8000/items/foo?short=1` 접속하면 {"item_id":"foo"} 반환

# 요청 본문 (POST, PUT)

GET은 주소로 값을 보내지만, POST·PUT은 **요청 본문(JSON)** 으로 데이터를 보낸다. 본문의 모양은 Pydantic 모델로 정한다.

```python
class Item(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):   # item_id는 경로에서, item은 본문(JSON)에서
    return {"item_name": item.name, "item_id": item_id}
```

FastAPI는 인자를 이렇게 나눠 받는다.

| 인자 | 어디서 받나 |
|---|---|
| 경로 `{...}`에 이름이 있는 인자 | 경로 매개변수 |
| `int`, `str`, `bool` 같은 단순 타입 | 쿼리 매개변수 |
| Pydantic 모델 타입 | 요청 본문(JSON) |

[request_body.py](request_body.py)의 `POST /items/`는 받은 `Item`을 그대로 돌려준다. 브라우저 주소창으로는 POST를 보낼 수 없으므로 `/docs`의 **Try it out**으로 테스트한다.

## 🔁 복습 질문

<details>
<summary>1. <code>uvicorn main:app --reload</code>에서 <code>main</code>, <code>app</code>, <code>--reload</code>는 각각 무엇인가?</summary>

`main`은 파일 이름(main.py), `app`은 그 안의 `FastAPI()` 객체 이름, `--reload`는 코드를 저장하면 서버를 자동으로 다시 시작하는 옵션이다.
</details>

<details>
<summary>2. <code>@app.get("/items/{item_id}")</code>와 <code>def read_item(item_id: int, q: str | None = None)</code>에서 <code>q</code>는 어떻게 전달하나?</summary>

경로에 없는 인자이므로 쿼리 매개변수다. `/items/12?q=google`처럼 주소 뒤에 `?이름=값`으로 붙인다. 기본값이 `None`이라 안 보내도 된다.
</details>

<details>
<summary>3. <code>/items/abc</code>에 접속하면? (item_id: int)</summary>

`abc`를 int로 바꿀 수 없으므로 422(Unprocessable Entity) 오류와 함께 어떤 값이 왜 틀렸는지 알려 준다.
</details>

<details>
<summary>4. 같은 주소에 함수 두 개를 등록하면?</summary>

먼저 등록된 함수만 실행된다. 그래서 `/users/me` 같은 고정 주소는 `/users/{user_id}`보다 먼저 적는다.
</details>

<details>
<summary>5. 경로 값을 정해진 몇 개로만 받으려면?</summary>

`class ModelName(str, Enum)`처럼 Enum을 만들어 타입 힌트로 쓴다. 목록에 없는 값이면 422 오류가 난다.
</details>

<details>
<summary>6. FastAPI는 인자가 경로·쿼리·본문 중 어디서 오는지 어떻게 구분하나?</summary>

경로에 이름이 있으면 경로 매개변수, 단순 타입이면 쿼리 매개변수, Pydantic 모델이면 요청 본문(JSON)이다.
</details>
