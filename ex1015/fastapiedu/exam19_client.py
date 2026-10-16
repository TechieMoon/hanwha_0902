"""
유니코 AI Agent 의 Streamlit 클라이언트
- FastAPI 서버(main.py)의 REST API 를 requests 로 호출
- 실행 : streamlit run exam19_client.py
- 먼저 FastAPI 서버를 띄워야 함 : uvicorn exam19:app --reload   (원래 주석은 main:app)
"""

import requests
import streamlit as st

st.set_page_config(page_title="유니코 AI Agent", page_icon="🤖")
st.title("🤖 유니코 AI Agent")
st.caption("FastAPI 로 서비스되는 에이전트와 대화해 보세요. 도구를 쓰면 '사용한 도구'가 함께 표시됩니다.")

EXAMPLES = [
    "지금 서울이랑 뉴욕 시간 알려줘",
    "주사위 2개 굴려서 나온 합에 7을 곱해줘",
    "오늘 너무 피곤한데 점심 뭐 먹을까?",
    "(123 + 456) * 3 계산해줘",
    "자기소개 해줘",
]

# ──────────────────────────────────────────────
# 세션 상태 초기화 (Streamlit 은 매번 스크립트를 처음부터 다시 실행하므로 session_state 에 보관)
# ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []  # 화면에 그릴 대화 목록
if "session_id" not in st.session_state:
    st.session_state.session_id = None  # FastAPI 서버가 발급한 session_id


# ──────────────────────────────────────────────
# 사이드바 : 서버 설정, 도구 목록, 예시 질문, 새 대화
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")
    api_url = st.text_input("API 서버 주소", "http://127.0.0.1:8000").rstrip("/")

    # 서버 상태 확인
    try:
        health = requests.get(f"{api_url}/", timeout=3).json()
        st.success(f"서버 연결됨 ({health.get('model')})")
        tools = requests.get(f"{api_url}/tools", timeout=3).json()
    except requests.RequestException:
        st.error("서버에 연결할 수 없습니다.")
        tools = []

    if tools:
        with st.expander("🧰 에이전트 도구 목록"):
            for t in tools:
                st.markdown(f"- **{t['name']}** : {t['description']}")

    st.divider()
    st.subheader("💡 예시 질문")
    for i, q in enumerate(EXAMPLES):
        if st.button(q, key=f"ex_{i}", use_container_width=True):
            st.session_state.pending = q

    st.divider()
    if st.session_state.session_id:
        st.caption(f"session_id : `{st.session_state.session_id}`")
    if st.button("🗑️ 새 대화 시작", use_container_width=True):
        if st.session_state.session_id:  # 서버 쪽 대화 기록도 삭제 (실패해도 무시)
            try:
                requests.delete(f"{api_url}/sessions/{st.session_state.session_id}", timeout=5)
            except requests.RequestException:
                pass
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()


# ──────────────────────────────────────────────
# 지난 대화 출력
# ──────────────────────────────────────────────
def show_tool_calls(tool_calls: list[dict]):
    """에이전트가 사용한 도구 기록을 접이식 영역으로 표시"""
    if not tool_calls:
        return
    with st.expander(f"🔧 사용한 도구 ({len(tool_calls)})"):
        for call in tool_calls:
            st.markdown(f"**{call['tool']}**")
            st.json({"args": call["args"], "result": call["result"]}, expanded=False)


for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        show_tool_calls(m.get("tool_calls", []))


# ──────────────────────────────────────────────
# 새 질문 처리 : 입력창 또는 사이드바 예시 버튼
# ──────────────────────────────────────────────
prompt = st.chat_input("유니코에게 무엇이든 물어보세요!") or st.session_state.pop("pending", None)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("유니코가 생각 중..."):
            try:
                res = requests.post(
                    f"{api_url}/chat",
                    json={"message": prompt, "session_id": st.session_state.session_id},
                    timeout=60,
                )
                res.raise_for_status()
                data = res.json()
            except requests.RequestException as e:
                st.error(f"API 호출 실패: {e}")
                st.stop()

        st.session_state.session_id = data["session_id"]
        st.markdown(data["answer"])
        show_tool_calls(data["tool_calls"])

    st.session_state.messages.append(
        {"role": "assistant", "content": data["answer"], "tool_calls": data["tool_calls"]}
    )
    st.rerun()  # 사이드바의 session_id 표시를 갱신
