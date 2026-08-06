# Logistic Regression for Pharmacy Analytics

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.7-orange)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Microsoft Fabric](https://img.shields.io/badge/Microsoft%20Fabric-ready-purple)

**Predicting high-cost Medicare Part D prescribers — and explaining (and testing) every coefficient.** A three-part tutorial that teaches logistic regression from a linear regression foundation, entirely on real CMS pharmacy claims data, with a graph at every step.

## Results

| Metric | Score |
|---|---|
| Accuracy | **84.8%** (vs. 74.9% do-nothing baseline) |
| ROC AUC | **0.879** |
| Top driver (found by the model) | brand-drug share — odds ratio ≈ **5.1×** per +1 SD (Wald z = 11.8, 95% CI [3.97×, 6.88×]) |
| Test set | 335 held-out providers (20% of a 2,040-provider pull) |

The model predicts whether a prescriber lands in the **top 25% of drug cost per claim without ever seeing cost** — it infers expensive prescribing from brand/generic mix, specialty, and patient panel characteristics. High cost-per-claim prescribing is dominated by brand and specialty drugs, so this is directly relevant wherever specialty pharmacy economics matter.

## What's inside

**Part 1 — Building the model** (assumes linear regression only)

- Why a straight line can't model a probability — shown, not told, on real data
- The sigmoid: keeping linear machinery, squashing the output into [0, 1]
- Real-data work: live download from the CMS API or bulk CSV (any row count up to all 1.4M), privacy-suppressed values, leakage-safe rate features, and an automatic guard against perfectly-predicting categories (separation)
- Evaluation graphs: confusion matrix, predicted-probability separation, ROC curve vs. baseline

**Part 2 — Understanding the coefficients**

- Odds vs. probability, and **log(odds)** — the scale where logistic regression *is* linear regression
- Coefficients as **log(odds ratios)**; exponentiating to odds ratios (charts on both scales)
- A worked example: each +1 SD of brand share multiplies the odds by 5.06 — the same multiplier every step — while probability jumps unevenly (19.9% → 55.8% → 86.5%), because the sigmoid is steep in the middle

**Part 3 — Statistical inference**

- Transforming the y-axis from probability to **log(odds)**: binned real data falls on the model's straight line, read exactly like a linear regression fit
- **Wald's test** computed by hand and via the full statsmodels regression table — z = coef/SE, p-values, and 95% confidence intervals plotted for every coefficient on both the log-odds and odds-ratio scales
- Why linear regression tests coefficients with **t** and logistic regression with **z**, plus the two-sample t-test's role in EDA vs. the Wald test's multivariable answer
- **Separation, shown not just mentioned:** why `converged: False` invalidates every standard error below it, and what a 394,000 standard error looks like when a category predicts the outcome perfectly

## Repository structure


```
logistic-regression-pharmacy/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── requirements.md
├── src/
│   └── logistic_regression_pharmacy.py            ← runnable script; saves all charts to ./charts/
├── notebooks/
│   ├── logistic_regression_pharmacy.ipynb         ← full tutorial, Parts 1–3, outputs included
│   └── logistic_regression_pharmacy_fabric.ipynb  ← Microsoft Fabric version (+ Lakehouse export)
└── docs/
    ├── Logistic Regression Tutorial.docx          ← concept tutorial with all graphs embedded
    ├── Fabric Setup Guide.md                      ← zero-to-running in Microsoft Fabric
    └── GitHub Setup Guide.md                      ← how this repo was set up
```

## Quick start (local)

```bash
git clone https://github.com/<username>/logistic-regression-pharmacy.git
cd logistic-regression-pharmacy
pip install -r requirements.txt
python src/logistic_regression_pharmacy.py
```

Or open [`notebooks/logistic_regression_pharmacy.ipynb`](notebooks/logistic_regression_pharmacy.ipynb) — the saved outputs and all 10 graphs are viewable right here on GitHub without running anything.

## Run in Microsoft Fabric

1. In a Fabric workspace, choose **Import → Notebook → From this computer**
2. Select [`notebooks/logistic_regression_pharmacy_fabric.ipynb`](notebooks/logistic_regression_pharmacy_fabric.ipynb)
3. Select **Run all** — `pandas`, `scikit-learn`, `matplotlib`, `requests`, `statsmodels`, and `scipy` are preinstalled, and the final cells show how to persist scored providers to a Lakehouse

New to Fabric? [`docs/Fabric Setup Guide.md`](docs/Fabric%20Setup%20Guide.md) covers everything from the free 60-day trial onward.

## Dataset

**Medicare Part D Prescribers — by Provider (2024 data year)** — Centers for Medicare & Medicaid Services (CMS). One row per prescribing provider: claims, drug cost, brand/generic mix, and beneficiary panel characteristics.

- Source: [data.cms.gov](https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/medicare-part-d-prescribers-by-provider) — public U.S. Government work, no API key required, refreshed annually
- **No data file is committed.** The code downloads live at run time; one setting controls how much:

  ```python
  DATA_ROWS = 2_040        # an integer, or "full" for all 1,416,883 providers
  ```

  Integers page the JSON API in seconds; `"full"` streams the complete 1.4M-provider bulk CSV in chunks (~2 GB). Everything downstream is size-agnostic.
- Known limitations (documented in the notebook): integer `DATA_ROWS` takes the first N providers by NPI rather than a random sample (use `"full"` to avoid this), privacy-suppressed small counts zero-filled, top-quartile label is a modeling choice, odds ratios describe association not causation

## License

Code is released under the [MIT License](LICENSE). The CMS dataset is a public U.S. Government work.
