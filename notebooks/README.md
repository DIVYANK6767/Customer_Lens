# Jupyter Notebooks Catalog

This directory contains analytical, exploratory, and machine learning notebooks for **CustomerLens**.

---

## Execution Sequence

| Sequence | Notebook File | Phase | Primary Purpose | Key Outputs |
| :---: | :--- | :---: | :--- | :--- |
| **03** | [`03_eda.ipynb`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/notebooks/03_eda.ipynb) | Phase 6 | Exploratory Data Analysis (EDA) of cleaned transaction data | Empirical KPIs, time-series velocity, repeat purchase rates, country breakdown, Pareto concentration |
| **04** | [`04_rfm_analysis.ipynb`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/notebooks/04_rfm_analysis.ipynb) | Phase 8 | Customer-level RFM behavioral feature engineering & segmentation | Distributions (raw & log), outlier characterization, quantile scoring, 2D heatmaps, 8-segment profiling |

---

## Execution Instructions

All notebooks are designed to be fully reproducible from project root:
```bash
# Execute 03 EDA notebook
jupyter execute notebooks/03_eda.ipynb

# Execute 04 RFM analysis notebook
jupyter execute notebooks/04_rfm_analysis.ipynb
```
