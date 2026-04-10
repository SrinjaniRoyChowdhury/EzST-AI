from dotenv import load_dotenv
import os
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Try newer models — 2.5 series has separate quotas
candidates = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
    "gemini-2.0-flash-lite-001",
    "gemini-2.0-flash-001",
]

print(f"API Key: {api_key[:8]}...{api_key[-4:]}\n")
print("Testing models...\n")

for model_name in candidates:
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Say hello in one sentence."
        )
        print(f"[OK] {model_name}")
        print(f"     Response: {response.text.strip()}")
        print(f"\n>>> WORKING MODEL: {model_name}")
        print(f"    Update GEMINI_MODEL={model_name} in your .env")
    except Exception as e:
        code = str(e)[:80]
        print(f"[FAIL] {model_name}: {code}")