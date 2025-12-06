"""Pipeline Monitoring Page"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path to import utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from login import require_auth
from components.sidebar import render_sidebar
from auth_utils import is_demo_mode, show_empty_state

st.set_page_config(page_title="Pipelines - EDQMP", page_icon="🔄", layout="wide")

# Enforce Authentication
require_auth()

# Render Sidebar
render_sidebar()

st.title("🔄 Pipeline Monitoring")
st.markdown("Track ETL/ELT workflow execution and SLA compliance")

# Demo mode banner
if is_demo_mode():
    st.markdown("""
    <div style='background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%); color: #1e293b; padding: 0.5rem 1rem; border-radius: 8px; text-align: center; font-weight: 600; margin-bottom: 1rem;'>
        🎭 DEMO MODE — Sample pipeline data shown. Sign up to monitor your own pipelines.
    </div>
    """, unsafe_allow_html=True)

if is_demo_mode():
    # Demo data
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Pipelines", "24", "All healthy")
    with col2:
        st.metric("Success Rate", "99.2%", "+0.5%")
    with col3:
        st.metric("Avg Latency", "2.3s", "-0.4s")
    with col4:
        st.metric("SLA Compliance", "99.9%", "On track")

    st.markdown("---")

    # Pipeline health overview
    st.subheader("📊 Pipeline Health Overview")

    health_data = pd.DataFrame({
        "Pipeline": ["Trade Settlement", "KYC Processing", "FX Rates", "Market Data", "Risk Calc"],
        "Status": ["🟢 Healthy", "🟢 Healthy", "🟡 Warning", "🟢 Healthy", "🟢 Healthy"],
        "Last Run": ["2 min ago", "5 min ago", "1 min ago", "30 sec ago", "10 min ago"],
        "Latency": ["1.2s", "3.4s", "5.1s", "0.8s", "8.2s"],
        "Success Rate": ["100%", "99.5%", "97.2%", "100%", "99.8%"]
    })
    st.dataframe(health_data, use_container_width=True, hide_index=True)

    # Latency chart
    st.subheader("⏱️ Latency Trend (Last 24 Hours)")

    times = pd.date_range(end=datetime.now(), periods=24, freq='H')
    latencies = [2.1, 2.3, 2.0, 1.9, 2.5, 3.1, 2.8, 2.4, 2.2, 2.0, 1.8, 2.1,
                 2.3, 2.5, 2.7, 3.0, 2.8, 2.5, 2.3, 2.1, 2.0, 1.9, 2.2, 2.4]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=latencies, mode='lines+markers', 
                             line=dict(color='#6366f1', width=2),
                             fill='tozeroy', fillcolor='rgba(99,102,241,0.1)'))
    fig.add_hline(y=5.0, line_dash="dash", line_color="#ef4444", annotation_text="SLA Limit")
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(title="Latency (seconds)", gridcolor='rgba(255,255,255,0.1)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Recent runs
    st.subheader("🔄 Recent Pipeline Runs")
    runs = pd.DataFrame({
        "ID": [f"RUN-{1000+i}" for i in range(5)],
        "Pipeline": ["Trade Settlement"] * 5,
        "Started": pd.date_range(end=datetime.now(), periods=5, freq='30T'),
        "Duration": ["1.2s", "1.4s", "1.1s", "1.3s", "1.5s"],
        "Records": [1523, 1456, 1589, 1478, 1534],
        "Status": ["✅ Success"] * 4 + ["🔄 Running"]
    })
    st.dataframe(runs, use_container_width=True, hide_index=True)

else:
    # Real user - empty state
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Pipelines", "0", help="No pipelines configured yet")
    with col2:
        st.metric("Success Rate", "—", "N/A")
    with col3:
        st.metric("Avg Latency", "—", "N/A")
    with col4:
        st.metric("SLA Compliance", "—", "N/A")

    st.markdown("---")

    show_empty_state(
        "No Pipelines Configured",
        "Set up your first data pipeline to start monitoring ETL/ELT workflows and track SLA compliance.",
        None, None
    )

    st.markdown("### ➕ Create Your First Pipeline")
    
    with st.form("pipeline_form"):
        col1, col2 = st.columns(2)
        with col1:
            pipeline_name = st.text_input("Pipeline Name", placeholder="e.g., Daily ETL Job")
            source = st.selectbox("Data Source", ["Select a source...", "PostgreSQL", "MySQL", "S3", "API"])
        with col2:
            schedule = st.selectbox("Schedule", ["Hourly", "Daily", "Weekly", "Custom Cron"])
            sla_threshold = st.number_input("SLA Threshold (seconds)", min_value=1, value=60)
        
        if st.form_submit_button("Create Pipeline"):
            st.info("Pipeline creation coming soon! First, connect a data source in the Data Quality page.")
