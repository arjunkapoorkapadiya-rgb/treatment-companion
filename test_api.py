import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("ERROR: GROQ_API_KEY not set in .env")
    exit(1)

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
body = {
    "model": "openai/gpt-oss-120b",
    "messages": [
        {"role": "user", "content": "Say hello in one word."}
    ],
}

print("Calling Groq API...")
response = requests.post(url, headers=headers, json=body)
print("Status:", response.status_code)

if response.status_code == 200:
    data = response.json()
    print("Response:", data["choices"][0]["message"]["content"])
else:
    print("Error:", response.text)