from langchain.tools import tool

# 계산기 도구: 이번 실습의 에이전트들이 공통으로 쓰는 도구
@tool 
def calculator(a: int, b: int, operation: str) -> str:
    """
    간단한 계산기 도구입니다.
    
    Args:
        a: 첫 번째 숫자
        b: 두 번째 숫자
        operation: 연산 종류 (add, subtract, multiply, divide)
    """
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b 
    elif operation == "multiply":
        result = a * b 
    elif operation == "divide":
        # 0으로 나누면 에러 대신 안내 문구를 결과로 돌려준다.
        result = a / b if b != 0 else "0으로 나눌 수 없습니다"
    else:
        return f"지원하지 않는 연산: {operation}"
    
    return f"{a} {operation} {b} = {result}"

# 다른 파일에서 from tools import tools로 가져다 쓴다.
tools = [calculator]