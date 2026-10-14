from langgraph.graph import MessagesState

# 그래프 전체가 함께 쓰는 상태. MessagesState를 상속해서 대화 기록(messages, add_messages 리듀서로 누적)을 그대로 쓰고,
# RAG 흐름에 필요한 값 4개를 더했다. (messages 외의 키는 리듀서가 없어서 노드가 돌려준 값으로 덮어써진다)
class AgentState(MessagesState):
    question: str  # 검색에 쓸 질문. chatbot이 사용자 질문으로 채우고, transform_query가 다시 쓴 질문으로 바꾼다
    context: str  # 검색 결과(쪽 번호 포함). context_organizer가 정리한 내용으로 바꾼다
    answer: str  # generate가 만든 답변. check_hallucinations가 이 답변이 context에 근거하는지 평가한다
    retry_num: int  # 질문을 다시 쓴 횟수. 3번이 되면 더 검색하지 않고 답변 단계로 넘어간다
    generate_num: int  # 답변을 만든 횟수. 3번이 되면 환각 평가 결과와 상관없이 종료한다 (무한 반복 방지용으로 추가)
