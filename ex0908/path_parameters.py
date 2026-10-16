# 경로 매개변수 + Enum: 경로에 올 수 있는 값을 정해진 것으로 제한하기
from enum import Enum

from fastapi import FastAPI


# str과 Enum을 같이 상속 -> 값이 문자열인 선택지 목록
class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


app = FastAPI()


# GET /models/alexnet, /models/resnet, /models/lenet 만 허용 (그 외 값은 422)
@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    # 비교 방법 1: Enum 멤버끼리 비교
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    # 비교 방법 2: .value로 실제 문자열을 꺼내 비교
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    # 남은 경우: resnet
    return {"model_name": model_name, "message": "Have some residuals"}
