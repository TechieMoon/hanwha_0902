from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()

# 파일 업로드 두 가지 방식 (둘 다 python-multipart 필요, 폼은 enctype="multipart/form-data")
# 1) bytes = File(): 파일 내용 전체를 메모리에 바이트로 받는다. 작은 파일에 적합. 11바이트 파일 -> {"file_size":11}
@app.post("/singlefile")
async def create_file(file: bytes = File()):
  return {"file_size": len(file)}

# 2) UploadFile: 파일 이름, 형식(content_type) 같은 정보를 함께 받고, 큰 파일은 디스크 임시 파일에 담는다. -> {"filename":"a.txt"}
@app.post("/singleuploadfile")
async def create_upload_file(file: UploadFile):
  return {"filename": file.filename}

@app.get("/")
async def main():
  content = """
      <body>
      <body>
      <h2>단일 파일 업로드</h2>
      <hr>
      <form action="/singlefile" enctype="multipart/form-data" method="post">
      <input name="file" type="file">
      <input type="submit">
      </form>
      <hr>
      <form action="/singleuploadfile" enctype="multipart/form-data" method="post">
      <input name="file" type="file">
      <input type="submit">
      </form>
      </body>
    """
  return HTMLResponse(content=content)
