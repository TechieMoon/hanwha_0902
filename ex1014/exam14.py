from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
  name: str
  description: str | None = None
  price: float | None = None
  tax: float | None = None
  tags: list[str] = []

# response_model: 응답 데이터를 이 모델 형식으로 검증하고 걸러서 내보낸다.
# 본문에 모델에 없는 필드(예: "secret")를 넣어 보내도 응답에서는 빠지고, 빠진 필드는 기본값(null, [])으로 채워진다.
@app.post("/items1", response_model=Item)
async def proc1(item: Item) :
  return item

# 딕셔너리 리스트를 돌려줘도 list[Item] 형식으로 바뀌어서 description, tax, tags가 기본값으로 채워진다.
@app.get("/items2", response_model=list[Item])
async def proc2() :
  return [
    {"name": "둘리", "price": 42.0},
    {"name": "또치", "price": 32.0},
    {"name": "도우너", "price": 32.0},
  ]

my_items = [
    {"name": "Foo", "description": "There comes my hero"},
    {"name": "Red", "description": "It's my aeroplane"},
]

@app.get("/items3", response_model=list[Item])
async def proc3():
    return my_items

# 모델이 아닌 일반 타입도 된다. 키는 문자열, 값은 실수인 딕셔너리
@app.get("/items4", response_model=dict[str, float])
async def proc4():
  return {"foo": 2.3, "bar": 3.4}
