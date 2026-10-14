from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse

app = FastAPI()

# 다중 파일 업로드: 리스트로 받는다. input 태그에 multiple을 붙이면 파일을 여러 개 고를 수 있다.
# 5바이트, 3바이트 파일 -> {"file_sizes":[5,3]}
@app.post("/files")
async def create_files(files: list[bytes] = File()):
    return {"file_sizes": [len(file) for file in files]}

# -> {"filenames":["a.txt","b.txt"]}
@app.post("/uploadfiles")
async def create_upload_files(files: list[UploadFile]):
    return {"filenames": [file.filename for file in files]}

@app.get("/")
async def main():
	content = """
					<body>
					<h2>다중 파일 업로드</h2>
					<hr>
					<form action="/files" enctype="multipart/form-data" method="post">
					<input name="files" type="file" multiple>
					<input type="submit">
					</form>
					<hr>
					<form action="/uploadfiles" enctype="multipart/form-data" method="post">
					<input name="files" type="file" multiple>
					<input type="submit">
					</form>
					</body>
					"""
	return HTMLResponse(content=content)
