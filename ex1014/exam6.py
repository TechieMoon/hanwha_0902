from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# 정적 파일: static 폴더를 /static 주소에 연결한다. 예) static/images/1.jpg -> /static/images/1.jpg
# (실행한 위치에 static 폴더가 있어야 한다. 이 저장소에는 강사님 이미지 파일은 넣지 않았다)
app.mount("/static", StaticFiles(directory="static"), name="static")

# bool 쿼리 파라미터는 true/false뿐 아니라 1/0, yes/no, on/off도 받는다. 그 외 값(short=abc)은 422 오류.
# /items/foo?q=hi&short=true -> {"item_id":"foo","q":"hi"} (short가 참이면 description을 붙이지 않음)
@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None, short: bool = False):
  item = {"item_id": item_id}
  if q:
    item.update({"q": q})
  if not short:
    item.update(
      {"description": "유용하고 잘 만들어진 상품"}
    )
  return item

# 기본값이 없는 쿼리 파라미터(needy)는 필수다. /items2/foo 처럼 빠뜨리면 422 오류(Field required).
@app.get("/items2/{item_id}")
async def read_user_item(item_id: str, needy: str):
  item = {"item_id": item_id, "needy": needy}
  return item
