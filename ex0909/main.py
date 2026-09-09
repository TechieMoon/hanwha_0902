from fastapi import FastAPI

app = FastAPI()

######################
# 다양한 GET 연습
######################

@app.get("/")
async def read_root():
    return {"message":"안녕~"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"{name}님, 안녕하세요!"}

@app.get("/add")
async def add(a: int, b: int):
    return {"result": a + b}

@app.get("/greet")
async def greet(name: str, count: int = 1):
    return {"message": [f"{name}님, 안녕하세요!"] * count}

# 127.0.0.1:8000
# {"message":"안녕~"}

# 127.0.0.1:8000/hello/John
# {"message":"John님, 안녕하세요!"}

# 127.0.0.1:8000/add?a=3&b=5
# {"result":8}

# 127.0.0.1:8000/greet?name=철수&count=5
# {"message":["철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!"]}

###############
# PUT 연습
###############