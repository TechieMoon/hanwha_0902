# FastAPI GET·POST·PUT·DELETE 연습

> **한눈에 보기**
> - HTTP 메서드 4가지로 데이터를 다루는 연습: **GET 조회, POST 추가, PUT 수정, DELETE 삭제** (합쳐서 CRUD)
> - GET은 경로·쿼리 매개변수로, POST·PUT은 요청 본문(JSON, Pydantic 모델)으로 값을 받는다.
> - 없는 데이터를 요청하면 `raise HTTPException(status_code=404, detail=...)`로 오류 응답을 보낸다.
> - 연습용 데이터는 파이썬 dict에 저장하므로 **서버를 다시 켜면 처음 상태로 돌아간다**.
> - 코드: [ex0909/main.py](main.py) (연습), [ex0909_2/main.py](../ex0909_2/main.py) (상품 CRUD 최종 정리, 6절)

## 1. GET 요청

```python
@app.get("/")
async def read_root():
    return {"message":"안녕~"}
```

`127.0.0.1:8000` 접속
{"message":"안녕~"} 반환

- GET으로 변수 대입

```python
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"{name}님, 안녕하세요!"}
```

`127.0.0.1:8000/hello/John` 접속
{"message":"John님, 안녕하세요!"} 반환


- GET으로 덧셈 요청

```python
@app.get("/add")
async def add(a: int, b: int):
    return {"result": a + b}
```

`127.0.0.1:8000/add?a=3&b=5` 접속
{"result":8} 반환

- GET으로 원하는 횟수만큼 반복하기

```python
@app.get("/greet")
async def greet(name: str, count: int = 1):
    return {"message": [f"{name}님, 안녕하세요!"] * count}
```

`127.0.0.1:8000/greet?name=철수&count=5` 접속
{"message":["철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!"]} 반환

## 2. POST 추가

```python
from pydantic import BaseModel


# 요청으로 받을 데이터의 구조
class User(BaseModel):
    name: str
    age: int


@app.post("/users")
async def create_user(user: User):
    return {
        "message": f"{user.name}님이 등록되었습니다!",
        "user": user.model_dump()
    }
```

Request body

```request body
{
  "name": "영희",
  "age": 27
}
```

Response body

```response body
{
  "message": "영희님이 등록되었습니다!",
  "user": {
    "name": "영희",
    "age": 27
  }
}
```

## 3. DELETE 삭제

```python
from fastapi import HTTPException

# 연습용 데이터: 사용자 ID가 key
users = {
    1: {"name": "철수", "age": 25},
    2: {"name": "영희", "age": 27}
}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    if user_id not in users:
        raise HTTPException(
            status_code=404,
            detail="해당 사용자가 없습니다."
        )

    deleted_user = users.pop(user_id)

    return {
        "message": "사용자가 삭제되었습니다.",
        "user": deleted_user
    }
```

/docs에서 테스트 
user_id에 1을 입력하고 테스트

```response body
{
  "message": "사용자가 삭제되었습니다.",
  "user": {
    "name": "철수",
    "age": 25
  }
}
```

한 번 더 하면 이미 1번 유저는 삭제되었기 때문에 404 오류가 발생

```response body
{
  "detail": "해당 사용자가 없습니다."
}
```


## 4. PUT 수정

```python
@app.put("/users/{user_id}")
async def update_user(user_id: int, user: User):
    if user_id not in users:
        raise HTTPException(
            status_code=404,
            detail="해당 사용자가 없습니다."
        )

    users[user_id] = user.model_dump()

    return {
        "message": "사용자 정보가 수정되었습니다.",
        "user": users[user_id]
    }
```

1. `http://127.0.0.1:8000/docs`에서 테스트
2. PUT /users/{user_id}에서 user_id에 2를 입력한다.
3. Request body에 다음과 같이 입력한다.

```request body
{
  "name": "카리나",
  "age": 26
}
```

4. 다음과 같이 반환된다.

```response body
{
  "message": "사용자 정보가 수정되었습니다.",
  "user": {
    "name": "카리나",
    "age": 26
  }
}
```

## 5. GET, POST, DELETE, PUT 요약

1. GET은 정보를 요청
2. POST는 정보를 추가
3. DELETE는 정보를 삭제
4. PUT은 정보를 수정

| 메서드 | 하는 일 | 값을 받는 곳 | 이 문서의 예 |
|---|---|---|---|
| GET | 조회 | 경로, 쿼리 | `/hello/{name}`, `/add?a=3&b=5` |
| POST | 추가 | 요청 본문(JSON) | `/users` |
| PUT | 수정(통째로 바꾸기) | 경로 + 요청 본문 | `/users/{user_id}` |
| DELETE | 삭제 | 경로 | `/users/{user_id}` |

## 6. 상품 CRUD 정리 ([ex0909_2/main.py](../ex0909_2/main.py))

같은 날 오후에 4가지 메서드를 상품(item) 하나로 묶어 다시 만들었다.

| 기능 | 요청 | 성공 응답 |
|---|---|---|
| 생성 | `POST /items/` + 본문 `{"name": ..., "price": ..., "desc": ...}` | 201, **전체** `items_db` |
| 전체 조회 | `GET /items/` | `{"msg": "전체 목록 조회 완료", "data": [...]}` |
| 단일 조회 | `GET /items/{item_id}` | `{"message": "단일 조회 완료", "data": {...}}` |
| 수정 | `PUT /items/{item_id}` + 본문 | `{"message": "수정 완료", "data": {...}}` |
| 삭제 | `DELETE /items/{item_id}` | `{"message": "삭제 완료", "data": {...}}` |

없는 `item_id`면 조회·수정·삭제 모두 404 `"제품을 찾을 수 없습니다."`를 돌려준다.

포인트

- `@app.post("/items/", status_code=201)`: 새로 만들었다는 뜻의 **201 Created**로 응답한다 (기본값은 200).
- `id_counter`로 번호를 하나씩 늘려 id를 붙인다. 함수 안에서 바깥 변수를 바꾸므로 `global id_counter`가 필요하다.
- `item.model_dump()`로 Pydantic 모델을 dict로 바꾼 뒤 `id`를 추가해 저장한다.
- 다시 볼 점: 생성 API만 새 항목이 아니라 **전체 `items_db`** 를 돌려주고, 전체 조회만 키 이름이 `message`가 아니라 `msg`다. 실제 서비스라면 응답 모양을 하나로 맞추는 게 좋다 (코드는 수업 그대로 두고 주석으로 표시).
- 생성 응답을 보면 `{"1": {...}}`처럼 id 키가 문자열 `"1"`로 바뀌어 있다. JSON 객체의 키는 항상 문자열이기 때문이다 (TestClient로 확인).

## 🔁 복습 질문

<details>
<summary>1. GET, POST, PUT, DELETE는 각각 어떤 일을 하나?</summary>

조회, 추가, 수정, 삭제. 데이터를 다루는 기본 4가지라 CRUD(Create, Read, Update, Delete)라고 부른다.
</details>

<details>
<summary>2. <code>/greet?name=철수&count=5</code>에서 count를 안 보내면?</summary>

`count: int = 1`로 기본값이 있으므로 1번만 인사한다. 기본값이 없는 `name`을 빼면 422 오류가 난다.
</details>

<details>
<summary>3. 없는 사용자를 삭제하려 하면 어떻게 응답하나? 그 코드는?</summary>

`raise HTTPException(status_code=404, detail="해당 사용자가 없습니다.")`로 404와 `{"detail": "해당 사용자가 없습니다."}`를 돌려준다.
</details>

<details>
<summary>4. DELETE로 1번 사용자를 지운 뒤 서버를 다시 켜면 1번은 어떻게 되나?</summary>

다시 생긴다. 데이터를 파일이나 DB가 아니라 파이썬 dict(메모리)에 두었기 때문이다.
</details>

<details>
<summary>5. 상품 생성 API에서 <code>global id_counter</code>가 필요한 이유는?</summary>

함수 안에서 `id_counter += 1`로 바깥(전역) 변수에 새 값을 넣기 때문이다. `global`이 없으면 파이썬은 지역 변수로 보고 `UnboundLocalError`를 낸다.
</details>

<details>
<summary>6. POST 성공 응답을 200이 아니라 201로 바꾸려면?</summary>

데코레이터에 `status_code=201`을 넣는다: `@app.post("/items/", status_code=201)`.
</details>