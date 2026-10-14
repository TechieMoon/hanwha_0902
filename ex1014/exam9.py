from typing import Annotated  # (이 파일에서는 쓰지 않음)

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# 곱셈 API. /calc?num1=3&num2=4 -> {"result":12}
# int로 받기 때문에 3.5처럼 소수를 넣으면 422 오류가 난다. (함수 이름이 login이지만 하는 일은 곱셈)
@app.get("/calc")
async def login(num1:int, num2:int):
    return {"result" : num1 * num2}

# HTML 문자열을 HTMLResponse로 돌려주면 브라우저에 페이지로 보인다.
# 폼을 제출하면 브라우저가 /calc/?num1=..&num2=.. 로 이동하고, 결과 JSON이 화면에 그대로 나온다(페이지 이동).
# action은 /calc/(끝에 /)인데 라우트는 /calc라서, FastAPI가 307 리다이렉트로 /calc에 다시 보내 준다.
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
            <h1 style="color:red">곱셈 연산</h1><hr>
            <form action="/calc/" method="get">
                <input name="num1" type="number" placeholder="숫자1을 입력하세요" required><br>
                <input name="num2" type="number" placeholder="숫자2를 입력하세요" required><br>
                <input type="submit" value="곱셈요청">
            </form>
        </body>
    """
    return HTMLResponse(content=content)
