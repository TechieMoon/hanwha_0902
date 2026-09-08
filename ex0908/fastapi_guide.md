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

Modelname 속성을 제외한 문자열이 전달되면 에러를 발생시킨다.

# 쿼리 매개변수 

```python
from fastapi import FastAPI

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

`http://127.0.0.1/items` 결과는 [{"item_name":"Foo"},{"item_name":"Bar"},{"item_name":"Baz"}] 입니다.

skip과 limit에 값을 대입하지 않았으므로 fake_items_db[0:10]을 반환하기 때문입니다.

`http://127.0.0.1:8000/items/?skip=1&limit=2` 결과는 [{"item_name":"Bar"},{"item_name":"Baz"}] 입니다.

skip=1, limit=2이므로 fake_items_db[1:3]을 반환하기 때문입니다.

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