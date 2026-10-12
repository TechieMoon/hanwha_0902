from langchain.graph import MessageState

class AgentState(MessageState):
    question: str 
    context: str 
    answer: str 
    retry_num: int 