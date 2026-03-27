"""
Final end-to-end endpoint verification script.
Run while the server is live on port 8000.
"""
import json
import sys
import httpx

BASE = "http://localhost:8000"
PASS = []
FAIL = []


def check(name: str, ok: bool, detail: str = ""):
    if ok:
        PASS.append(name)
        print(f"  ✅ {name}")
    else:
        FAIL.append(name)
        print(f"  ❌ {name}" + (f" — {detail}" if detail else ""))


def post(path, body):
    r = httpx.post(f"{BASE}{path}", json=body, timeout=30)
    return r


# ── 1. Health check ───────────────────────────────────────────────────────────
print("\n[1] Server health")
r = httpx.get(f"{BASE}/health", timeout=10)
check("GET /health → 200", r.status_code == 200)
check("/health returns status:ok", r.json().get("status") == "ok")

# ── 2. Tax — Judge case ───────────────────────────────────────────────────────
print("\n[2] Tax — 87A rebate judge cases")
r = post("/api/v1/calculate/tax/compare", {"gross_income": 1275000, "deductions": {"sec80c": 0}})
check("POST /tax/compare → 200", r.status_code == 200)
new_tax = r.json().get("new_regime", {}).get("total_tax", -1)
check("₹12.75L → new regime tax = 0", new_tax == 0.0, f"got {new_tax}")

r2 = post("/api/v1/calculate/tax/compare", {"gross_income": 1500000, "deductions": {"sec80c": 150000}})
new_tax2 = r2.json().get("new_regime", {}).get("total_tax", -1)
check("₹15L → new regime tax > 0", new_tax2 > 0, f"got {new_tax2}")

# ── 3. SIP ────────────────────────────────────────────────────────────────────
print("\n[3] SIP calculator")
r = post("/api/v1/calculate/sip", {"monthly_investment": 10000, "annual_return_pct": 12, "tenure_years": 10})
check("POST /sip → 200", r.status_code == 200)
check("/sip has maturity_amount", "maturity_amount" in r.json())

# ── 4. FIRE ───────────────────────────────────────────────────────────────────
print("\n[4] FIRE calculator")
r = post("/api/v1/calculate/fire", {"annual_expenses": 600000, "inflation_pct": 6, "expected_return_pct": 12, "safe_withdrawal_rate": 4, "current_corpus": 500000, "years_to_retirement": 20})
check("POST /fire → 200", r.status_code == 200)
check("/fire has fire_number", "fire_number" in r.json())

# ── 5. Health Score — 6 dimensions ───────────────────────────────────────────
print("\n[5] Health Score — 6 dimensions")
r = post("/api/v1/calculate/health", {
    "monthly_income": 100000, "monthly_expenses": 60000,
    "emergency_fund": 360000, "monthly_fixed_expenses": 60000,
    "total_emi": 15000, "life_cover": 12000000, "health_cover": 1000000,
    "equity_investments": 500000, "debt_investments": 200000, "gold_investments": 50000,
    "age": 30, "gross_income": 1200000, "sec80c_used": 100000,
    "nps_used": 50000, "has_elss": True, "monthly_sip": 10000, "current_corpus": 1200000
})
check("POST /health → 200", r.status_code == 200)
body = r.json()
check("/health has overall_score", "overall_score" in body, str(body.get("overall_score")))
check("/health has grade", "grade" in body)
dims = body.get("dimensions", [])
check("/health returns 6 dimensions", len(dims) == 6, f"got {len(dims)}")
dim_names = {d["name"] for d in dims}
for expected in ["emergency_fund", "insurance", "debt", "investment_diversification", "tax_efficiency", "retirement_readiness"]:
    check(f"  dimension: {expected}", expected in dim_names)

# ── 6. XIRR ───────────────────────────────────────────────────────────────────
print("\n[6] Portfolio XIRR")
r = post("/api/v1/calculate/portfolio/xirr", {
    "transactions": [
        {"date": "2023-01-01", "amount": -100000},
        {"date": "2024-01-01", "amount": 112000}
    ]
})
check("POST /portfolio/xirr → 200", r.status_code == 200)
check("/portfolio/xirr has xirr_pct", "xirr_pct" in r.json())

# ── 7. Advisor — extract ──────────────────────────────────────────────────────
print("\n[7] Advisor — extract profile")
r = post("/api/v1/advisor/extract", {
    "text": "I am 28, earning 15 lakhs per year, spending 60k a month, have 2L savings, want to retire at 50"
})
check("POST /advisor/extract → 200", r.status_code == 200)
extracted = r.json()
check("extracted age == 28", extracted.get("age") == 28, f"got {extracted.get('age')}")
check("extracted retirement_age == 50", extracted.get("retirement_age") == 50, f"got {extracted.get('retirement_age')}")

# ── 8. Advisor — context ──────────────────────────────────────────────────────
print("\n[8] Advisor — build context")
r = post("/api/v1/advisor/context", {
    "profile": {"age": 28, "monthly_income": 125000, "monthly_expenses": 60000},
    "calculated_results": {}
})
check("POST /advisor/context → 200", r.status_code == 200)
check("/advisor/context has context string", "context" in r.json())

# ── 9. Advisor — explain ─────────────────────────────────────────────────────
print("\n[9] Advisor — explain insight")
r = post("/api/v1/advisor/explain", {
    "insight_type": "xirr",
    "data": {"xirr_pct": 11.3, "benchmark_pct": 13.8, "invested_amount": 100000},
    "user_age": 28,
    "user_income": 1500000
})
check("POST /advisor/explain → 200", r.status_code == 200)
expl = r.json().get("explanation", "")
check("/advisor/explain returns non-empty text", len(expl) > 20, f"len={len(expl)}")

# ── 10. Advisor — chat ───────────────────────────────────────────────────────
print("\n[10] Advisor — chat")
r = post("/api/v1/advisor/chat", {
    "message": "Should I invest in ELSS or NPS for tax saving?",
    "user_context": "Age: 28, Monthly Income: ₹1.25 L",
    "conversation_history": []
})
check("POST /advisor/chat → 200", r.status_code == 200)
reply = r.json().get("response", "")
check("/advisor/chat returns non-empty reply", len(reply) > 20, f"len={len(reply)}")

# ── CORS check ────────────────────────────────────────────────────────────────
print("\n[11] CORS headers")
r = httpx.options(f"{BASE}/api/v1/calculate/tax/compare",
                  headers={"Origin": "http://localhost:5173",
                           "Access-Control-Request-Method": "POST"}, timeout=10)
cors = r.headers.get("access-control-allow-origin", "")
check("CORS allows localhost:5173", "5173" in cors or cors == "*", f"header={cors}")

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  PASSED: {len(PASS)}")
print(f"  FAILED: {len(FAIL)}")
if FAIL:
    print(f"\n  Failed checks:")
    for f in FAIL:
        print(f"    ✗ {f}")
sys.exit(0 if not FAIL else 1)
