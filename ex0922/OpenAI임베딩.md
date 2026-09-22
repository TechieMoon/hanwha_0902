# OpenAI Embeddings 실습

텍스트를 벡터(숫자 배열)로 변환하는 임베딩(embedding)을 OpenAI의 임베딩 모델로 실습했다. 문장 하나를 벡터로 바꾸는 것부터, 여러 문장을 한 번에 임베딩하기, 벡터 차원 수 조절하기, 그리고 임베딩 벡터끼리 코사인 유사도(cosine similarity)로 문장 간 의미적 유사성을 비교하는 것까지 다뤘다.

## 1. 임베딩 모델 준비 및 문장 벡터화

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

text = "임베딩 테스트를 하기 위한 샘플 문장입니다."
query_result = embeddings.embed_query(text)
query_result[:5]
```

출력:

```txt
[-0.007762908935546875,
 0.036712646484375,
 0.01953125,
 -0.0196990966796875,
 0.0172119140625]
```

`text-embedding-3-small`은 비교적 가볍고 저렴하면서도 성능이 좋은 임베딩 모델이다. `embed_query()`는 질의(query) 하나를 임베딩 벡터로 변환할 때 쓰는 메서드다.

## 2. 여러 문서를 한 번에 벡터로 변환

```python
doc_result = embeddings.embed_documents(
    [text, text, text, text]
)
len(doc_result)  # 4
doc_result[0][:5]
```

`embed_documents()`는 여러 텍스트를 리스트로 받아 한 번에 임베딩한다. 같은 문장을 `embed_query`로 임베딩했을 때와 `embed_documents`로 임베딩했을 때 벡터 값이 동일하다.

## 3. 임베딩 벡터의 차원 수

```python
len(doc_result[0])  # 1536
```

`text-embedding-3-small` 모델의 기본 벡터 차원은 1536이다.

## 4. 벡터 차원 수 줄이기

```python
embeddings_1024 = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=1024)
len(embeddings_1024.embed_documents([text])[0])  # 1024
```

`dimensions` 인자를 지정하면 모델의 기본 차원(1536)보다 더 작은 차원으로 임베딩 벡터를 줄여서 받을 수 있다. 벡터가 작아지면 저장 공간과 검색 속도 면에서 유리하지만, 그만큼 정보 손실이 발생할 수 있는 트레이드오프가 있다.

## 5. 문장 간 의미적 유사도 비교

```python
sentence1 = "안녕하세요? 반갑습니다."
sentence2 = "안녕하세요? 반갑습니다!"
sentence3 = "안녕하세요? 만나서 반가워요."
sentence4 = "Hi, nice to meet you"
sentence5 = "I like to eat apples"

from sklearn.metrics.pairwise import cosine_similarity

sentences = [sentence1, sentence2, sentence3, sentence4, sentence5]
embedded_sentences = embeddings_1024.embed_documents(sentences)

def similarity(a, b):
    return cosine_similarity([a], [b])[0][0]

for i, sentence in enumerate(embedded_sentences):
    for j, other_sentence in enumerate(embedded_sentences):
        if i < j:
            print(
                f"[유사도 {similarity(sentence, other_sentence):.4f}] {sentences[i]} \t <=====> \t {sentences[j]}"
            )
```

출력(일부):

```txt
[유사도 0.9644] 안녕하세요? 반갑습니다. 	 <=====> 	 안녕하세요? 반갑습니다!
[유사도 0.8422] 안녕하세요? 반갑습니다. 	 <=====> 	 안녕하세요? 만나서 반가워요.
[유사도 0.4842] 안녕하세요? 반갑습니다. 	 <=====> 	 Hi, nice to meet you
[유사도 0.1295] 안녕하세요? 반갑습니다. 	 <=====> 	 I like to eat apples
```

의미가 비슷하거나 다른 여러 문장을 준비했다. 1~3번은 표현만 조금씩 다른 비슷한 한국어 인사말이고, 4번은 같은 뜻의 영어 문장, 5번은 전혀 다른 의미의 문장이다. `cosine_similarity`는 두 벡터가 얼마나 같은 방향을 가리키는지로 유사도를 계산한다(1에 가까울수록 유사, 0에 가까울수록 무관).

결과를 보면 의미가 비슷한 한국어 문장들끼리(1↔2: 0.9644, 1↔3: 0.8422) 유사도가 매우 높고, 같은 뜻이라도 언어가 다른 경우(1↔4: 0.4842)는 유사도가 크게 떨어지며, 의미 자체가 다른 문장(1↔5: 0.1295)은 유사도가 가장 낮다. 임베딩 벡터가 문장의 "의미"를 잘 포착하고 있다는 것을 확인할 수 있다.

## 정리

- `embed_query(text)` : 문장 하나를 벡터로 변환. 검색 질의(query)를 임베딩할 때 사용.
- `embed_documents([text, ...])` : 여러 문장을 한 번에 벡터로 변환. 문서 집합을 임베딩할 때 사용.
- `dimensions` : 임베딩 벡터의 차원 수를 모델 기본값보다 줄일 수 있는 옵션(저장 공간/속도 vs 정밀도 트레이드오프).
- 코사인 유사도로 벡터 사이의 거리를 재면, 의미가 비슷한 문장일수록 값이 1에 가깝고 무관한 문장일수록 0에 가까워진다. 이 원리가 이후 배울 벡터 검색(유사도 기반 문서 검색)의 기반이 된다.
