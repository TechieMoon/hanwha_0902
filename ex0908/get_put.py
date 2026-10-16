# GET + PUT 예제: PUT은 요청 본문(JSON)을 Pydantic 모델로 받는다
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# 요청 본문의 모양
class Item(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None   # 선택 항목

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

# PUT /items/5  본문: {"name": "펜", "price": 1000}
# item_id는 경로에서, item은 본문(JSON)에서 받는다
@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}
