import argparse
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DEFAULT_CSV = "sample_data.csv"


def resolve_csv(csv_path: str | None = None) -> Path:
    """Resolve the CSV file path from user input or default project files."""
    candidates = []
    if csv_path:
        candidates.append(Path(csv_path))
    candidates.extend(
        [
            Path(DEFAULT_CSV),
            Path("data") / DEFAULT_CSV,
            Path("examples") / DEFAULT_CSV,
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "No CSV file was found. Pass one with --file or place a sample_data.csv in the project root."
    )


def load_csv(csv_path: str | None = None) -> pd.DataFrame:
    """Load and normalize CSV content."""
    resolved = resolve_csv(csv_path)
    df = pd.read_csv(resolved)
    return df


def summarize_dataframe(df: pd.DataFrame) -> dict:
    """Return a basic summary of the DataFrame."""
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    return {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "count": int(len(df.columns)),
        "numeric_columns": numeric_columns,
        "missing_values": int(df.isna().sum().sum()),
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
    }


def build_chart(df: pd.DataFrame):
    """Create a chart from the first numeric column using the first categorical column if available."""
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    if not numeric_columns:
        return None

    numeric_column = numeric_columns[0]
    label_column = None
    for column in df.columns:
        if column != numeric_column and df[column].nunique() <= min(len(df), 20):
            label_column = column
            break

    if label_column:
        chart_df = df[[label_column, numeric_column]].copy()
        chart_df = chart_df.dropna(subset=[label_column, numeric_column])
        if chart_df.empty:
            return None
        return px.bar(chart_df, x=label_column, y=numeric_column, title=f"{numeric_column} by {label_column}")

    chart_df = df[[numeric_column]].copy().dropna()
    if chart_df.empty:
        return None
    chart_df = chart_df.reset_index(drop=True)
    return px.line(chart_df, y=numeric_column, title=f"{numeric_column} trend")


def render_dashboard(csv_path: str | None = None) -> None:
    """Render the dashboard in Streamlit."""
    st.set_page_config(page_title="CSV Dashboard", layout="wide")
    df = load_csv(csv_path)
    st.title("CSV Dashboard")

    if df.empty:
        st.warning("The CSV file is empty.")
        return

    summary = summarize_dataframe(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", summary["rows"])
    col2.metric("Columns", summary["count"])
    col3.metric("Numeric columns", len(summary["numeric_columns"]))

    st.subheader("Preview")
    st.dataframe(df.head(25), use_container_width=True)

    st.subheader("Summary")
    st.json(summary)

    chart = build_chart(df)
    if chart is not None:
        st.subheader("Visualization")
        st.plotly_chart(chart, use_container_width=True)

    summary_table = df.describe(include="all").transpose()
    st.subheader("Descriptive statistics")
    st.dataframe(summary_table, use_container_width=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a dashboard summary from a CSV file.")
    parser.add_argument("--file", dest="csv_path", help="Path to a CSV file to analyze.")
    args = parser.parse_args()

    try:
        df = load_csv(args.csv_path)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    result = summarize_dataframe(df)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
