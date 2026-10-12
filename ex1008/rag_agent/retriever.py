from langchain_chroma import Chroma 
from langchain_openai import OpenAIEmbeddings 
# create_retriever_tool: retriever(검색기)를 에이전트가 호출할 수 있는 도구로 감싸 주는 함수
from langchain_core.tools import create_retriever_tool

from dotenv import load_dotenv

# .env의 OPENAI_API_KEY를 불러온다. (검색어를 임베딩할 때 필요)
load_dotenv()

# 6.5.2 노트북이 만든 벡터 DB 폴더. 실행한 위치(ex1008 폴더) 기준 상대 경로라서, 다른 위치에서 실행하면
# 에러 없이 빈 DB가 새로 만들어지고 검색 결과도 비어 버린다.
DB_PATH = "./rag_agent/chroma_db"

# 저장해 둔 Chroma DB를 다시 불러온다. 임베딩을 새로 만들지 않으므로 API 비용이 들지 않는다.
# 저장할 때와 같은 임베딩 모델, 같은 collection_name을 써야 한다. (검색어도 같은 모델로 벡터로 바꿔야 비교가 된다)
vectorstore = Chroma(
    persist_directory=DB_PATH,
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
    collection_name="korean_pdf",
)

# DB에 저장된 전체 데이터(ids, documents, metadatas 등)를 꺼내는 메서드. 반환값을 쓰지 않아서 실행 결과에는 영향이 없다.
# DB가 제대로 불러와졌는지 보려면 print(len(vectorstore.get()["ids"]))처럼 개수를 출력하면 된다. (510이 나와야 함)
vectorstore.get()

# 벡터 DB -> retriever: 질문과 가장 비슷한 청크 3개를 돌려주는 검색기
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# retriever -> 도구. 인자는 query(검색어) 하나이고, name과 description이 LLM에게 전달되는 도구 설명서가 된다.
retriever_tool = create_retriever_tool(
    retriever,
    name="pdf_search",
    # LLM은 이 설명을 보고 언제 이 도구를 쓸지 판단한다.
    description="use this tool to search information from the Korean Spelling Rules PDF document",
)

if __name__ == "__main__":
    # 도구를 직접 실행: 검색된 청크 3개의 본문이 빈 줄로 이어진 문자열 하나가 돌아온다. (쪽 번호 같은 메타데이터는 빠짐)
    response = retriever_tool.invoke("부엌이 들어간 경우 어떻게 발음하나요?")
    print(response)