"""Quick LLM connectivity test."""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from openai import OpenAI

API_KEY = (
    os.environ.get("OPENROUTER_API_KEY")
    or os.environ.get("RETROCAUSE_OPENROUTER_KEY")
    or ""
).strip()
MODEL = "deepseek/deepseek-chat-v3-0324"
BASE_URL = "https://openrouter.ai/api/v1"

if not API_KEY:
    raise SystemExit("Set OPENROUTER_API_KEY or RETROCAUSE_OPENROUTER_KEY before running.")

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
