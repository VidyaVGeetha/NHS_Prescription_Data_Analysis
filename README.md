# NHS Prescription Data Analysis (Scotland) 📊💊

This project explores **NHS prescription data** and presents insights through:
- A **Jupyter Notebook analysis** (EDA + charts)
- An **interactive Streamlit dashboard app** for filtering, visualising, and exploring trends

> Goal: Turn public prescription data into clear, decision-friendly insights with reproducible analysis and an easy-to-run dashboard.

---

## Project Highlights

- ✅ Data cleaning & preprocessing
- ✅ Exploratory Data Analysis (EDA)
- ✅ Trend analysis (time-based patterns)
- ✅ Top items / categories exploration (interactive filters)
- ✅ **Scotland Health Board map visualisation** using GeoJSON boundaries

A dark, purple-themed **Streamlit dashboard** that pulls **NHS Scotland prescribing data** directly from the NHS Open Data API and visualises:
- Key KPIs (items, cost, medicines, practices)
- Top medicines by spend (bar chart)
- Cost split by prescribed type (donut chart)
- **Folium choropleth map** of medicine usage by **Health Board** (GeoJSON)

---

## ✨ Features

- **Live API data loading** with pagination (limit/offset)
- Sidebar controls:
  - **Rows to load** (10k → 100k)
  - **Health Board filter**
  - **Top-N medicines** selector
- KPI cards (custom CSS styling)
- Plotly charts (dark UI friendly)
- Folium choropleth map (Carto dark tiles)
- Optional raw cleaned data preview

---

## 🗂️ Data Source

This dashboard uses the NHS Scotland Open Data API (CKAN) with:

- **resource_id:** `381166dd-3a07-4c12-93c3-6db7b12c042a`
- endpoint: `https://www.opendata.nhs.scot/api/3/action/datastore_search`

> Note: The app loads data in batches of 10,000 rows until it reaches the chosen max rows.

---

## 🧠 What the App Shows

### KPIs
- Total prescription **Items**
- Total **Cost (£)**
- Number of **Unique Medicines**
- Number of **GP Practices**

### Charts
- **Top medicines by spend** (horizontal bar chart)
- **Cost by prescribed type** (donut chart)

### Map
- Pick a medicine → choropleth map shows **Total Items Prescribed** by **Health Board**
- Darker purple = higher usage

---

## 🗺️ GeoJSON Requirement (Important)

To render the map you must provide a **Scottish Health Boards GeoJSON** file.

In your code you currently have:

```python
GEOJSON_PATH = "query.json"


## Tech Stack

- Python
- Pandas / NumPy
- Plotly / Matplotlib (visualisation)
- Streamlit (interactive dashboard)
- GeoJSON mapping (Scottish Health Boards)

---

## Repository Structure

- `NHS_Prescription_final.ipynb` → Final notebook analysis
- `NHS_Prescription.ipynb` → Working notebook / earlier version
- `NHS_prescription_app.py` → Streamlit dashboard app
- `query.json` → Query configuration used by the project/app
- `scottish_health_boards.geojson` → Scotland Health Board boundaries for map
- `config.toml` → Streamlit configuration
- `requirements.txt` → Python dependencies

---

## How to Run Locally

### 1) Clone the repo
```bash
git clone https://github.com/VidyaVGeetha/NHS_Prescription_Data_Analysis.git
cd NHS_Prescription_Data_Analysis
