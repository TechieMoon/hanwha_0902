# 항공 이용 가이드 RAG 챗봇 UI

import requests
import streamlit as st

API_URL = "http://localhost:8000/chat"  # exam22.py 서버의 /chat
# Streamlit은 입력할 때마다 스크립트를 처음부터 다시 실행해서, 대화 기록은 st.session_state에 보관한다.

st.set_page_config(page_title="항공 이용 가이드 챗봇", page_icon="✈️")
st.title("✈️ 항공 이용 가이드 챗봇")
st.caption("항공권 예약, 수하물, 체크인, 기내 서비스 등 무엇이든 물어보세요.")

user_input = st.chat_input("질문을 입력하세요...")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input:   
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("검색하는 중..."):
            try:
                res = requests.post(
                    API_URL,
                    json={
                        "message": user_input
                    },
                    timeout=60,
                )
                res.raise_for_status()
                data = res.json()

                st.markdown(data["ai_message"])
                st.session_state.messages.append({"role": "assistant", "content": data["ai_message"]})
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
