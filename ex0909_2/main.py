# 상품(item) CRUD API: 생성(POST)·조회(GET)·수정(PUT)·삭제(DELETE)
# 실행: fastapi dev main.py  -> http://127.0.0.1:8000/docs 에서 테스트
from fastapi  import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# 데이터용 (요청 본문의 모양)
class ItemSchema(BaseModel):
    name: str
    price: float
    desc: str | None=None   # 설명은 선택

# 메모리 저장소: {id: 상품 dict}. 서버를 다시 켜면 비워진다
items_db:dict[int, dict] = {}
id_counter = 1   # 다음에 붙일 id

# 생성 Create
# status_code=201: "새로 만들었다"는 뜻의 응답 코드 (기본은 200)
@app.post("/items/", status_code=201)
async def create_item(item: ItemSchema):
    global id_counter               # 바깥 변수 id_counter를 바꾸기 위해 필요
    new_item = item.model_dump()    # 모델 -> dict
    new_item["id"] = id_counter

    items_db[id_counter] = new_item
    id_counter += 1

    # 참고: 새 항목이 아니라 전체 items_db를 돌려준다.
    #       다른 API처럼 맞추려면 {"message": "생성 완료", "data": new_item}이 더 자연스럽다.
    return items_db

# 조회(전체) Read
# 참고: 이 API만 키 이름이 "message"가 아니라 "msg"
@app.get("/items/")
async def get_all_items():
    return {"msg": "전체 목록 조회 완료", "data":list(items_db.values())}
# 조회(단일) Read
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id not in items_db:     # 없는 id -> 404
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")

    return {"message": "단일 조회 완료", "data": items_db[item_id]}

# 수정 Update
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: ItemSchema):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")

    updated_data = item.model_dump()
    updated_data["id"] = item_id    # 본문에는 id가 없으므로 경로의 id를 다시 붙인다
    items_db[item_id] = updated_data

    return {"message": "수정 완료", "data": updated_data}

# 삭제 Delete
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다.")

    deleted_item = items_db.pop(item_id)   # 꺼내면서 삭제
    return {"message": "삭제 완료", "data": deleted_item}
