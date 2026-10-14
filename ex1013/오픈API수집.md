# 오픈 API로 데이터 수집: 공공데이터와 네이버 검색

웹 페이지 HTML을 긁어 오는 대신, 기관이나 회사가 데이터를 가져가라고 열어 둔 **오픈 API(REST API)**를 호출했다. 인증키를 발급받아 URL이나 헤더에 넣어 요청하면 XML이나 JSON으로 정리된 데이터를 돌려준다. 서울시 버스·청소년 강좌·지하철 승하차 데이터와 네이버 블로그·뉴스 검색 결과를 수집했다.

- 코드: [`dataexam/exam2.ipynb`](dataexam/exam2.ipynb)

## 1. 서울시 버스 노선 API (XML)

```python
url1 = 'http://ws.bus.go.kr/api/rest/busRouteInfo/getBusRouteList?serviceKey=' + key + '&strSrch=' + busNum
soup = BeautifulSoup(req.urlopen(url1).read().decode('utf-8'), "xml")
for itemList in soup.find_all('itemList'):
    busRouteId = itemList.find('busRouteId').string     # 360번 → 100100057
    ...
url2 = 'http://ws.bus.go.kr/api/rest/busRouteInfo/getStaionByRoute?ServiceKey=' + key + '&busRouteId=' + busRouteId
```

- 두 번 호출했다. ① 노선 번호 "360"으로 노선 ID(`100100057`)를 찾고, ② 그 ID로 노선 정보를 조회했다(`Staion`은 API 이름 자체의 철자).
- XML은 `BeautifulSoup(..., "xml")`로 파싱한다. 이 파서를 쓰려면 `lxml`을 설치해야 해서 노트북 맨 앞에서 `%pip install lxml`을 했다.

**결과 해석에서 확인한 점**: 출력은 "360번 버스 91대 운행중..."이었지만, `getStaionByRoute`는 노선이 지나는 **정류소 목록**을 돌려주는 API다. 그래서 91은 운행 중인 버스 대수가 아니라 **정류소 개수**이고, 찍힌 좌표도 정류소 위치다. 실시간 버스 위치를 보려면 버스 위치 정보를 주는 API를 따로 호출해야 한다. API가 무엇을 돌려주는지 문서를 확인하지 않으면 결과를 잘못 읽을 수 있다는 예시였다.

## 2. 서울 열린데이터광장 API (XML)

```python
url = 'http://openapi.seoul.go.kr:8088/' + key + '/xml/LampScpgmtb/1/1000/'
```

| 데이터 | 서비스명 | 결과 |
|---|---|---|
| 서울 청소년 수련관 강좌 | `LampScpgmtb` | 수련관 이름, 강좌명, 대상, 수강료 |
| 지하철 호선별·역별 승하차 인원 (2026-10-09) | `CardSubwayStatsNew` | 616개 역. 예: 2호선 홍대입구 승차 85,280명 / 하차 96,136명 |

- 이 API는 인증키를 쿼리 파라미터가 아니라 **URL 경로**에 넣는다(`/키/형식/서비스명/시작번호/끝번호/`). 한 번에 최대 1000건을 요청했다.
- 값이 비어 있는 태그는 `.string`이 `None`이라 `'없음'`으로 바꿨다.
- 결과를 쉼표로 이어 붙여 출력했는데, "성인,청소년(14세부터)"처럼 값 안에 쉼표가 있는 경우가 있었다. 이대로 CSV로 저장하면 열이 어긋나므로 pandas나 `csv` 모듈로 저장해야 한다.

## 3. 네이버 검색 API (JSON)

```python
naver_url = 'https://openapi.naver.com/v1/search/blog.json?query=' + urllib.parse.quote_plus('스마트폰') + '&display=100'
headers = {"X-Naver-Client-Id": client_key, "X-Naver-Client-Secret": client_secret}
response = requests.get(naver_url, headers=headers)
data_dict = response.json()
```

- 네이버는 인증 정보를 URL이 아니라 **요청 헤더**로 보낸다. `requests` 방식과 `urllib.request.Request` + `add_header()` 방식 두 가지로 해 봤다.
- 응답 JSON에는 `total`(전체 결과 수, 이날 '스마트폰' 블로그 글 23,004,542건), `items`(글 목록)가 있고 글마다 `title`, `link`, `description`, `bloggername`, `postdate`가 들어 있다.
- 주소만 `blog.json` → `news.json`으로 바꾸면 같은 키로 뉴스 검색도 된다('아시안게임' 뉴스 100건).
- 같은 검색을 두 번 했는데 두 번째 글부터 순서가 달랐다. 검색 결과는 요청할 때마다 조금씩 바뀔 수 있다.

### 정리해서 CSV로 저장

```python
title = [re.sub("</?b>", "", d["title"]) for d in data_dict["items"]]   # 검색어 강조용 <b> 태그 제거
df = pd.DataFrame({"title": title, "description": desc})                # 100행 × 2열
df.to_csv("output/smartphone.csv")
```

확인한 점:

- `<b>` 태그는 지워졌지만 `&amp;`, `&quot;` 같은 HTML 엔티티는 남았다(예: `사진&amp;영상`). `html.unescape()`를 같이 써야 원래 글자가 된다.
- `to_csv()`는 인덱스 열까지 저장한다(`index=False`로 뺄 수 있음). 엑셀에서 한글이 깨지지 않게 하려면 `encoding='utf-8-sig'`를 준다.
- 오류 처리 코드 `print('오류 코드 : ' + rescode)`는 `rescode`가 정수라서 실제로 오류가 나면 `TypeError`가 난다. `str(rescode)`로 바꿔야 한다. 또 `urllib`은 200이 아닌 응답이면 이 줄까지 오기 전에 `HTTPError` 예외를 내므로 `try/except`로 처리하는 게 맞다.

## 4. API 키 관리 (이 저장소에서 바꾼 것)

강사님 원본 노트북에는 공공데이터포털, 서울 열린데이터광장, 네이버 API 키가 **코드에 문자열로** 들어 있었고, URL을 출력하는 셀 때문에 **실행 결과에도** 키가 그대로 찍혀 있었다. 노트북을 그대로 깃허브에 올리면 코드를 고쳐도 출력에 남은 키가 노출된다.

이 저장소의 사본에서는 다음처럼 바꿨다.

| 위치 | 원본 | 사본 |
|---|---|---|
| 버스 API 셀 | `key = '...'` | `key = os.environ.get("DATA_GO_KR_SERVICE_KEY")` |
| 서울 열린데이터 셀 2개 | `key = '...'` | `key = os.environ.get("SEOUL_OPENAPI_KEY")` |
| 네이버 검색 셀 3개 | `client_key = '...'`, `client_secret = '...'` | `os.environ.get("NAVER_CLIENT_ID")`, `os.environ.get("NAVER_CLIENT_SECRET")` |
| URL 출력 | `print(url)` → 출력에 키가 찍힘 | `print(url.replace(key, "<SEOUL_OPENAPI_KEY>"))`, 기존 출력의 키도 자리표시자로 교체 |

환경변수는 윈도우 명령 프롬프트에서 이렇게 등록한다(새 터미널부터 적용).

```bat
setx DATA_GO_KR_SERVICE_KEY "발급받은_인증키"
setx SEOUL_OPENAPI_KEY "발급받은_인증키"
setx NAVER_CLIENT_ID "발급받은_Client_ID"
setx NAVER_CLIENT_SECRET "발급받은_Client_Secret"
```

또는 `.env` 파일에 적고 `python-dotenv`의 `load_dotenv()`로 읽는다(`.env`는 `.gitignore`에 들어 있어서 저장소에 올라가지 않는다).

배운 점: 키는 **코드에도, 출력에도** 남기지 않는다. 키가 들어간 URL을 출력하고 싶으면 키 부분을 가려서 출력한다. 혹시 키가 공개 저장소에 올라갔다면 커밋을 지워도 기록이 남으므로 **키를 재발급**하는 게 확실하다.

## 정리

| API | 인증키 위치 | 응답 | 파싱 |
|---|---|---|---|
| 서울시 버스 (`ws.bus.go.kr`) | 쿼리 파라미터 `serviceKey` | XML | `BeautifulSoup(..., "xml")` + `find_all('itemList')` |
| 서울 열린데이터광장 (`openapi.seoul.go.kr`) | URL 경로 | XML | `find_all('row')` |
| 네이버 검색 (`openapi.naver.com`) | 요청 헤더 | JSON | `response.json()` → 딕셔너리 |

> 네이버 블로그·뉴스 검색 결과는 다른 사람이 쓴 글의 일부라 노트북 출력에는 앞부분만 남겼고, 결과 CSV는 저장소에 올리지 않았다.
