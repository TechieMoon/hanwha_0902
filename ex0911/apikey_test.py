import os
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6-luna",
    input="안녕하세요라고 한마디만 해줘."
)

print(response.output_text)