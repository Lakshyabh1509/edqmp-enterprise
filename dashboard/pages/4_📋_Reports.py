"""Reports Page"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path to import login
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from login import require_auth
from components.sidebar import render_sidebar

st.set_page_config(page_title="Reports - EDQMP", page_icon="📋", layout="wide")

# Enforce Authentication
require_auth()

# Render Sidebar
render_sidebar()

st.title("📋 Compliance Reports")
st.markdown("Generate audit-ready reports for regulatory compliance")

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
        st.success("Report generated!")

with col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b, #334155); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
        <h3>🔍 Audit Trail</h3>
        <p style="color: #94a3b8;">Complete audit log of all data changes, validations, and user actions.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Generate", key="audit"):
        st.success("Report generated!")

with col3:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b, #334155); border-radius: 12px; padding: 1.5rem; border: 1px solid rgba(255,255,255,0.1);">
        <h3>⚖️ Compliance Report</h3>
        <p style="color: #94a3b8;">SOX, Basel III, SEC filing compliance status and evidence.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Generate", key="compliance"):
        st.success("Report generated!")

st.markdown("---")

# Report configuration
st.subheader("⚙️ Generate Custom Report")

col1, col2 = st.columns(2)
with col1:
    report_type = st.selectbox("Report Type", ["Data Quality Summary", "Audit Trail", "Compliance Report", "Pipeline Performance"])
    date_range = st.date_input("Date Range", value=(datetime.now().date(), datetime.now().date()))
with col2:
    sources = st.multiselect("Data Sources", ["All Sources", "Trade Settlement", "KYC API", "FX Rates"])
    format = st.selectbox("Export Format", ["PDF", "Excel", "CSV", "JSON"])

if st.button("🚀 Generate Report", type="primary"):
    with st.spinner("Generating report..."):
        st.success("Report generated successfully!")
        st.download_button("📥 Download Report", data="Sample report content", file_name=f"edqmp_report_{datetime.now().strftime('%Y%m%d')}.pdf")

# Recent reports
st.subheader("📁 Recent Reports")
reports = pd.DataFrame({
    "Name": ["Weekly Quality Summary", "Monthly Audit Trail", "Q3 Compliance Report"],
    "Type": ["Data Quality", "Audit", "Compliance"],
    "Generated": ["Today", "Yesterday", "3 days ago"],
    "Size": ["2.4 MB", "5.1 MB", "3.8 MB"]
})
st.dataframe(reports, use_container_width=True, hide_index=True)
