# 📊 CSV to Dashboard

Upload any sales CSV and instantly get KPI cards, a trend chart, anomaly detection,
top-category breakdown and plain-language insights. Built with Python, Streamlit, Pandas and Plotly.

## Features
- Upload your own CSV, or tick "Use sample data" (generated in code, no file needed)
- `sample_data.csv` is a small example file to test the upload
- Auto-detects date, numeric and category columns
- KPI cards with period-over-period change
- Trend chart (day / week / month) with anomalies marked (z-score ≥ 3)
- Breakdown by any category column
- Auto-generated insights, downloadable as Markdown
- Filter by date range and category; export the filtered data

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy free
1. Push this folder to a public GitHub repo.
2. Go to https://share.streamlit.io, sign in with GitHub, choose the repo and `app.py`.
3. Add the live link to this README.

## Run with Docker (also works on Hugging Face Spaces)
```bash
docker build -t csv-dashboard .
docker run -p 8501:8501 csv-dashboard
```

## Expected CSV format
At least one numeric column (e.g. `revenue`). A date column and a category column unlock trends and breakdowns.
Example: `date, product, category, region, quantity, revenue`.

## Ideas to extend
- French / English interface toggle
- Revenue forecasting (e.g. Prophet or statsmodels)
- Customer segmentation (RFM)
