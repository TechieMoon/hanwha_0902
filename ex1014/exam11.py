from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

# 경로 파라미터 + 요청 본문 + 쿼리 파라미터를 한 번에 받는다.
# PUT /items/5?q=hello, 본문 {"name":"둘리","price":3} -> {"item_id":5,"name":"둘리",...,"q":"hello"}
# 구분 규칙: 경로에 있으면 경로 파라미터, pydantic 모델이면 본문, 단순 타입(str, int 등)이면 쿼리 파라미터
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"q": q})
    return result
