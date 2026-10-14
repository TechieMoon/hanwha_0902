from fastapi import FastAPI
from contextlib import asynccontextmanager
import random

app = FastAPI()  # (아래에서 lifespan을 넣어 다시 만들기 때문에 이 줄은 쓰이지 않는다)

friends = []
# lifespan: 서버가 켜질 때와 꺼질 때 한 번씩 실행할 코드. yield 앞은 시작할 때, 뒤는 종료할 때 실행된다.
# 모델 불러오기, DB 연결처럼 요청마다 하면 느린 준비 작업을 여기서 한 번만 한다.
@asynccontextmanager
async def startup(app: FastAPI):
  print("UVICORN에 의해 서버가 기동될 때 실행됩니다요~~~")
  friends.extend(["둘리", "또치", "도우너", "희동이", "마이콜"])
  yield
  print("UVICORN이 종료될 때 실행됩니다요~~~")

app = FastAPI(lifespan=startup)

# 요청할 때마다 친구 5명 중 한 명을 무작위로 돌려준다. 예) {"myfriend":"희동이"}
@app.get("/myfriend")
async def main():
  return {"myfriend" : random.choice(friends)}
