

# [1차 버전] 코드 실행 도구만 가진 에이전트. 아래 2차 버전을 만들면서 주석 처리했다.
################################################
############ 코드 생성 에이전트 #################
# from dotenv import load_dotenv 

# from langchain.agents import create_agent 
# from langchain_openai import ChatOpenAI 

# from tools import python_exec_tool

# load_dotenv()

# tools = [python_exec_tool]

# llm = ChatOpenAI(model="gpt-4o")
# graph = create_agent(llm, tools)

# if __name__ == "__main__":
#     response = graph.stream(
#         {
#             "messages": [
#                 "첫 번째 항이 1인 피보나치 수열을 출력하는 파이썬 코드를 작성해주세요."
#             ],
#         }
#     )
    
#     for chunk in response:
#         for node, value in chunk.items():
#             if node:
#                 print("---", node, "---")
#             if "messages" in value:
#                 print(value["messages"][0].content)


# [2차 버전] 코드 실행 + 파일 저장 도구를 가진 에이전트 (지금 실행되는 코드)
##################### 코드 생성 및 파일 저장 에이전트 ########################
############################################################################
from dotenv import load_dotenv 

# .env의 OPENAI_API_KEY를 환경변수로 불러온다.
load_dotenv()

# 같은 폴더의 tools.py에서 직접 만든 도구 두 개를 가져온다.
from tools import python_exec_tool, file_write_tool

from langchain.agents import create_agent 
from langchain_openai import ChatOpenAI 

# 에이전트가 쓸 수 있는 도구 목록
tools = [python_exec_tool, file_write_tool]

llm = ChatOpenAI(model="gpt-4o")
# create_agent: 6.2에서 직접 만든 'chatbot ↔ tools 반복 그래프'를 한 줄로 만들어 주는 함수.
# 노드 이름은 model(LLM 호출)과 tools(도구 실행)이다.
graph = create_agent(llm, tools)

if __name__ == "__main__":
    response = graph.stream(
        {
            # 메시지 두 개를 넣으면 HumanMessage 두 개로 들어간다: 코드 작성·실행 확인 요청, 파일 저장 요청
            "messages": [
                "첫 번째 항이 1인 피보나치 수열을 출력하는 파이썬 코드를 작성해주세요. 정상적으로 실행되는지 확인도 해주세요.",
                "확인했다면 그 코드는 .py 파일로 저장하세요."
            ]
        }
    )
    
    # updates 모드: 노드가 끝날 때마다 {노드 이름: 그 노드가 추가한 값}을 받는다.
    for chunk in response:
        for node, value in chunk.items():
            if node:
                print("---", node, "---")
            # 각 노드가 추가한 첫 번째 메시지의 내용만 출력 (도구를 요청하는 model 응답은 content가 비어 있다)
            if "messages" in value:
                print(value["messages"][0].content)