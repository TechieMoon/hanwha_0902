# Pydantic

> **한눈에 보기**
> - Pydantic은 **타입 힌트로 데이터 모양을 정해 두고, 들어온 값이 맞는지 검사·변환**해 주는 라이브러리다.
> - `BaseModel`을 상속해 모델을 만들고, 잘못된 값이 오면 `ValidationError`가 난다.
> - `Field(ge=, le=, min_length=)`로 범위·길이 규칙을, `| None = None`으로 선택 항목을, 모델 안의 모델로 중첩 JSON을 표현한다.
> - `model_dump()`는 dict로, `model_dump_json()`은 JSON 문자열로 바꾼다.
> - FastAPI의 요청 검증이 바로 이 Pydantic으로 동작한다 (→ [ex0908 FastAPI 기초](../ex0908/fastapi_guide.md)).

| 단계 | 배울 것 | 핵심 | 코드 |
|---|---|---|---|
| 1 | BaseModel | 타입 검증과 자동 변환 | [day4_pydantic01.py](day4_pydantic01.py) |
| 2 | Field, Optional, 중첩 모델 | 복잡한 데이터 검증 | [day4_pydantic02.py](day4_pydantic02.py) |
| 3 | API 데이터 모델링 | 실무에서 검증 + 변환 | [day4_pydantic03.py](day4_pydantic03.py) |
| 공식 문서 예제 | `ValidationError`, `Literal`, `model_dump` 옵션 | 출력 옵션 비교 | [pydantic.ipynb](pydantic.ipynb) |

## 1. 기본: 데이터 검증과 타입 변환

핵심 개념

- **BaseModel**: Pydantic 모델의 기본 클래스
- **타입 힌트**: 데이터의 형태를 정의 (`name: str`, `age: int`)
- **자동 타입 변환**: `age="25"`처럼 문자열로 넣어도 `int` 25로 바꿔 준다
- **ValidationError**: 바꿀 수 없는 값(`"not an int"` 등)이 오면 오류

```python
class User(BaseModel):
    name: str
    age: int
    email: str

user = User(name="Alice", age="25", email="alice@example.com")
print(type(user.age))   # <class 'int'>
```

## 2. 실전: 기본값, Optional, 중첩 모델

핵심 개념

- **`Field()`**: 값의 규칙을 정한다. `age: int = Field(ge=0, le=150)` → `0 <= age <= 150`
  (`ge`=크거나 같음, `le`=작거나 같음, `gt`/`lt`는 등호 없는 버전)
- **`| None = None`**: 없어도 되는 항목(Optional). 안 넣으면 `None`
- **기본값**: `name: str = "John Doe"`처럼 값을 주면 안 넣어도 된다
- **중첩 모델(Nested Model)**: 모델 안에 다른 모델을 필드로 넣는다. dict로 넣어도 알아서 `Address` 객체가 된다
- 이렇게 하면 복잡한 JSON 데이터도 한 번에 검증할 수 있다

```python
class Address(BaseModel):
    city: str
    zip_code: str

class User(BaseModel):
    age: int = Field(ge=0, le=150)
    address: Address
    nickname: str | None = None

user.address.city   # 'Daejeon'  (dict가 Address 객체로 바뀜)
```

## 3. API 요청 → 검증 → 데이터 변환

Pydantic의 역할은 **비즈니스 로직에 들어가기 전에 데이터가 올바른지 검사하는 것**이다.
`signup()` 함수는 이미 검증된 `SignupRequest`만 받으므로, 함수 안에서는 길이·나이 검사를 다시 할 필요가 없다.

```python
class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)  # 문자열 길이 규칙
    password: str = Field(min_length=8)
    age: int = Field(ge=14)
```

**`model_dump()`는 Python dict로 변환**하고, **`model_dump_json()`은 JSON 문자열로 변환**한다.

## 4. 출력 옵션 정리 ([pydantic.ipynb](pydantic.ipynb))

| 옵션 | 뜻 | 예시 결과 |
|---|---|---|
| `exclude_unset=True` | 직접 넣지 않은 필드는 빼기 | `why`(기본값만 있음) 빠짐 |
| `exclude={'where'}` | 지정한 필드 빼기 | `where` 빠짐 |
| `mode='json'` | JSON에 맞는 값으로 (datetime → 문자열) | `'2020-01-01T12:00:00'` |
| `exclude_defaults=True` | 기본값과 같은 필드 빼기 | `why='No idea'` 빠짐 |

> `exclude_unset`과 `exclude_defaults`의 차이: 기본값과 **같은 값을 직접 넣었을 때** `exclude_unset`은 남기고, `exclude_defaults`는 뺀다.

## 🔁 복습 질문

<details>
<summary>1. <code>User(name="Alice", age="25", ...)</code>처럼 age에 문자열을 넣으면 어떻게 되나?</summary>

오류가 아니라 `int` 25로 자동 변환된다. 숫자로 바꿀 수 없는 문자열(`"not an int"`)이면 `ValidationError`가 난다.
</details>

<details>
<summary>2. 나이를 0~150 사이로 제한하려면?</summary>

`age: int = Field(ge=0, le=150)`. `ge`는 "크거나 같다", `le`는 "작거나 같다".
</details>

<details>
<summary>3. 없어도 되는 필드는 어떻게 선언하나?</summary>

`nickname: str | None = None`. 기본값을 주지 않으면 `| None`이 있어도 필수 항목이 된다.
</details>

<details>
<summary>4. <code>model_dump()</code>와 <code>model_dump_json()</code>의 차이는?</summary>

`model_dump()`는 파이썬 dict를, `model_dump_json()`은 JSON 문자열을 돌려준다. dict에서 datetime까지 문자열로 받고 싶으면 `model_dump(mode='json')`.
</details>

<details>
<summary>5. 회원가입 함수에 Pydantic 모델을 쓰면 좋은 점은?</summary>

함수에 들어오기 전에 길이·나이 같은 규칙 검사가 끝나 있으므로, 함수 안에는 실제 처리(비즈니스 로직)만 쓰면 된다. FastAPI도 같은 방식으로 요청을 검증한다.
</details>
