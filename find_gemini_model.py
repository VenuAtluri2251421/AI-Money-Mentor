"""
Find which Gemini 2.5 Pro model name works with this API key.
Run this standalone: python find_gemini_model.py
"""
from dotenv import load_dotenv
import os, json

load_dotenv(r'D:\AI advisor Backend\.env')

import google.generativeai as genai
genai.configure(api_key=os.environ['GEMINI_API_KEY'])

# Collect all available models
all_models = [
    m.name for m in genai.list_models()
    if 'generateContent' in m.supported_generation_methods
]

candidates_25 = [m for m in all_models if '2.5' in m]
candidates_20 = [m for m in all_models if '2.0' in m]

print("=== Gemini 2.5 models ===")
for m in candidates_25:
    print(" ", m)
print("\n=== Gemini 2.0 models ===")
for m in candidates_20:
    print(" ", m)

# Quick test — find first working 2.5-pro variant
test_prompt = 'Say only: WORKING'
best_model = None

for candidate in candidates_25:
    if 'pro' in candidate.lower() or 'flash' in candidate.lower():
        # Strip 'models/' prefix for GenerativeModel call
        short = candidate.replace('models/', '')
        try:
            m = genai.GenerativeModel(short, generation_config={'max_output_tokens': 10, 'temperature': 0})
            resp = m.generate_content(test_prompt)
            print(f"\n[PASS] {short} -> {resp.text.strip()[:30]}")
            if best_model is None:
                best_model = short
        except Exception as e:
            print(f"\n[FAIL] {short}: {str(e)[:60]}")

# Fallback: test gemini-2.0-flash which we know works
if best_model is None:
    try:
        m = genai.GenerativeModel('gemini-2.0-flash', generation_config={'max_output_tokens':10,'temperature':0})
        resp = m.generate_content(test_prompt)
        best_model = 'gemini-2.0-flash'
        print(f"\n[FALLBACK] gemini-2.0-flash: {resp.text.strip()[:30]}")
    except Exception as e:
        print(f"[FAIL] gemini-2.0-flash: {e}")

print(f"\n>>> Best model for .env: {best_model}")

# Write result to a file for easy reference
with open(r'D:\AI advisor Backend\best_model.txt', 'w') as f:
    f.write(best_model or 'gemini-2.0-flash')
