## OpenAI API key 테스트

```python
import os
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6-luna",
    input="안녕하세요라고 한마디만 해줘."
)

print(response.output_text)
```

윈도우의 환경변수에 들어가서 변수명은 `OPENAI_API_KEY`로 넣고, 변수 값은 OpenAI Platform에서 발급 받은 api key로 넣는다.

OpenAI 라이브러리가 `OPENAI_API_KEY` 변수명을 알아서 찾기 때문에 코드에서 api key를 입력할 필요가 없다.

`.env`로도 가능하다.

`.env.에 다음과 같이 저장한다.

```env
OPENAI_API_KEY=sk-*****************************
```

코드 상단에 다음 내용을 추가한다.

```python
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
```

그러면 운영체제 환경변수처럼 똑같이 작동한다.