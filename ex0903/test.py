# Streamlit 버튼 연습: streamlit run ex0903/test.py 로 실행
import streamlit as st 

# 화면을 같은 너비의 칸 3개로 나눈다
left, middle, right = st.columns(3)

# button()은 누른 그 실행에서만 True를 돌려준다.
# 버튼을 누르면 스크립트 전체가 다시 실행되고, 이때 if 안의 내용이 화면에 그려진다.
# width="stretch": 버튼을 칸 너비에 꽉 차게
if left.button("Plain button", width="stretch"):
    left.markdown("You clicked the plain button.")
if middle.button("Emoji button", icon="😊", width="stretch"):  # icon: 이모지
    middle.markdown("You clicked the emoji button.")  # 수정: 오타 cliked -> clicked
if right.button("Material button", icon=":material/mood:", width="stretch"):  # icon: Material 아이콘 이름
    right.markdown("You clicked")  # 수정: 오타 cliked -> clicked
