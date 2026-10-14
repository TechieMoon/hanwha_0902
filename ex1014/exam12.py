from typing import Union
from fastapi import FastAPI, Query

app = FastAPI()

# Union[str, None]은 str | None과 같은 뜻(옛 표기법)
@app.get("/items1/")
async def read_items1(q: Union[str, None] = None):
  results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
  if q:
    results.update({"q": q})
  return results

# Query()로 쿼리 파라미터에 검증 조건을 붙인다. 5 ~ 50글자만 허용
# ?q=abc -> 422 "String should have at least 5 characters"
@app.get("/items2/")
async def read_items2(q: Union[str, None] = Query(default=None, min_length=5, max_length=50)):
  results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
  if q:
    results.update({"q": q})
  return results


# 정규식 조건(pattern): "unico"로 시작하는 3 ~ 10글자
# ?q=unicorn -> 통과, ?q=hello -> 422(패턴 불일치), ?q=unico12345678 -> 422(10글자 초과)
@app.get("/items3/")
async def read_items3(q: Union[str, None] = Query(default=None, min_length=3, max_length=10, pattern="^unico")):
  results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
  if q:
    results.update({"q": q})
  return results
