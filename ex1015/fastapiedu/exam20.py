import os
import time
import math
from fastapi import FastAPI
from pydantic import BaseModel, Field
from openai import OpenAI

# 두 문장을 임베딩해서 코사인 유사도를 계산해 주는 API
# 실행: uvicorn exam20:app --reload  ->  POST /api/similarity  {"textA": "...", "textB": "..."}

# 1. 환경 설정
client = OpenAI()
app = FastAPI()

# 2. 요청 JSON 모델
class SimilarityRequest(BaseModel):
    textA: str = Field(min_length=1)
    textB: str = Field(min_length=1)

# 3. 코사인 유사도 계산 함수: 내적 / (두 벡터 길이의 곱). 같은 방향이면 1, 직각이면 0
# (strict=True: 두 벡터의 길이(차원)가 다르면 조용히 잘라 버리지 않고 오류를 낸다)
# OpenAI 임베딩은 길이가 1로 정규화되어 나와서 사실상 내적만 해도 같은 값이다.
def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


# 4. REST API
@app.post("/api/similarity")
def similarity(request: SimilarityRequest):
    start = time.perf_counter()

    # 두 문장을 한 번에 임베딩
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[request.textA, request.textB],
    )

    vector_a = response.data[0].embedding
    vector_b = response.data[1].embedding

    # 코사인 유사도 계산
    score = cosine_similarity(vector_a, vector_b)
    score = max(-1.0, min(1.0, score))

    # 유사도 해석 (실습용 기준)
    # 주의: 노트북(exam3) 실험에서 정답 문장과 질문의 유사도는 0.546이었다. 이 기준이면 정답도 "유사도가 낮음"이 된다.
    if score >= 0.95:
        interpretation = "거의 동일한 의미 (≥ 0.95)"
    elif score >= 0.8:
        interpretation = "매우 유사한 의미"
    elif score >= 0.6:
        interpretation = "유사한 의미"
    else:
        interpretation = "유사도가 낮음"

    elapsed_ms = round(
        (time.perf_counter() - start) * 1000
    )

    return {
        "textA": request.textA,
        "textB": request.textB,
        "cosineSimilarity": round(score, 4),
        "similarityPercent": round(score * 100, 2),
        "interpretation": interpretation,
        "elapsedMs": elapsed_ms,
    }
