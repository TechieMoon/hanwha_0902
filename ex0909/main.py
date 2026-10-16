# FastAPI GET·POST·DELETE·PUT 연습
# 실행: fastapi dev main.py  -> http://127.0.0.1:8000/docs 에서 테스트
from fastapi import FastAPI

app = FastAPI()

######################
# 다양한 GET 연습
######################

# 가장 단순한 GET: 고정된 메시지
@app.get("/")
async def read_root():
    return {"message":"안녕~"}

# 경로 매개변수: /hello/John -> name="John"
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"{name}님, 안녕하세요!"}

# 쿼리 매개변수 2개(기본값 없음 -> 둘 다 필수): /add?a=3&b=5
@app.get("/add")
async def add(a: int, b: int):
    return {"result": a + b}

# 기본값 있는 쿼리 매개변수: count를 안 보내면 1
# 리스트 * 숫자 -> 리스트를 그 횟수만큼 반복
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


# POST /users  본문: {"name": "영희", "age": 27}
# 받은 데이터를 저장하지는 않고, 확인 메시지와 함께 돌려주기만 한다
@app.post("/users")
async def create_user(user: User):
    return {
        "message": f"{user.name}님이 등록되었습니다!",
        "user": user.model_dump()   # Pydantic 모델 -> dict
    }


#############
# DELETE 연습
#############

from fastapi import HTTPException

# 연습용 데이터: 사용자 ID가 key
# 메모리에만 있으므로 서버를 다시 켜면 이 상태로 돌아온다
users = {
    1: {"name": "철수", "age": 25},
    2: {"name": "영희", "age": 27}
}

# DELETE /users/1
@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    # 없는 id면 404 오류 응답 (raise하면 함수가 여기서 끝난다)
    if user_id not in users:
        raise HTTPException(
            status_code=404,
            detail="해당 사용자가 없습니다."
        )

    deleted_user = users.pop(user_id)   # pop: 꺼내면서 dict에서 지움

    return {
        "message": "사용자가 삭제되었습니다.",
        "user": deleted_user
    }

############
# PUT 요청
############

# PUT /users/2  본문: {"name": "카리나", "age": 26}
# 경로의 user_id로 대상을 찾고, 본문 내용으로 통째로 바꾼다
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
