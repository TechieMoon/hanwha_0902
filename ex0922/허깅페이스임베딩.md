# HuggingFace Embeddings 실습

OpenAI가 아닌 HuggingFace 생태계의 임베딩 모델들을 실습했다. HuggingFace의 추론 엔드포인트(Endpoint)를 원격으로 호출하는 방법, 모델을 직접 내 컴퓨터로 내려받아 로컬에서 돌리는 방법, 그리고 다국어 임베딩에 강한 `BAAI/bge-m3` 모델을 LangChain 없이 `FlagEmbedding` 라이브러리로 직접 다루면서 dense·sparse·multi-vector(ColBERT) 세 가지 임베딩 방식까지 다뤘다. HuggingFace API 토큰(`HF_TOKEN`)을 `.env`에서 불러와 사용했다.

## 1. 환경 설정 및 예시 문장 준비

```python
import os
import warnings

warnings.filterwarnings("ignore")
os.environ["HF_HOME"] = "./cache/"

texts = [
    "안녕, 만나서 반가워.",
    "LangChain simplifies the process of building applications with large language models",
    "랭체인 한국어 튜토리얼은 LangChain의 공식 문서, cookbook 및 다양한 실용 예제를 바탕으로 하여 사용자가 LangChain을 더 쉽고 효과적으로 활용할 수 있도록 구성되어 있습니다. ",
    "LangChain은 초거대 언어모델로 애플리케이션을 구축하는 과정을 단순화합니다.",
    "Retrieval-Augmented Generation (RAG) is an effective technique for improving AI responses.",
]
```

`HF_HOME` 환경변수로 HuggingFace 모델 다운로드 캐시 경로를 프로젝트 안의 `./cache/` 폴더로 지정했다(기본값은 사용자 홈 디렉터리 아래 공용 캐시). 한국어·영어가 섞인 5개 문장을 준비해서, 이후 이 문장들을 임베딩해 서로 의미가 얼마나 가까운지 비교한다.

## 2. HuggingFace Endpoint로 임베딩(원격 호출)

```python
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings

model_name = "intfloat/multilingual-e5-large-instruct"

hf_embeddings = HuggingFaceEndpointEmbeddings(
    model=model_name,
    task="feature-extraction",
    huggingfacehub_api_token=os.environ["HF_TOKEN"]
)

%%time
embedded_documents = hf_embeddings.embed_documents(texts)
```

`HuggingFaceEndpointEmbeddings`는 모델을 내 컴퓨터에 내려받지 않고, HuggingFace의 추론 서버에 API로 요청을 보내 임베딩 결과만 받아오는 방식이다. `intfloat/multilingual-e5-large-instruct`는 다국어(한국어 포함)를 잘 지원하는 임베딩 모델이다. 원격 API 호출이라 네트워크 왕복 시간이 포함되어 5개 문장 임베딩에 약 5.86초가 걸렸다.

## 3. 질의(query) 임베딩 및 유사도 기반 검색

```python
embedded_query = hf_embeddings.embed_query("LangChain에 대해서 알려주세요.")

import numpy as np
np.array(embedded_query) @ np.array(embedded_documents).T

sorted_idx = (np.array(embedded_query) @ np.array(embedded_documents).T).argsort()[::-1]

for i, idx in enumerate(sorted_idx):
    print(f"[{i}] {texts[idx]}")
```

`numpy`의 행렬 곱(`@`)으로 질의 벡터와 각 문서 벡터 사이의 내적(유사도 점수 역할)을 한 번에 계산했다. `HuggingFaceEndpointEmbeddings`가 반환하는 벡터는 이미 정규화되어 있어서, 내적값을 코사인 유사도처럼 유사도 점수로 바로 사용할 수 있다. `argsort()[::-1]`로 유사도가 높은 순서로 정렬해서 출력해보면, LangChain을 직접 언급하는 한국어/영어 문장들이 상위에 오고, 관련 없는 인사말·RAG 문장은 하위로 밀린다.

## 4. HuggingFaceEmbeddings로 로컬 실행

```python
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

model_name = "intfloat/multilingual-e5-large-instruct"

hf_embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
```

이번에는 모델을 원격 API가 아니라 내 컴퓨터로 직접 내려받아 실행하는 `HuggingFaceEmbeddings`를 사용했다. `model_kwargs={"device": "cpu"}`는 CPU에서 모델을 돌리겠다는 설정이고, `encode_kwargs={"normalize_embeddings": True}`는 임베딩 벡터를 정규화(크기를 1로 통일)해서, 내적만으로도 코사인 유사도와 같은 값을 얻을 수 있게 한다.

## 5. 다른 모델로 교체: BAAI/bge-m3

같은 방식(`HuggingFaceEmbeddings`)으로 다국어 검색에 강한 것으로 널리 쓰이는 `BAAI/bge-m3` 모델로 바꿔서 로컬 실행해봤다. 이 과정에서 `%%time`(셀 전체를 재는 셀 매직)이 아니라 `%time`(같은 줄만 재는 라인 매직)을 코드 한 줄만 따로 적어 쓴 경우가 있었는데, 이 경우 다음 줄의 실제 임베딩 코드는 측정 대상에 포함되지 않아 측정 시간이 0으로 나왔다. 의도한 측정이라면 `%%time`처럼 셀 전체를 재는 셀 매직을 써야 한다.

## 6. FlagEmbedding으로 BGE-M3 직접 사용하기

```python
from FlagEmbedding import BGEM3FlagModel

model_name = "BAAI/bge-m3"
bge_embeddings = BGEM3FlagModel(model_name, use_fp16=True)

bge_embedded = bge_embeddings.encode(
    texts,
    batch_size=12,
    max_length=8192,
)["dense_vecs"]

bge_embedded.shape  # (5, 1024)
```

`BAAI/bge-m3`는 LangChain 래퍼 없이도 원 제작사가 만든 `FlagEmbedding` 라이브러리로 직접 쓸 수 있다. 이렇게 하면 이 모델의 세 가지 임베딩 방식(dense·sparse·multi-vector)을 모두 활용할 수 있다. `use_fp16=True`는 16비트 부동소수점 연산으로 속도를 높이는 옵션이고, `batch_size`/`max_length`는 한 번에 처리할 문장 수와 최대 토큰 길이다.

### dense(밀집) 벡터

`encode(texts, return_dense=True)`로 명시적으로 요청할 수도 있다. 문장 전체를 하나의 벡터로 압축한 것으로, 의미적 유사도 비교에 쓰인다.

### sparse(어휘 기반) 벡터

```python
bge_encoded = bge_flagmodel.encode(texts, return_sparse=True)

lexical_scores1 = bge_flagmodel.compute_lexical_matching_score(
    bge_encoded["lexical_weights"][0], bge_encoded["lexical_weights"][0]
)
lexical_scores2 = bge_flagmodel.compute_lexical_matching_score(
    bge_encoded["lexical_weights"][0], bge_encoded["lexical_weights"][1]
)
```

출력: `0.30156046`, `0`

sparse 벡터는 dense 벡터처럼 의미를 압축한 것이 아니라, 문장에 실제로 등장하는 단어(토큰)별 가중치를 담고 있어서 전통적인 키워드 검색과 비슷한 방식으로 활용할 수 있다(`lexical_weights`로 접근). 같은 문장끼리 비교하면 공유하는 단어가 많아 점수가 나오고(0.3016), 언어와 내용이 전혀 다른 문장끼리 비교하면 겹치는 단어가 없어 점수가 0이 된다.

### ColBERT 방식의 multi-vector 임베딩

```python
bge_encoded = bge_flagmodel.encode(texts, return_colbert_vecs=True)

colbert_scores1 = bge_flagmodel.colbert_score(
    bge_encoded["colbert_vecs"][0], bge_encoded["colbert_vecs"][0]
)
colbert_scores2 = bge_flagmodel.colbert_score(
    bge_encoded["colbert_vecs"][0], bge_encoded["colbert_vecs"][1]
)
```

출력: `tensor(1.)`, `tensor(0.3748)`

문장 전체를 벡터 하나로 압축하는 대신, 문장을 이루는 토큰마다 각각의 벡터를 가지는 방식(multi-vector)이라서 더 세밀한 매칭이 가능하다. 같은 문장끼리는 최대값인 1.0이 나오고, 다른 문장끼리는 0.3748로 dense/sparse와는 또 다른 관점의 유사도 점수가 나온다.

## 정리

| 방식 | 클래스/라이브러리 | 실행 위치 | 비고 |
|---|---|---|---|
| HuggingFace Endpoint | `HuggingFaceEndpointEmbeddings` | 원격(HuggingFace 서버) | 모델을 내려받지 않고 API로 호출, `HF_TOKEN` 필요 |
| HuggingFace 로컬 실행 | `HuggingFaceEmbeddings` | 로컬(CPU/GPU) | 모델 가중치를 직접 다운로드해서 실행 |
| BGE-M3 직접 사용 | `FlagEmbedding.BGEM3FlagModel` | 로컬 | LangChain 래퍼 없이 원 라이브러리로 세 가지 임베딩 방식 모두 활용 |

`BAAI/bge-m3`는 한 모델에서 세 가지 임베딩을 동시에 지원하는 것이 특징이다.

- **dense**: 문장 전체를 하나의 벡터로 압축 — 의미적 유사도 비교에 사용.
- **sparse(lexical)**: 문장에 등장하는 단어별 가중치 — 키워드 매칭에 가까움, 같은 단어를 공유하지 않으면 점수 0.
- **ColBERT(multi-vector)**: 토큰마다 벡터를 가져 더 세밀한 매칭 — 같은 문장은 1.0, 다른 문장은 그보다 낮은 점수.

실무에서는 이 세 방식을 조합(하이브리드 검색)해서 의미 기반 검색과 키워드 기반 검색의 장점을 모두 활용하기도 한다.
