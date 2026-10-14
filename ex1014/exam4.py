from enum import Enum
from fastapi import FastAPI

# Enum으로 경로 파라미터에 들어올 수 있는 값을 미리 정해 둔다. (str도 상속해서 JSON에 문자열로 나온다)
class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

app = FastAPI()

# 정해진 값(alexnet, resnet, lenet) 외의 값(/models/vgg)이 오면 422 오류: "Input should be 'alexnet', 'resnet' or 'lenet'"
# /docs 문서에도 선택지 3개가 드롭다운으로 표시된다.
@app.get("/models/{model_name}") 
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:  # Enum 멤버와 비교
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":  # .value로 실제 문자열 값과 비교
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}

# {file_path:path}: '/'가 들어간 경로 전체를 하나의 파라미터로 받는다.
# /files//home/user/a.txt -> {"file_path":"/home/user/a.txt"} (앞의 '/'까지 받으려면 //를 두 번 쓴다)
@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}
