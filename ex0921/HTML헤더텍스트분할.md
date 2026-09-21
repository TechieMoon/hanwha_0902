# HTMLHeaderTextSplitter 실습

지금까지 다룬 분할기들은 글자 수·토큰 수·문장 경계처럼 텍스트의 "양"을 기준으로 나눴다면, `HTMLHeaderTextSplitter`는 HTML의 `<h1>`, `<h2>`, `<h3>` 같은 제목 태그 구조를 기준으로 나눈다. 제목 계층에 따라 나뉜 조각마다 "이 내용이 어떤 제목 아래에 있었는지"를 `metadata`로 함께 기록해주는 것이 특징이다. 간단한 예시 HTML로 먼저 동작을 확인한 뒤, 실제 웹페이지를 가져와 적용해봤다.

## 1. 기본 동작 확인

```python
from langchain_text_splitters import HTMLHeaderTextSplitter

html_string = """
<!DOCTYPE html>
<html>
<body>
    <div>
        <h1>헤더1</h1>
        <p>헤더1에 포함된 본문</p>
        <div>
            <h2>헤더2-1 제목</h2>
            <p>헤더2-1에 포함된 본문</p>
            <h3>헤더3-1 제목</h3>
            <p>헤더3-1에 포함된 본문</p>
            <h3>헤더3-2 제목</h3>
            <p>헤더3-2에 포함된 본문</p>
        </div>
        <div>
            <h2>헤더2-2 제목</h2>
            <p>헤더2-2에 포함된 본문</p>
        </div>
        <br>
        <p>마지막 내용</p>
    </div>
</body>
</html>
"""

headers_to_split_on = [
    ("h1", "Header 1"),
    ("h2", "Header 2"),
    ("h3", "Header 3"),
]

html_splitter = HTMLHeaderTextSplitter(headers_to_split_on)
html_header_splits = html_splitter.split_text(html_string)

for header in html_header_splits:
    print(f"{header.page_content}")
    print(f"{header.metadata}", end="\n=========================\n")
```

출력(일부):

```txt
헤더3-1 제목
{'Header 1': '헤더1', 'Header 2': '헤더2-1 제목', 'Header 3': '헤더3-1 제목'}
=========================
헤더3-1에 포함된 본문
{'Header 1': '헤더1', 'Header 2': '헤더2-1 제목', 'Header 3': '헤더3-1 제목'}
=========================
```

`headers_to_split_on`은 어떤 태그를 "헤더"로 인식하고, 그걸 metadata의 어떤 키로 저장할지 매핑한다. 결과를 보면 각 조각의 `metadata`에 그 시점까지의 제목 계층이 전부 담긴다(예: `h3` 아래 본문은 `Header 1`, `Header 2`, `Header 3` 세 단계 모두 포함). `<h2>헤더2-2 제목</h2>` 이후의 `<br>`, `마지막 내용`처럼 더 하위 헤더가 없는 내용은 가장 가까운 상위 헤더(`Header 1`)의 metadata만 붙는다.

## 2. 실제 웹페이지에 적용: 헤더 구조로 나눈 뒤 다시 크기로 나누기

```python
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter

url = "https://plato.stanford.edu/entries/goedel/"

headers_to_split_on = [
    ("h1", "Header 1"),
    ("h2", "Header 2"),
    ("h3", "Header 3"),
    ("h4", "Header 4"),
]

html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

response = requests.get(url)
response.raise_for_status()
html_header_splits = html_splitter.split_text(response.text)

chunk_size = 500
chunk_overlap = 30
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size, chunk_overlap=chunk_overlap
)

splits = text_splitter.split_documents(html_header_splits)
```

실제 웹페이지(스탠퍼드 철학 백과사전의 괴델 항목)를 `requests`로 가져와서 두 단계로 분할했다.

1. `HTMLHeaderTextSplitter`로 먼저 제목 구조(`h1`~`h4`) 기준으로 나눠서 각 조각에 "어느 섹션에 속하는지" metadata를 붙인다.
2. 이렇게 나뉜 조각이 여전히 너무 길 수 있으므로, `RecursiveCharacterTextSplitter`(`chunk_size=500`, `chunk_overlap=30`)로 한 번 더 잘라서 LLM 컨텍스트 크기에 맞춘다. `split_documents()`를 쓰면 원래 `Document`의 metadata(헤더 정보)가 새로 나뉜 조각에도 그대로 유지된다.

출력을 보면 각 조각의 `metadata`에 `Header 1`부터 `Header 4`까지 섹션 경로가 그대로 남아 있다(예: `{'Header 1': 'Kurt Gödel', 'Header 2': '2. Gödel's Mathematical Work', 'Header 3': '2.2 The Incompleteness Theorems', 'Header 4': '2.2.2 The proof of the First Incompleteness Theorem'}`). (실시간으로 가져온 페이지라 나중에 다시 실행하면 사이트 내용이 바뀌어 출력이 달라질 수 있다.)

## 3. 현실적인 웹페이지의 한계: 광고·스크립트가 섞인 경우

```python
url = "https://www.cnn.com/2023/09/25/weather/el-nino-winter-us-climate/index.html"

headers_to_split_on = [
    ("h1", "Header 1"),
    ("h2", "Header 2"),
]

html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

response = requests.get(url)
response.raise_for_status()

html_header_splits = html_splitter.split_text(response.text)
```

이번에는 뉴스 기사 페이지(CNN)에 같은 방식을 적용해봤다. `headers_to_split_on`을 `h1`, `h2`만으로 단순화했다.

결과를 보면 실제 기사 제목("An El Niño winter is coming...")과 본문은 잘 뽑히지만, "Ad Feedback"처럼 광고 관련 텍스트나 앱 다운로드 QR 코드 안내, `<![CDATA[...` 같은 스크립트 조각까지 헤더 구조 밖(빈 `metadata={}`)으로 함께 뽑히는 것을 볼 수 있다. `HTMLHeaderTextSplitter`는 페이지의 "제목 태그 구조"만 보고 나누기 때문에, 실제 웹페이지처럼 광고·내비게이션·스크립트가 뒤섞인 HTML에서는 본문과 상관없는 내용도 함께 섞여 들어올 수 있다는 한계를 보여준다. (역시 실시간으로 가져온 페이지라 나중에 실행하면 결과가 달라질 수 있다.)

## 정리

`HTMLHeaderTextSplitter`는 문서의 제목(heading) 구조를 그대로 metadata로 남기고 싶을 때 유용하다. 기술 문서나 위키처럼 제목 계층이 잘 갖춰진 페이지에서는 "이 조각이 어느 챕터/섹션에 속하는지" 알 수 있어 검색·요약 품질에 도움이 되지만, 광고나 스크립트가 많은 일반 웹페이지에서는 노이즈가 함께 섞여 들어올 수 있어 후처리(예: 빈 metadata 조각 걸러내기)가 필요할 수 있다. 실무에서는 이번처럼 `HTMLHeaderTextSplitter`로 구조를 먼저 잡고, `RecursiveCharacterTextSplitter`로 크기를 다시 맞추는 2단계 조합이 자주 쓰인다.
