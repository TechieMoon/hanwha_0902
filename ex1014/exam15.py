from typing import Annotated

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# Form(): JSON이 아니라 HTML 폼이 보내는 형식(application/x-www-form-urlencoded)으로 값을 받는다.
# Form을 쓰려면 python-multipart 패키지가 필요하다. 값을 빠뜨리면 422 오류(Field required)
@app.post("/insert")
async def login(username: Annotated[str, Form()], emailaddress: Annotated[str, Form()]):
  print(username, emailaddress)  # 서버 터미널에 출력
  return {"username" : username, "emailaddress" : emailaddress}

# 개인 정보 입력 폼. method="post"라서 입력값이 URL이 아니라 요청 본문에 담겨 간다.
# action이 /insert/(끝에 /)라서 307 리다이렉트로 /insert에 다시 보내진다. 307은 POST 방식과 본문을 그대로 유지한다.
@app.get("/")
async def main():
  content = """
      <!DOCTYPE html> 
      <html>
        <head>
        <meta charset="UTF-8">
        <title>HTML학습</title>
      </head>
      <body>
        <h1>개인 정보 작성</h1><hr>
        <form action="/insert/" method="post">
        <input name="username" type="text" placeholder="계정을 입력하세요"><br>
        <input name="emailaddress" type="email" placeholder="메일주소를 입력하세요"><br>
        <input type="submit" value="요청">
        </form>
      </body>
    """
  return HTMLResponse(content=content)
