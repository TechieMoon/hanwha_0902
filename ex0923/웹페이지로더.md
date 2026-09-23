# WebBaseLoader로 웹 페이지 불러오기

`WebBaseLoader`로 웹 페이지(네이버 뉴스 기사)를 불러와 원하는 부분만 파싱하는 법을 실습한다. 단일 URL 로드, 여러 URL 동시 로드, 그리고 `nest_asyncio` + `aload()`로 비동기 로드까지 다룬다.

## 1. 웹 페이지 로드 및 원하는 부분만 파싱

`WebBaseLoader`는 URL을 받아서 웹 페이지의 HTML을 가져오고 텍스트를 추출하는 로더다. `bs_kwargs`에 `bs4.SoupStrainer`를 지정하면, 페이지 전체가 아니라 원하는 HTML 태그/클래스(여기서는 네이버 뉴스 기사 본문과 제목 클래스)만 골라서 파싱하기 때문에 불필요한 메뉴/광고 등이 섞이지 않는다. `header_template`으로 요청 헤더를 지정할 수 있는데, 일부 사이트는 `User-Agent`가 없거나 브라우저처럼 보이지 않는 요청을 차단하기도 해서 브라우저의 User-Agent 문자열을 흉내낸다. (참고: 원래 이 키가 `"User_Agent"`로 되어 있었는데, HTTP 헤더 이름은 하이픈을 쓰는 `User-Agent`가 맞는 표기라 밑줄을 하이픈으로 고쳤다. 네이버 뉴스가 이 헤더를 엄격히 검사하지 않아 오타 상태로도 우연히 실행은 됐었다.)

```python
import bs4 
from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader(
    web_paths=("https://n.news.naver.com/article/437/0000378416",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            "div",
            attrs={"class": ["newsct_article _article_body", "media_end_head_title"]},
        )
    ),
    header_template={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
    },
)

docs = loader.load()
print(f"문서의 수: {len(docs)}")
docs
```

출력:

```txt
문서의 수: 1

[Document(metadata={'source': 'https://n.news.naver.com/article/437/0000378416'}, page_content="\n출산 직원에게 '1억원' 쏜다…회사의 파격적 저출생 정책\n\n\n[앵커]올해 아이 낳을 계획이 있는 가족이라면 솔깃할 소식입니다. 정부가 저출생 대책으로 매달 주는 부모 급여, 0세 아이는 100만원으로 올렸습니다. 여기에 첫만남이용권, 아동수당까지 더하면 아이 돌까지 1년 동안 1520만원을 받습니다. 지자체도 경쟁하듯 지원에 나섰습니다. 인천시는 새로 태어난 아기, 18살될 때까지 1억원을 주겠다. 광주시도 17살될 때까지 7400만원 주겠다고 했습니다. 선거 때면 나타나서 아이 낳으면 현금 주겠다고 밝힌 사람이 있었죠. 과거에는 표만 노린 '황당 공약'이라는 비판이 따라다녔습니다. 그런데 지금은 출산율이 이보다 더 나쁠 수 없다보니, 이런 현금성 지원을 진지하게 정책화 하는 상황까지 온 겁니다. 게다가 기업들도 뛰어들고 있습니다. 이번에는 출산한 직원에게 단번에 1억원을 주겠다는 회사까지 나타났습니다.이상화 기자가 취재했습니다.[기자]한 그룹사가 오늘 파격적인 저출생 정책을 내놨습니다.2021년 이후 태어난 직원 자녀에 1억원씩, 총 70억원을 지원하고 앞으로도 이 정책을 이어가기로 했습니다.해당 기간에 연년생과 쌍둥이 자녀가 있으면 총 2억원을 받게 됩니다.[오현석/부영그룹 직원 : 아이 키우는 데 금전적으로 많이 힘든 세상이잖아요. 교육이나 생활하는 데 큰 도움이 될 거라 생각합니다.]만약 셋째까지 낳는 경우
... (일부 생략)
```

`requests_kwargs = {"verify": True}`로 SSL 인증서 검증 여부 등 requests 라이브러리에 전달할 추가 옵션을 지정할 수 있다.

```python
loader.requests_kwargs = {"verify": True}

docs = loader.load()
```

## 2. 여러 URL을 한 번에 로드

`web_paths`에 URL 리스트를 주면 여러 페이지를 한 번에 불러온다.

```python
loader = WebBaseLoader(
    web_paths=[
        "https://n.news.naver.com/article/437/0000378416",
        "https://n.news.naver.com/mnews/hotissue/article/092/0002340014?type=series&cid=2000063",
    ],
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            "div",
            attrs={"class": ["newsct_article _article_body", "media_end_head_title"]},
        )
    ),
    header_template={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"
    }
)

docs = loader.load() 

print(len(docs))
```

출력:

```txt
2
```

각 문서(페이지)의 앞부분 내용을 확인한다.

```python
print(docs[0].page_content[:500])
print("===" * 10)
print(docs[1].page_content[:500])
```

출력:

```txt
출산 직원에게 '1억원' 쏜다…회사의 파격적 저출생 정책


[앵커]올해 아이 낳을 계획이 있는 가족이라면 솔깃할 소식입니다. 정부가 저출생 대책으로 매달 주는 부모 급여, 0세 아이는 100만원으로 올렸습니다. 여기에 첫만남이용권, 아동수당까지 더하면 아이 돌까지 1년 동안 1520만원을 받습니다. 지자체도 경쟁하듯 지원에 나섰습니다. 인천시는 새로 태어난 아기, 18살될 때까지 1억원을 주겠다. 광주시도 17살될 때까지 7400만원 주겠다고 했습니다. 선거 때면 나타나서 아이 낳으면 현금 주겠다고 밝힌 사람이 있었죠. 과거에는 표만 노린 '황당 공약'이라는 비판이 따라다녔습니다. 그런데 지금은 출산율이 이보다 더 나쁠 수 없다보니, 이런 현금성 지원을 진지하게 정책화 하는 상황까지 온 겁니다. 게다가 기업들도 뛰어들고 있습니다. 이번에는 출산한 직원에게 단번에 1억원을 주겠다는 회사까지 나타났습니다.이상화 기자가 취재했습니다.[기자]한 그룹사가 오늘 파격적인 저출생 정책을 내놨
==============================

고속 성장하는 스타트업엔 레드팀이 필요하다


[이균성의 溫技] 초심, 본질을 잃을 때한 스타트업 창업자와 최근 점심을 같이 했다. 조언을 구할 게 있다고 했다. 당장 급한 현안이 있는 건 아니었다. 여러 번 창업한 경험이 있는데 지금 하고 있는 아이템은 대박 느낌이 든다고 헸다. 그런데 오히려 더 조심해야겠다는 생각이 들더란다. 조언을 구하고자 하는 바도 성장이 예상될 때 무엇을 경계해야 할지 알고 싶다는 거였다. 적잖은 스타트업 창업자를 만났지만 드문 사례였다.2년 가까이
... (일부 생략)
```

## 3. 비동기로 여러 페이지 빠르게 로드하기

`nest_asyncio`는 주피터 노트북처럼 이미 비동기 이벤트 루프가 돌고 있는 환경에서 추가로 `asyncio` 기반 코드를 실행할 수 있게 해주는 패치 라이브러리다. `WebBaseLoader.aload()`(비동기 로드)를 노트북에서 쓰려면 필요하다.

```python
import nest_asyncio 

nest_asyncio.apply()
```

`requests_per_second`로 초당 요청 수를 제한해서(여기서는 1) 짧은 시간에 요청이 몰려 상대 서버에 부담을 주지 않도록 조절한 뒤, `aload()`로 여러 페이지를 비동기로 가져온다.

```python
loader.requests_per_second = 1 

docs = loader.aload()
```

출력:

```txt
C:\Users\user\AppData\Local\Temp\ipykernel_16780\3575961884.py:3: LangChainDeprecationWarning: See API reference for updated usage: https://python.langchain.com/api_reference/community/document_loaders/langchain_community.document_loaders.web_base.WebBaseLoader.html
  docs = loader.aload()
Fetching pages: 100%|##########| 2/2 [00:00<00:00,  5.48it/s]
```

비동기로 가져온 결과를 확인한다.

```python
docs
```

출력:

```txt
[Document(metadata={'source': 'https://n.news.naver.com/article/437/0000378416'}, page_content="\n출산 직원에게 '1억원' 쏜다…회사의 파격적 저출생 정책\n\n\n[앵커]올해 아이 낳을 계획이 있는 가족이라면 솔깃할 소식입니다. 정부가 저출생 대책으로 매달 주는 부모 급여, 0세 아이는 100만원으로 올렸습니다. 여기에 첫만남이용권, 아동수당까지 더하면 아이 돌까지 1년 동안 1520만원을 받습니다. 지자체도 경쟁하듯 지원에 나섰습니다. 인천시는 새로 태어난 아기, 18살될 때까지 1억원을 주겠다. 광주시도 17살될 때까지 7400만원 주겠다고 했습니다. 선거 때면 나타나서 아이 낳으면 현금 주겠다고 밝힌 사람이 있었죠. 과거에는 표만 노린 '황당 공약'이라는 비판이 따라다녔습니다. 그런데 지금은 출산율이 이보다 더 나쁠 수 없다보니, 이런 현금성 지원을 진지하게 정책화 하는 상황까지 온 겁니다. 게다가 기업들도 뛰어들고 있습니다. 이번에는 출산한 직원에게 단번에 1억원을 주겠다는 회사까지 나타났습니다.이상화 기자가 취재했습니다.[기자]한 그룹사가 오늘 파격적인 저출생 정책을 내놨습니다.2021년 이후 태어난 직원 자녀에 1억원씩, 총 70억원을 지원하고 앞으로도 이 정책을 이어가기로 했습니다.해당 기간에 연년생과 쌍둥이 자녀가 있으면 총 2억원을 받게 됩니다.[오현석/부영그룹 직원 : 아이 키우는 데 금전적으로 많이 힘든 세상이잖아요. 교육이나 생활하는 데 큰 도움이 될 거라 생각합니다.]만약 셋째까지 낳는 경우엔 국민주택을 제공
... (일부 생략)
```

## 정리

| 기능 | 코드 |
|---|---|
| 단일 페이지 로드 | `WebBaseLoader(web_paths=(url,))` |
| 원하는 부분만 파싱 | `bs_kwargs=dict(parse_only=bs4.SoupStrainer(...))` |
| 요청 헤더 지정 | `header_template={"User-Agent": ...}` |
| 여러 페이지 로드 | `web_paths=[url1, url2, ...]` |
| 비동기 로드 | `nest_asyncio.apply()` 후 `loader.aload()` |
| 요청 속도 제한 | `loader.requests_per_second = N` |

`bs_kwargs`로 파싱 범위를 좁히는 것과, `header_template`으로 브라우저처럼 보이는 요청을 보내는 것이 크롤링 실습의 핵심이다.
