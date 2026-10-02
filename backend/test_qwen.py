import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

print("Token loaded:", HF_TOKEN is not None)

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b:fastest",
    messages=[
        {
            "role": "user",
            "content": "Explain artificial intelligence in one simple sentence."
        }
    ]
)

print("\nHugging Face Response:")
print(response.choices[0].message.content)