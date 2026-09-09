# FastAPI 연습


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






