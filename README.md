# Workora Interactive Business Intelligence Dashboard

A Streamlit + Plotly dashboard built from the supplied Workora synthetic analytics data pack.

## Features
- KPI cards: Total Revenue, Active Users (session proxy), Churn Rate, Average Ticket Size
- Sidebar filters: Date Range, Region/City, Category
- Acquisition & engagement: sessions over time, traffic source, device mix, registration funnel
- Customer retention: churn by contract, tenure distribution, monthly charges, payment methods
- Regional market: interactive map, state demand, market data table
- A/B testing: variant conversion rates and revenue
- Data-quality notes, metric definitions and assumptions

## Run locally
1. Install Python 3.10 or newer.
2. Extract this project folder.
3. Open a terminal in the project folder and run:

   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

4. Open the local URL shown in the terminal (usually http://localhost:8501).

## Publish a public dashboard (Streamlit Community Cloud)
1. Create/sign in to GitHub and create a new public repository.
2. Upload `app.py`, `requirements.txt`, and the complete `data` folder.
3. Visit https://share.streamlit.io/ and connect GitHub.
4. Select your repository, branch, and `app.py` as the main file.
5. Deploy. Copy the public `*.streamlit.app` URL after the app finishes building.
6. Open the URL in a private/incognito browser window to verify public access, then submit that URL to Workora.

## Data and methodology
All records in the supplied files are synthetic and intended for learning, not actual Workora business performance.

- Duplicates are removed by the dataset's stated unique key.
- Invalid dates are excluded from date-based views.
- Numeric fields are coerced to numeric values. Missing customer total charges are estimated as MonthlyChargesINR × TenureMonths.
- Session duration outliers are capped at the 99th percentile for chart display. Original CSV files are not modified.
- Revenue is the sum of OrderValueINR for converted visitors in the filtered A/B dataset.
- Average Ticket Size is the mean OrderValueINR among converted visitors.
- Active Users is represented by unique website sessions because the traffic data has SessionID but no user-level ID.
- Churn Rate is the share of customers marked `Yes` in the churn dataset. That dataset has no date field, so the date filter does not affect churn.
- Region filters match `Region` in traffic/churn and `City` in regional market.
- Category filters match `DeviceCategory`, `Device`, or `SubscriptionType` in their respective views.
- A/B results are descriptive; the dashboard does not claim statistical significance.

## Files
- `app.py` — dashboard application
- `requirements.txt` — Python dependencies
- `data/` — four supplied CSV datasets
