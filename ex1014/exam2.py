from fastapi import FastAPI

app = FastAPI()

# 무엇을 돌려주든 기본 응답 형식은 JSON이다.
@app.get("/test1")
async def root1():
  return {"name": "둘리"}  # 딕셔너리 -> JSON 객체 {"name":"둘리"}

@app.get("/test2")
async def root2():
  return ["둘리", "또치", "도우너"]  # 리스트 -> JSON 배열

@app.get("/test3")
async def root3():
  # HTML처럼 보이지만 JSON 문자열 "<h1>안녕?</h1>"로 응답된다(Content-Type: application/json).
  # 브라우저에 HTML로 보여 주려면 HTMLResponse를 써야 한다. (exam9, exam15 참고)
  return "<h1>안녕?</h1>"

@app.get("/test4")
async def root4():
  return 1000  # 숫자 -> JSON 숫자 1000
