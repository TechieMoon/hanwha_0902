# 백엔드(FastAPI): Streamlit 화면이 보낸 이름·나이를 받아 결과 메시지를 돌려준다
# 실행: uvicorn main:app --reload  (http://127.0.0.1:8000)
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Streamlit이 보내는 JSON의 모양: {"name": "홍길동", "age": 20}
class UserInput(BaseModel):
    name: str
    age: int

# 서버가 켜졌는지 확인용
@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상 동작 중입니다."}

# POST /predict: 검증된 UserInput을 받아 처리
@app.post("/predict")
def process_data(data: UserInput):
    # 비즈니스 로직 및 AI 모델 추론 처리 위치
    is_adult = data.age >= 19
    # 조건 표현식: (참일 때 값) if 조건 else (거짓일 때 값)
    message = f"안녕하세요 {data.name}님! " + ("성인입니다." if is_adult else "미성년자입니다.")

    # dict를 돌려주면 JSON 응답이 된다. Streamlit은 result_message를 화면에 쓴다
    return {
        "status": "success",
        "result_message": message,
        "is_adult": is_adult
    }
