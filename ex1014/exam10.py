from fastapi import FastAPI
from pydantic import BaseModel

# 요청 본문(Request Body): POST/PUT으로 보내는 JSON의 형식을 pydantic 모델로 정의한다.
# 기본값이 없는 name, price는 필수, None 기본값이 있는 description, tax는 선택이다.
class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


app = FastAPI()

# status_code=201: 성공 시 200 대신 201 Created로 응답한다. (새 데이터를 만들었다는 의미)
# {"name":"둘리","price":10.5,"tax":1.5} -> 201, price_with_tax 12.0 추가
# price를 빠뜨리면 422 오류(Field required). 정수 10을 보내도 float 10.0으로 바뀐다.
@app.post("/items", status_code=201)
async def create_item(item: Item):
  item_dict = item.model_dump()  # pydantic 모델 -> 딕셔너리
  item_dict.update({"method":"POST"}) 
  print(item_dict)  # 서버 터미널에 출력
  # 주의: tax가 0이면 if item.tax가 거짓이라 price_with_tax가 붙지 않는다. (None만 거르려면 if item.tax is not None)
  if item.tax:
    price_with_tax = item.price + item.tax
    item_dict.update({"price_with_tax": price_with_tax})
  return item_dict


# 경로 파라미터(item_id) + 요청 본문(item)을 함께 받는다. FastAPI가 경로에 있는 것은 경로에서, pydantic 모델은 본문에서 찾는다.
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
  return {"method":"PUT", "item_id": item_id, **item.model_dump()}
