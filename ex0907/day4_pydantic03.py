# 3. API 요청 → 검증 → 데이터 변환
# 요청 데이터를 모델로 먼저 검증하고, 검증된 객체만 처리 함수에 넘기는 구조

from pydantic import BaseModel, Field


# 회원가입 요청 데이터의 규칙
class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)   # 3~20글자
    password: str = Field(min_length=8)                  # 8글자 이상
    age: int = Field(ge=14)                              # 14세 이상


# 이 함수는 이미 검증된 데이터만 받으므로, 안에서 길이·나이를 다시 검사하지 않는다
def signup(data: SignupRequest):
    print("회원가입 처리")
    print(f"username: {data.username}")
    print(f"age: {data.age}")   # 비밀번호는 화면에 출력하지 않는다


request = SignupRequest(
    username="alice",
    password="12345678",
    age=25,
)

signup(request)

# -----
# 회원가입 처리
# username: alice
# age: 25
# # -----
# 참고: username="al"이나 age=10이면 SignupRequest(...)를 만드는 순간 ValidationError가 난다.
