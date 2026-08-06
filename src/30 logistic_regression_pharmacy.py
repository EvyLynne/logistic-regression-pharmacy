"""
Logistic Regression for Pharmacy Analytics
==========================================

Predicts whether a Medicare Part D prescriber lands in the top 25% of drug
cost per claim -- without letting the model see cost. Companion script to
"40 logistic_regression_pharmacy.ipynb"; saves all graphs to ./charts/.

Assumes you know linear regression; logistic regression is introduced as
"linear regression squashed through the sigmoid" (Part 1), interpreted via
log(odds) and odds ratios (Part 2), and tested with Wald's test, p-values,
and confidence intervals -- including the log-odds y-axis transformation
that turns the S-curve into a straight fitted line (Part 3).

Suppressed values (blank counts of 1-10) are imputed as 5 following CMS's
published methodology; see the note at STEP 2 and "90 CMS Documentation
References.xlsx" for the source documents.

Dataset source:
    Medicare Part D Prescribers - by Provider (2024 data year)
    Centers for Medicare & Medicaid Services (CMS), public U.S. Government
    work, refreshed annually. Downloaded live over the internet at run time
    (no API key, no local data file):
    https://data.cms.gov/provider-summary-by-type-of-service/
        medicare-part-d-prescribers/medicare-part-d-prescribers-by-provider

Requirements:
    pip install scikit-learn pandas matplotlib requests statsmodels scipy

Run:
    python "30 logistic_regression_pharmacy.py"              # default row count
    python "30 logistic_regression_pharmacy.py" 50000        # 50,000 providers
    python "30 logistic_regression_pharmacy.py" full         # all 1,416,883
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import matplotlib
matplotlib.use("Agg")           # save charts to files; no display needed
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, roc_auc_score, roc_curve,
                             confusion_matrix, classification_report)

CHARTS = Path("charts")
CHARTS.mkdir(exist_ok=True)

def save(fig, name):
    fig.tight_layout()
    fig.savefig(CHARTS / name, dpi=130)
    plt.close(fig)
    print(f"  [chart saved: charts/{name}]")

# ---------------------------------------------------------------
# PART 1, STEP 1 -- Download live from CMS
# ---------------------------------------------------------------
# DATA_ROWS: an integer (first N providers via the JSON API, seconds) or
# "full" (all 1,416,883 providers streamed from the bulk CSV, ~2 GB).
DATA_ROWS = 2_040
MIN_CLAIMS = 50

# Optional command-line override: `python <script> full` or `python <script> 50000`.
# Anything unrecognized is ignored, so pasting this into a Jupyter/Fabric notebook
# is safe -- kernels put their own arguments (like "-f kernel.json") in sys.argv.
_arg = sys.argv[1].strip().lower() if len(sys.argv) > 1 else ""
if _arg == "full":
    DATA_ROWS = "full"
elif _arg.replace("_", "").replace(",", "").isdigit():
    DATA_ROWS = int(_arg.replace("_", "").replace(",", ""))

DATASET_ID = "14d8e8a9-7e9b-4370-a044-bf97c46b4b44"
API_URL = f"https://data.cms.gov/data-api/v1/dataset/{DATASET_ID}/data"
BULK_CSV_URL = ("https://data.cms.gov/sites/default/files/2026-05/"
                "e9cd7dfb-9c27-4b3f-8f5d-2454091303ee/MUP_DPR_RY26_P04_V10_DY24_NPI.csv")
COLS = ["Prscrbr_Type", "Tot_Clms", "Tot_Drug_Cst", "Brnd_Tot_Clms", "Gnrc_Tot_Clms",
        "LIS_Tot_Clms", "Opioid_Tot_Clms", "Bene_Avg_Age", "Bene_Avg_Risk_Scre",
        "Bene_Dual_Cnt"]
NUMERIC = [c for c in COLS if c != "Prscrbr_Type"]


def _to_numeric(frame):
    """Every CMS value arrives as text; make the numeric columns numeric."""
    for c in NUMERIC:
        frame[c] = pd.to_numeric(frame[c], errors="coerce")
    return frame


def load_partd(n_rows=DATA_ROWS, page=5_000, chunk=250_000, verbose=True):
    """Download Medicare Part D prescriber data live from data.cms.gov."""
    if n_rows == "full":
        # Bulk CSV: stream in chunks so the raw 2 GB file never sits in memory.
        header = pd.read_csv(BULK_CSV_URL, nrows=0)
        actual = {c.lower(): c for c in header.columns}   # CMS varies capitalization
        usecols = [actual[c.lower()] for c in COLS]
        parts, seen = [], 0
        for piece in pd.read_csv(BULK_CSV_URL, usecols=usecols, dtype=str,
                                 chunksize=chunk, low_memory=False):
            piece = piece.rename(columns=dict(zip(usecols, COLS)))
            parts.append(_to_numeric(piece))
            seen += len(piece)
            if verbose:
                print(f"  streamed {seen:,} rows", end="\r")
        frame = pd.concat(parts, ignore_index=True)
    else:
        # JSON API: page through the first n_rows records.
        records, offset = [], 0
        while offset < n_rows:
            resp = requests.get(API_URL, timeout=120, params={
                "size": min(page, n_rows - offset), "offset": offset,
                "column": ",".join(COLS)})
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break                                # ran past the end of the data
            records.extend(batch)
            offset += len(batch)
            if verbose:
                print(f"  downloaded {offset:,} rows", end="\r")
        # reindex: the API returns all columns when the request is long, so select ours
        frame = _to_numeric(pd.DataFrame(records).reindex(columns=COLS))
    if verbose:
        print(" " * 40, end="\r")
    return frame


print("=" * 62)
print("PART 1 -- BUILDING THE MODEL")
print("=" * 62)
print(f"Step 1: downloading live from data.cms.gov (DATA_ROWS = {DATA_ROWS!r}) ...")
raw = load_partd()
print(f"        {len(raw):,} providers x {raw.shape[1]} columns")

# ---------------------------------------------------------------
# STEP 2 -- Clean (impute suppressed counts; drop tiny practices)
# ---------------------------------------------------------------
# A blank count is a SUPPRESSED value, not a zero: CMS hides counts of 1-10 to
# protect beneficiary privacy (true zeros are written as "0"). Their methodology
# warns that letting software read blanks as zeros "will result in ... under-
# estimates of the true values," and suggests imputing a value such as five --
# the midpoint of the suppressed range. We follow that recommendation.
#   Methodology, section "Data Redaction and Suppression":
#   https://data.cms.gov/sites/default/files/2023-05/MUP_DPR_RY23_20230424_Methodology_508.pdf
SUPPRESSED_IMPUTE = 5

df = raw.copy()
count_cols = ["Brnd_Tot_Clms", "Gnrc_Tot_Clms", "LIS_Tot_Clms",
              "Opioid_Tot_Clms", "Bene_Dual_Cnt"]
n_suppressed = int(df[count_cols].isna().sum().sum())
df[count_cols] = df[count_cols].fillna(SUPPRESSED_IMPUTE)
df = df.dropna(subset=["Tot_Clms", "Tot_Drug_Cst", "Bene_Avg_Age", "Bene_Avg_Risk_Scre"])
df = df[df["Tot_Clms"] >= MIN_CLAIMS]
print(f"Step 2: {len(df):,} providers after cleaning "
      f"({len(raw) - len(df):,} dropped); "
      f"{n_suppressed:,} suppressed counts imputed as {SUPPRESSED_IMPUTE}")

# ---------------------------------------------------------------
# STEP 3 -- Label + leakage-safe features
# ---------------------------------------------------------------
df["cost_per_claim"] = df["Tot_Drug_Cst"] / df["Tot_Clms"]
threshold = df["cost_per_claim"].quantile(0.75)
df["high_cost"] = (df["cost_per_claim"] >= threshold).astype(int)

df["brand_share"] = (df["Brnd_Tot_Clms"] /
                     (df["Brnd_Tot_Clms"] + df["Gnrc_Tot_Clms"]).replace(0, np.nan)).fillna(0)
df["lis_share"] = df["LIS_Tot_Clms"] / df["Tot_Clms"]
df["opioid_share"] = df["Opioid_Tot_Clms"] / df["Tot_Clms"]
df["dual_per_100_clms"] = df["Bene_Dual_Cnt"] / df["Tot_Clms"] * 100
df["log10_claims"] = np.log10(df["Tot_Clms"])
top10 = df["Prscrbr_Type"].value_counts().head(10).index
df["specialty"] = df["Prscrbr_Type"].where(df["Prscrbr_Type"].isin(top10), "Other")

# Guard against SEPARATION. A specialty in which every provider is high-cost --
# or none is -- predicts the outcome perfectly. Maximum likelihood then pushes
# that coefficient toward +/- infinity: the fit fails to converge and the Wald
# standard errors in Part 3 explode into meaningless intervals. Folding such
# groups into "Other" keeps every reported interval trustworthy. On large pulls
# this usually finds nothing to do, which is exactly the point of testing rather
# than assuming.
rates = df.groupby("specialty")["high_cost"].mean()
separated = [s for s in rates.index if s != "Other" and rates[s] in (0.0, 1.0)]
if separated:
    print(f"        separation guard: merged into 'Other' -> {', '.join(separated)}")
    df["specialty"] = df["specialty"].where(~df["specialty"].isin(separated), "Other")

numeric_features = ["brand_share", "lis_share", "opioid_share", "dual_per_100_clms",
                    "log10_claims", "Bene_Avg_Age", "Bene_Avg_Risk_Scre"]
X = pd.concat([df[numeric_features],
               pd.get_dummies(df["specialty"], prefix="spec", drop_first=True)], axis=1)
y = df["high_cost"]

# ---- plain-English names, used by every chart and table from here on ----
# get_dummies(drop_first=True) leaves one specialty out; it becomes the baseline
# every other specialty is compared against, so the charts must say which one.
SPEC_REFERENCE = sorted(df["specialty"].unique())[0]
FEATURE_LABELS = {
    "brand_share":        "Brand-drug share of claims",
    "lis_share":          "Low-income-subsidy share of claims",
    "opioid_share":       "Opioid share of claims",
    "dual_per_100_clms":  "Dual-eligible patients per 100 claims",
    "log10_claims":       "Practice size (log10 of total claims)",
    "Bene_Avg_Age":       "Patient panel: average age",
    "Bene_Avg_Risk_Scre": "Patient panel: average risk score",
}


def pretty(name):
    """Turn a model feature name into something a reader understands."""
    if name in FEATURE_LABELS:
        return FEATURE_LABELS[name]
    if name.startswith("spec_"):
        return f"Specialty: {name[5:]}"
    return "Intercept" if name == "const" else name


print(f"        specialty comparisons are all relative to: {SPEC_REFERENCE}")
print(f"Step 3: high-cost threshold ${threshold:.2f}/claim; "
      f"{y.sum()} high-cost vs {(1-y).sum()} typical; {X.shape[1]} features")

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
counts = y.value_counts().sort_index()
axes[0].bar(["typical (0)", "high-cost (1)"], counts.values, color=["#4878A8", "#C44E52"])
axes[0].set_title("Class balance"); axes[0].set_ylabel("providers")
axes[1].hist(df.loc[y == 0, "brand_share"], bins=30, alpha=0.6, density=True,
             label="typical", color="#4878A8")
axes[1].hist(df.loc[y == 1, "brand_share"], bins=30, alpha=0.6, density=True,
             label="high-cost", color="#C44E52")
axes[1].set_title("Brand share by class"); axes[1].set_xlabel("brand share of claims")
axes[1].legend()
save(fig, "01_data_overview.png")

# ---------------------------------------------------------------
# STEP 4 -- Why linear regression fails for a 0/1 outcome
# ---------------------------------------------------------------
xb = df[["brand_share"]].values
lin = LinearRegression().fit(xb, y)
log1 = LogisticRegression().fit(xb, y)
grid = np.linspace(-0.15, 1.15, 300).reshape(-1, 1)
rng = np.random.default_rng(0)

fig = plt.figure(figsize=(9, 5))
plt.scatter(xb, y + rng.uniform(-0.04, 0.04, len(y)), s=8, alpha=0.25,
            color="gray", label="providers (y jittered)")
plt.plot(grid, lin.predict(grid), "--", color="#C44E52", lw=2, label="linear regression")
plt.plot(grid, log1.predict_proba(grid)[:, 1], color="#2E7D32", lw=2.5,
         label="logistic regression")
plt.axhline(0, color="black", lw=0.6); plt.axhline(1, color="black", lw=0.6)
plt.ylim(-0.35, 1.35); plt.xlim(-0.15, 1.15)
plt.xlabel("brand share of claims"); plt.ylabel("high-cost (0/1)")
plt.title("A straight line can't model a probability")
plt.legend(loc="center right")
save(fig, "02_linear_vs_logistic.png")
print("Step 4: linear regression predicts 'probabilities' outside [0, 1];")
print("        logistic regression squashes the same line through the sigmoid")

fig = plt.figure(figsize=(9, 4.5))
zg = np.linspace(-8, 8, 400)
plt.plot(zg, 1 / (1 + np.exp(-zg)), lw=2.5, color="#2E7D32")
plt.axhline(0.5, color="gray", ls=":"); plt.axvline(0, color="gray", ls=":")
plt.xlabel("z  (the familiar linear combination)"); plt.ylabel("p  (probability)")
plt.title("The sigmoid: p = 1 / (1 + e^(-z))")
save(fig, "03_sigmoid.png")

# ---------------------------------------------------------------
# STEP 5 -- Split, scale, train
# ---------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)
model = LogisticRegression(max_iter=2000, random_state=42)
model.fit(X_train_s, y_train)
print(f"Step 5: trained on {len(X_train)} providers; testing on {len(X_test)}")

# ---------------------------------------------------------------
# STEP 6 -- Evaluate
# ---------------------------------------------------------------
y_pred = model.predict(X_test_s)
y_prob = model.predict_proba(X_test_s)[:, 1]
print("\nStep 6: evaluation on the held-out test set")
print(f"  Baseline (always 'typical'): {(y_test == 0).mean():.3f}")
print(f"  Accuracy:                    {accuracy_score(y_test, y_pred):.3f}")
print(f"  ROC AUC:                     {roc_auc_score(y_test, y_prob):.3f}\n")
print(classification_report(y_test, y_pred, target_names=["typical", "high-cost"]))

fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
cm = confusion_matrix(y_test, y_pred)
axes[0].imshow(cm, cmap="Blues")
for (i, j), v in np.ndenumerate(cm):
    axes[0].text(j, i, str(v), ha="center", va="center", fontsize=14,
                 color="white" if v > cm.max()/2 else "black")
axes[0].set_xticks([0, 1], ["typical", "high-cost"])
axes[0].set_yticks([0, 1], ["typical", "high-cost"])
axes[0].set_xlabel("predicted"); axes[0].set_ylabel("actual")
axes[0].set_title("Confusion matrix")
axes[1].hist(y_prob[y_test == 0], bins=25, alpha=0.65, label="actually typical", color="#4878A8")
axes[1].hist(y_prob[y_test == 1], bins=25, alpha=0.65, label="actually high-cost", color="#C44E52")
axes[1].axvline(0.5, color="black", ls="--", lw=1)
axes[1].set_xlabel("predicted probability of high-cost")
axes[1].set_title("Probabilities by true class"); axes[1].legend()
fpr, tpr, _ = roc_curve(y_test, y_prob)
axes[2].plot(fpr, tpr, lw=2.5, color="#2E7D32",
             label=f"model (AUC = {roc_auc_score(y_test, y_prob):.3f})")
axes[2].plot([0, 1], [0, 1], "--", color="gray", label="coin flip")
axes[2].set_xlabel("false positive rate"); axes[2].set_ylabel("true positive rate")
axes[2].set_title("ROC curve"); axes[2].legend(loc="lower right")
save(fig, "04_evaluation.png")

# ---------------------------------------------------------------
# PART 2 -- ODDS, LOG(ODDS), AND LOG(ODDS RATIOS)
# ---------------------------------------------------------------
print("=" * 62)
print("PART 2 -- UNDERSTANDING THE COEFFICIENTS")
print("=" * 62)

p_high = y_train.mean()
print(f"Step 7: odds and log(odds), from our own training data")
print(f"  p(high-cost) = {p_high:.3f}")
print(f"  odds     = p/(1-p) = {p_high/(1-p_high):.3f}")
print(f"  log-odds = {np.log(p_high/(1-p_high)):+.3f}")
print("  Rearranging the sigmoid:  log(p/(1-p)) = b0 + b1*x1 + ... + bn*xn")
print("  -> logistic regression IS linear regression on the log(odds) scale")

p_grid = np.linspace(0.001, 0.999, 500)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
axes[0].plot(p_grid, p_grid/(1-p_grid), lw=2.5, color="#4878A8")
axes[0].axvline(0.5, color="gray", ls=":"); axes[0].axhline(1, color="gray", ls=":")
axes[0].set_ylim(0, 20)
axes[0].set_xlabel("probability p"); axes[0].set_ylabel("odds")
axes[0].set_title("Odds: asymmetric")
axes[1].plot(p_grid, np.log(p_grid/(1-p_grid)), lw=2.5, color="#2E7D32")
axes[1].axvline(0.5, color="gray", ls=":"); axes[1].axhline(0, color="gray", ls=":")
axes[1].set_xlabel("probability p"); axes[1].set_ylabel("log(odds)")
axes[1].set_title("log(odds): symmetric -- the model's linear scale")
save(fig, "05_odds_logodds.png")

# Step 8 -- coefficients on both scales
weights = pd.Series(model.coef_[0], index=X.columns).sort_values()
or_series = np.exp(weights)
labels = [pretty(n) for n in weights.index]
colors = ["#C44E52" if w > 0 else "#4878A8" for w in weights]
print(f"\nStep 8: intercept (log-odds at all-average) = {model.intercept_[0]:+.2f}")
print("  Top positive log(odds ratios):")
print(weights.tail(3).iloc[::-1].rename(pretty).round(2).to_string())
print("  As odds ratios (e^coef):")
print(or_series.tail(3).iloc[::-1].rename(pretty).round(2).to_string())

fig, axes = plt.subplots(1, 2, figsize=(14, 6.5), sharey=True)
axes[0].barh(labels, weights.values, color=colors)
axes[0].axvline(0, color="black", lw=0.8)
axes[0].set_xlabel("log(odds ratio) = coefficient")
axes[0].set_title("Additive scale: log(odds ratios)")
axes[1].scatter(or_series.values, labels, color=colors, s=45, zorder=3)
for lab, v in zip(labels, or_series.values):
    axes[1].plot([1, v], [lab, lab], color="gray", lw=1, zorder=2)
axes[1].axvline(1, color="black", lw=0.8)
axes[1].set_xscale("log")
axes[1].set_xticks([0.25, 0.5, 1, 2, 4], ["0.25x", "0.5x", "1x", "2x", "4x"])
axes[1].set_xlabel("odds ratio per +1 SD (log axis)")
axes[1].set_title("Multiplicative scale: odds ratios")
fig.suptitle(f"Specialty rows compare against {SPEC_REFERENCE}; 1x means no effect",
             y=1.02, fontsize=10, color="#404040")
save(fig, "06_coefficients_odds_ratios.png")

# Step 9 -- worked example: brand share on the sigmoid
b0 = model.intercept_[0]
b_brand = model.coef_[0][list(X.columns).index("brand_share")]
print("\nStep 9: worked example -- brand share (all else average)")
for sds in [0, 1, 2]:
    z = b0 + b_brand * sds
    print(f"  +{sds} SD: log-odds {z:+.2f} | odds {np.exp(z):.2f} | "
          f"p(high-cost) {1/(1+np.exp(-z)):.1%}")
print(f"  Each +1 SD multiplies the odds by e^{b_brand:.2f} = {np.exp(b_brand):.2f} -- "
      f"the same multiplier every step:\n  'linear in log(odds)'.")

zg = np.linspace(-5, 4, 300)
fig = plt.figure(figsize=(9, 4.8))
plt.plot(zg, 1/(1+np.exp(-zg)), lw=2, color="#2E7D32")
for sds, mc in zip([0, 1, 2], ["#4878A8", "#E1A03C", "#C44E52"]):
    zv = b0 + b_brand * sds
    plt.scatter([zv], [1/(1+np.exp(-zv))], s=90, color=mc, zorder=3,
                label=f"+{sds} SD brand share: p = {1/(1+np.exp(-zv)):.0%}")
plt.axhline(0.5, color="gray", ls=":")
plt.xlabel("z = log(odds)"); plt.ylabel("p(high-cost)")
plt.title("Equal steps in log(odds), unequal steps in probability")
plt.legend()
save(fig, "07_worked_example.png")

# ---------------------------------------------------------------
# PART 3 -- STATISTICAL INFERENCE
# ---------------------------------------------------------------
import statsmodels.api as sm
from scipy import stats

print("=" * 62)
print("PART 3 -- STATISTICAL INFERENCE")
print("=" * 62)

# Step 10 -- transform the y-axis: probability -> log(odds)
m1 = LogisticRegression().fit(xb, y)          # one-feature model (brand share)
b0_1, b1_1 = m1.intercept_[0], m1.coef_[0][0]
bins = pd.qcut(df["brand_share"], 10, duplicates="drop")
g = (df.assign(hc=y).groupby(bins, observed=True)
       .agg(x=("brand_share", "mean"), p=("hc", "mean"), n=("hc", "size")))
g = g[(g["p"] > 0) & (g["p"] < 1)]
g["log_odds"] = np.log(g["p"] / (1 - g["p"]))
grid1 = np.linspace(df["brand_share"].min(), df["brand_share"].max(), 200)

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6))
axes[0].scatter(g["x"], g["p"], s=g["n"] * 0.6, color="#4878A8", zorder=3,
                label="observed share high-cost (bin)")
axes[0].plot(grid1, 1 / (1 + np.exp(-(b0_1 + b1_1 * grid1))), color="#2E7D32",
             lw=2.5, label="fitted logistic curve")
axes[0].set_xlabel("brand share of claims"); axes[0].set_ylabel("probability")
axes[0].set_title("Probability scale: the S-curve"); axes[0].legend()
axes[1].scatter(g["x"], g["log_odds"], s=g["n"] * 0.6, color="#4878A8", zorder=3,
                label="observed log(odds) (bin)")
axes[1].plot(grid1, b0_1 + b1_1 * grid1, color="#2E7D32", lw=2.5,
             label=f"fitted line:  z = {b0_1:.2f} + {b1_1:.2f} × (brand share)")
axes[1].set_xlabel("brand share of claims"); axes[1].set_ylabel("log(odds)")
axes[1].set_title("Log(odds) scale: a straight line"); axes[1].legend()
save(fig, "08_logodds_line.png")
print("Step 10: y-axis transformed to log(odds) -- binned data falls on the")
print(f"         model's straight line: intercept {b0_1:+.2f}, slope {b1_1:+.2f}")

# Step 11 -- statsmodels refit: the regression table + Wald's test
Xs_train = pd.DataFrame(X_train_s, columns=X.columns, index=X_train.index).astype(float)
sm_model = sm.Logit(y_train.astype(float), sm.add_constant(Xs_train)).fit(disp=0)
print("\nStep 11: statsmodels regression table (coef | std err | z | P>|z| | 95% CI)")
print(f"  (McFadden pseudo R-squared: {sm_model.prsquared:.3f})")

b_hat, se = sm_model.params["brand_share"], sm_model.bse["brand_share"]
z_wald = b_hat / se
p_wald = 2 * (1 - stats.norm.cdf(abs(z_wald)))
print("\n  Wald's test for brand_share, by hand:")
print(f"    z = coef/SE = {b_hat:+.3f}/{se:.3f} = {z_wald:+.2f}  (|z| > 1.96 -> significant)")
print(f"    p-value = {p_wald:.2e}")
print(f"    95% CI (odds ratio): [{np.exp(b_hat-1.96*se):.2f}x, {np.exp(b_hat+1.96*se):.2f}x]"
      "  <- excludes 1")

params = sm_model.params.drop("const")
conf = sm_model.conf_int().drop("const")
pvals = sm_model.pvalues.drop("const")
order = params.sort_values().index
sig = pvals < 0.05
fig, axes = plt.subplots(1, 2, figsize=(14.5, 6.8), sharey=True)
for name in order:
    lab = pretty(name)
    color = "#C44E52" if params[name] > 0 else "#4878A8"
    filled = color if sig[name] else "white"
    axes[0].plot(conf.loc[name], [lab, lab], color=color, lw=2)
    axes[0].scatter(params[name], lab, s=55, color=filled, edgecolor=color, zorder=3)
    axes[1].plot(np.exp(conf.loc[name]), [lab, lab], color=color, lw=2)
    axes[1].scatter(np.exp(params[name]), lab, s=55, color=filled, edgecolor=color, zorder=3)
axes[0].axvline(0, color="black", lw=0.8)
axes[0].set_xlabel("coefficient (log odds ratio) with 95% CI")
axes[0].set_title("Wald intervals, log-odds scale (filled = p < 0.05)")
axes[1].axvline(1, color="black", lw=0.8)
axes[1].set_xscale("log")
axes[1].set_xticks([0.25, 0.5, 1, 2, 4], ["0.25x", "0.5x", "1x", "2x", "4x"])
axes[1].set_xlabel("odds ratio with 95% CI (log axis)")
axes[1].set_title("Wald intervals, odds-ratio scale")
fig.suptitle(f"Specialty rows compare against {SPEC_REFERENCE}",
             y=1.02, fontsize=10, color="#404040")
save(fig, "09_wald_intervals.png")
print(f"  {sig.sum()} of {len(sig)} features significant at p < 0.05")

# Step 12 -- where the t-test fits in
t_stat, p_t = stats.ttest_ind(df.loc[y == 1, "brand_share"],
                              df.loc[y == 0, "brand_share"], equal_var=False)
print("\nStep 12: the t-test connection")
print("  Linear regression tests coefficients with t (residual variance is")
print("  estimated); logistic regression has no residual variance, so Wald's")
print("  z is compared to the standard normal instead. Same structure: estimate/SE.")
print(f"  EDA two-sample (Welch) t-test on brand share: t = {t_stat:.2f}, p = {p_t:.2e}")
print("  t-test says the group MEANS differ; Wald says brand share predicts")
print("  high-cost even holding all other features fixed.")

print("\nDone. All charts are in ./charts/")
print("=" * 62)
