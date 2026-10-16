# FastAPI로 HTML 응답하기: Jinja2 템플릿과 AJAX

JSON만 돌려주는 API가 아니라 브라우저에 **HTML 페이지**를 보여 주는 방법을 실습했다. HTML 문자열을 직접 돌려주는 `HTMLResponse`, HTML 파일에 값을 채워 넣는 **Jinja2 템플릿**, 페이지 이동 없이 자바스크립트로 서버를 호출하는 **AJAX**를 비교했다. 실습하면서 HTML 태그(제목, 이미지, 링크, 목록, 폼)도 같이 익혔다.

- 코드: [`exam7.py`](exam7.py), [`exam7_1.py`](exam7_1.py), [`exam8.py`](exam8.py), [`exam9.py`](exam9.py), [`exam9_1.py`](exam9_1.py), [`exam15_2.py`](exam15_2.py), 템플릿은 [`templates/`](templates/)
- 강의 교안(PDF)은 강사님 자료라 저장소에는 넣지 않고, 내용을 5절에 요약했다.
- 템플릿을 쓰려면 `jinja2` 패키지가 필요하다.

## 1. 템플릿 응답 (exam7)

```python
templates = Jinja2Templates(directory="templates")

@app.get("/html1")
async def test1(request: Request):
    return templates.TemplateResponse(request, "exam7_1.html")
```

`templates` 폴더의 HTML 파일을 읽어 `text/html` 응답을 만든다. `request`는 템플릿 안에서 `url_for()`로 주소를 만들 때 필요해서 항상 첫 인자로 넘긴다.

## 2. 템플릿에 데이터 넘기기 (exam7_1, exam8)

```python
return templates.TemplateResponse(request, "exam7_3.html", {"fd": formatted_date, "ft": formatted_time})
```

```html
<h3>서버 기준 날짜 : {{ fd }}</h3>
<h3>서버 기준 시간 : {{ ft }}</h3>
<script>
  const now = new Date();
  output.innerHTML += `<h3>클라이언트 기준 날짜와 시간 : ${now.toLocaleString()}</h3>`;
</script>
```

세 번째 인자(context) 딕셔너리의 키를 템플릿에서 `{{ 키 }}`로 쓴다. 이 페이지는 **서버(파이썬)가 만든 시간**과 **브라우저(자바스크립트)가 만든 시간**을 같이 보여 준다. 서버 쪽 `{{ }}`는 응답을 보내기 전에 채워지고, `<script>`는 브라우저에 도착한 뒤에 실행된다.

### url_for()로 주소 만들기

| 템플릿 코드 | 결과 (테스트 서버 기준) |
|---|---|
| `{{ url_for('static', path='images/hf1.png') }}` | `http://testserver/static/images/hf1.png` |
| `{{ url_for('test3') }}` | `http://testserver/html3` (함수 이름 → 주소) |
| `{{ url_for('test4', shownum=100) }}` | `http://testserver/html4/100` (경로 파라미터 채우기) |

주소를 직접 적지 않고 함수 이름으로 만들기 때문에, 라우트 주소가 바뀌어도 템플릿을 고칠 필요가 없다. 실제 서버에서는 `http://127.0.0.1:8000/...`처럼 접속한 주소가 앞에 붙는다.

- `/html4/{shownum}`: 홀수면 `hf1.png`, 짝수면 `hf2.png`를 보여 준다(3 → hf1, 4 → hf2 확인).
- `/html5`의 `imgname`은 `doolys.png`인데 실제 파일은 `doolys.jpg`다. 이 페이지는 주소만 출력해서 드러나지 않지만, `url_for`는 **파일이 있는지 확인하지 않고** 주소만 만든다.

### 이미지 넘겨 보기 (exam8)

`/items/3` → 3번 이미지와 "Item ID: 4" 링크, `/items/10` → 다음 링크가 1번으로 돌아간다. 이미지는 1 ~ 10번만 있어서 `/items/11`을 직접 입력하면 페이지는 열리지만 이미지 요청(`/static/images/11.jpg`)은 404가 된다. 템플릿 `exam8_v.html`의 `<h1>`에 여는 태그 없이 들어 있던 `</a>`는 지웠다.

## 3. 폼 제출 vs AJAX (exam9, exam9_1)

같은 곱셈 API(`/calc?num1=3&num2=4` → `{"result":12}`)를 두 가지 방식으로 호출했다.

| | exam9: 폼 제출 | exam9_1: AJAX |
|---|---|---|
| 화면 | `HTMLResponse`로 HTML 문자열을 직접 응답 | `exam9_v.html` 템플릿 |
| 동작 | 제출하면 `/calc/?num1=..`로 **페이지 이동**, JSON이 화면에 그대로 보임 | `e.preventDefault()`로 이동을 막고 `XMLHttpRequest`로 `/calc` 호출 |
| 결과 표시 | `{"result":12}` 원문 | `JSON.parse(...).result`만 꺼내서 같은 페이지의 `<output>`에 출력 |

확인한 점:

- **폼의 action이 `/calc/`(끝에 `/`)인데 라우트는 `/calc`다.** FastAPI가 307 리다이렉트로 `/calc?num1=3&num2=4`에 다시 보내서 결과는 정상으로 나왔다. 요청이 한 번 더 오가는 셈이라 주소를 맞추는 게 좋다.
- `int`로 받기 때문에 `3.5`를 넣으면 422 오류가 난다. 폼의 `type="number"`는 기본으로 정수만 입력받아서 화면에서는 잘 드러나지 않는다.
- **exam9_1은 수업 환경 버전에서 그대로는 실행되지 않았다.** `templates.TemplateResponse("exam9_v.html", {"request": request})`처럼 템플릿 이름을 먼저 쓰는 옛 방식이었는데, starlette 1.7.0에서는 첫 인자가 `request`여야 해서 `TypeError: unhashable type: 'dict'`가 났다. 다른 예제와 같은 `TemplateResponse(request, "exam9_v.html")`로 고쳤더니 200으로 페이지가 나왔다.

## 4. 주기적 AJAX (exam15_2)

```javascript
function commAjax() {
  const xhr = new XMLHttpRequest();
  xhr.addEventListener("load", function() {
    h3Dom.textContent = `${JSON.parse(xhr.responseText).myfriend}`;
  });
  xhr.open("GET", `/myfriend`, true);
  xhr.send();
}
window.setInterval(commAjax, 2000);
```

`setInterval`로 2초마다 `/myfriend`(친구 5명 중 무작위 1명)를 호출해서 `<h3>`의 글자만 바꾼다. 페이지를 새로고침하지 않고 화면 일부만 계속 갱신하는 방식이다. 친구 목록은 서버가 켜질 때 lifespan에서 채운다([폼과파일업로드.md](폼과파일업로드.md)).

## 5. 강의 교안 정리: Jinja2 템플릿

- Jinja2는 파이썬용 웹 템플릿 엔진이다. FastAPI의 결과를 JSON이 아니라 HTML로 응답할 때 쓰고, `{{ 변수 }}` 자리에 서버가 넘긴 데이터를 채워 넣는다.
- **교안 코드와 실습 코드의 차이**: 교안의 exam7, exam8은 `templates.TemplateResponse("exam7_1.html", {"request": request})`처럼 **템플릿 이름을 먼저** 넘기는 옛 방식이다. 수업에서 실행한 코드는 대부분 `TemplateResponse(request, "exam7_1.html")`로 바뀌어 있었는데, exam9_1만 옛 방식이 남아 있었다. 수업 환경(starlette 1.7.0)에서는 옛 방식이 `TypeError`를 내서 3절처럼 고쳤다. 다른 자료를 보고 따라 할 때 버전에 따라 호출 방식이 다를 수 있다.

## 정리

| 방식 | 코드 | 특징 |
|---|---|---|
| HTML 문자열 | `return HTMLResponse(content=...)` | 간단한 페이지. 코드와 HTML이 섞임 |
| 템플릿 | `templates.TemplateResponse(request, "파일.html", {...})` | HTML을 파일로 분리, `{{ }}`로 값 채우기 |
| 주소 생성 | `url_for('static', path=...)`, `url_for('함수이름', 파라미터=...)` | 주소를 직접 적지 않음 |
| 폼 제출 | `<form action="/calc" method="get">` | 페이지가 이동함 |
| AJAX | `XMLHttpRequest` + `JSON.parse` | 페이지 이동 없이 결과만 갱신 |
| 주기적 갱신 | `setInterval(함수, 2000)` | 일정 간격으로 서버 호출 |
