from fastapi import FastAPI, Path, HTTPException
from typing import Annotated


app = FastAPI()

items = {"dooly": "귀여운 아기 공룡"}

# HTTPException: 원하는 상태 코드와 메시지로 오류 응답을 보낸다.
# /items/dooly -> {"item":"귀여운 아기 공룡"},  /items/ddochi -> 404 {"detail":"ddochi 명의 아이템은 존재하지 않습니다."}
@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
      raise HTTPException(status_code=404, detail=f"{item_id} 명의 아이템은 존재하지 않습니다.")
    return {"item": items[item_id]}

# Annotated[타입, Path(...)]: 경로 파라미터에 검증 조건과 문서용 설명(title)을 붙인다. ge=1은 1 이상
# /items2/0 -> 422 "Input should be greater than or equal to 1",  /items2/5 -> {"item_id":5,"q":"unico"}
@app.get("/items2/{item_id}")
async def read_item2(item_id: Annotated[int, Path(title="The ID of the item to get", ge=1)],
                    q: str = 'unico'):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results
