import streamlit as st
import pandas as pd

st.title("Sample Data – No CSV Used")

# Create a small sample dataset manually
data = {
    "Drug_Name": ["Paracetamol", "Ibuprofen", "Amoxicillin", "Metformin"],
    "Quantity": [120, 95, 60, 150],
    "Cost": [45.50, 38.20, 62.10, 55.00],
    "Month": ["Aug 2025", "Aug 2025", "Aug 2025", "Aug 2025"]
}

df = pd.DataFrame(data)

st.subheader("📊 Sample Data Preview (Hard-coded)")
st.dataframe(df)
