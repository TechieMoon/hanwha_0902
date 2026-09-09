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

#####################
# 결과
#####################

# 127.0.0.1:8000
# {"message":"안녕~"}

# 127.0.0.1:8000/hello/John
# {"message":"John님, 안녕하세요!"}

# 127.0.0.1:8000/add?a=3&b=5
# {"result":8}

# 127.0.0.1:8000/greet?name=철수&count=5
# {"message":["철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!","철수님, 안녕하세요!"]}

###############
# POST 연습
###############

from pydantic import BaseModel 

# 요청으로 받을 데이터 구조
class User(BaseModel):
    name: str 
    age: int 


@app.post("/users")
async def create_user(user: User):
    return {
        "message": f"{user.name}님이 등록되었습니다!",
        "user": user.model_dump()
    }


#############
# DELETE 연습
#############

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

############
# PUT 요청
############

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