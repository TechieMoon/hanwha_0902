from fastapi import FastAPI
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import datetime

templates = Jinja2Templates(directory="templates")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# 템플릿에 데이터 넘기기: 세 번째 인자(context) 딕셔너리의 키를 템플릿에서 {{ fd }}처럼 쓴다.
# exam7_3.html은 서버(파이썬)가 만든 날짜·시간과, 브라우저(자바스크립트 new Date())가 만든 날짜·시간을 같이 보여 준다.
@app.get("/html3")
async def test3(request: Request):
    now = datetime.datetime.now()
    formatted_date = now.strftime("%Y년 %m월 %d일")
    formatted_time = now.strftime("%p %I시 %M분 %S초")  # %p: AM/PM, %I: 12시간제
    return templates.TemplateResponse(request, 
                                        "exam7_3.html", 
                                        {"fd": formatted_date, "ft": formatted_time});  # (끝의 ;는 파이썬에서는 없어도 된다)

# 경로 파라미터에 따라 다른 이미지를 보여 준다. 홀수면 hf1.png, 짝수면 hf2.png
# 템플릿에서 url_for('static', path=imgname)이 /static/images/hf1.png 같은 전체 주소를 만들어 준다.
@app.get("/html4/{shownum}") 
async def test4(request: Request, shownum : int):
    imgname = "images/hf1.png" if shownum % 2 else "images/hf2.png"
    return templates.TemplateResponse(request, "exam7_4.html",{"imgname": imgname})

# url_for() 연습: 정적 파일 주소뿐 아니라 함수 이름으로 엔드포인트 주소도 만들 수 있다.
# url_for('test4', shownum=100) -> http://127.0.0.1:8000/html4/100
# (imgname의 doolys.png는 주소만 만드는 예시라 실제 파일이 있는지는 확인하지 않는다. static/images에는 doolys.jpg만 있다)
@app.get("/html5")
async def test5(request: Request):    
    return templates.TemplateResponse(request=request, name="exam7_5.html",
                        context={"description" : "둘리와친구들", "imgname" : "doolys.png"});
