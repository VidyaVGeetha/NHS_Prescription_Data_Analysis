import urllib.request
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium

# --------------------------------
# Page config
# --------------------------------
st.set_page_config(
    page_title="NHS Scotland Prescription Dashboard",
    page_icon="💊",
    layout="wide",
)

# --------------------------------
# Purple/black styling for KPI cards
# --------------------------------
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# --------------------------------
# Title
# --------------------------------
st.title("💊 NHS Scotland Prescription Dashboard – API Version")
st.caption(
    "Dark–purple themed Streamlit dashboard using NHS Scotland prescribing data "
    "(resource_id=381166dd-3a07-4c12-93c3-6db7b12c042a). "
    "Includes a map of medicine usage by Health Board."
)

# --------------------------------
# Constants
# --------------------------------
API_URL = (
    "https://www.opendata.nhs.scot/api/3/action/datastore_search"
    "?resource_id=381166dd-3a07-4c12-93c3-6db7b12c042a"
)

# 👇 Adjust this path: place your Scottish Health Board GeoJSON here.
# The GeoJSON should have a property (e.g. HBCode) that matches HealthBoard codes in the data.
GEOJSON_PATH = "query.json"  # put this file in the same folder as the app


# --------------------------------
# Load data from NHS API
# --------------------------------
@st.cache_data(show_spinner=True)
def load_data(max_rows: int = 50_000) -> pd.DataFrame:
    all_records = []
    limit = 10_000
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


@st.cache_data(show_spinner=True)
def load_healthboard_geojson(path: str):
    """Load GeoJSON used for Folium map."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


# --------------------------------
# Sidebar – data settings
# --------------------------------
st.sidebar.header("⚙ Data Settings")

max_rows = st.sidebar.slider(
    "Rows to load from API",
    min_value=10_000,
    max_value=100_000,
    step=10_000,
    value=50_000,
    help="Higher values give more detail but may load slower.",
)

df = load_data(max_rows=max_rows)
st.sidebar.success(f"{len(df):,} rows loaded from NHS API")

# --------------------------------
# Cleaning & renaming
# --------------------------------
# Drop rows without a medicine name
df = df.dropna(subset=["BNFItemDescription"]).copy()

# Convert numerics
for col in ["NumberOfPaidItems", "GrossIngredientCost", "PaidQuantity"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Rename columns to friendly names
df = df.rename(
    columns={
        "BNFItemDescription": "Medicine",
        "NumberOfPaidItems": "Items",
        "GrossIngredientCost": "Cost",
        "PaidQuantity": "Quantity",
        "GPPractice": "Practice",
        "HBT": "HealthBoard",
        "PrescribedType": "Type",
    }
)

# Basic safety – drop rows with missing HealthBoard
df = df.dropna(subset=["HealthBoard"])

# --------------------------------
# Sidebar – Health Board filter
# --------------------------------
boards = ["All Health Boards"] + sorted(df["HealthBoard"].unique().tolist())
selected_board = st.sidebar.selectbox("Filter by Health Board", boards)

df_view = df.copy()
if selected_board != "All Health Boards":
    df_view = df_view[df_view["HealthBoard"] == selected_board]

if df_view.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# --------------------------------
# KPI cards (top row)
# --------------------------------
total_items = int(df_view["Items"].sum())
total_cost = float(df_view["Cost"].sum())
unique_meds = df_view["Medicine"].nunique()
unique_practices = df_view["Practice"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Items", f"{total_items:,}")
k2.metric("Total Cost (£)", f"{total_cost:,.0f}")
k3.metric("Unique Medicines", f"{unique_meds:,}")
k4.metric("GP Practices", f"{unique_practices:,}")

st.markdown("---")

# --------------------------------
# Middle row: Top medicines (left) + Donut chart (right)
# --------------------------------
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("📊 Top Medicines by NHS Spend")

    top_n = st.sidebar.slider("Top N medicines", 5, 25, 10, step=1)

    top_cost = (
        df_view.groupby("Medicine", as_index=False)["Cost"]
        .sum()
        .sort_values("Cost", ascending=False)
        .head(top_n)
    )

    fig_top = px.bar(
        top_cost,
        x="Cost",
        y="Medicine",
        orientation="h",
        title=f"Top {top_n} Medicines by Cost",
        text_auto=True,
        color_discrete_sequence=["#9b59b6"],
    )

    fig_top.update_layout(
        plot_bgcolor="#0e0e0e",
        paper_bgcolor="#0e0e0e",
        font_color="white",
        xaxis_title="Cost (£)",
        yaxis_title="",
    )

    left_col.plotly_chart(fig_top, use_container_width=True)

with right_col:
    st.subheader("💰 Cost by Prescribed Type")

    type_cost = (
        df_view.groupby("Type", as_index=False)["Cost"].sum().sort_values("Cost", ascending=False)
    )

    fig_donut = px.pie(
        type_cost,
        names="Type",
        values="Cost",
        hole=0.55,
        color_discrete_sequence=px.colors.sequential.Purples,
    )

    # Make donut text white
    fig_donut.update_traces(
        textfont_color="white",
        textposition="inside",
    )

    fig_donut.update_layout(
        font_color="white",
        legend_font_color="white",
        plot_bgcolor="#0e0e0e",
        paper_bgcolor="#0e0e0e",
        showlegend=True,
    )

    right_col.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# --------------------------------
# Map: Medicine usage intensity by Health Board
# --------------------------------
st.subheader("🗺 Medicine Usage Map by Health Board")

geojson = load_healthboard_geojson(GEOJSON_PATH)
if geojson is None:
    st.error(
        "GeoJSON file for Scottish Health Boards not found.\n\n"
        f"Please add a file named `{GEOJSON_PATH}` in the app folder.\n"
        "The GeoJSON should have a property (e.g. `HBCode`) that matches the `HealthBoard` codes."
    )
else:
    # Choose a medicine
    # Sort medicines by total items (descending) for nicer dropdown
    medicine_order = (
        df_view.groupby("Medicine", as_index=False)["Items"]
        .sum()
        .sort_values("Items", ascending=False)
    )
    med_list = medicine_order["Medicine"].tolist()

    selected_medicine = st.selectbox(
        "Select a medicine to map usage intensity",
        med_list,
        help="Map shows total number of prescription items for each Health Board.",
    )

    df_med = df_view[df_view["Medicine"] == selected_medicine].copy()

    if df_med.empty:
        st.info("No records for this medicine with the current filters.")
    else:
        agg_med = (
            df_med.groupby("HealthBoard", as_index=False)["Items"].sum().rename(
                columns={"Items": "TotalItems"}
            )
        )

        # Base map – center roughly on Scotland
        m = folium.Map(location=[57.0, -4.0], zoom_start=6, tiles="cartodbdark_matter")

        # 💡 IMPORTANT:
        # In the GeoJSON, ensure there is a property like 'HBCode' or 'code'
        # that matches the HealthBoard codes in `agg_med["HealthBoard"]`.
        key_on_field = "feature.properties.HBCode"  # change if your property is different

        choropleth = folium.Choropleth(
            geo_data=geojson,
            name="choropleth",
            data=agg_med,
            columns=["HealthBoard", "TotalItems"],
            key_on=key_on_field,
            fill_color="Purples",
            fill_opacity=0.7,
            line_opacity=0.2,
            nan_fill_opacity=0.1,
            legend_name="Total Items Prescribed",
        ).add_to(m)

        # Add tooltip with Health Board & Items
        folium.GeoJsonTooltip(
            fields=["HBName"],  # adjust field names based on your GeoJSON
            aliases=["Health Board:"],
            sticky=False,
        ).add_to(choropleth.geojson)

        st.markdown(
            f"**Selected medicine:** `{selected_medicine}` – darker purple = higher number of items."
        )
        st_folium(m, width=None, height=550)

# --------------------------------
# Raw data (optional) – collapsible
# --------------------------------
with st.expander("Show sample raw data (cleaned)"):
    st.dataframe(df_view.head(500), use_container_width=True)
