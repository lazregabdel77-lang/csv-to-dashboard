# CSV to Dashboard

This project turns a CSV file into a small interactive dashboard.

## Quick start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run app.py -- --file sample_data.csv
   ```
3. Or use the CLI summary mode:
   ```bash
   python app.py --file sample_data.csv
   ```

## What it does

- Loads a CSV file
- Shows a preview table
- Summarizes key metrics
- Visualizes numeric columns with Plotly charts
- Works with common CSV files without extra setup
