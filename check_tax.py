"""Quick tax judge-case assertion script."""
import sys
sys.path.insert(0, r'D:\AI advisor Backend')

from engine.tax import calculate_tax, TaxRegime

results = []

# Case 1: 12L gross → 0 tax
r = calculate_tax(1_200_000, TaxRegime.NEW)
results.append(f"Case1: 12L gross | taxable={r.taxable_income} | tax={r.total_tax} | {'PASS' if r.total_tax == 0 else 'FAIL'}")

# Case 2: 12.75L gross → 0 tax
r = calculate_tax(1_275_000, TaxRegime.NEW)
results.append(f"Case2: 12.75L gross | taxable={r.taxable_income} | tax={r.total_tax} | {'PASS' if r.total_tax == 0 else 'FAIL'}")

# Case 3: 15L gross → 97,500
r = calculate_tax(1_500_000, TaxRegime.NEW)
results.append(f"Case3: 15L gross | taxable={r.taxable_income} | tax={r.total_tax} | {'PASS' if r.total_tax == 97_500 else 'FAIL'}")

# Case 4: 10L old regime → 1,06,600
r = calculate_tax(1_000_000, TaxRegime.OLD)
results.append(f"Case4: 10L old | taxable={r.taxable_income} | tax={r.total_tax} | {'PASS' if r.total_tax == 106_600 else 'FAIL'}")

for line in results:
    print(line)
