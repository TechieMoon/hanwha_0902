# FastAPI GET 연습

## GET 요청

```python
@app.get("/")
async def read_root():
    return {"message":"안녕~"}
```

`127.0.0.1:8000` 접속
{"message":"안녕~"} 반환

## GET으로 변수 대입

```python
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"{name}님, 안녕하세요!"}
```

`127.0.0.1:8000/hello/John` 접속
{"message":"John님, 안녕하세요!"} 반환


## GET으로 덧셈 요청

```python
@app.get("/add")
async def add(a: int, b: int):
    return {"result": a + b}
```

`127.0.0.1:8000/add?a=3&b=5` 접속
{"result":8} 반환

## GET으로 원하는 횟수만큼 반복하기

```python
@app.get("/greet")
async def greet(name: str, count: int = 1):
    return {"message": [f"{name}님, 안녕하세요!"] * count}
```

`127.0.0.1:8000/greet?name=철수&count=5` 접속
{"message":["철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!"]} 반환

## POST 추가

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

## DELETE 삭제

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


## PUT 수정

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

## GET, POST, DELETE, PUT 요약

1. GET은 정보를 요청
2. POST는 정보를 추가
3. DELETE는 정보를 삭제
4. PUT은 정보를 수정