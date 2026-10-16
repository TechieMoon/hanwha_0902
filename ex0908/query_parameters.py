# 쿼리 매개변수 연습: 경로에 없는 함수 인자는 ?이름=값 으로 받는다
# 연습 단계마다 앞의 함수는 주석 처리하고 마지막 함수만 살려 둠
from fastapi import FastAPI

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

#################
# 쿼리 매개변수 연습
#################

# GET /items/?skip=1&limit=2 -> fake_items_db[1:3]
# 기본값이 있으므로 둘 다 안 보내도 된다 (skip=0, limit=10)
# @app.get("/items/")
# async def read_item(skip: int = 0, limit: int = 10):
#     return fake_items_db[skip : skip + limit]

##################
# 쿼리 매개변수 선택
##################

# q가 있을 때만 응답에 넣기
# @app.get("/items/{item_id}")
# async def read_item(item_id: str, q: str | None = None):
#     if q:
#         return {"item_id": item_id, "q": q}
#     return {"item_id": item_id}

###################
# 쿼리 매개변수 타입 변경
###################

# GET /items/foo?short=1 -> {"item_id": "foo"}
# short: bool -> 1, true, True, on, yes 는 True / 0, false, off, no 는 False
@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})        # dict에 키 추가
    if not short:                    # short가 아니면 긴 설명도 추가
        item.update(
            {"description": "This is an amazing item that has a long description"}  # 수정: 오타 descripton -> description
        )
    return item
