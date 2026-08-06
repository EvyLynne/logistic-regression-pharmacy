# Setting Up a GitHub Repository for This Project

## Overview

This guide assumes **no prior knowledge and no existing GitHub account**. It takes you from nothing to a published GitHub repository containing this project — a strong portfolio piece for a job search, since employers can see both your code and your documentation.

The path in brief:

1. Create a free GitHub account
2. Create the repository
3. Add the project files — the no-install way (web upload) or the standard way (Git command line)
4. Organize the files into the recommended repository structure
5. Polish the repo so it presents well
6. (Optional) Connect your Microsoft Fabric workspace to the repo

**Time required:** 15–20 minutes for the web-upload route; add 15 minutes if installing Git.

---

## Part 1 — Create a GitHub account

1. Go to [github.com](https://github.com) and select **Sign up**.
2. Register with your email address, create a password and username. The username appears in your repo's public URL (e.g., `github.com/evylivant/...`), so pick something professional.
3. Verify your email when prompted. The free plan is all you need — it includes unlimited public and private repositories.

## Part 2 — Create the repository

1. Once signed in, click the **+** icon (upper-right) → **New repository**.
2. Fill in:
   - **Repository name:** e.g., `logistic-regression-pharmacy` (lowercase with hyphens is the convention)
   - **Description:** e.g., "Logistic regression tutorial on real CMS Medicare Part D pharmacy data — predicting high-cost prescribers, with odds-ratio interpretation and Microsoft Fabric notebooks"
   - **Visibility:** **Public** for a portfolio piece; Private if you're not ready to share
3. Under "Initialize this repository with":
   - Check **Add a README file** (you'll replace its contents with `80 GitHub README.md` shortly)
   - **Add .gitignore:** choose the **Python** template
   - **Choose a license:** MIT is a common, permissive default for tutorial code
4. Select **Create repository**.

## Part 3A — Add files the no-install way (web upload)

Easiest route; nothing to install.

1. In your new repo, select **Add file** → **Upload files**.
2. Drag in all the project files (10 through 80) from this folder. There is no data file — the notebooks download from CMS at run time.
3. Scroll down, type a commit message (e.g., `Add logistic regression tutorial project`), and select **Commit changes**.
4. To make the repo homepage show your project: open `80 GitHub README.md` on GitHub, copy its contents into the repo's `README.md` (Edit → paste → Commit changes). GitHub only auto-displays a file named exactly `README.md` — the `80` file is written specifically for this purpose, with badges, results, and repo navigation.

## Part 3B — Add files the standard way (Git command line)

The professional workflow; worth learning if you'll use GitHub regularly.

1. Install Git from [git-scm.com/downloads](https://git-scm.com/downloads) (accept the defaults on Windows).
2. Open **Git Bash** (installed with Git) or PowerShell, then set your identity (one-time):

   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```

3. Clone the empty repo (find the URL under the green **Code** button):

   ```bash
   git clone https://github.com/<username>/logistic-regression-pharmacy.git
   cd logistic-regression-pharmacy
   ```

4. Copy the project files in (quote paths — the filenames contain spaces):

   ```bash
   cp "/m/evelyn/Evelyn/Career/2026 Job Search/Shields Health Machine Learning/"* .
   ```

5. Stage, commit, and push:

   ```bash
   git add .
   git commit -m "Add logistic regression tutorial project"
   git push
   ```

6. When prompted to sign in, use your browser or a **fine-grained personal access token** (GitHub → Settings → Developer settings → Personal access tokens), not your password — password authentication for Git is no longer supported.

## Part 4 — Recommended repository structure

A flat pile of files works, but this layout is the convention reviewers expect — code, notebooks, and documentation separated:

```
logistic-regression-pharmacy/
├── README.md                                      ← contents of "80 GitHub README.md"
├── LICENSE                                        ← added at repo creation (MIT)
├── .gitignore                                     ← Python template, added at repo creation
├── requirements.txt                               ← dependencies (see below)
├── src/
│   └── logistic_regression_pharmacy.py            ← from "30 ..."
├── notebooks/
│   ├── logistic_regression_pharmacy.ipynb         ← from "40 ..."
│   └── logistic_regression_pharmacy_fabric.ipynb  ← from "60 ..."
└── docs/
    ├── Logistic Regression Tutorial.docx          ← from "20 ..."
    ├── Fabric Setup Guide.md                      ← from "50 ..."
    └── GitHub Setup Guide.md                      ← from "70 ..."
```

How to apply it:

1. **Drop the numeric prefixes inside the repo.** They exist to order files in a Windows folder; in a repo, the README provides reading order, and prefixes with spaces make awkward URLs (`src/30%20logistic...`).
2. **Create `requirements.txt`** (Add file → Create new file) with one dependency per line:

   ```
   scikit-learn
   pandas
   requests
   matplotlib
   statsmodels
   scipy
   ```

   This lets anyone reproduce your environment with `pip install -r requirements.txt`.
3. **Creating folders on the GitHub website:** there's no "new folder" button — when creating or moving a file, type the folder name and a slash in the filename box (e.g., `src/logistic_regression_pharmacy.py`) and GitHub creates the folder. To move an existing file, open it → pencil icon → edit the filename path the same way.
4. **With Git locally:** just make the folders, `mv` the files in, then `git add . && git commit -m "Organize repo structure" && git push`.
5. **Update the file list in README.md** so its links point to the new paths, e.g., `[the script](src/logistic_regression_pharmacy.py)`.

## Part 5 — Polish the repo

- **README first impression:** the repo homepage renders `README.md` — make sure it contains the content of `80 GitHub README.md` (Part 3A step 4), since that's what a hiring manager sees first. It leads with results and badges, which is what reviewers scan for.
- **Notebooks render automatically:** GitHub displays `.ipynb` files with their saved outputs — reviewers can read your results without running anything. This is why the executed outputs were kept in files 40 and 60.
- **Add topics:** repo main page → gear icon next to About → add topics like `machine-learning`, `logistic-regression`, `scikit-learn`, `microsoft-fabric`, `healthcare-analytics`, `tutorial` — these make the repo discoverable.
- **Check the .gitignore:** the Python template already excludes `__pycache__/`, virtual environments, and `.ipynb_checkpoints/` — the usual clutter.
- **What not to commit:** never commit secrets (API keys, connection strings) or large private datasets. This project is safe — the CMS dataset is a public U.S. Government work and nothing here contains credentials.

## Part 6 (Optional) — Connect Microsoft Fabric to the repo

Fabric's Git integration can sync your Fabric workspace directly to GitHub, so notebook changes made in Fabric are version-controlled.

1. In GitHub, create a **fine-grained personal access token** with Read/Write access to **Contents** for this repository (Settings → Developer settings → Personal access tokens).
2. In Fabric, open your workspace → **Workspace settings** → **Git integration**.
3. Choose **GitHub** as the provider, add an account connection using the token, then select your repository and branch and select **Connect and sync**.
4. Afterward, the **Source control** pane in the workspace shows changed items; use it to commit Fabric edits to GitHub or pull updates the other way.
5. Notes: only a workspace admin can connect the workspace, and (from November 1, 2026) you need read-write permission on workspace items to use Git integration.

## Troubleshooting

- **`git push` rejected (authentication):** use a personal access token or the browser sign-in; passwords don't work for Git operations.
- **Repo homepage doesn't show the tutorial:** GitHub only renders a file named exactly `README.md` — copy `80 GitHub README.md`'s contents into it.
- **Notebook shows "Invalid Notebook":** re-upload the `.ipynb`; partial uploads can truncate the JSON.
- **Fabric can't see the repo:** confirm the token has Contents read/write scope for that specific repository and hasn't expired.

## Sources

- [Get started with Git integration — Microsoft Learn](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/git-get-started)
- [GitHub integration for source control — Microsoft Fabric Blog](https://blog.fabric.microsoft.com/en-US/blog/announcing-github-integration-for-source-control-preview/)
