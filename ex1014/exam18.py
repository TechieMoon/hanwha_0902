from fastapi import FastAPI, UploadFile
from fastapi.responses import HTMLResponse
import os
from contextlib import asynccontextmanager
import signal  # (이 파일에서는 쓰지 않음)

# 서버가 켜질 때 업로드 파일을 저장할 static/files 폴더가 없으면 만든다.
# (os.mkdir는 상위 폴더 static이 없으면 실패한다. os.makedirs(..., exist_ok=True)를 쓰면 한 번에 만든다)
@asynccontextmanager
async def my_lifespan(app: FastAPI):
    print("서버 기동시 실행")
    if not os.path.isdir("static/files"):
      os.mkdir("static/files")
    yield

app = FastAPI(lifespan=my_lifespan) 

# 업로드한 파일을 서버의 static/files 폴더에 저장한다.
@app.post("/singleuploadfile")
async def create_upload_file(file: UploadFile):
  # 수정: 원래는 path = f"static/files/{file.filename}"이었다.
  # 파일 이름은 클라이언트가 보내는 값이라, 브라우저가 아닌 프로그램으로 "../evil.txt" 같은 이름을 보내면
  # static/files 밖(static/evil.txt)에 파일이 써진다(경로 조작). 테스트로 실제로 확인해서 이름 부분만 쓰도록 바꿨다.
  path = f"static/files/{os.path.basename(file.filename)}"
  content = await file.read()  # UploadFile의 내용은 await file.read()로 읽는다
  with open(path, 'w+b') as fp:  # 같은 이름의 파일이 있으면 덮어쓴다
    fp.write(content)

  return {
      'file': file.filename,
      'content': file.content_type,  # 파일 형식(MIME), 예) text/plain, image/png
      'path': path,
  }

# 여러 파일을 한 번에 저장한다. 결과는 파일마다 정보 딕셔너리의 리스트
@app.post("/multiuploadfiles")
async def create_upload_files(files: list[UploadFile]):
  result = []
  for file in files:
    path = f"static/files/{os.path.basename(file.filename)}"  # 수정: 위와 같은 이유로 파일 이름 부분만 사용
    content = await file.read()
    with open(path, 'w+b') as fp:
      fp.write(content) 

    result.append({
      'file': file.filename,
      'content': file.content_type,
      'path': path,
    })
  return result


@app.get("/")
async def main():
  content = """
      <body>
        <h2>파일 업로드하여 서버에 저장하기</h2>
        <hr>
        <form action="/singleuploadfile" enctype="multipart/form-data" method="post">
        <input name="file" type="file">
        <input type="submit" value="싱글파일 업로드">
        </form>
        <hr>
        <form action="/multiuploadfiles" enctype="multipart/form-data" method="post">
        <input name="files" type="file" multiple>
        <input type="submit" value="다중파일 업로드">
        </form>
      </body>
    """
  return HTMLResponse(content=content)
