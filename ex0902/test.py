# 함수 정의와 호출 연습 (9/2)
# def 이름(매개변수): 로 함수를 만들고, return으로 결과를 돌려준다.

def cel(f):
    # 이름은 섭씨(celsius) 변환처럼 보이지만, 실제로는 100을 더하는 연습용 함수다.
    # (화씨 -> 섭씨 변환이라면 (f - 32) * 5 / 9)
    return f + 100

print(cel(77))  # 177

def f1(x):
    return x + 100

def f2(x):
    return x - 100

def f3(x):
    return x * 100

def f4(x):
    return x / 100  # 나눗셈(/)은 항상 실수(float)를 돌려준다

print(f1(5))  # 105
print(f2(5))  # -95
print(f3(5))  # 500
print(f4(5))  # 0.05
