from fastapi import FastAPI

app = FastAPI()

fake_items_db = [{"item_name": "Dooly"}, {"item_name": "Ddochi"}, {"item_name": "Dauner"}, {"item_name": "Olaf"}]


# 쿼리 파라미터: 경로에 없는 함수 인자는 URL의 ?뒤(쿼리 문자열)에서 받는다.
# 기본값이 있으면 생략할 수 있다. /items?skip=1&limit=2 -> 2번째부터 2개 [Ddochi, Dauner]
@app.get("/items")
async def read_item(skip: int = 0, limit: int = 10):
  return fake_items_db[skip : skip + limit]

# 경로 파라미터(item_id) + 선택 쿼리 파라미터(q). str | None = None 이면 없어도 되는 값이다.
# /items/foo?q=bar -> {"item_id":"foo","q":"bar"},  /items/foo -> {"item_id":"foo"}
@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None):
  if q:
    return {"item_id": item_id, "q": q}
  return {"item_id": item_id}
