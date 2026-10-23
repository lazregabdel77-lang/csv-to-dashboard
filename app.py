"""CSV-to-Dashboard: upload any sales CSV and get KPIs, trends, anomalies and insights."""
import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="CSV to Dashboard", page_icon="📊", layout="wide")


# ---------- helpers ----------
@st.cache_data
def generate_sample() -> pd.DataFrame:
    """Synthetic daily sales data (2024-2025) so the demo works without any file."""
    rng = np.random.default_rng(42)
    days = pd.date_range("2024-01-01", "2025-12-31", freq="D")
    prods = {"Laptop": ("Electronics", 620), "Phone": ("Electronics", 410), "Headphones": ("Accessories", 75),
             "Keyboard": ("Accessories", 45), "Desk": ("Furniture", 230), "Chair": ("Furniture", 160),
             "Monitor": ("Electronics", 280)}
    regions = ["Oran", "Algiers", "Constantine", "Annaba"]
    rows = []
    for d in days:
        for _ in range(rng.poisson(5 + 3 * (d.month in (11, 12)) + 0.004 * (d - days[0]).days)):
            p = rng.choice(list(prods))
            cat, price = prods[p]
            q = int(rng.integers(1, 4))
            rows.append((d, p, cat, rng.choice(regions), q, round(q * price * rng.uniform(0.9, 1.1), 2)))
    return pd.DataFrame(rows, columns=["date", "product", "category", "region", "quantity", "revenue"])


@st.cache_data
def load_data(file) -> pd.DataFrame:
    df = generate_sample() if isinstance(file, str) and file == "__sample__" else pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns]
    df = df.drop_duplicates()
    return df


def detect_columns(df: pd.DataFrame):
    """Guess date, numeric and categorical columns."""
    date_cols, num_cols, cat_cols = [], [], []
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            num_cols.append(c)
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parsed = pd.to_datetime(df[c], errors="coerce", format="mixed")
        if parsed.notna().mean() > 0.8:
            date_cols.append(c)
        elif df[c].nunique() <= max(50, len(df) * 0.05):
            cat_cols.append(c)
    return date_cols, num_cols, cat_cols


def find_anomalies(series: pd.Series, threshold: float = 3.0) -> pd.DataFrame:
    """Flag points whose z-score is beyond +/- threshold."""
    std = series.std()
    if std == 0 or np.isnan(std):
        return pd.DataFrame(columns=["period", "value", "z_score"])
    z = (series - series.mean()) / std
    out = pd.DataFrame({"period": series.index, "value": series.values, "z_score": z.values})
    return out[out["z_score"].abs() >= threshold].reset_index(drop=True)


def pct_change(new: float, old: float):
    return None if old in (0, None) or np.isnan(old) else (new - old) / abs(old) * 100


def fmt(x: float) -> str:
    return f"{x:,.0f}" if abs(x) >= 100 else f"{x:,.2f}"


# ---------- sidebar ----------
st.title("📊 CSV to Dashboard")
st.caption("Upload a sales CSV and get KPIs, trends, anomaly detection and plain-language insights.")

with st.sidebar:
    st.header("1. Data")
    uploaded = st.file_uploader("Upload a CSV file", type="csv")
    use_sample = st.checkbox("Use sample data", value=uploaded is None)

source = uploaded if uploaded is not None else ("__sample__" if use_sample else None)
if source is None:
    st.info("Upload a CSV or tick 'Use sample data' in the sidebar.")
    st.stop()

try:
    df = load_data(source)
except Exception as e:  # noqa: BLE001
    st.error(f"Could not read this file: {e}")
    st.stop()

date_cols, num_cols, cat_cols = detect_columns(df)
if not num_cols:
    st.error("No numeric columns found. The dashboard needs at least one number column (e.g. revenue).")
    st.stop()

with st.sidebar:
    st.header("2. Columns")
    metric = st.selectbox("Metric to analyse", num_cols, index=num_cols.index("revenue") if "revenue" in num_cols else 0)
    date_col = st.selectbox("Date column", date_cols + ["(none)"]) if date_cols else "(none)"
    cat_col = st.selectbox("Group by", cat_cols + ["(none)"],
                           index=cat_cols.index("category") if "category" in cat_cols else 0) if cat_cols else "(none)"
    agg = st.radio("Aggregation", ["sum", "mean"], horizontal=True)

    if date_col != "(none)":
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        st.header("3. Filters")
        lo, hi = df[date_col].min().date(), df[date_col].max().date()
        start, end = st.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
        df = df[(df[date_col].dt.date >= start) & (df[date_col].dt.date <= end)]
        freq_label = st.radio("Trend granularity", ["Day", "Week", "Month"], index=2, horizontal=True)
        freq = {"Day": "D", "Week": "W", "Month": "MS"}[freq_label]

    if cat_col != "(none)":
        options = sorted(df[cat_col].dropna().astype(str).unique())
        chosen = st.multiselect(f"Filter {cat_col}", options, default=options)
        df = df[df[cat_col].astype(str).isin(chosen)]

if df.empty:
    st.warning("No rows match the current filters.")
    st.stop()

# ---------- KPIs ----------
total = df[metric].sum()
k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Total {metric}", fmt(total))
k2.metric(f"Average {metric} per row", fmt(df[metric].mean()))
k3.metric("Rows", f"{len(df):,}")

insights = []
trend = None
if date_col != "(none)":
    trend = df.set_index(date_col)[metric].resample(freq).agg(agg).dropna()
    if len(trend) >= 2:
        change = pct_change(trend.iloc[-1], trend.iloc[-2])
        k4.metric(f"Last {freq_label.lower()} vs previous", fmt(trend.iloc[-1]),
                  None if change is None else f"{change:+.1f}%")
        if change is not None:
            direction = "up" if change > 0 else "down"
            insights.append(f"The latest {freq_label.lower()} is **{direction} {abs(change):.1f}%** versus the one before.")
        best = trend.idxmax()
        insights.append(f"The best {freq_label.lower()} was **{best:%Y-%m-%d}** with {fmt(trend.max())}.")
else:
    k4.metric("Max", fmt(df[metric].max()))

# ---------- charts ----------
left, right = st.columns([3, 2])

with left:
    st.subheader("Trend")
    if trend is not None and len(trend) > 1:
        fig = px.line(trend.reset_index(), x=date_col, y=metric, markers=len(trend) < 60)
        anomalies = find_anomalies(trend)
        if not anomalies.empty:
            fig.add_scatter(x=anomalies["period"], y=anomalies["value"], mode="markers",
                            marker=dict(color="red", size=11, symbol="x"), name="Anomaly")
            top = anomalies.reindex(anomalies["z_score"].abs().sort_values(ascending=False).index).head(5)
            for _, a in top.iterrows():
                kind = "spike" if a["z_score"] > 0 else "drop"
                insights.append(f"Unusual **{kind}** on **{a['period']:%Y-%m-%d}** ({fmt(a['value'])}, z-score {a['z_score']:+.1f}).")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Pick a date column in the sidebar to see a trend.")

with right:
    st.subheader(f"{metric.title()} by {cat_col}" if cat_col != "(none)" else "Distribution")
    if cat_col != "(none)":
        grp = df.groupby(cat_col)[metric].agg(agg).sort_values(ascending=False).head(10).reset_index()
        st.plotly_chart(px.bar(grp, x=metric, y=cat_col, orientation="h").update_yaxes(autorange="reversed"),
                        width="stretch")
        share = grp[metric].iloc[0] / grp[metric].sum() * 100
        insights.append(f"**{grp[cat_col].iloc[0]}** leads {cat_col} with {fmt(grp[metric].iloc[0])} "
                        f"({share:.0f}% of the top-10 total).")
    else:
        st.plotly_chart(px.histogram(df, x=metric), width="stretch")

# ---------- insights ----------
st.subheader("💡 Auto-generated insights")
if insights:
    for line in insights:
        st.markdown(f"- {line}")
else:
    st.write("Select a date column and a grouping column to unlock more insights.")

# ---------- data & export ----------
with st.expander("Preview and download data"):
    st.dataframe(df.head(200), width="stretch")
    st.download_button("Download filtered data (CSV)", df.to_csv(index=False).encode("utf-8"),
                       file_name="filtered_data.csv", mime="text/csv")
    report = "# Insights\n\n" + "\n".join(f"- {i.replace('**', '')}" for i in insights)
    st.download_button("Download insights (Markdown)", report.encode("utf-8"),
                       file_name="insights.md", mime="text/markdown")
