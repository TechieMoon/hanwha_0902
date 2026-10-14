from fastapi import FastAPI
from contextlib import asynccontextmanager
import random
from fastapi.responses import HTMLResponse

app = FastAPI()  # (아래에서 다시 만들기 때문에 쓰이지 않는다)

friends = []
@asynccontextmanager
async def startup(app: FastAPI):
  print("UVICORN 에 의해 서버가 기동될 때 실행됩니다요~~~")
  friends.extend(["둘리", "또치", "도우너", "희동이", "마이콜"])
  yield

app = FastAPI(lifespan=startup)

@app.get("/myfriend")
async def main1():
  return {"myfriend" : random.choice(friends)}

# 주기적 AJAX: setInterval로 2초마다 /myfriend를 호출해서, 페이지를 새로고침하지 않고 h3의 글자만 바꾼다.
@app.get("/")
async def main2():
  content = """
      <!DOCTYPE html> 
      <html>
        <head>
        <meta charset="UTF-8">
        <title>주기적 요청</title>  
        <style>
          h3 {
            color : #000066;            
            text-shadow : 2px 2px 2px #3399ff;
          }
        </style>      
      </head>
      <body>
        <h1>주기적 요청하는 AJAX</h1>
        <hr>
        <h3>잠시 기다리숑~~</h3>
        <script>
          const h3Dom = document.querySelector("h3");
          function commAjax() {
            const xhr = new XMLHttpRequest();
            xhr.addEventListener("load", function() {        
              h3Dom.textContent = `${JSON.parse(xhr.responseText).myfriend}`;
            });
            xhr.open("GET", `/myfriend`, true);
            xhr.send();
          }          
          window.setInterval(commAjax, 2000);
        </script>
      </body>
      </html>
    """
  return HTMLResponse(content=content)
