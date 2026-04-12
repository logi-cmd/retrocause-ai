"""Quick LLM connectivity test."""

import sys

sys.stdout.reconfigure(encoding="utf-8")

from openai import OpenAI

API_KEY = "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"
MODEL = "deepseek/deepseek-chat-v3-0324"
BASE_URL = "https://openrouter.ai/api/v1"

print(f"Testing LLM: {MODEL} via {BASE_URL}")

try:
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": 'Respond with JSON: {"status":"ok"}'}],
        max_tokens=50,
    )
    print(f"SUCCESS: {resp.choices[0].message.content}")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
