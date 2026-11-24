import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Workora | Interactive BI Dashboard", page_icon="📊", layout="wide")
DATA = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    traffic = pd.read_csv(DATA / "web_traffic.csv")
    churn = pd.read_csv(DATA / "customer_churn.csv")
    market = pd.read_csv(DATA / "regional_market.csv")
    ab = pd.read_csv(DATA / "checkout_ab_test.csv")

    traffic["Date"] = pd.to_datetime(traffic["Date"], errors="coerce")
    ab["Timestamp"] = pd.to_datetime(ab["Timestamp"], errors="coerce")
    for c in ["SessionDurationSec", "PageViews"]:
        traffic[c] = pd.to_numeric(traffic[c], errors="coerce")
    for c in ["MonthlyChargesINR", "TotalChargesINR", "TenureMonths", "SupportTickets", "LatePayments"]:
        churn[c] = pd.to_numeric(churn[c], errors="coerce")
    churn["TotalChargesINR"] = churn["TotalChargesINR"].fillna(
        churn["MonthlyChargesINR"] * churn["TenureMonths"]
    )
    for c in ["OrderValueINR"]:
        ab[c] = pd.to_numeric(ab[c], errors="coerce").fillna(0)
    traffic = traffic.drop_duplicates(subset="SessionID")
    churn = churn.drop_duplicates(subset="CustomerID")
    market = market.drop_duplicates(subset="RegionID")
    ab = ab.drop_duplicates(subset="VisitorID")
    traffic = traffic.dropna(subset=["Date"])
    ab = ab.dropna(subset=["Timestamp"])
    # Keep plausible values; cap extreme durations at the 99th percentile for display.
    upper = traffic["SessionDurationSec"].quantile(0.99)
    traffic["SessionDurationSec"] = traffic["SessionDurationSec"].clip(upper=upper)
    return traffic, churn, market, ab

traffic, churn, market, ab = load_data()

st.title("📊 Workora | Interactive Business Intelligence Dashboard")
st.caption("Learning project • Synthetic sample data • INR currency • Updated from the supplied CSV data pack")

with st.sidebar:
    st.header("Dashboard Filters")
    min_date = min(traffic["Date"].min().date(), ab["Timestamp"].min().date())
    max_date = max(traffic["Date"].max().date(), ab["Timestamp"].max().date())
    date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    regions = sorted(set(traffic["Region"].dropna().astype(str)) |
                     set(churn["Region"].dropna().astype(str)) |
                     set(market["City"].dropna().astype(str)))
    region_choice = st.selectbox("Region / City", ["All"] + regions)
    categories = sorted(set(traffic["DeviceCategory"].dropna().astype(str)) |
                        set(churn["SubscriptionType"].dropna().astype(str)) |
                        set(ab["Device"].dropna().astype(str)))
    category_choice = st.selectbox("Category", ["All"] + categories)
    st.divider()
    st.caption("Region filters use the matching Region or City field. Category filters use DeviceCategory, Device, or SubscriptionType depending on the view.")

if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
else:
    start, end = pd.Timestamp(min_date), pd.Timestamp(max_date) + pd.Timedelta(days=1)

tf = traffic[(traffic["Date"] >= start) & (traffic["Date"] <= end)].copy()
af = ab[(ab["Timestamp"] >= start) & (ab["Timestamp"] <= end)].copy()
cf = churn.copy()
mf = market.copy()

if region_choice != "All":
    tf = tf[tf["Region"].astype(str) == region_choice]
    cf = cf[cf["Region"].astype(str) == region_choice]
    mf = mf[mf["City"].astype(str) == region_choice]
if category_choice != "All":
    tf = tf[tf["DeviceCategory"].astype(str) == category_choice]
    cf = cf[cf["SubscriptionType"].astype(str) == category_choice]
    af = af[af["Device"].astype(str) == category_choice]

converted = af[af["Converted"].astype(str).str.lower() == "yes"]
revenue = converted["OrderValueINR"].sum()
avg_ticket = converted["OrderValueINR"].mean() if len(converted) else 0
churn_rate = (cf["Churn"].astype(str).str.lower() == "yes").mean() * 100 if len(cf) else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"₹{revenue:,.0f}")
k2.metric("Active Users*", f"{tf['SessionID'].nunique():,}")
k3.metric("Churn Rate", f"{churn_rate:.1f}%")
k4.metric("Average Ticket Size", f"₹{avg_ticket:,.0f}")
st.caption("*Active Users is represented by unique website sessions because the supplied traffic dataset contains SessionID rather than a user-level ID. Revenue and average ticket size are calculated from converted A/B checkout records.")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Acquisition & Engagement", "👥 Customer Retention", "🌍 Regional Market", "🧪 A/B Testing"])

with tab1:
    st.subheader("Website acquisition and engagement")
    c1, c2 = st.columns(2)
    if len(tf):
        daily = tf.groupby(tf["Date"].dt.date).agg(Sessions=("SessionID", "nunique"), Registrations=("Registered", lambda x: (x.astype(str).str.lower()=="yes").sum())).reset_index()
        c1.plotly_chart(px.line(daily, x="Date", y="Sessions", markers=True, title="Sessions over time"), use_container_width=True)
        source = tf.groupby("Source", as_index=False).agg(Sessions=("SessionID", "nunique"))
        c2.plotly_chart(px.bar(source, x="Source", y="Sessions", title="Sessions by traffic source"), use_container_width=True)
        c3, c4 = st.columns(2)
        device = tf.groupby("DeviceCategory", as_index=False).agg(Sessions=("SessionID", "nunique"))
        c3.plotly_chart(px.pie(device, names="DeviceCategory", values="Sessions", title="Device distribution"), use_container_width=True)
        funnel = pd.DataFrame({"Stage":["Sessions","Started registration","Registered"], "Count":[len(tf), (tf["StartedRegistration"].astype(str).str.lower()=="yes").sum(), (tf["Registered"].astype(str).str.lower()=="yes").sum()]})
        c4.plotly_chart(px.funnel(funnel, x="Count", y="Stage", title="Registration funnel"), use_container_width=True)
    else:
        st.info("No website traffic records match the selected filters.")

with tab2:
    st.subheader("Customer retention and churn")
    if len(cf):
        c1, c2 = st.columns(2)
        churn_by_contract = cf.groupby("ContractType", as_index=False).agg(Churned=("Churn", lambda x: (x.astype(str).str.lower()=="yes").sum()), Customers=("CustomerID","nunique"))
        churn_by_contract["Churn rate (%)"] = 100 * churn_by_contract["Churned"] / churn_by_contract["Customers"].replace(0, 1)
        c1.plotly_chart(px.bar(churn_by_contract, x="ContractType", y="Churn rate (%)", title="Churn rate by contract type"), use_container_width=True)
        c2.plotly_chart(px.histogram(cf, x="TenureMonths", color="Churn", nbins=18, title="Customer tenure distribution"), use_container_width=True)
        c3, c4 = st.columns(2)
        c3.plotly_chart(px.box(cf, x="Churn", y="MonthlyChargesINR", title="Monthly charges by churn status"), use_container_width=True)
        payment = cf.groupby("PaymentMethod", as_index=False).agg(Customers=("CustomerID","nunique"))
        c4.plotly_chart(px.bar(payment, x="PaymentMethod", y="Customers", title="Customers by payment method"), use_container_width=True)
    else:
        st.info("No customer records match the selected filters.")

with tab3:
    st.subheader("Regional market opportunity")
    if len(mf):
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.scatter_mapbox(mf, lat="Latitude", lon="Longitude", size="MonthlySearchDemand", color="State", hover_name="City", hover_data=["MonthlySearchDemand","ExistingCompetitors","LeadConversionRate"], zoom=3, height=480, mapbox_style="open-street-map", title="Demand by geographic location"), use_container_width=True)
        state = mf.groupby("State", as_index=False).agg(Search_Demand=("MonthlySearchDemand","sum"), Avg_Lead_Conversion=("LeadConversionRate","mean"))
        c2.plotly_chart(px.bar(state, x="State", y="Search_Demand", title="Monthly search demand by state"), use_container_width=True)
        st.dataframe(mf[["City","State","PopulationSegment","MonthlySearchDemand","ExistingCompetitors","LeadConversionRate","EstimatedAcquisitionCostINR"]], use_container_width=True, hide_index=True)
    else:
        st.info("No regional market records match the selected filters.")

with tab4:
    st.subheader("Checkout experiment performance")
    if len(af):
        variant = af.groupby("Variant", as_index=False).agg(Visitors=("VisitorID","nunique"), Conversions=("Converted", lambda x: (x.astype(str).str.lower()=="yes").sum()), Revenue=("OrderValueINR","sum"))
        variant["Conversion rate (%)"] = 100 * variant["Conversions"] / variant["Visitors"].replace(0, 1)
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.bar(variant, x="Variant", y="Conversion rate (%)", text_auto=".2f", title="Conversion rate by variant"), use_container_width=True)
        c2.plotly_chart(px.bar(variant, x="Variant", y="Revenue", text_auto=".2s", title="Revenue by variant"), use_container_width=True)
        st.dataframe(variant, use_container_width=True, hide_index=True)
        st.caption("This is a descriptive comparison. No statistical significance claim is made in this dashboard.")
    else:
        st.info("No A/B test records match the selected filters.")

with st.expander("Data quality, definitions and assumptions"):
    st.markdown("""
    - Source files are synthetic learning datasets supplied in the Workora data pack; they are not actual company results.
    - Duplicate records are removed using SessionID, CustomerID, RegionID and VisitorID respectively.
    - Invalid dates are excluded. Numeric fields are converted to numeric values; missing customer total charges are estimated as monthly charges × tenure.
    - Extreme session durations are capped at the 99th percentile for visualization; source CSV files remain unchanged.
    - Total Revenue = sum of OrderValueINR for converted checkout visitors in the selected date range and filters.
    - Average Ticket Size = mean OrderValueINR among converted checkout visitors.
    - Active Users is a proxy: unique SessionID count, since no user identifier exists in web_traffic.csv.
    - Churn Rate = customers marked Churn = Yes divided by filtered customers. The churn dataset has no date field, so the date filter does not apply to this KPI or retention tab.
    - Regional market records are filtered by City. Website and churn records are filtered by their Region field.
    - Category is matched to DeviceCategory (traffic), Device (A/B testing), and SubscriptionType (churn). Therefore, a category may apply to one or more views depending on matching values.
    """)
st.divider()
st.caption("Workora Interactive Dashboard | Built with Streamlit, Pandas and Plotly")
