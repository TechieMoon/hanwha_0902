# OpenAI API 키가 잘 설정됐는지 확인하는 코드
# 키는 코드에 쓰지 않는다. 윈도우 환경변수 OPENAI_API_KEY에 넣어 두면 OpenAI()가 알아서 찾는다.
import os   # 참고: 이 코드에서는 쓰지 않음 (키를 직접 읽으려면 os.environ["OPENAI_API_KEY"])
from openai import OpenAI

client = OpenAI()   # 환경변수에서 키를 읽어 클라이언트 생성 (키가 없으면 여기서 오류)

# Responses API로 한 번 요청
response = client.responses.create(
    model="gpt-5.6-luna",
    input="안녕하세요라고 한마디만 해줘."
)

print(response.output_text)   # 응답 객체에서 답 글자만 꺼내기
