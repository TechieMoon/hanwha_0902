from fastapi import Request

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

app = FastAPI()

# exam9와 같은 곱셈 API
@app.get("/calc")
async def calc(num1:int, num2:int):
    return {"result" : num1 * num2}

# exam9_v.html: 폼을 제출해도 페이지를 이동하지 않고, 자바스크립트(XMLHttpRequest, AJAX)로 /calc를 호출해서
# 받은 JSON의 result만 같은 페이지 아래에 출력한다.
@app.get("/")
async def main(request: Request):
    # 수정: 원래는 templates.TemplateResponse("exam9_v.html", {"request": request})였다.
    # 템플릿 이름을 먼저 쓰는 옛 방식인데, 수업 환경의 starlette 1.7.0에서는 첫 인자가 request여야 해서
    # "TypeError: unhashable type: 'dict'" 오류가 났다. 다른 예제처럼 (request, 템플릿 이름) 순서로 바꿨다.
    return templates.TemplateResponse(request, "exam9_v.html")
