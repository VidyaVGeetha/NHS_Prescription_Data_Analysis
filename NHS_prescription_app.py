import urllib.request
import json
import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="NHS Scotland Prescription Dashboard",
    page_icon="💊",
    layout="wide",
)

# -----------------------------
# PURPLE-BLACK THEME STYLING
# -----------------------------
st.markdown("""
<style>

div[data-testid="stMetric"] {
    background-color: #1c1c1c;
    border: 1px solid #9b59b6;
    border-radius: 10px;
    padding: 10px;
}

div[data-testid="stMetricLabel"] {
    color: #b37fe0;
}

div[data-testid="stMetricValue"] {
    color: white;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# Title
# -----------------------------
st.title("💊 NHS Scotland Prescription Dashboard – API Version")
st.caption("Dark–Purple Theme • NHS OpenData API • Clean single-screen dashboard")

# -----------------------------
# API URL
# -----------------------------
API_URL = (
    "https://www.opendata.nhs.scot/api/3/action/datastore_search"
    "?resource_id=381166dd-3a07-4c12-93c3-6db7b12c042a"
)

# -----------------------------
# Load Data From API
# -----------------------------
@st.cache_data(show_spinner=True)
def load_data(max_rows=50000):
    all_records = []
    limit = 10000
    offset = 0

    while len(all_records) < max_rows:
        url = f"{API_URL}&limit={limit}&offset={offset}"
        with urllib.request.urlopen(url) as response:
            raw = response.read()
        data = json.loads(raw.decode("utf-8"))
        rows = data["result"]["records"]
        if not rows:
            break
        all_records.extend(rows)
        offset += limit

    return pd.DataFrame(all_records[:max_rows])


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("⚙ Data Settings")

max_rows = st.sidebar.slider(
    "Rows from API",
    10000, 100000, 50000, 10000
)

df = load_data(max_rows=max_rows)
st.sidebar.success(f"{len(df):,} rows loaded")

# -----------------------------
# Cleaning
# -----------------------------
df = df.dropna(subset=["BNFItemDescription"]).copy()

for col in ["NumberOfPaidItems", "GrossIngredientCost", "PaidQuantity"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.rename(columns={
    "BNFItemDescription": "Medicine",
    "NumberOfPaidItems": "Items",
    "GrossIngredientCost": "Cost",
    "PaidQuantity": "Quantity",
    "GPPractice": "Practice",
    "HBT": "HealthBoard",
    "PrescribedType": "Type"
})

# -----------------------------
# Health Board Filter
# -----------------------------
boards = ["All"] + sorted(df["HealthBoard"].dropna().unique())
selected_board = st.sidebar.selectbox("Health Board", boards)

df_view = df.copy()
if selected_board != "All":
    df_view = df_view[df_view["HealthBoard"] == selected_board]

# -----------------------------
# KPIs (Top Row)
# -----------------------------
total_items = int(df_view["Items"].sum())
total_cost = float(df_view["Cost"].sum())
unique_meds = df_view["Medicine"].nunique()
unique_practices = df_view["Practice"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Items", f"{total_items:,}")
c2.metric("Total Cost (£)", f"{total_cost:,.0f}")
c3.metric("Unique Medicines", f"{unique_meds:,}")
c4.metric("GP Practices", f"{unique_practices:,}")

st.markdown("---")

# -----------------------------
# MIDDLE ROW: LEFT (Top Medicines) + RIGHT (Donut Chart)
# -----------------------------
left, right = st.columns([2, 1])

with left:
    st.subheader("📊 Top Medicines")
    top_n = st.sidebar.slider("Top N", 5, 20, 10)

    top_cost = (
        df_view.groupby("Medicine")["Cost"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
        .reset_index()
    )

    fig_top = px.bar(
        top_cost,
        x="Cost",
        y="Medicine",
        orientation="h",
        title=f"Top {top_n} Medicines by Cost",
        color_discrete_sequence=['#9b59b6']
    )
    fig_top.update_layout(
        plot_bgcolor="#0e0e0e",
        paper_bgcolor="#0e0e0e",
        font_color="white"
    )
    left.plotly_chart(fig_top, use_container_width=True)

with right:
    st.subheader("💰 Cost by Prescribed Type")
    type_cost = df_view.groupby("Type")["Cost"].sum().reset_index()

    fig_donut = px.pie(
        type_cost,
        names="Type",
        values="Cost",
        hole=0.55,
        title="",
        color_discrete_sequence=px.colors.sequential.Purples
    )

    fig_donut.update_layout(
        plot_bgcolor="#0e0e0e",
        paper_bgcolor="#0e0e0e",
        font_color="white",
        showlegend=True
    )

    right.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# -----------------------------
# 3rd Row (Tabs)
# -----------------------------
st.subheader("🏥 Health Board Summary")

tab1, tab2 = st.tabs(["Items by Health Board", "Cost by Health Board"])

with tab1:
    hb_items = (
        df_view.groupby("HealthBoard")["Items"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig_hb1 = px.bar(
        hb_items,
        x="HealthBoard",
        y="Items",
        color_discrete_sequence=['#9b59b6']
    )
    fig_hb1.update_layout(
        plot_bgcolor="#0e0e0e",
        paper_bgcolor="#0e0e0e",
        font_color="white",
    )
    st.plotly_chart(fig_hb1, use_container_width=True)

with tab2:
    hb_cost = (
        df_view.groupby("HealthBoard")["Cost"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig_hb2 = px.bar(
        hb_cost,
        x="HealthBoard",
        y="Cost",
        color_discrete_sequence=['#9b59b6']
    )
    fig_hb2.update_layout(
        plot_bgcolor="#0e0e0e",
        paper_bgcolor="#0e0e0e",
        font_color="white",
    )
    st.plotly_chart(fig_hb2, use_container_width=True)

# -----------------------------
# Raw Data Expander
# -----------------------------
with st.expander("Show Raw Data"):
    st.dataframe(df_view.head(500), use_container_width=True)
