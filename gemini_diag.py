"""Diagnose Gemini extract — writes raw API response to gemini_diag.txt"""
from dotenv import load_dotenv
import os, json

load_dotenv(r'D:\AI advisor Backend\.env')

key = os.environ.get('GEMINI_API_KEY', '')

out = []
out.append(f"Key present: {'YES len=' + str(len(key)) if key else 'NO'}")

try:
    import google.generativeai as genai
    genai.configure(api_key=key)

    # Test 1: Simple JSON extraction
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config={'max_output_tokens': 512, 'temperature': 0.1}
    )
    prompt = (
        'Return ONLY valid JSON with no explanation, no markdown.\n'
        'Extract: age (number), monthly_income (number in rupees), retirement_age (number).\n'
        'Use null if not mentioned.\n'
        'User text: I am 28 years old, earning 1.25 lakh per month, want to retire at 50'
    )
    resp = model.generate_content(prompt)
    raw = resp.text if resp.text else "<EMPTY RESPONSE>"
    out.append(f"RAW RESPONSE (len={len(raw)}):\n{raw}")

    # Try to parse
    try:
        cleaned = raw.strip().strip('`').strip()
        if cleaned.startswith('json'):
            cleaned = cleaned[4:].strip()
        parsed = json.loads(cleaned)
        out.append(f"PARSED OK: {parsed}")
    except Exception as e:
        out.append(f"PARSE FAILED: {e}")

except Exception as e:
    out.append(f"ERROR: {e}")

result = '\n'.join(out)
print(result)
with open(r'D:\AI advisor Backend\gemini_diag.txt', 'w', encoding='utf-8') as f:
    f.write(result)
