from pydantic import Field 
from langchain.tools import tool 

# 코드 실행 도구 (6.3.2): LLM이 작성한 파이썬 코드를 exec()로 실제 실행한다.
# 인자 기본값으로 pydantic Field(description=...)를 주면, 그 설명이 LLM이 읽는 도구 설명서(args)에 들어간다.
@tool 
def python_exec_tool(
    # import 문만 따로 받는다.
    imports: str = Field(description="임포트 구문"),
    # import 문을 뺀 나머지 코드
    code: str = Field(description="임포트 구문을 제외한 코드 블록"),
) -> str:
    """
    파이썬 코드를 실행하는 도구입니다. 만약 코드 실행에 실패하면 에러 메시지를 반환합니다.
    실행 결과를 확인하고 싶다면 `print(...)`를 사용하여 출력해야 합니다.
    
    Args:
        imports: 임포트 구문 
        code: 임포트 구문을 제외한 코드 블록 
        
    Returns:
        실행 결과 또는 에러 메시지
    """
    # 1단계: import 문만 먼저 실행해서 모듈을 불러올 수 있는지 확인
    # Check imports 
    try:
        exec(imports)
    except Exception as e:
        return f"모듈을 임포트하는 데 실패했습니다. ERROR: {repr(e)}"
    
    # 2단계: import 문 + 코드를 함께 실행. 에러가 나면 에러 메시지를 LLM에게 돌려준다.
    # Check execution 
    try:
        # 주의: 코드 안의 print() 결과는 터미널에 찍힐 뿐, 이 도구의 반환값(LLM이 보는 내용)에는 들어가지 않는다.
        exec(imports + "\n" + code)
    except Exception as e:
        return f"코드 실행에 실패했습니다. ERROR: {repr(e)}"
    
    # 성공하면 실행한 코드를 그대로 돌려준다. (실행 결과가 아니라 '에러 없이 실행됐다'는 사실만 전달)
    result_str = f"성공적으로 코드가 실행되었습니다. :\n```python\n{code}\n```"
    
    return result_str 

# 파일 저장 도구 (6.3.3): LLM이 정한 경로에 내용을 써서 파일로 저장한다.
@tool 
def file_write_tool(
    file_path: str = Field(description="생성/수정할 파일의 경로"),
    content: str = Field(description="파일에 작성할 내용")
) -> str:
    """
    파일을 생성하거나 내용을 작성하는 도구입니다.
    
    Args:
        file_path: 생성/수정할 파일의 경로
        content: 파일에 작성할 내용
        
    Returns:
        성공/실패 메시지
    """
    # 상대 경로면 프로그램을 실행한 폴더(현재 작업 폴더) 기준으로 저장된다.
    try:
        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(content)
        return f"파일 '{file_path}'에 성공적으로 작성했습니다."
    # 실패해도 프로그램을 멈추지 않고, 실패 메시지를 LLM에게 돌려준다.
    except Exception as e:
        return f"파일 작성 실패: {repr(e)}"    