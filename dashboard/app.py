"""
EDQMP Dashboard - Main Application
Enterprise Data Quality & Monitoring Platform
"""

import streamlit as st
import os
from dotenv import load_dotenv
from login import login_page
from auth_utils import is_demo_mode, is_authenticated, show_empty_state

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

    /* Welcome Card for New Users */
    .welcome-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
    }
    
    /* Demo Mode Banner */
    .demo-banner {
        background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
        color: #1e293b;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

import sys

# Add components to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from components.sidebar import render_sidebar

# Session state initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_demo" not in st.session_state:
    st.session_state.is_demo = False


def render_demo_dashboard():
    """Render dashboard with sample/demo data"""
    # Demo Mode Banner
    st.markdown("""
    <div class='demo-banner'>
        🎭 DEMO MODE — You're viewing sample data. Sign up for your own account to add real data.
    </div>
    """, unsafe_allow_html=True)
    
    st.title("Executive Overview")
    st.markdown("Real-time operational intelligence and risk monitoring.")
    
    # Financial Impact Section (Demo Data)
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


def render_user_dashboard():
    """Render dashboard for authenticated users (blank canvas)"""
    st.title("Executive Overview")
    
    user = st.session_state.get("user", {})
    user_name = user.get("full_name") or user.get("email", "").split("@")[0]
    
    st.markdown(f"Welcome back, **{user_name}**! 👋")
    st.markdown("---")
    
    # Quick Stats (User's own data - empty for new users)
    st.markdown("### 📊 Your Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Data Sources", "0", help="Connect your first data source")
    with col2:
        st.metric("Quality Rules", "0", help="Create quality validation rules")
    with col3:
        st.metric("Active Pipelines", "0", help="Set up data pipelines")
    with col4:
        st.metric("Alerts Configured", "0", help="Configure monitoring alerts")
    
    st.markdown("---")
    
    # Getting Started Section
    st.markdown("### 🚀 Get Started")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%); border: 1px solid #3b82f6; border-radius: 12px; padding: 1.5rem;'>
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>📁</div>
            <h4 style='color: #f8fafc; margin: 0;'>1. Connect Data Source</h4>
            <p style='color: #94a3b8; font-size: 0.9rem; margin-top: 0.5rem;'>Link your database, data warehouse, or upload files.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Connect Source", key="btn_source"):
            st.switch_page("pages/1_✅_Data_Quality.py")
    
    with col_b:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%); border: 1px solid #3b82f6; border-radius: 12px; padding: 1.5rem;'>
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>📝</div>
            <h4 style='color: #f8fafc; margin: 0;'>2. Create Quality Rules</h4>
            <p style='color: #94a3b8; font-size: 0.9rem; margin-top: 0.5rem;'>Define validation rules for your data quality checks.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Create Rules", key="btn_rules"):
            st.switch_page("pages/1_✅_Data_Quality.py")
    
    with col_c:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%); border: 1px solid #3b82f6; border-radius: 12px; padding: 1.5rem;'>
            <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🔔</div>
            <h4 style='color: #f8fafc; margin: 0;'>3. Set Up Alerts</h4>
            <p style='color: #94a3b8; font-size: 0.9rem; margin-top: 0.5rem;'>Get notified when data quality issues are detected.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Configure Alerts", key="btn_alerts"):
            st.switch_page("pages/3_🔔_Alerts.py")
    
    st.markdown("---")
    st.info("💡 **Tip:** Start by connecting a data source in the Data Quality section, then create rules to validate your data.")


def main():
    if not st.session_state.authenticated:
        login_page()
        return

    # Render Shared Sidebar
    render_sidebar()

    # Render appropriate dashboard based on user type
    if is_demo_mode():
        render_demo_dashboard()
    else:
        render_user_dashboard()


if __name__ == "__main__":
    main()
