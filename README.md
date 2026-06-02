# UAE Customer Analytics Dashboard

## Setup & Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Place your CSV file (`uae_customers_2000_improved.csv`) in the same folder.  
The app auto-generates sample data if the file is not found.

---

## Features

### 1. 📊 EDA — Drilled-Down Analysis
- Dynamic primary + secondary dimension breakdown
- Aggregation: Mean / Sum / Count / Median
- Correlation heatmap with selectable columns
- Scatter drill-down with OLS trendline, colour & size encoding
- Box plots by category
- KPI summary row

### 2. 🤖 Classification — All Algorithms
Trains **10 classifiers** simultaneously:
- Logistic Regression, Decision Tree, Random Forest, Gradient Boosting,
  AdaBoost, Extra Trees, SVM, KNN, Naive Bayes, Neural Network (MLP)

Outputs: Accuracy · Precision · Recall · F1 · AUC-ROC comparison table,
grouped bar chart, radar chart, confusion matrices (top 4), feature importance.

### 3. 📈 ARIMA Forecasting
- ADF stationarity test
- Seasonal decomposition (if ≥24 data points)
- Configurable p / d / q sliders
- Forecast with 95% confidence interval
- MAE · RMSE · AIC · BIC metrics + forecast table

### 4. 🔗 Clustering
- **Elbow method** (inertia) + **Silhouette score** side-by-side
- K-Means scatter with cluster profiles table
- **Hierarchical clustering** with interactive Dendrogram
- Agglomerative clustering scatter
- Adjusted Rand Index (KMeans vs HC comparison)

### 5. 🛒 Association Rule Mining
- Apriori with min-support / confidence / lift controls
- Rules table with gradient highlight
- **Scatter plot**: Support × Confidence sized by Lift
- Top-15 rules bar chart
- Lift distribution histogram

### 6. 🎛️ What-If Simulator
- Drop-down menus for categorical features
- Sliders for numeric features (auto-scaled to data range)
- Random Forest prediction with confidence %
- Class probability bar chart
- Percentile position in distribution
- **Sensitivity analysis** — vary any feature and see prediction change
