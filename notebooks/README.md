# Jupyter Notebooks Catalog

This directory contains analytical, exploratory, and machine learning notebooks for **CustomerLens**.

---

## Execution Sequence

| Sequence | Notebook File | Phase | Primary Purpose | Key Outputs |
| :---: | :--- | :---: | :--- | :--- |
| **03** | [`03_eda.ipynb`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/notebooks/03_eda.ipynb) | Phase 6 | Exploratory Data Analysis (EDA) of cleaned transaction data | Empirical KPIs, time-series velocity, repeat purchase rates, country breakdown, Pareto concentration |
| **04** | [`04_rfm_analysis.ipynb`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/notebooks/04_rfm_analysis.ipynb) | Phase 8 | Customer-level RFM behavioral feature engineering & segmentation | Distributions (raw & log), outlier characterization, quantile scoring, 2D heatmaps, 8-segment profiling |
| **05** | [`05_customer_segmentation.ipynb`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/notebooks/05_customer_segmentation.ipynb) | Phase 9 | Unsupervised machine learning customer segmentation using K-Means clustering | Skewness & log1p stabilization, $K=2..10$ metric curves (Elbow, Silhouette, Davies-Bouldin, Calinski-Harabasz), 2D PCA & RFM pairwise cluster projections, radar/box plot profiles, cluster-to-RFM cross-tabulation |
| **06** | [`06_business_insights.ipynb`](file:///c:/Users/divya/OneDrive/Desktop/Customer_Lens/notebooks/06_business_insights.ipynb) | Phase 10 | Business segmentation personas, revenue concentration, and strategic marketing opportunities | Customer share vs. revenue share disparity, concentration ratios, behavioral RFM comparisons, experimentation frameworks |

---

## Execution Instructions

All notebooks are designed to be fully reproducible from project root:
```bash
# Execute 03 EDA notebook
jupyter execute notebooks/03_eda.ipynb

# Execute 04 RFM analysis notebook
jupyter execute notebooks/04_rfm_analysis.ipynb

# Execute 05 Customer segmentation notebook
jupyter execute notebooks/05_customer_segmentation.ipynb

# Execute 06 Business insights notebook
jupyter execute notebooks/06_business_insights.ipynb
```
