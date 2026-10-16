# 2. 실전: 기본값, Optional, 중첩 모델

from pydantic import BaseModel, Field

# 주소만 담는 작은 모델 (User 안에 넣어서 쓸 것)
class Address(BaseModel):
    city: str
    zip_code: str   # 우편번호는 앞자리 0이 사라지지 않게 문자열로

class User(BaseModel):
    name: str
    age: int = Field(ge=0, le=150)   # 0 <= age <= 150 이 아니면 ValidationError
    email: str
    address: Address                 # 중첩 모델: dict로 넣어도 Address 객체가 된다
    nickname: str | None = None      # 선택 항목: 안 넣으면 None

user = User(
    name="Alice",
    age=25,
    email="alice@example.com",
    address={                        # dict -> Address(city=..., zip_code=...)로 변환
        "city": "Daejeon",
        "zip_code": "34100",
    },
)                                    # nickname은 안 넣었으므로 None

print(user)
print(user.address.city)   # 점(.)으로 중첩 모델의 값에 접근
print(user.nickname)

# ------
# name='Alice' age=25 email='alice@example.com' address=Address(city='Daejeon', zip_code='34100') nickname=None
# Daejeon
# None
# # -----
