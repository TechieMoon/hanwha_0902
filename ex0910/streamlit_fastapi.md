# streamlit으로 프론트엔드, fastapi로 백엔드 연결하기

1. Streamlit

```python
import requests 
import streamlit as st 

FASTAPI_URL = "http://127.0.0.1:8000"

st.title("Streamlit & FastAPI 연결 예제")

# 입력 폼 구성 
with st.form("user_form"):
    name = st.text_input("이름", value="홍길동")
    age = st.number_input("나이", min_value=1, max_value=120, value=20)
    submit_button = st.form_submit_button("백엔드로 전송")

if submit_button:
    # FastAPI로 보낼 데이터 페이로드 
    payload = {
        "name": name,
        "age": age
    }

    try:
        # FastAPI /predict 엔드포인트에 POST 요청
        response = requests.post(f"{FASTAPI_URL}/predict", json=payload)

        if response.status_code == 200:
            result = response.json()
            st.success("FastAPI 응답 성공!")
            st.write(f"**결과:** {result['result_message']}")
        else:
            st.error(f"오류 발생 (상태 코드: {response.status_code})")

    except requests.exceptions.ConnectionError:
        st.error("FastAPI 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해 주세요.")
```

2.FastAPI

```python
from fastapi import FastAPI 
from pydantic import BaseModel

app = FastAPI()

class UserInput(BaseModel):
    name: str 
    age: int 

@app.get("/")
def read_root():
    return {"message": "FastAPI 서버가 정상 동작 중입니다."}

@app.post("/predict")
def process_data(data: UserInput):
    # 비즈니스 로직 및 AI 모델 추론 처리 위치 
    is_adult = data.age >= 19
    message = f"안녕하세요 {data.name}님! " + ("성인입니다." if is_adult else "미성년자입니다.")

    return {
        "status": "success",
        "result_message": message,
        "is_adult": is_adult 
    }
```

3. 결과

![result]()