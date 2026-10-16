# FastAPI 첫 예제: GET 요청 두 개
# 실행: fastapi dev main.py  (또는 uvicorn main:app --reload)
from fastapi import FastAPI

app = FastAPI()   # 서버 앱 객체. 아래 데코레이터로 주소와 함수를 연결한다

# GET / -> {"Hello": "World"}
@app.get("/")
def read_root():
    return{"Hello": "World"}   # dict를 돌려주면 JSON 응답이 된다

# GET /items/12?q=google
# item_id: 경로 매개변수(int로 변환, 숫자가 아니면 422)
# q: 쿼리 매개변수(기본값 None이므로 안 보내도 됨)
@app.get("/items/{item_id}")
def read_item(item_id:int, q:str | None=None):
    return {"item_id":item_id, "q": q}
