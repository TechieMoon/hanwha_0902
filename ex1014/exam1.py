# 실행: 이 폴더에서 uvicorn exam1:app --reload  (기본 주소 http://127.0.0.1:8000)
# --reload는 코드를 저장하면 서버를 자동으로 다시 띄운다. /docs로 들어가면 자동 생성된 API 문서(Swagger UI)를 볼 수 있다.
from fastapi import FastAPI

# FastAPI 앱 객체. uvicorn이 이 app을 찾아서 실행한다.
app = FastAPI()

# @app.get("/"): "/" 주소로 GET 요청이 오면 아래 함수를 실행한다. (경로 + HTTP 메서드 = 엔드포인트)
@app.get("/")
async def root():
    # 딕셔너리를 돌려주면 FastAPI가 JSON으로 바꿔서 응답한다. 결과: {"message":"안녕? FastAPI!! ^^"}
    return {"message": "안녕? FastAPI!! ^^"}
