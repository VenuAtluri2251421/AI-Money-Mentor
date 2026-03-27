"""Test which model actually works and can extract JSON"""
from dotenv import load_dotenv
import os, json

load_dotenv(r'D:\AI advisor Backend\.env')

import google.generativeai as genai
genai.configure(api_key=os.environ['GEMINI_API_KEY'])

# List all available models
print("=== AVAILABLE MODELS ===")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)

# Try extraction with different model names
test_models = ['gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-2.5-flash']
prompt = 'Return ONLY this JSON, no text: {"age": 28, "monthly_income": 125000, "retirement_age": 50}. Confirm by returning that exact JSON.'

print("\n=== MODEL TESTS ===")
for model_name in test_models:
    try:
        m = genai.GenerativeModel(model_name, generation_config={'max_output_tokens': 100, 'temperature': 0})
        r = m.generate_content(prompt)
        print(f"{model_name}: OK -> {r.text[:80]}")
    except Exception as e:
        print(f"{model_name}: FAIL -> {str(e)[:80]}")
