from fastapi import FastAPI

app = FastAPI()

# 경로 파라미터: URL 경로의 {item_id} 부분이 함수 인자로 들어온다.
# 타입을 적지 않으면 문자열(str)로 받는다. /items/3 -> {"item_id":"3"} (숫자가 아니라 문자열 "3")
@app.get("/items/{item_id}")
def read_item(item_id):
  return {"item_id": item_id}

# 타입을 적으면 FastAPI가 변환과 검사를 해 준다. /friend/둘리/10 -> {"이름":"둘리","나이":10}
# age에 숫자가 아닌 값(/friend/둘리/열살)을 넣으면 함수가 실행되지 않고 422 오류(int_parsing)가 응답된다.
# (위 함수와 이름이 같지만, 라우트는 데코레이터가 등록할 때 이미 연결되므로 둘 다 동작한다)
@app.get("/friend/{name}/{age}")
async def read_item(name : str, age : int):
  return {"이름": name, "나이" : age}
