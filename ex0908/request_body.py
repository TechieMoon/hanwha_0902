# 요청 본문(Request Body): POST로 받은 JSON을 Pydantic 모델로 검증
from fastapi import FastAPI
from pydantic import BaseModel


# 본문의 모양: name, price는 필수 / description, tax는 선택
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


app = FastAPI()


# POST /items/  본문 예: {"name": "Foo", "price": 35.4}
# 검증을 통과한 Item을 그대로 돌려준다 (안 보낸 선택 항목은 null)
# 브라우저 주소창으로는 POST를 못 보내므로 /docs 에서 테스트
@app.post("/items/")
async def create_item(item: Item):
    return item
