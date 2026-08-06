# Setting Up Microsoft Fabric and Running the Logistic Regression Notebook

## Overview

This guide assumes you have a **business (work/school) Microsoft account with admin rights** — the simplest possible setup path. It takes you from signing in to running `60 logistic_regression_pharmacy_fabric.ipynb` in Microsoft Fabric, using the **free 60-day Fabric trial** (no credit card, no charge).

The path in brief:

1. Verify the tenant settings that allow trials (you're the admin, so you control these)
2. Sign in to Fabric and activate the 60-day free trial
3. Create a workspace
4. Import the notebook — or create one from scratch
5. Run it
6. (Optional) Save results to a Lakehouse and connect the notebook to GitHub

**Time required:** roughly 15–20 minutes.

**No business account?** See the Appendix for the personal-email route via a free Azure account.

---

## Part 1 — Verify tenant settings (admin)

Trials are enabled by default, but two tenant settings control whether they work. Since you're an admin, confirm both up front rather than troubleshooting later:

1. Go to the [Fabric portal](https://app.fabric.microsoft.com) and sign in with your business account.
2. Select the **gear icon** (upper-right) → **Admin portal** → **Tenant settings**.
3. Under **Microsoft Fabric**, confirm **Users can create Fabric items** is **Enabled** (optionally scoped to specific security groups — make sure you're in one if scoped).
4. Under **Help and support settings**, confirm **Users can try Microsoft Fabric paid features** is **Enabled** (this is what allows the 60-day trial; it's on by default).
5. Select **Apply** if you changed anything. Settings can take up to 15 minutes to take effect.

## Part 2 — Activate the free trial

1. In the Fabric portal, click your **profile icon** (upper-right corner).
2. Select **Free trial**, choose a **capacity region** (closest to you, or accept the default), agree to the terms, and select **Activate**.

You now have a **60-day trial capacity with 64 capacity units (CUs)** — more than enough for this project. No credit card is required.

## Part 3 — Create a workspace

Workspaces are folders that hold your Fabric items (notebooks, lakehouses, reports).

1. In the Fabric portal, select **Workspaces** in the left navigation.
2. Select **+ New workspace**.
3. Name it (e.g., `ML Tutorial`).
4. Expand **Advanced** and confirm **License mode** is set to **Trial** capacity.
5. Select **Apply**.

## Part 4A — Import the notebook (recommended)

1. Open your new workspace.
2. Select **Import** → **Notebook** → **From this computer** (on some layouts: **+ New item** → search "notebook" → import option).
3. Select **Upload**, browse to your project folder, and choose `60 logistic_regression_pharmacy_fabric.ipynb`.
4. The notebook appears as a new item in the workspace — click it to open.

## Part 4B — Create the notebook from scratch (no file to import)

If you're starting in Fabric with nothing to import, build the notebook directly:

1. In your workspace, select **+ New item**, search for **Notebook**, and select it. A new notebook opens with one empty code cell.
2. Rename it: click the name in the top-left (e.g., "Notebook 1"), type a new name such as `logistic_regression_pharmacy`, and press Enter. Fabric saves automatically — there is no Save button to worry about.
3. Add cells by hovering below an existing cell and selecting **+ Code** or **+ Markdown**. Use Markdown cells for explanation, Code cells for Python.
4. Build the content one step per code cell, in this order (copy each block from `30 logistic_regression_pharmacy.py`, which is organized into the same steps):
   - Part 1: download the CMS data live from data.cms.gov (any row count, or all 1.4M), clean it, engineer the label and features, visualize why linear regression fails, train, and evaluate with graphs
   - Part 2: odds and log(odds), coefficients as log(odds ratios), odds-ratio charts, and the worked brand-share example
   - Part 3: the log-odds y-axis transformation (S-curve → straight line), the statsmodels regression table, Wald's test with confidence intervals, and the t-test comparison
5. Run each cell with **Shift+Enter** as you go — you'll see output under each cell, which is the best way to catch typos early.
6. No installs are needed: `scikit-learn`, `pandas`, `matplotlib`, `requests`, `statsmodels`, and `scipy` are preinstalled in the Fabric runtime, and charts render inline under each cell.

## Part 5 — Run the notebook

1. With the notebook open, simply select **Run all** in the toolbar.
2. The first run takes 1–3 minutes while Fabric starts a compute session (watch the status at the bottom left); later runs are faster.
3. `scikit-learn`, `pandas`, `matplotlib`, `requests`, `statsmodels`, and `scipy` are **preinstalled** — no setup cells are needed. If your environment somehow lacks them, uncomment the `%pip install` cell near the top and run it first.
4. Expected results: ~85% accuracy (vs. a 75% baseline) and ~0.89 ROC AUC on the held-out test set, with 10 graphs rendering inline — matching the outputs already saved in the notebook. The first cell downloads the data live from data.cms.gov; Fabric has outbound internet access by default, so nothing needs uploading.
5. **To run on the complete 1,416,883-provider dataset,** change one line near the top of the notebook to `DATA_ROWS = "full"` and select **Run all** again. Fabric is well suited to this — the trial capacity has ample memory, and the ~2 GB download runs on Microsoft's network rather than your laptop's. Expect 5–15 minutes, and much tighter confidence intervals in Part 3.

## Part 6 (Optional) — Save predictions to a Lakehouse

A Lakehouse is Fabric's data storage item. The notebook's final cell shows how to persist predictions.

1. In the notebook's left **Explorer** panel, select **Add data items** → **New lakehouse** (or attach an existing one) → name it and **Create**.
2. In the final notebook cell, uncomment **Option A** (Spark/Delta table) if using the default notebook experience, or **Option B** (CSV) if you converted it to a pure Python notebook.
3. Run the cell; the results appear under the Lakehouse's **Tables** or **Files**.

## Part 7 (Optional) — Connect the notebook to a GitHub repo

Fabric's Git integration works at the **workspace** level: connect the workspace once, and every item in it (including your notebook) becomes version-controlled in GitHub.

**Prerequisites:** a GitHub account and repository (see `70 GitHub Setup Guide` Parts 1–2), and a **fine-grained personal access token** with Read/Write access to **Contents** for that repository (GitHub → Settings → Developer settings → Personal access tokens).

1. Open your workspace and select **Workspace settings** → **Git integration**.
2. Choose **GitHub** as the provider and select **Add account**: give the connection a name, paste the personal access token, and enter the repository URL (`https://github.com/<username>/<repo>`).
3. Select the **branch** (e.g., `main`) and optionally a **folder** within the repo (e.g., `fabric/` keeps Fabric-synced items separate from the rest of your files), then select **Connect and sync**.
4. On first sync, choose the direction: commit workspace items into the repo, or pull repo content into the workspace. For a new connection with your notebook already in the workspace, commit **workspace → repo**.
5. From now on, the **Source control** button in the workspace shows pending changes. After editing the notebook, open it, review the changes, add a commit message, and select **Commit** to push to GitHub; use **Update** to pull changes made in GitHub back into the workspace.
6. Notes:
   - Fabric stores synced notebooks in the repo in its own item-folder format (source code as `notebook-content.py` plus metadata) — this is normal and diff-friendly; it's separate from the standalone `.ipynb` files you may have uploaded to the repo yourself.
   - Only a workspace admin can connect the workspace (you are one), and from November 1, 2026, users need read-write permission on workspace items to use Git integration.

---

## Costs and what happens after 60 days

- The trial is free; each trial user gets 64 CUs for 60 days. Fabric shows days remaining under your profile icon.
- To keep working afterward, as admin you can purchase a small **F2 pay-as-you-go capacity** through Azure (pause it when idle to minimize cost) and assign workspaces to it in the Admin portal, or export your notebooks (workspace item → **⋯** → **Export**) and run them locally for free with Jupyter — the plain `40 logistic_regression_pharmacy.ipynb` in this folder does exactly that.

## Troubleshooting

- **"Start trial" / "Free trial" option missing:** as admin, check both tenant settings in Part 1; allow up to 15 minutes after enabling. Also confirm your account has at least a (free) Fabric license assigned.
- **Notebook won't import:** confirm the file extension is `.ipynb` and the workspace License mode is **Trial**.
- **Session won't start / capacity errors:** check Workspace settings → License info and confirm Trial capacity.
- **Colleagues can't create items:** scope of **Users can create Fabric items** may exclude them — adjust the security group in Tenant settings.

## Appendix — No business account? (personal-email route)

If you ever need to set this up without a work/school account:

1. Create a free Azure account with your personal email at the [Azure free account page](https://azure.microsoft.com/pricing/purchase-options/azure-account?icid=azurefreeaccount) (payment method may be requested for verification only).
2. In the Azure portal, open **Microsoft Entra ID** → **Manage** → **Users** → **New user** → **Create new user**; note the user principal name (UPN, `...onmicrosoft.com`).
3. Sign in to [app.fabric.microsoft.com](https://app.fabric.microsoft.com) with that UPN (not the personal email), then continue from Part 2.

Full walkthrough: [Start a Microsoft Fabric free trial with a personal email](https://learn.microsoft.com/en-us/fabric/fundamentals/free-trial-account-personal-email).

## Sources

- [Fabric trial capacity — Microsoft Learn](https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial)
- [Help and support admin settings — Microsoft Learn](https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-help-support)
- [How to use notebooks — Microsoft Learn](https://learn.microsoft.com/en-us/fabric/data-engineering/how-to-use-notebook)
- [Fabric free trial with a personal email — Microsoft Learn](https://learn.microsoft.com/en-us/fabric/fundamentals/free-trial-account-personal-email)
- [Get started with Git integration — Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-get-started)
