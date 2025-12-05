"""
EDQMP Dashboard - Main Application
Enterprise Data Quality & Monitoring Platform
"""

import streamlit as st
import httpx
import os
from dotenv import load_dotenv
from login import login_page

load_dotenv()

# Page config
st.set_page_config(
    page_title="EDQMP | Enterprise Data Quality",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background-color: #020617;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    h1 {
        background: linear-gradient(to right, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        border-color: #6366f1;
    }
    
    /* Tables */
    div[data-testid="stDataFrame"] {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #4f46e5;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #4338ca;
    }
    
    /* Status Indicators */
    .status-dot {
        height: 10px;
        width: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .status-green { background-color: #22c55e; box-shadow: 0 0 8px #22c55e; }
    .status-red { background-color: #ef4444; box-shadow: 0 0 8px #ef4444; }
    .status-yellow { background-color: #eab308; box-shadow: 0 0 8px #eab308; }

</style>
""", unsafe_allow_html=True)

import sys
import os

# Add components to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from components.sidebar import render_sidebar

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def main():
    if not st.session_state.authenticated:
        login_page()
        return

    # Render Shared Sidebar
    render_sidebar()

    # Main Dashboard Content
    st.title("Executive Overview")
    st.markdown("Real-time operational intelligence and risk monitoring.")
    
    # Financial Impact Section (New Logic)
    st.markdown("### 💰 Risk & Financial Impact")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Risk Exposure (24h)", "$142,500", "12%", delta_color="inverse")
    with col2:
        st.metric("Data Quality Score", "98.2%", "+0.4%")
    with col3:
        st.metric("Critical Incidents", "2", "-1", delta_color="inverse")
    with col4:
        st.metric("SLA Compliance", "99.9%", "Stable")

    # High-level charts
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.subheader("📉 Financial Risk Trend")
        # Placeholder for chart
        import pandas as pd
        import numpy as np
        import plotly.express as px
        
        dates = pd.date_range(start="2024-01-01", periods=30)
        risk_data = pd.DataFrame({
            "Date": dates,
            "Risk Exposure ($)": np.random.randint(50000, 200000, size=30)
        })
        fig = px.area(risk_data, x="Date", y="Risk Exposure ($)", 
                      color_discrete_sequence=["#ef4444"])
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
        
    with col_chart2:
        st.subheader("🚨 Active Threats")
        st.markdown("""
        <div style='background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 4px solid #ef4444; margin-bottom: 10px;'>
            <div style='font-weight: bold; color: #ef4444;'>CRITICAL: Trade Settlement Break</div>
            <div style='font-size: 0.9em; color: #cbd5e1;'>Detected 15 mins ago • Potential Loss: $85k</div>
        </div>
        <div style='background-color: #1e293b; padding: 15px; border-radius: 10px; border-left: 4px solid #eab308; margin-bottom: 10px;'>
            <div style='font-weight: bold; color: #eab308;'>WARNING: KYC Data Lag</div>
            <div style='font-size: 0.9em; color: #cbd5e1;'>Feed delayed by 45s • Compliance Risk</div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
