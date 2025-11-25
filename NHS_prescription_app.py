import urllib.request
import json

import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="NHS Scotland Prescription Dashboard – API Version",
    page_icon="💊",
    layout="wide",
)

st.title("💊 NHS Scotland Prescription Dashboard – API Version")
st.caption(
    "Data source: NHS Scotland Open Data API "
    "(resource_id = 381166dd-3a07-4c12-93c3-6db7b12c042a). "
    "This app loads a sampled number of rows for learning / analysis only."
)

# -----------------------------
# NHS Open Data API details
# -----------------------------
API_URL = (
    "https://www.opendata.nhs.scot/api/3/action/datastore_search"
    "?resource_id=381166dd-3a07-4c12-93c3-6db7b12c042a"
)


# -----------------------------
# Helper: load data from API
# -----------------------------
@st.cache_data(show_spinner=True)
def load_prescriptions_from_api(max_rows: int | None = 50000) -> pd.DataFrame:
    """
    Load prescription data directly from the NHS Open Data API.

    - Uses pagination with offset/limit.
    - If max_rows is None → loads all available rows (can be very large).
    - If max_rows is a number (e.g. 50000) → stops after that many rows.
    """
    all_records: list[dict] = []
    limit = 10_000  # rows per API call
    offset = 0

    while True:
        # Stop if we've already collected the requested number of rows
        if max_rows is not None and len(all_records) >= max_rows:
            break

        url = f"{API_URL}&limit={limit}&offset={offset}"

        # Call the API
        with urllib.request.urlopen(url) as response:
            raw_data = response.read()

        # JSON → Python dict
        data = json.loads(raw_data.decode("utf-8"))

        # Extract actual rows
        records = data["result"]["records"]

        # If there are no more rows, stop
        if not records:
            break

        all_records.extend(records)
        offset += limit

        # Safety: trim to max_rows if set
        if max_rows is not None and len(all_records) >= max_rows:
            all_records = all_records[:max_rows]
            break

    # List[dict] → DataFrame
    df = pd.DataFrame(all_records)
    return df


# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.header("Data options")

max_rows = st.sidebar.slider(
    "Number of rows to load from API",
    min_value=10_000,
    max_value=100_000,
    step=10_000,
    value=50_000,
    help="Higher values give more detail but load slower.",
)

# -----------------------------
# Load & clean data
# -----------------------------
df_prescriber_loc = load_prescriptions_from_api(max_rows=max_rows)

st.sidebar.success(f"Loaded {len(df_prescriber_loc):,} rows from NHS API")

# Basic cleaning: drop rows with no medicine name
df_prescriber_loc_clean = df_prescriber_loc.dropna(subset=["BNFItemDescription"]).copy()

# Convert key numeric columns
for col in ["NumberOfPaidItems", "GrossIngredientCost", "PaidQuantity"]:
    if col in df_prescriber_loc_clean.columns:
        df_prescriber_loc_clean[col] = pd.to_numeric(
            df_prescriber_loc_clean[col], errors="coerce"
        )

# Rename columns to friendlier names (same as in your notebook)
rename_map = {
    "BNFItemDescription": "Medicine",
    "NumberOfPaidItems": "Items",
    "GrossIngredientCost": "Cost",
    "PaidQuantity": "Quantity",
    "GPPractice": "Practice",
    "HBT": "HealthBoard",
}
df_prescriber_loc_clean = df_prescriber_loc_clean.rename(columns=rename_map)

# Keep only rows where the renamed columns are present
required_cols = ["Medicine", "Items", "Cost", "Quantity", "Practice", "HealthBoard"]
available_cols = [c for c in required_cols if c in df_prescriber_loc_clean.columns]
df_prescriber_loc_clean = df_prescriber_loc_clean[available_cols].copy()

# -----------------------------
# Sidebar filter – Health Board
# -----------------------------
if "HealthBoard" in df_prescriber_loc_clean.columns:
    boards = (
        ["All Health Boards"]
        + sorted(df_prescriber_loc_clean["HealthBoard"].dropna().unique().tolist())
    )
    selected_board = st.sidebar.selectbox("Filter by Health Board", boards)
else:
    selected_board = "All Health Boards"
    boards = [selected_board]

df_view = df_prescriber_loc_clean.copy()
if "HealthBoard" in df_view.columns and selected_board != "All Health Boards":
    df_view = df_view[df_view["HealthBoard"] == selected_board]

if df_view.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# -----------------------------
# KPI cards
# -----------------------------
total_items = int(df_view["Items"].sum()) if "Items" in df_view.columns else 0
total_cost = float(df_view["Cost"].sum()) if "Cost" in df_view.columns else 0.0
unique_meds = int(df_view["Medicine"].nunique()) if "Medicine" in df_view.columns else 0
unique_practices = (
    int(df_view["Practice"].nunique()) if "Practice" in df_view.columns else 0
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Prescription Items", f"{total_items:,.0f}")
col2.metric("Total NHS Spend (£)", f"£{total_cost:,.0f}")
col3.metric("Distinct Medicines", f"{unique_meds:,}")
col4.metric("Distinct GP Practices", f"{unique_practices:,}")

st.markdown("---")

# -----------------------------
# Top medicines – by items & cost
# -----------------------------
top_n = st.sidebar.slider(
    "Top N medicines", min_value=5, max_value=25, value=10, step=1
)

if "Medicine" in df_view.columns and "Items" in df_view.columns:
    top_items = (
        df_view.groupby("Medicine", as_index=False)["Items"]
        .sum()
        .sort_values("Items", ascending=False)
        .head(top_n)
    )

    fig_items = px.bar(
        top_items,
        x="Medicine",
        y="Items",
        title=f"Top {top_n} Medicines by Number of Items",
        text_auto=True,
    )
    fig_items.update_layout(xaxis_title="", yaxis_title="Items")
    st.plotly_chart(fig_items, use_container_width=True)

if "Medicine" in df_view.columns and "Cost" in df_view.columns:
    top_cost = (
        df_view.groupby("Medicine", as_index=False)["Cost"]
        .sum()
        .sort_values("Cost", ascending=False)
        .head(top_n)
    )

    fig_cost = px.bar(
        top_cost,
        x="Medicine",
        y="Cost",
        title=f"Top {top_n} Medicines by NHS Cost (£)",
        text_auto=True,
    )
    fig_cost.update_layout(xaxis_title="", yaxis_title="Cost (£)")
    st.plotly_chart(fig_cost, use_container_width=True)

st.markdown("---")

# -----------------------------
# Items & cost by Health Board
# -----------------------------
if "HealthBoard" in df_view.columns:
    hb_items = (
        df_view.groupby("HealthBoard", as_index=False)["Items"].sum().sort_values(
            "Items", ascending=False
        )
    )
    hb_cost = (
        df_view.groupby("HealthBoard", as_index=False)["Cost"].sum().sort_values(
            "Cost", ascending=False
        )
    )

    col_a, col_b = st.columns(2)

    with col_a:
        fig_hb_items = px.bar(
            hb_items,
            x="HealthBoard",
            y="Items",
            title="Total Prescription Items by Health Board",
            text_auto=True,
        )
        fig_hb_items.update_layout(xaxis_title="", yaxis_title="Items")
        st.plotly_chart(fig_hb_items, use_container_width=True)

    with col_b:
        fig_hb_cost = px.bar(
            hb_cost,
            x="HealthBoard",
            y="Cost",
            title="Total NHS Cost by Health Board (£)",
            text_auto=True,
        )
        fig_hb_cost.update_layout(xaxis_title="", yaxis_title="Cost (£)")
        st.plotly_chart(fig_hb_cost, use_container_width=True)

st.markdown("---")

# -----------------------------
# High cost, low quantity table
# -----------------------------
if {"Quantity", "Cost", "Medicine"}.issubset(df_view.columns):
    mask = (df_view["Quantity"] < 5) & (df_view["Cost"] > 200)
    high_cost_low_qty = (
        df_view.loc[mask, ["Medicine", "HealthBoard", "Quantity", "Cost"]]
        .sort_values("Cost", ascending=False)
        .head(50)
    )

    st.subheader("High-cost Medicines with Low Usage")
    st.caption("Filters: Quantity < 5 and Cost > £200.")
    st.dataframe(high_cost_low_qty, use_container_width=True)

# -----------------------------
# Raw data expander
# -----------------------------
with st.expander("Show raw data (cleaned)"):
    st.dataframe(df_view.head(500))




