#### Logistic Regression for Pharmacy Analytics — Python dependencies
##### Install with:  pip install -r requirements.txt

scikit-learn>=1.3     # LogisticRegression, train/test split, scaling, metrics <br>
pandas>=2.0           # data handling <br>
numpy>=1.24           # numerics (pulled in by pandas, pinned here for clarity) <br>
requests>=2.31        # live download from the CMS JSON API <br>
matplotlib>=3.7       # all 10 graphs <br>
statsmodels>=0.14     # regression table, Wald test, confidence intervals (Part 3) <br>
scipy>=1.10           # normal/t distributions for the hand-computed tests (Part 3) <br>
