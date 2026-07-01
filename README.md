# Medicare Billing & Cost Efficiency Analysis

Analyzing 9.7M CMS Medicare records to identify regional pricing disparities, billing anomalies, and provider efficiency gaps across U.S. healthcare providers.

Built as a portfolio project targeting U.S. finance/consulting rotational programs.

---

## Dashboard
[View the live interactive dashboard on Tableau Public](https://public.tableau.com/app/profile/claire.kodama/viz/MedicareBillingCostEfficiencyAnalysis/Dashboard1)

---

## Tools & Stack
- **SQL / DuckDB** — data cleaning, filtering, aggregation (9.7M → 777K rows)
- **Excel** — pivot analysis and insight development
- **Tableau Public** — interactive dashboard (5 views)

## Data Source
CMS Medicare Physician & Other Practitioners Dataset, 2024
https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners

## Focus Procedures
| Code | Description | National Volume |
|------|-------------|----------------|
| 99214 | Office visit, moderate complexity | 102M services |
| 99213 | Office visit, low complexity | 68M services |
| 97110 | Physical therapy exercise | 63M services |
| 36415 | Blood draw | 40M services |

---

## Key Findings

**Finding 1 — Billing Anomaly Concentration**
Billing anomalies cluster in five states (OH, CA, NY, NJ, FL) accounting for 77% of all flagged cases nationally, driven disproportionately by Nurse Practitioners and Physical Therapists in Private Practice. In Ohio specifically, these two provider types account for 48% of the state's anomaly cases.

**Finding 2 — Regional Cost Variation**
Office visit reimbursements vary 43% across states ($91.41 in Maine to $130.45 in Alaska), largely tracking CMS geographic adjustment factors. The notable exception is Ohio — below-average per-visit costs ($96.79) combined with the highest national anomaly volume suggests a billing integrity issue independent of pricing.

**Finding 3 — Provider Efficiency Paradox**
Non-physician practitioners (NPs, PAs) bill 8% below state benchmarks on average — yet drive the largest share of flagged anomaly cases. This bimodal pattern reinforces targeted audit prioritization over broad specialty review.

---

## Executive Summary
This analysis examined 9.7 million Medicare claims across four high-volume procedures to identify cost inefficiencies and billing risk. Billing anomalies concentrate geographically (five states account for 77% of cases) and by provider type (NPs and PTs lead anomaly counts despite billing conservatively on average). Regional cost variation is largely structural and predictable, with Ohio as a notable exception. Recommendation: prioritize audit resources by state (starting with Ohio) and provider type (NP/PT) to efficiently surface high-risk outliers.

---

## Repository Structure
- /sql — DuckDB queries and Python scripts
- /output — Exported summary datasets (full 238MB dataset excluded via .gitignore)

## Project Status
- [x] Phase 1: Data extraction and SQL cleaning
- [x] Phase 2: Excel pivot analysis and insight development
- [x] Phase 3: Tableau Public dashboard
