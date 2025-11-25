# Step 1: Import required libraries
import streamlit as st      # Import Streamlit (for building the interactive app)
import pandas as pd         # Import Pandas (Data Processing & Analysis)
import plotly.express as px  # Import Plotly Express (Data Visualization)

# Step 2: Page configuration 
# (Streamlit Page Settings (Title, Icon, Layout)
#(This block of code controls how your Streamlit web page looks when it opens.)

st.set_page_config(
    page_title="NHS Scotland Prescription Dashboard – Aug 2025",
    page_icon="💊",
    layout="wide"
)

# Step 3: Load Data
@st.cache_data    #.................special tag) used by Streamlit for cache.
def load_data():  #.................defines a function called load_data.   
      



