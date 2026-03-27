"""Quick inline e2e checks — writes results to e2e_results.txt"""
import httpx, json, sys

BASE = "http://localhost:8000"
results = []

def post(path, body):
    try:
        return httpx.post(f"{BASE}{path}", json=body, timeout=30)
    except Exception as e:
        return None

def chk(name, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {name}" + (f" | {detail}" if detail else "")
    results.append(line)

# 1. Health
r = httpx.get(f"{BASE}/health", timeout=10)
chk("GET /health 200", r.status_code == 200)
chk("/health status:ok", r.json().get("status") == "ok")

# 2. Tax judge cases
r = post("/api/v1/calculate/tax/compare", {"gross_income": 1275000, "deductions": {"sec80c": 0}})
chk("POST /tax/compare 200", r and r.status_code == 200, r and r.text[:80])
if r and r.status_code == 200:
    new = r.json().get("new_regime", {})
    chk("12.75L new regime tax=0", new.get("total_tax") == 0.0, str(new.get("total_tax")))
    chk("recommended key exists", "recommended" in r.json(), str(r.json().keys()))

r = post("/api/v1/calculate/tax/compare", {"gross_income": 1500000, "deductions": {"sec80c": 0}})
if r and r.status_code == 200:
    new = r.json().get("new_regime", {})
    chk("15L new regime tax=97500", new.get("total_tax") == 97500, str(new.get("total_tax")))

# 3. SIP
r = post("/api/v1/calculate/sip", {"monthly_investment": 10000, "annual_return_pct": 12, "tenure_years": 10})
chk("POST /sip 200", r and r.status_code == 200)
if r: chk("/sip maturity_amount", "maturity_amount" in r.json())

# 4. FIRE
r = post("/api/v1/calculate/fire", {"annual_expenses": 600000, "inflation_pct": 6, "expected_return_pct": 12, "safe_withdrawal_rate": 4, "current_corpus": 0})
chk("POST /fire 200", r and r.status_code == 200)
if r: chk("/fire fire_number", "fire_number" in r.json(), str(r.json().get("fire_number")))

# 5. Health 6-dim
r = post("/api/v1/calculate/health", {
    "monthly_income": 100000, "monthly_expenses": 60000,
    "emergency_fund": 360000, "monthly_fixed_expenses": 60000,
    "total_emi": 15000, "life_cover": 12000000, "health_cover": 1000000,
    "equity_investments": 500000, "debt_investments": 200000,
    "age": 30, "gross_income": 1200000, "sec80c_used": 100000,
    "nps_used": 50000, "has_elss": True, "monthly_sip": 10000, "current_corpus": 1200000
})
chk("POST /health 200", r and r.status_code == 200, r and r.text[:120])
if r and r.status_code == 200:
    body = r.json()
    dims = body.get("dimensions", [])
    chk("/health 6 dimensions", len(dims) == 6, f"got {len(dims)}: {[d.get('name') for d in dims]}")
    chk("/health overall_score", "overall_score" in body, str(body.get("overall_score")))
    chk("/health grade", "grade" in body, str(body.get("grade")))
    for exp in ["emergency_fund","insurance","debt","investment_diversification","tax_efficiency","retirement_readiness"]:
        chk(f"  dim:{exp}", exp in {d["name"] for d in dims})

# 6. XIRR
r = post("/api/v1/calculate/portfolio/xirr", {"transactions": [{"date":"2023-01-01","amount":-100000},{"date":"2024-01-01","amount":112000}]})
chk("POST /portfolio/xirr 200", r and r.status_code == 200)
if r and r.status_code == 200: chk("/xirr ~12%", abs(r.json().get("xirr_pct",0)-12) < 0.5, str(r.json().get("xirr_pct")))

# 7. Advisor extract
r = post("/api/v1/advisor/extract", {"text": "I am 28 years old, earning 15 lakhs per year, spending 60 thousand a month, want to retire at 50"})
chk("POST /advisor/extract 200", r and r.status_code == 200)
if r and r.status_code == 200:
    ex = r.json()
    chk("extract age=28", ex.get("age") == 28, str(ex.get("age")))
    chk("extract retirement_age=50", ex.get("retirement_age") == 50, str(ex.get("retirement_age")))

# 8. Advisor context
r = post("/api/v1/advisor/context", {"profile": {"age": 28, "monthly_income": 125000}, "calculated_results": {}})
chk("POST /advisor/context 200", r and r.status_code == 200)
if r: chk("context non-empty", len(r.json().get("context","")) > 50)

# 9. Advisor explain
r = post("/api/v1/advisor/explain", {"insight_type": "xirr", "data": {"xirr_pct": 11.3, "benchmark_pct": 13.8}, "user_age": 28, "user_income": 1500000})
chk("POST /advisor/explain 200", r and r.status_code == 200)
if r: chk("explain non-empty", len(r.json().get("explanation","")) > 20, str(len(r.json().get("explanation",""))))

# 10. Advisor chat
r = post("/api/v1/advisor/chat", {"message": "Should I invest in ELSS or NPS?", "user_context": "Age:28, Income: 1.25L/mo", "conversation_history": []})
chk("POST /advisor/chat 200", r and r.status_code == 200)
if r: chk("chat reply non-empty", len(r.json().get("response","")) > 20)

# 11. Docs live
r = httpx.get(f"{BASE}/docs", timeout=10)
chk("GET /docs 200 (Swagger)", r.status_code == 200)

# Write results
passed = [x for x in results if x.startswith("[PASS]")]
failed = [x for x in results if x.startswith("[FAIL]")]
with open("e2e_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))
    f.write(f"\n\nSUMMARY: {len(passed)} passed, {len(failed)} failed\n")
    if failed:
        f.write("\nFAILED:\n")
        for ff in failed:
            f.write(f"  {ff}\n")

print(f"Done. {len(passed)} passed, {len(failed)} failed. See e2e_results.txt")
