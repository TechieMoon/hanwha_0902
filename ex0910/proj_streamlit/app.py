# 프론트엔드(Streamlit): 이름·나이를 입력받아 FastAPI 백엔드로 보내고 결과를 보여 준다
# 실행: streamlit run app.py  (먼저 proj_fastapi 서버를 켜 둘 것)
import requests
import streamlit as st

FASTAPI_URL = "http://127.0.0.1:8000"   # 백엔드 주소

st.title("Streamlit & FastAPI 연결 예제")

# 입력 폼 구성
# form 안의 입력은 제출 버튼을 누를 때 한 번에 처리된다
with st.form("user_form"):
    name = st.text_input("이름", value="홍길동")
    age = st.number_input("나이", min_value=1, max_value=120, value=20)
    submit_button = st.form_submit_button("백엔드로 전송")   # 누른 그 실행에서만 True

if submit_button:
    # FastAPI로 보낼 데이터 페이로드
    # 키 이름이 백엔드의 UserInput 필드(name, age)와 같아야 한다
    payload = {
        "name": name,
        "age": age
    }

    try:
        # FastAPI /predict 엔드포인트에 POST 요청
        # json=payload -> dict를 JSON 본문으로 바꿔 보낸다
        response = requests.post(f"{FASTAPI_URL}/predict", json=payload)

        if response.status_code == 200:
            result = response.json()    # 응답 JSON -> dict
            st.success("FastAPI 응답 성공!")
            st.write(f"**결과:** {result['result_message']}")
        else:
            # 예: 값이 잘못돼 422가 오면 여기로
            st.error(f"오류 발생 (상태 코드: {response.status_code})")

    # 백엔드 서버가 꺼져 있으면 연결 자체가 실패한다
    except requests.exceptions.ConnectionError:
        st.error("FastAPI 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해 주세요.")
