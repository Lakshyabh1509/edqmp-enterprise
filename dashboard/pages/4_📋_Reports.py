"""Reports Page"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path to import utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from login import require_auth
from components.sidebar import render_sidebar
from auth_utils import is_demo_mode, show_empty_state

st.set_page_config(page_title="Reports - EDQMP", page_icon="📋", layout="wide")

# Enforce Authentication
require_auth()

# Render Sidebar
render_sidebar()

st.title("📋 Compliance Reports")
st.markdown("Generate audit-ready reports for regulatory compliance")

# Demo mode banner
if is_demo_mode():
    st.markdown("""
    <div style='background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%); color: #1e293b; padding: 0.5rem 1rem; border-radius: 8px; text-align: center; font-weight: 600; margin-bottom: 1rem;'>
        🎭 DEMO MODE — Sample reports shown. Sign up to generate your own compliance reports.
    </div>
    """, unsafe_allow_html=True)

# Report types
st.subheader("📑 Available Report Templates")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b, #334155); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
        <h3>📊 Data Quality Summary</h3>
        <p style="color: #94a3b8;">Weekly/Monthly quality metrics, trend analysis, and SLA compliance overview.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Generate", key="dq"):
        if is_demo_mode():
            st.success("Report generated! (Demo)")
        else:
            st.info("No data available. Run some validations first.")

with col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b, #334155); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
        <h3>🔍 Audit Trail</h3>
        <p style="color: #94a3b8;">Complete audit log of all data changes, validations, and user actions.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Generate", key="audit"):
        if is_demo_mode():
            st.success("Report generated! (Demo)")
        else:
            st.info("No audit data available yet.")

with col3:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b, #334155); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
        <h3>⚖️ Compliance Report</h3>
        <p style="color: #94a3b8;">SOX, Basel III, SEC filing compliance status and evidence.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Generate", key="compliance"):
        if is_demo_mode():
            st.success("Report generated! (Demo)")
        else:
            st.info("No compliance data available yet.")

st.markdown("---")

# Report configuration
st.subheader("⚙️ Generate Custom Report")

col1, col2 = st.columns(2)
with col1:
    report_type = st.selectbox("Report Type", ["Data Quality Summary", "Audit Trail", "Compliance Report", "Pipeline Performance"])
    date_range = st.date_input("Date Range", value=(datetime.now().date(), datetime.now().date()))
with col2:
    if is_demo_mode():
        sources = st.multiselect("Data Sources", ["All Sources", "Trade Settlement", "KYC API", "FX Rates"], default=["All Sources"])
    else:
        sources = st.multiselect("Data Sources", ["No sources configured..."], disabled=True)
    format_choice = st.selectbox("Export Format", ["PDF", "Excel", "CSV", "JSON"])

if st.button("🚀 Generate Report", type="primary"):
    if is_demo_mode():
        with st.spinner("Generating report..."):
            import time
            time.sleep(1)
            st.success("Report generated successfully!")
            st.download_button(
                "📥 Download Report", 
                data="Sample report content - This is a demo report for EDQMP.\n\nData Quality Score: 98.2%\nTotal Records Processed: 1,234,567\nValidation Pass Rate: 99.1%", 
                file_name=f"edqmp_report_{datetime.now().strftime('%Y%m%d')}.txt"
            )
    else:
        st.info("No data available to generate report. Start by running validations in the Data Quality section.")

# Recent reports
st.subheader("📁 Recent Reports")

if is_demo_mode():
    reports = pd.DataFrame({
        "Name": ["Weekly Quality Summary", "Monthly Audit Trail", "Q3 Compliance Report"],
        "Type": ["Data Quality", "Audit", "Compliance"],
        "Generated": ["Today", "Yesterday", "3 days ago"],
        "Size": ["2.4 MB", "5.1 MB", "3.8 MB"]
    })
    st.dataframe(reports, use_container_width=True, hide_index=True)
else:
    show_empty_state(
        "No Reports Generated Yet",
        "Run data validations and generate your first compliance report.",
        None, None
    )
