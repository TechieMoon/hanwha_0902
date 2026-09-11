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

윈도우의 환경변수에 들어가서 변수명은 `OPENAI_API_KEY` 변수 값은 OpenAI Platform에서 발급 받은 api key로 넣는다.

OpenAI 라이브러리가 `OPENAI_API_KEY` 변수명을 알아서 찾기 때문에 코드에서 api key를 입력할 필요가 없다.