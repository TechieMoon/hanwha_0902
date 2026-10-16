from fastapi import FastAPI, Request ,HTTPException
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from pydantic import BaseModel
# psycopg는 파이썬에서 PostgreSQL 데이터베이스에 연결하고 조작할 수 있게 해주는 
# 대표적인 PostgreSQL 어댑터(드라이버) 라이브러리
import psycopg
from psycopg.rows import dict_row
from pgvector import Vector
from pgvector.psycopg import register_vector

# 노트북(exam3)에서 mydoc3 테이블에 넣은 항공 이용 안내 15개 청크를 검색해 답하는 RAG 챗봇 서버
# 실행: uvicorn exam22:app --reload, 화면은 streamlit run exam22_client.py

class QuestionRequest(BaseModel):
    message: str

class QuestionResponse(BaseModel):
    ai_message: str

app = FastAPI()
templates = Jinja2Templates(directory=".") # 현재 경로 (이 파일에서는 쓰지 않음)

openai_client = OpenAI()

# 주의: async 함수 안에서 동기 OpenAI·DB 호출을 하므로, 응답을 기다리는 동안 다른 요청을 처리하지 못한다.
# 동기 함수(def)로 선언하면 FastAPI가 별도 스레드에서 실행해 준다.
@app.post("/chat")
async def question(req : QuestionRequest) -> QuestionResponse:
    print(req)
    response_text=""
    message=req.message
    response_text=ask(message)

    return QuestionResponse(ai_message=response_text)

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
EMBEDDING_DIM = 1536

# 텍스트 -> 백터 변환
def text_to_embedding(text: str)->list[float]:
    cleaned = text.replace("\n", " ").strip()
    embed_resp = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=cleaned)
    return embed_resp.data[0].embedding

# 실습용 로컬 도커 컨테이너 접속 정보 (exam21처럼 환경변수로 읽는 게 좋다)
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "edu",
    "password": "1234",
    "dbname": "edudb"
}

def get_connection():
    conn = psycopg.connect(**DB_CONFIG, row_factory=dict_row)
    register_vector(conn)
    return conn

def ask(question: str):
    if not question.strip():
        raise HTTPException(400, "질문을 입력해 주세요.")
    chunks = search_similar_chunks(question)
    if not chunks:
        return "유사한 내용을 찾을 수 없습니다"
    
    answer = ask_llm(question, chunks)
    return answer    

def ask_llm(question: str, context_chunks: list[dict]) -> str:
    """검색된 청크(페이지)를 컨텍스트로 삼아 답변을 생성한다."""
    context_text = "\n\n".join(
        f"[출처: {c['id']} ]\n{c['content']}"
        for c in context_chunks
    )
    system_prompt = (
        # 수정: 원래는 "호텔 메뉴얼"이었는데, 검색하는 데이터(mydoc3)와 화면(exam22_client.py)은 항공 이용 가이드라 맞췄다.
        "당신은 제공된 항공 이용 가이드를 근거로만 답변하는 어시스턴트입니다. "
        "컨텍스트에 없는 내용은 추측하지 말고 '문서에서 확인되지 않습니다'라고 답하세요. "
        "답변은 한국어로 작성하고, 필요하면 목록으로 정리해 간결하게 설명하세요."
    )
    user_prompt = f"""
                        [컨텍스트]
                        {context_text}
                        
                        [질문]
                        {question}"""

    response = openai_client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.output_text

"""
청크 vs 입력 코사인 유사도 구하는 함수
"""
TOP_K = 3  # 거리 순으로 가장 가까운 3개 (유사도 기준이 없어서 관련 없는 질문에도 3개를 근거로 쓴다)
def search_similar_chunks(question: str,top_k: int = TOP_K,)-> list[dict]:
    question_embedding = text_to_embedding(question)
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, content,
                        embedding <=> %s AS distance
                FROM mydoc3
                ORDER BY distance ASC
                LIMIT %s
                """,
                (Vector(question_embedding), top_k),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
        
    return rows

