from fastapi import FastAPI
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Jinja2 템플릿: templates 폴더의 HTML 파일을 읽어서 응답으로 돌려준다.
templates = Jinja2Templates(directory="templates")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# TemplateResponse(request, 템플릿 파일 이름): HTML 응답(text/html)을 만든다. request는 템플릿 안에서 url_for 등을 쓰기 위해 필요하다.
@app.get("/html1")
async def test1(request: Request):
    return templates.TemplateResponse(request, "exam7_1.html")  # h1 ~ h6 제목 태그 연습

@app.get("/html2") 
async def test2(request: Request):
    return templates.TemplateResponse(request, "exam7_2.html")  # 이미지, 링크, 목록, 로그인 폼 태그 연습
