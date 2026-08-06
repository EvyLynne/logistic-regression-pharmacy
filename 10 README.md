# Logistic Regression for Pharmacy Analytics: A Supervised Machine Learning Tutorial

## Overview

- This project teaches **logistic regression** to someone who understands **linear regression** but has never seen classification — built entirely on a real pharmacy dataset (CMS Medicare Part D prescriber claims).
- **The task:** predict whether a prescriber lands in the top 25% of drug cost per claim — *without* letting the model see cost. The model infers expensive prescribing from the prescribing mix: brand/generic share, specialty, patient panel characteristics.
- **Part 1** builds the model with a graph at every step: why a straight line fails for yes/no outcomes, the sigmoid, leakage-safe feature engineering, and evaluation (confusion matrix, probability separation, ROC curve).
- **Part 2** interprets the model: odds, **log(odds)** as the scale where logistic regression is linear, coefficients as **log(odds ratios)**, and odds ratios — with a worked end-to-end example.
- **Part 3** covers statistical inference: transforming the y-axis to log(odds) so the S-curve becomes a straight fitted line, **Wald's test** with p-values and confidence intervals (via statsmodels), and how the **t-test** from linear regression relates (and where it still applies in EDA).
- **Results:** 84.8% accuracy vs. a 74.9% do-nothing baseline; ROC AUC 0.879. Top driver discovered by the model: brand-drug share (odds ratio ≈ 5.1× per +1 SD, Wald z = 11.8, 95% CI [3.97×, 6.88×]).

## The big idea (one paragraph)

Linear regression fits `y = b0 + b1x1 + … + bnxn` to predict a number. For a yes/no outcome that line predicts impossible "probabilities" above 1 and below 0. Logistic regression keeps the identical linear machinery but squashes its output through the sigmoid, `p = 1/(1+e^(−z))`, so predictions are always valid probabilities. Equivalently: **logistic regression is linear regression on the log(odds) scale** — which is also what makes its coefficients interpretable as odds ratios.

## Dataset source

- **Name:** Medicare Part D Prescribers — by Provider (2024 data year)
- **Publisher:** Centers for Medicare & Medicaid Services (CMS); public U.S. Government work, refreshed annually
- **Contents:** one row per prescribing provider (NPI): claims, drug cost, brand/generic mix, opioid counts, beneficiary panel demographics
- **Access:** [data.cms.gov](https://data.cms.gov/provider-summary-by-type-of-service/medicare-part-d-prescribers/medicare-part-d-prescribers-by-provider) — **downloaded live from the internet by the code**, no API key, and **no data file to manage**
- **Size:** 1,416,883 providers in the full release

### How much data you pull is one setting

Every script and notebook opens with:

```python
DATA_ROWS = 2_040        # an integer, or "full" for all 1,416,883 providers
```

| Value | What you get | Route | Time |
|---|---|---|---|
| an integer | that many providers, in NPI order | JSON data API, paged | seconds |
| `"full"` | the complete release, all 1.4M providers | bulk CSV, streamed in chunks | ~5–15 min (≈2 GB) |

Everything after the download is **size-agnostic** — identical code trains on 2,000 rows or 1,400,000. Saved notebook outputs correspond to the value shown above; change it and *Run all* to recompute. On the full dataset the Wald confidence intervals in Part 3 tighten dramatically, since standard errors shrink with the square root of sample size.

## Files in this folder, numbered in order of usage

- `10 README.md` — this file: start here for orientation.
- `20 Logistic Regression Tutorial.docx` — the concept tutorial with all graphs embedded: linear→logistic bridge, sigmoid, case study results, log(odds), odds ratios, and Wald's test.
- `30 logistic_regression_pharmacy.py` — runnable script; prints all results and saves every graph to `./charts/`.
- `40 logistic_regression_pharmacy.ipynb` — the full interactive tutorial (Parts 1–3, 10 graphs, outputs included).
- `50 Fabric Setup Guide.docx` / `.md` — zero-to-running instructions for Microsoft Fabric (same guide, two formats).
- `60 logistic_regression_pharmacy_fabric.ipynb` — Fabric-ready notebook with the same graphs, plus Lakehouse export cells.
- `70 GitHub Setup Guide.docx` / `.md` — publish this project as a GitHub portfolio repo.
- `80 GitHub README.md` — ready-made repo homepage: paste its contents into the repo's `README.md` when publishing.

There is no data file in this folder by design — the data arrives over the internet at run time.

## Setup (local)

```bash
pip install scikit-learn pandas matplotlib requests statsmodels scipy

python "30 logistic_regression_pharmacy.py"           # default row count
python "30 logistic_regression_pharmacy.py" 50000     # 50,000 providers
python "30 logistic_regression_pharmacy.py" full      # all 1,416,883
```

The script needs an internet connection and saves every graph to `./charts/`. Or open `40 logistic_regression_pharmacy.ipynb` in Jupyter. For Microsoft Fabric, follow guide 50 and import notebook 60.

## Key evaluation concepts

- **Baseline first:** with 75% of providers "typical," 75% accuracy is free — a model must beat it.
- **Confusion matrix:** separates false positives from false negatives, which have different business costs.
- **ROC AUC:** ranking quality across all thresholds (1.0 = perfect, 0.5 = coin flip).
- **Odds ratio:** e^coefficient — the multiplier applied to the odds per one-unit feature increase; 1 = no effect.
- **Wald's test:** z = coefficient / standard error, compared to the standard normal; |z| > 1.96 ⇔ p < 0.05 ⇔ the odds-ratio CI excludes 1.

## Common pitfalls the project demonstrates

- **Data leakage:** drug cost defines the label, so it must not be a feature; scalers are fit on training data only.
- **Separation:** a category that perfectly predicts the outcome sends its coefficient to infinity and breaks the Wald standard errors — the code detects and merges those groups, and Part 3 shows what the broken output looks like.
- **Class imbalance:** accuracy alone misleads; compare to the baseline.
- **The 0.5 threshold is a choice:** tune it to your error costs.
- **Odds ratios are associations, not causes** — and p-values inherit every sampling caveat.

## Where to go next

- Set `DATA_ROWS = "full"` and re-run on all 1.4M providers.
- Add geography features (state, urban/rural), or try the likelihood-ratio test — more robust than Wald for small samples.
- Compare with `RandomForestClassifier` or gradient boosting on the same features.
