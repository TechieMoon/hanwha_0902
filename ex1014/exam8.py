from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# /items/3 -> 3번 이미지(static/images/3.jpg)와 "다음 이미지" 링크(/items/4)를 보여 준다. 10번 다음은 1번으로 돌아간다.
# response_class=HTMLResponse는 /docs 문서에 이 엔드포인트가 HTML을 돌려준다고 표시해 준다.
# 이미지는 1 ~ 10번만 있어서 /items/11처럼 범위 밖 번호를 직접 입력하면 페이지는 열리지만 이미지는 404로 깨진다.
@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: int):

  return templates.TemplateResponse(request, name="exam8_v.html",   
                    context={"id": id, "nextid" : 1 if id == 10 else id+1, "img_name" : f"images/{id}.jpg"})
