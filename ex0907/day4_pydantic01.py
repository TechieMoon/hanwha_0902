# 1. 기본: 데이터 검증과 타입 변환
# BaseModel을 상속하고 타입 힌트만 적으면, 객체를 만들 때 Pydantic이 값을 검사·변환한다.

from pydantic import BaseModel


class User(BaseModel):
    name: str
    age: int     # int로 선언했으므로 "25" 같은 숫자 문자열은 25로 바뀐다
    email: str


user = User(
    name="Alice",
    age="25",    # 일부러 문자열로 넣음 -> int 25로 자동 변환
    email="alice@example.com",
)

print(user)
print(user.age)
print(type(user.age))   # 변환됐는지 확인: <class 'int'>

# -------
# name='Alice' age=25 email='alice@example.com'
# 25
# <class 'int'>
# -------
# 참고: age="스물다섯"처럼 숫자로 바꿀 수 없는 값이면 ValidationError가 난다.
