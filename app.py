# =============================================================================
#  UAE Customer Analytics Dashboard — Final Production Version
# =============================================================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from plotly.subplots import make_subplots
import warnings, glob, pickle
warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UAE Customer Analytics",
    layout="wide",
    page_icon="🏙️",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main .block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
    max-width: 100%;
}
/* SIDEBAR */
section[data-testid="stSidebar"] { background-color: #0f2744 !important; }
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] strong { color: #ffffff !important; }
section[data-testid="stSidebar"] hr { border-color: #2d4a6d; }
section[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #2563eb !important; color: #fff !important;
}
/* TABS */
.stTabs [data-baseweb="tab-list"] {
    background: #dde4ee;
    padding: 5px 8px;
    border-radius: 12px;
    gap: 4px;
    flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    background: #fff !important;
    color: #1e293b !important;
    border: 1px solid #c1cad8 !important;
    border-radius: 8px !important;
    padding: 7px 15px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
}
.stTabs [aria-selected="true"] {
    background: #1d4ed8 !important;
    color: #ffffff !important;
    border-color: #1d4ed8 !important;
}
.stTabs [data-baseweb="tab"]:hover {
    background: #bfdbfe !important;
    color: #1e40af !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }
/* HEADINGS */
h1 { color: #0f2744 !important; }
h2 { color: #1d4ed8 !important; }
h3 { color: #334155 !important; }
/* KPI CARDS */
.kpi { background: linear-gradient(135deg,#eff6ff,#dbeafe);
       border-left: 5px solid #2563eb; border-radius: 10px;
       padding: 12px 16px; margin-bottom: 6px; }
.kpi-label { color:#475569; font-size:.75rem; font-weight:700;
             text-transform:uppercase; letter-spacing:.05em; margin:0; }
.kpi-value { color:#0f2744; font-size:1.6rem; font-weight:700; margin:4px 0 0 0; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA
# =============================================================================
def make_data(n: int = 2000) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    emirates   = ["Dubai","Abu Dhabi","Sharjah","Ajman","Ras Al Khaimah","Fujairah","Umm Al Quwain"]
    categories = ["Electronics","Fashion","Home & Garden","Sports","Groceries","Beauty","Toys"]
    payments   = ["Credit Card","Debit Card","Cash","Digital Wallet"]
    segments   = ["Premium","Standard","Economy"]
    seg = rng.choice(segments, n, p=[0.25,.50,.25])
    inc = np.exp(rng.normal(10.8,.6,n)).astype(int)
    amt = rng.exponential(500,n).round(2)
    inc = np.where(seg=="Premium",(inc*1.5).astype(int),inc)
    amt = np.where(seg=="Premium", amt*1.8, amt).round(2)
    return pd.DataFrame({
        "customer_id":      range(1,n+1),
        "age":              rng.integers(18,70,n).tolist(),
        "gender":           rng.choice(["Male","Female"],n).tolist(),
        "emirate":          rng.choice(emirates,n,p=[.35,.30,.15,.07,.06,.04,.03]).tolist(),
        "annual_income":    inc.tolist(),
        "purchase_amount":  amt.tolist(),
        "num_purchases":    rng.poisson(8,n).tolist(),
        "product_category": rng.choice(categories,n).tolist(),
        "payment_method":   rng.choice(payments,n).tolist(),
        "customer_segment": seg.tolist(),
        "satisfaction_score": rng.integers(1,6,n).tolist(),
        "churn":            rng.choice([0,1],n,p=[.75,.25]).tolist(),
        "tenure_months":    rng.integers(1,60,n).tolist(),
        "date":             pd.date_range("2022-01-01",periods=n,freq="8h"),
        "loyalty_points":   rng.integers(0,5000,n).tolist(),
        "discount_used":    rng.choice([0,1],n,p=[.60,.40]).tolist(),
        "return_customer":  rng.choice([0,1],n,p=[.50,.50]).tolist(),
    })

@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    for pat in ["uae_customers*.csv","*.csv"]:
        for f in glob.glob(pat):
            try:
                df = pd.read_csv(f)
                df.columns = df.columns.str.strip().str.lower().str.replace(" ","_")
                for c in df.columns:
                    if any(k in c for k in ("date","time")):
                        df[c] = pd.to_datetime(df[c], errors="coerce")
                return df
            except Exception:
                pass
    return make_data()

df = load_data()

# =============================================================================
# HELPERS
# =============================================================================
def num_cols(d: pd.DataFrame) -> list:
    return d.select_dtypes(include=[np.number]).columns.tolist()

def cat_cols(d: pd.DataFrame) -> list:
    cols = []
    for c in d.columns:
        if d[c].dtype == object or str(d[c].dtype) in ("string","category"):
            cols.append(c)
    return cols

def kpi_card(label: str, val: str) -> str:
    return (f'<div class="kpi">'
            f'<p class="kpi-label">{label}</p>'
            f'<p class="kpi-value">{val}</p></div>')

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("# 🏙️ UAE Analytics")
    st.markdown("---")
    st.markdown("### 🔍 Global Filters")

    em_col  = next((c for c in df.columns if c in ("emirate","city","region")), None)
    seg_col = next((c for c in df.columns if "segment" in c), None)
    gen_col = next((c for c in df.columns if "gender" in c), None)

    fdf = df.copy()
    if em_col:
        opts = sorted(df[em_col].dropna().unique().tolist())
        sel  = st.multiselect("🏴 Emirate", opts, default=opts)
        if sel: fdf = fdf[fdf[em_col].isin(sel)]
    if seg_col:
        opts = sorted(df[seg_col].dropna().unique().tolist())
        sel  = st.multiselect("👥 Segment", opts, default=opts)
        if sel: fdf = fdf[fdf[seg_col].isin(sel)]
    if gen_col:
        opts = sorted(df[gen_col].dropna().unique().tolist())
        sel  = st.multiselect("⚧ Gender", opts, default=opts)
        if sel: fdf = fdf[fdf[gen_col].isin(sel)]

    st.markdown("---")
    st.markdown(f"**Records:** {len(fdf):,} / {len(df):,}")
    st.markdown(f"**Columns:** {len(df.columns)}")

# =============================================================================
# PAGE TITLE
# =============================================================================
st.markdown("# 🏙️ UAE Customer Analytics Dashboard")
st.markdown("Use the sidebar to filter data globally. Click any tab to explore the analysis.")
st.markdown("---")

# =============================================================================
# TABS
# =============================================================================
t_eda, t_clf, t_arima, t_clust, t_arm, t_sim = st.tabs([
    "📊 EDA",
    "🤖 Classification",
    "📈 ARIMA Forecast",
    "🔗 Clustering",
    "🛒 Association Rules",
    "🎛️ What-If Simulator",
])

# =============================================================================
# TAB 1 — EDA
# =============================================================================
with t_eda:
    st.header("📊 Exploratory Data Analysis")
    nc = num_cols(fdf)
    cc = cat_cols(fdf)

    # KPIs
    amt_c = next((c for c in nc if any(k in c for k in ("amount","purchase","spend","revenue"))), nc[0] if nc else None)
    age_c = next((c for c in nc if "age" in c), None)
    chu_c = next((c for c in nc if "churn" in c), None)
    inc_c = next((c for c in nc if "income" in c), None)

    k1,k2,k3,k4 = st.columns(4)
    with k1: st.markdown(kpi_card("Total Customers", f"{len(fdf):,}"), unsafe_allow_html=True)
    with k2: st.markdown(kpi_card("Avg Purchase", f"AED {fdf[amt_c].mean():,.0f}" if amt_c else "—"), unsafe_allow_html=True)
    with k3: st.markdown(kpi_card("Churn Rate", f"{fdf[chu_c].mean()*100:.1f}%" if chu_c else "—"), unsafe_allow_html=True)
    with k4: st.markdown(kpi_card("Avg Income", f"AED {fdf[inc_c].mean():,.0f}" if inc_c else "—"), unsafe_allow_html=True)
    st.markdown("---")

    # Drill-down
    st.subheader("🔎 Drill-Down Analysis")
    if cc and nc:
        d1,d2,d3 = st.columns(3)
        with d1: dp = st.selectbox("Primary Dimension", cc, key="dp")
        with d2: ds = st.selectbox("Secondary Breakdown", ["None"]+cc, key="ds")
        with d3: dm = st.selectbox("Metric", nc, key="dm")
        ag_name = st.radio("Aggregation", ["Mean","Sum","Count","Median"], horizontal=True)
        ag_fn = {"Mean":"mean","Sum":"sum","Count":"count","Median":"median"}[ag_name]
        try:
            if ds == "None":
                g = fdf.groupby(dp)[dm].agg(ag_fn).reset_index().sort_values(dm,ascending=False)
                fig = px.bar(g, x=dp, y=dm, color=dp, template="plotly_white",
                             title=f"{ag_name} of {dm} by {dp}", height=380)
            else:
                g = fdf.groupby([dp,ds])[dm].agg(ag_fn).reset_index()
                fig = px.bar(g, x=dp, y=dm, color=ds, barmode="group", template="plotly_white",
                             title=f"{ag_name} of {dm} by {dp} & {ds}", height=380)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Drill-down error: {e}")

    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1:
        st.subheader("📉 Distribution")
        hc = st.selectbox("Column", nc, key="hcol")
        hcolor = st.selectbox("Colour by", ["None"]+cc, key="hcol2")
        fig_h = px.histogram(fdf, x=hc, color=(None if hcolor=="None" else hcolor),
                             nbins=40, marginal="box", template="plotly_white",
                             title=f"Distribution: {hc}")
        st.plotly_chart(fig_h, use_container_width=True)
    with c2:
        st.subheader("🌡️ Correlation Heatmap")
        corr_sel = st.multiselect("Columns", nc, default=nc[:min(8,len(nc))], key="corrsel")
        if len(corr_sel) >= 2:
            corr = fdf[corr_sel].corr()
            fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                                 aspect="auto", template="plotly_white", title="Correlation Matrix")
            st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown("---")
    st.subheader("🔵 Scatter Plot")
    s1,s2,s3,s4 = st.columns(4)
    with s1: sx = st.selectbox("X axis", nc, key="scx")
    with s2: sy = st.selectbox("Y axis", nc, index=min(1,len(nc)-1), key="scy")
    with s3: sc = st.selectbox("Colour", ["None"]+cc, key="scc")
    with s4: sz = st.selectbox("Size",   ["None"]+nc, key="scz")
    try:
        fig_sc = px.scatter(fdf, x=sx, y=sy,
                            color=(None if sc=="None" else sc),
                            size=(None if sz=="None" else sz),
                            opacity=0.6, template="plotly_white", title=f"{sx} vs {sy}")
        st.plotly_chart(fig_sc, use_container_width=True)
    except Exception as e:
        st.error(f"Scatter error: {e}")

    if cc:
        st.markdown("---")
        st.subheader("📦 Box Plot")
        b1,b2 = st.columns(2)
        with b1: bn = st.selectbox("Numeric",  nc, key="bn")
        with b2: bc = st.selectbox("Category", cc, key="bc")
        try:
            fig_box = px.box(fdf, x=bc, y=bn, color=bc, points="outliers",
                             template="plotly_white", title=f"{bn} by {bc}")
            st.plotly_chart(fig_box, use_container_width=True)
        except Exception as e:
            st.error(f"Box error: {e}")

        st.markdown("---")
        st.subheader("🥧 Category Distribution")
        pie_c = st.selectbox("Column", cc, key="pie")
        pc = fdf[pie_c].value_counts().reset_index()
        pc.columns = [pie_c,"count"]
        fig_pie = px.pie(pc, names=pie_c, values="count",
                         template="plotly_white", title=f"{pie_c} Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)

# =============================================================================
# TAB 2 — CLASSIFICATION
# =============================================================================
with t_clf:
    st.header("🤖 Classification — All Algorithms Comparison")
    from sklearn.preprocessing   import LabelEncoder, StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics         import (accuracy_score, precision_score, recall_score,
                                          f1_score, confusion_matrix, roc_auc_score)
    from sklearn.linear_model    import LogisticRegression
    from sklearn.tree            import DecisionTreeClassifier
    from sklearn.ensemble        import (RandomForestClassifier, GradientBoostingClassifier,
                                          AdaBoostClassifier, ExtraTreesClassifier)
    from sklearn.svm             import SVC
    from sklearn.neighbors       import KNeighborsClassifier
    from sklearn.naive_bayes     import GaussianNB
    from sklearn.neural_network  import MLPClassifier

    nc_c = num_cols(fdf); cc_c = cat_cols(fdf)
    bin_c = [c for c in nc_c if fdf[c].nunique() == 2]
    tgt_opts = bin_c + cc_c
    if not tgt_opts:
        st.warning("No binary or categorical target columns found.")
    else:
        col1,col2 = st.columns(2)
        with col1:
            clf_tgt = st.selectbox("🎯 Target variable", tgt_opts, key="clf_tgt")
        feat_pool = [c for c in nc_c if c != clf_tgt]
        with col2:
            clf_feats = st.multiselect("📐 Features", feat_pool,
                                        default=feat_pool[:min(6,len(feat_pool))], key="clf_feats")
        test_sz = st.slider("Test split %", 10, 40, 20, key="clf_test") / 100

        if st.button("🚀 Run All 10 Classifiers", key="clf_run"):
            if not clf_feats:
                st.warning("Select at least one feature.")
            else:
                with st.spinner("Training 10 models…"):
                    try:
                        tmp = fdf[clf_feats + [clf_tgt]].dropna()
                        X   = tmp[clf_feats].values.astype(float)
                        le_y = LabelEncoder()
                        y    = le_y.fit_transform(tmp[clf_tgt].astype(str).values)
                        n_cls = len(np.unique(y))
                        Xtr,Xte,ytr,yte = train_test_split(
                            X, y, test_size=test_sz, random_state=42,
                            stratify=y if n_cls < 20 else None)
                        sc_std = StandardScaler()
                        Xtr_s = sc_std.fit_transform(Xtr)
                        Xte_s = sc_std.transform(Xte)
                        avg = "weighted" if n_cls > 2 else "binary"

                        MODELS = [
                            ("Logistic Regression",  LogisticRegression(max_iter=1000,random_state=42), True),
                            ("Decision Tree",         DecisionTreeClassifier(random_state=42),           False),
                            ("Random Forest",         RandomForestClassifier(100,random_state=42,n_jobs=-1), False),
                            ("Gradient Boosting",     GradientBoostingClassifier(random_state=42),       False),
                            ("AdaBoost",              AdaBoostClassifier(random_state=42),               False),
                            ("Extra Trees",           ExtraTreesClassifier(100,random_state=42,n_jobs=-1), False),
                            ("SVM",                   SVC(probability=True,random_state=42),             True),
                            ("KNN (k=5)",             KNeighborsClassifier(5),                           True),
                            ("Naive Bayes",           GaussianNB(),                                      False),
                            ("Neural Net (MLP)",      MLPClassifier((64,32),max_iter=500,random_state=42), True),
                        ]

                        rows, cms, trained = [], {}, {}
                        for name, mdl, scaled in MODELS:
                            Xt = Xtr_s if scaled else Xtr
                            Xv = Xte_s if scaled else Xte
                            mdl.fit(Xt, ytr)
                            pred = mdl.predict(Xv)
                            trained[name] = mdl
                            try:
                                prob = mdl.predict_proba(Xv)
                                auc  = roc_auc_score(yte, prob if n_cls>2 else prob[:,1],
                                                      multi_class="ovr" if n_cls>2 else "raise")
                            except Exception:
                                auc = np.nan
                            rows.append({
                                "Model":     name,
                                "Accuracy":  round(accuracy_score(yte,pred),4),
                                "Precision": round(precision_score(yte,pred,average=avg,zero_division=0),4),
                                "Recall":    round(recall_score(yte,pred,average=avg,zero_division=0),4),
                                "F1 Score":  round(f1_score(yte,pred,average=avg,zero_division=0),4),
                                "AUC-ROC":   round(float(auc),4) if not np.isnan(auc) else "N/A",
                            })
                            cms[name] = confusion_matrix(yte,pred)

                        res = pd.DataFrame(rows).sort_values("F1 Score",ascending=False).reset_index(drop=True)
                        res.index += 1

                        st.subheader("📋 Performance Table")
                        num_m = ["Accuracy","Precision","Recall","F1 Score"]
                        st.dataframe(res.style.background_gradient(subset=num_m,cmap="YlGnBu"),
                                     use_container_width=True)

                        melt = res.melt(id_vars="Model",value_vars=num_m,var_name="Metric",value_name="Score")
                        fig_bar = px.bar(melt,x="Model",y="Score",color="Metric",barmode="group",
                                         template="plotly_white",height=430,
                                         title="All Models — Accuracy / Precision / Recall / F1")
                        fig_bar.update_layout(xaxis_tickangle=-30)
                        st.plotly_chart(fig_bar, use_container_width=True)

                        st.subheader("🕸️ Radar Chart")
                        fig_rad = go.Figure()
                        cats = num_m + [num_m[0]]
                        for _,row in res.iterrows():
                            vals = [row[m] for m in num_m] + [row[num_m[0]]]
                            fig_rad.add_trace(go.Scatterpolar(r=vals,theta=cats,fill="toself",name=row["Model"]))
                        fig_rad.update_layout(polar=dict(radialaxis=dict(range=[0,1])),
                                               template="plotly_white",title="Radar Comparison",height=480)
                        st.plotly_chart(fig_rad, use_container_width=True)

                        st.subheader("🟥 Confusion Matrices (Top 4)")
                        cm_cols = st.columns(2)
                        for i,m in enumerate(res["Model"].head(4)):
                            with cm_cols[i%2]:
                                fig_cm = px.imshow(cms[m],text_auto=True,color_continuous_scale="Blues",
                                                    title=m,template="plotly_white",aspect="auto")
                                st.plotly_chart(fig_cm, use_container_width=True)

                        tree_names = [n for n in trained if hasattr(trained[n],"feature_importances_")]
                        if tree_names:
                            bst = res[res["Model"].isin(tree_names)].iloc[0]["Model"]
                            fi  = pd.Series(trained[bst].feature_importances_,
                                             index=clf_feats).sort_values(ascending=True)
                            fig_fi = px.bar(fi,orientation="h",template="plotly_white",
                                             title=f"Feature Importance — {bst}",
                                             labels={"value":"Importance","index":"Feature"})
                            st.plotly_chart(fig_fi, use_container_width=True)

                    except Exception as e:
                        st.error(f"Classification failed: {e}")
                        import traceback; st.code(traceback.format_exc())

# =============================================================================
# TAB 3 — ARIMA
# =============================================================================
with t_arima:
    st.header("📈 ARIMA Time-Series Forecasting")

    nc_a = num_cols(fdf)
    date_col = next((c for c in fdf.columns
                     if any(k in c.lower() for k in ("date","time","month","year"))
                     and pd.api.types.is_datetime64_any_dtype(fdf[c])), None)
    default_m = next((c for c in nc_a if any(k in c for k in
                      ("amount","purchase","revenue","spend"))), nc_a[0] if nc_a else None)

    if not nc_a:
        st.warning("No numeric columns found.")
    else:
        r1,r2,r3 = st.columns(3)
        with r1:
            ts_metric = st.selectbox("📊 Metric to forecast", nc_a,
                                      index=nc_a.index(default_m) if default_m in nc_a else 0,
                                      key="ts_metric")
        with r2:
            ts_freq = st.selectbox("📅 Frequency", ["Monthly","Weekly","Daily"], key="ts_freq")
        with r3:
            ts_periods = st.slider("🔮 Forecast periods", 3, 24, 6, key="ts_periods")

        pc,dc,qc = st.columns(3)
        with pc: p_val = st.slider("p  (AR order)",      0, 5, 1, key="ap")
        with dc: d_val = st.slider("d  (differencing)",  0, 2, 1, key="ad")
        with qc: q_val = st.slider("q  (MA order)",      0, 5, 1, key="aq")

        if st.button("▶️ Run ARIMA Forecast", key="arima_run"):
            with st.spinner("Fitting ARIMA model…"):
                try:
                    from statsmodels.tsa.arima.model  import ARIMA as ARIMA_MDL
                    from statsmodels.tsa.stattools    import adfuller
                    from statsmodels.tsa.seasonal     import seasonal_decompose
                    from sklearn.metrics              import mean_absolute_error, mean_squared_error

                    freq_map = {"Monthly":"MS","Weekly":"W-MON","Daily":"D"}
                    alias    = freq_map[ts_freq]

                    # Build time series
                    if date_col:
                        ts = (fdf.set_index(date_col)[ts_metric]
                                 .sort_index()
                                 .resample(alias).mean()
                                 .dropna())
                    else:
                        # Synthesise a date index
                        idx = pd.date_range("2022-01-01", periods=len(fdf), freq="D")
                        ts  = (pd.Series(fdf[ts_metric].values, index=idx)
                                 .resample(alias).mean()
                                 .dropna())

                    if len(ts) < 8:
                        st.error(f"Only {len(ts)} data points after resampling. "
                                  "Switch to Daily or Weekly frequency.")
                        st.stop()

                    # ADF test
                    adf_stat, adf_p = adfuller(ts, autolag="AIC")[:2]
                    label_s = "✅ Stationary" if adf_p < 0.05 else "⚠️ Non-stationary — consider d ≥ 1"
                    st.info(f"**ADF Statistic:** {adf_stat:.4f}  |  **p-value:** {adf_p:.4f}  →  {label_s}")

                    # Seasonal decomposition
                    if len(ts) >= 24:
                        try:
                            dec = seasonal_decompose(ts, model="additive", period=12,
                                                      extrapolate_trend="freq")
                            fig_dec = make_subplots(rows=4, cols=1, shared_xaxes=True,
                                                     subplot_titles=["Observed","Trend","Seasonal","Residual"],
                                                     vertical_spacing=0.06)
                            colours = ["#2563eb","#10b981","#f59e0b","#ef4444"]
                            for i,(comp,col) in enumerate(zip(
                                    [dec.observed,dec.trend,dec.seasonal,dec.resid], colours),1):
                                fig_dec.add_trace(
                                    go.Scatter(x=comp.index, y=comp.values, mode="lines",
                                               line=dict(color=col,width=1.5),
                                               name=["Observed","Trend","Seasonal","Residual"][i-1]),
                                    row=i, col=1)
                            fig_dec.update_layout(height=640, title="Seasonal Decomposition",
                                                   template="plotly_white", showlegend=True)
                            st.plotly_chart(fig_dec, use_container_width=True)
                        except Exception:
                            pass

                    # Fit ARIMA
                    mdl_a  = ARIMA_MDL(ts, order=(p_val,d_val,q_val))
                    fit_a  = mdl_a.fit(method_kwargs={"warn_convergence": False})

                    # Forecast
                    fc_obj  = fit_a.get_forecast(steps=ts_periods)
                    fc_mean = fc_obj.predicted_mean
                    fc_ci   = fc_obj.conf_int(alpha=0.05)          # always shape (steps,2)
                    fc_lo   = fc_ci.iloc[:, 0]                     # position-based — name-safe
                    fc_hi   = fc_ci.iloc[:, 1]

                    # Chart
                    fig_fc = go.Figure()
                    fig_fc.add_trace(go.Scatter(x=ts.index, y=ts.values,
                                                 name="Historical", mode="lines",
                                                 line=dict(color="#2563eb",width=2)))
                    fv = fit_a.fittedvalues
                    fig_fc.add_trace(go.Scatter(x=fv.index, y=fv.values,
                                                 name="Fitted", mode="lines",
                                                 line=dict(color="#10b981",width=1.5,dash="dot")))
                    # CI band
                    ci_x = list(fc_ci.index) + list(fc_ci.index[::-1])
                    ci_y = list(fc_hi.values) + list(fc_lo.values[::-1])
                    fig_fc.add_trace(go.Scatter(x=ci_x, y=ci_y, fill="toself",
                                                 fillcolor="rgba(245,158,11,0.15)",
                                                 line=dict(color="rgba(0,0,0,0)"),
                                                 name="95% CI", hoverinfo="skip"))
                    fig_fc.add_trace(go.Scatter(x=fc_mean.index, y=fc_mean.values,
                                                 name="Forecast", mode="lines+markers",
                                                 line=dict(color="#f59e0b",width=2.5),
                                                 marker=dict(size=7)))
                    fig_fc.update_layout(
                        title=f"ARIMA({p_val},{d_val},{q_val}) Forecast — {ts_metric}",
                        xaxis_title="Date", yaxis_title=ts_metric,
                        template="plotly_white", height=460,
                        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
                    st.plotly_chart(fig_fc, use_container_width=True)

                    # Metrics
                    fv_c = fv.dropna()
                    av_c = ts.reindex(fv_c.index).dropna()
                    common = fv_c.index.intersection(av_c.index)
                    mae_v  = mean_absolute_error(av_c[common], fv_c[common])
                    rmse_v = float(np.sqrt(mean_squared_error(av_c[common], fv_c[common])))
                    mape_v = float(np.mean(np.abs((av_c[common]-fv_c[common])/(av_c[common]+1e-9)))*100)

                    m1,m2,m3,m4,m5 = st.columns(5)
                    m1.metric("AIC",  f"{fit_a.aic:.2f}")
                    m2.metric("BIC",  f"{fit_a.bic:.2f}")
                    m3.metric("MAE",  f"{mae_v:.2f}")
                    m4.metric("RMSE", f"{rmse_v:.2f}")
                    m5.metric("MAPE", f"{mape_v:.1f}%")

                    # Forecast table
                    st.subheader("📋 Forecast Table")
                    fc_df = pd.DataFrame({
                        "Period":    [str(d.date()) if hasattr(d,"date") else str(d)
                                      for d in fc_mean.index],
                        "Forecast":  fc_mean.values.round(2),
                        "Lower 95%": fc_lo.values.round(2),
                        "Upper 95%": fc_hi.values.round(2),
                    })
                    st.dataframe(fc_df, use_container_width=True)

                    # Residuals
                    st.subheader("📉 Residual Analysis")
                    resid = fit_a.resid.dropna()
                    rc1,rc2 = st.columns(2)
                    with rc1:
                        fig_res = px.line(x=resid.index, y=resid.values,
                                           template="plotly_white", title="Residuals over Time",
                                           labels={"x":"Date","y":"Residual"})
                        fig_res.add_hline(y=0, line_dash="dash", line_color="red")
                        st.plotly_chart(fig_res, use_container_width=True)
                    with rc2:
                        fig_rh = px.histogram(resid, nbins=30, template="plotly_white",
                                               title="Residual Distribution",
                                               labels={"value":"Residual"})
                        st.plotly_chart(fig_rh, use_container_width=True)

                except Exception as e:
                    st.error(f"❌ ARIMA Error: {e}")
                    import traceback; st.code(traceback.format_exc())

# =============================================================================
# TAB 4 — CLUSTERING
# =============================================================================
with t_clust:
    st.header("🔗 Clustering — K-Means + Hierarchical")

    from sklearn.cluster         import KMeans, AgglomerativeClustering
    from sklearn.preprocessing   import StandardScaler as SS
    from sklearn.metrics         import silhouette_score, adjusted_rand_score
    from scipy.cluster.hierarchy import linkage as sp_linkage

    nc_cl = num_cols(fdf)
    if len(nc_cl) < 2:
        st.warning("Need at least 2 numeric columns.")
    else:
        cl_feat = st.multiselect("Features", nc_cl, default=nc_cl[:min(4,len(nc_cl))], key="cl_feat")
        cc1,cc2,cc3 = st.columns(3)
        with cc1: max_k    = st.slider("Max K to test", 2, 15, 10, key="maxk")
        with cc2: chosen_k = st.slider("Final K",       2, 15,  4, key="chosenk")
        with cc3: lm       = st.selectbox("Linkage", ["ward","complete","average","single"], key="lm")

        if st.button("🔍 Run Clustering", key="cl_run") and len(cl_feat) >= 2:
            with st.spinner("Running…"):
                try:
                    tmp_cl = fdf[cl_feat].dropna().reset_index(drop=True)
                    Xcl    = SS().fit_transform(tmp_cl)

                    ine, sils = [], []
                    for k in range(2, max_k+1):
                        km  = KMeans(n_clusters=k, random_state=42, n_init=10)
                        lb  = km.fit_predict(Xcl)
                        ine.append(km.inertia_)
                        sils.append(silhouette_score(Xcl, lb))

                    k_ax = list(range(2, max_k+1))
                    fig_es = make_subplots(rows=1, cols=2,
                                           subplot_titles=["Elbow — Inertia","Silhouette Score"])
                    fig_es.add_trace(go.Scatter(x=k_ax, y=ine, mode="lines+markers",
                                                 name="Inertia", line=dict(color="#2563eb")), row=1,col=1)
                    fig_es.add_trace(go.Scatter(x=k_ax, y=sils, mode="lines+markers",
                                                 name="Silhouette", line=dict(color="#10b981")), row=1,col=2)
                    best_k = k_ax[int(np.argmax(sils))]
                    fig_es.add_trace(go.Scatter(x=[best_k], y=[max(sils)], mode="markers",
                                                 marker=dict(size=12,color="red"),
                                                 name=f"Best K={best_k}"), row=1,col=2)
                    fig_es.update_layout(title="K Selection: Elbow & Silhouette",
                                          template="plotly_white", height=360)
                    st.plotly_chart(fig_es, use_container_width=True)
                    st.success(f"Best K by Silhouette: **{best_k}** (score = {max(sils):.4f})")

                    # K-Means
                    km_f   = KMeans(n_clusters=chosen_k, random_state=42, n_init=10)
                    lbl_km = km_f.fit_predict(Xcl)
                    tmp_out = tmp_cl.copy()
                    tmp_out["KMeans"] = lbl_km.astype(str)

                    cxc,cyc = st.columns(2)
                    with cxc: cx = st.selectbox("X axis", cl_feat, key="cx")
                    with cyc: cy = st.selectbox("Y axis", cl_feat, index=min(1,len(cl_feat)-1), key="cy")

                    fig_km = px.scatter(tmp_out, x=cx, y=cy, color="KMeans",
                                         opacity=0.7, template="plotly_white",
                                         title=f"K-Means (K={chosen_k})")
                    st.plotly_chart(fig_km, use_container_width=True)

                    st.subheader("📋 Cluster Mean Profiles")
                    prof = tmp_out.groupby("KMeans")[cl_feat].mean().round(2)
                    st.dataframe(prof.style.background_gradient(cmap="Blues"), use_container_width=True)

                    # Dendrogram
                    st.subheader("🌳 Hierarchical Dendrogram")
                    n_s  = min(300, len(Xcl))
                    Xs   = Xcl[:n_s]
                    try:
                        fig_dend = ff.create_dendrogram(
                            Xs, linkagefun=lambda x: sp_linkage(x, method=lm),
                            color_threshold=0.6)
                        fig_dend.update_layout(
                            title=f"Dendrogram — linkage='{lm}', n={n_s}",
                            template="plotly_white", height=480,
                            xaxis=dict(showticklabels=False))
                        st.plotly_chart(fig_dend, use_container_width=True)
                    except Exception as de:
                        st.warning(f"Dendrogram: {de}")

                    # Agglomerative
                    hc     = AgglomerativeClustering(n_clusters=chosen_k, linkage=lm)
                    lbl_hc = hc.fit_predict(Xcl)
                    tmp_out["HClust"] = lbl_hc.astype(str)
                    fig_hc = px.scatter(tmp_out, x=cx, y=cy, color="HClust",
                                         opacity=0.7, template="plotly_white",
                                         title=f"Agglomerative Clustering (K={chosen_k})")
                    st.plotly_chart(fig_hc, use_container_width=True)

                    ari = adjusted_rand_score(lbl_km, lbl_hc)
                    st.info(f"**Adjusted Rand Index (KMeans vs HC):** {ari:.4f}  "
                             "(1.0 = identical, 0 = random)")

                except Exception as e:
                    st.error(f"Clustering error: {e}")
                    import traceback; st.code(traceback.format_exc())

# =============================================================================
# TAB 5 — ASSOCIATION RULES
# =============================================================================
with t_arm:
    st.header("🛒 Association Rule Mining")
    try:
        from mlxtend.frequent_patterns import apriori, association_rules
        from mlxtend.preprocessing     import TransactionEncoder

        cc_ar = cat_cols(fdf)
        if len(cc_ar) < 2:
            st.warning("Need at least 2 categorical columns.")
        else:
            a1,a2 = st.columns(2)
            with a1:
                basket_cols = st.multiselect("Basket columns", cc_ar,
                                              default=cc_ar[:min(3,len(cc_ar))], key="arm_bc")
            with a2:
                min_sup = st.slider("Min Support",    0.01, 0.5,  0.05, 0.01, key="arm_sup")
            min_conf = st.slider("Min Confidence", 0.1,  1.0,  0.30, 0.05, key="arm_conf")
            min_lift = st.slider("Min Lift",        1.0,  10.0, 1.20, 0.10, key="arm_lift")

            if st.button("⛏️ Mine Rules", key="arm_run"):
                if len(basket_cols) < 2:
                    st.warning("Select at least 2 columns.")
                else:
                    with st.spinner("Mining…"):
                        try:
                            tmp_ar = fdf[basket_cols].dropna().astype(str)
                            txns   = tmp_ar.apply(
                                lambda r: [f"{c}={v}" for c,v in r.items()], axis=1).tolist()
                            te  = TransactionEncoder()
                            bdf = pd.DataFrame(te.fit_transform(txns), columns=te.columns_)
                            freq = apriori(bdf, min_support=min_sup, use_colnames=True)
                            if len(freq) == 0:
                                st.warning("No itemsets found — lower min support.")
                            else:
                                rules = association_rules(freq, metric="lift",
                                                           min_threshold=min_lift)
                                rules = rules[rules["confidence"] >= min_conf].sort_values(
                                    "lift",ascending=False).reset_index(drop=True)
                                st.success(f"**{len(rules)}** rules from **{len(freq)}** itemsets.")

                                rd = rules.copy()
                                rd["antecedents"] = rd["antecedents"].apply(lambda x:", ".join(list(x)))
                                rd["consequents"]  = rd["consequents"].apply(lambda x:", ".join(list(x)))
                                show = [c for c in ["antecedents","consequents","support",
                                                     "confidence","lift","leverage"] if c in rd.columns]
                                st.dataframe(rd[show].head(30).style.background_gradient(
                                    subset=["lift","confidence"],cmap="Greens"), use_container_width=True)

                                st.subheader("🔵 Scatter: Support × Confidence × Lift")
                                sc1,sc2 = st.columns(2)
                                with sc1: asx = st.selectbox("X",["support","confidence","lift"],index=0,key="asx")
                                with sc2: asy = st.selectbox("Y",["support","confidence","lift"],index=1,key="asy")
                                rd["rule"] = rd["antecedents"] + " → " + rd["consequents"]
                                fig_asc = px.scatter(rd.head(100), x=asx, y=asy, size="lift",
                                                      color="lift", hover_data=["rule","support","confidence","lift"],
                                                      color_continuous_scale="Viridis",
                                                      title=f"Rules Scatter — {asx} vs {asy}",
                                                      template="plotly_white", height=480)
                                st.plotly_chart(fig_asc, use_container_width=True)

                                st.subheader("📊 Lift Distribution")
                                fig_lh = px.histogram(rd, x="lift", nbins=30,
                                                       color_discrete_sequence=["#2563eb"],
                                                       template="plotly_white", title="Lift Distribution")
                                st.plotly_chart(fig_lh, use_container_width=True)

                                st.subheader("🏆 Top 15 Rules by Lift")
                                fig_top = px.bar(rd.head(15), x="lift", y="rule", orientation="h",
                                                  color="confidence", color_continuous_scale="Blues",
                                                  template="plotly_white", height=480,
                                                  title="Top 15 Rules by Lift")
                                st.plotly_chart(fig_top, use_container_width=True)

                        except Exception as e:
                            st.error(f"Error: {e}")
                            import traceback; st.code(traceback.format_exc())
    except ImportError:
        st.error("mlxtend not installed — run: pip install mlxtend")

# =============================================================================
# TAB 6 — WHAT-IF SIMULATOR   ← ROOT CAUSE FIXED HERE
# =============================================================================
with t_sim:
    st.header("🎛️ What-If Simulator")
    st.caption("Configure a customer profile and get a predicted outcome from a trained Random Forest.")

    from sklearn.ensemble      import RandomForestClassifier as RFC, RandomForestRegressor as RFR
    from sklearn.preprocessing import LabelEncoder as LE

    nc_s  = num_cols(fdf)
    cc_s  = cat_cols(fdf)
    bin_s = [c for c in nc_s if fdf[c].nunique() == 2]
    tgt_s = bin_s + cc_s

    if not tgt_s:
        st.warning("No suitable target columns found.")
    else:
        with st.expander("⚙️ Model Settings", expanded=True):
            ws1,ws2 = st.columns(2)
            with ws1:
                sim_tgt = st.selectbox("🎯 Target", tgt_s, key="sim_tgt")
            nfp = [c for c in nc_s if c not in bin_s]
            with ws2:
                sim_nf = st.multiselect("📐 Numeric features", nfp,
                                         default=nfp[:min(5,len(nfp))], key="sim_nf")
            sim_cf = st.multiselect("🏷️ Categorical features", cc_s,
                                     default=cc_s[:min(3,len(cc_s))], key="sim_cf")

        # ── All feature lists are plain Python lists throughout ──────────────
        num_feats = list(sim_nf)   # guaranteed list
        cat_feats = list(sim_cf)   # guaranteed list
        all_feats = num_feats + cat_feats

        if not all_feats:
            st.info("Select at least one feature to continue.")
        else:
            # ── Train model ──────────────────────────────────────────────────
            # Cache key uses a string hash — avoids any tuple/list concat issues
            cache_key = f"{sim_tgt}|{'|'.join(all_feats)}|{len(fdf)}"

            @st.cache_data(show_spinner=False)
            def train_sim_model(df_pickle_bytes: bytes, target: str,
                                 num_f: list, cat_f: list) -> tuple:
                """Train RF on pickled dataframe. All args are plain Python types."""
                data = pickle.loads(df_pickle_bytes)
                all_cols = num_f + cat_f + [target]        # list + list + list = list ✓
                tmp = data[all_cols].dropna()

                X = tmp[num_f + cat_f].copy()              # list concat — always safe
                y = tmp[target].copy()

                # Encode categoricals
                encoders = {}
                for col in cat_f:
                    enc = LE()
                    X[col] = enc.fit_transform(X[col].astype(str))
                    encoders[col] = enc

                # Encode target
                is_cls = (y.dtype == object) or (y.nunique() <= 10)
                tgt_enc = None
                if y.dtype == object:
                    tgt_enc = LE()
                    y = pd.Series(tgt_enc.fit_transform(y.astype(str)), index=y.index)
                else:
                    y = y.astype(float)

                mdl = (RFC(n_estimators=100, random_state=42, n_jobs=-1)
                       if is_cls
                       else RFR(n_estimators=100, random_state=42, n_jobs=-1))
                mdl.fit(X, y)
                return mdl, encoders, tgt_enc, is_cls

            df_bytes = pickle.dumps(fdf)
            try:
                sim_mdl, sim_enc, sim_tgt_enc, sim_is_cls = train_sim_model(
                    df_bytes,
                    sim_tgt,
                    num_feats,    # plain list
                    cat_feats,    # plain list
                )
                st.success("✅ Model trained. Build a profile below and click Predict.")
            except Exception as e:
                st.error(f"Model training failed: {e}")
                import traceback; st.code(traceback.format_exc())
                sim_mdl = None

            if sim_mdl is not None:
                st.markdown("---")
                st.subheader("🎚️ Customer Profile Builder")
                input_vals = {}

                # Numeric sliders
                if num_feats:
                    for i in range(0, len(num_feats), 3):
                        batch = num_feats[i:i+3]
                        cols_r = st.columns(len(batch))
                        for col_w, feat in zip(cols_r, batch):
                            mn  = float(fdf[feat].min())
                            mx  = float(fdf[feat].max())
                            med = float(fdf[feat].median())
                            # Ensure min != max to avoid slider crash
                            if mn == mx:
                                mx = mn + 1.0
                            with col_w:
                                input_vals[feat] = st.slider(
                                    feat.replace("_"," ").title(),
                                    min_value=mn, max_value=mx, value=med,
                                    key=f"ss_{feat}")

                # Categorical dropdowns
                if cat_feats:
                    for i in range(0, len(cat_feats), 3):
                        batch = cat_feats[i:i+3]
                        cols_r = st.columns(len(batch))
                        for col_w, feat in zip(cols_r, batch):
                            opts = sorted(fdf[feat].dropna().unique().tolist())
                            with col_w:
                                input_vals[feat] = st.selectbox(
                                    feat.replace("_"," ").title(), opts,
                                    key=f"sd_{feat}")

                if st.button("🔮 Predict Outcome", key="sim_pred"):
                    try:
                        # Build encoded input row — all plain dict operations
                        row_enc = {}
                        for feat in num_feats:
                            row_enc[feat] = float(input_vals[feat])
                        for feat in cat_feats:
                            enc = sim_enc[feat]
                            val = str(input_vals[feat])
                            row_enc[feat] = int(enc.transform([val])[0]) if val in enc.classes_ else 0

                        X_in = pd.DataFrame([row_enc])[num_feats + cat_feats]

                        st.markdown("---")
                        r1,r2,_ = st.columns(3)

                        if sim_is_cls:
                            pred_c  = sim_mdl.predict(X_in)[0]
                            pred_p  = sim_mdl.predict_proba(X_in)[0]
                            classes = sim_mdl.classes_
                            label   = (str(sim_tgt_enc.inverse_transform([pred_c])[0])
                                        if sim_tgt_enc else str(pred_c))
                            conf    = float(pred_p.max())
                            cls_lbl = ([str(sim_tgt_enc.inverse_transform([c])[0]) for c in classes]
                                        if sim_tgt_enc else [str(c) for c in classes])
                            with r1: st.markdown(kpi_card("Predicted Class",  label),          unsafe_allow_html=True)
                            with r2: st.markdown(kpi_card("Confidence",       f"{conf*100:.1f}%"), unsafe_allow_html=True)
                            fig_pb = px.bar(x=cls_lbl, y=pred_p, color=cls_lbl,
                                             title="Class Probability", template="plotly_white",
                                             labels={"x":"Class","y":"Probability"})
                            st.plotly_chart(fig_pb, use_container_width=True)

                        else:
                            pred_v = float(sim_mdl.predict(X_in)[0])
                            actual = fdf[sim_tgt].dropna()
                            pct    = float((actual < pred_v).mean() * 100)
                            with r1: st.markdown(kpi_card(f"Predicted {sim_tgt.replace('_',' ').title()}", f"{pred_v:,.2f}"), unsafe_allow_html=True)
                            with r2: st.markdown(kpi_card("Percentile",       f"{pct:.0f}th"),   unsafe_allow_html=True)
                            fig_dv = px.histogram(actual, nbins=40, template="plotly_white",
                                                   title="Your Prediction vs Dataset Distribution")
                            fig_dv.add_vline(x=pred_v, line_color="red", line_width=2,
                                              annotation_text=f"Pred: {pred_v:,.2f}",
                                              annotation_position="top right")
                            st.plotly_chart(fig_dv, use_container_width=True)

                        # Feature importance
                        st.subheader("📊 Feature Importance")
                        fi = pd.Series(sim_mdl.feature_importances_,
                                        index=num_feats + cat_feats).sort_values(ascending=True)
                        fig_fi = px.bar(fi, orientation="h", template="plotly_white",
                                         title="Feature Importance — Random Forest",
                                         labels={"value":"Importance","index":"Feature"})
                        st.plotly_chart(fig_fi, use_container_width=True)

                        # Sensitivity analysis
                        if num_feats:
                            st.subheader("📐 Sensitivity Analysis")
                            sens_f = st.selectbox("Vary this feature", num_feats, key="sf")
                            sens_x = np.linspace(float(fdf[sens_f].min()),
                                                  float(fdf[sens_f].max()), 40)
                            sens_y = []
                            for v in sens_x:
                                ri = row_enc.copy()
                                ri[sens_f] = float(v)
                                Xi = pd.DataFrame([ri])[num_feats + cat_feats]
                                if sim_is_cls:
                                    sens_y.append(float(sim_mdl.predict_proba(Xi)[0].max()))
                                else:
                                    sens_y.append(float(sim_mdl.predict(Xi)[0]))
                            fig_sa = px.line(x=sens_x, y=sens_y, template="plotly_white",
                                              title=f"How {sens_f} influences {sim_tgt}",
                                              labels={"x":sens_f,"y":"Prediction / Confidence"})
                            fig_sa.add_vline(x=float(input_vals[sens_f]), line_dash="dash",
                                              line_color="red", annotation_text="Current value")
                            st.plotly_chart(fig_sa, use_container_width=True)

                    except Exception as e:
                        st.error(f"Prediction error: {e}")
                        import traceback; st.code(traceback.format_exc())
