"""Alerts Management Page"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path to import login
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from login import require_auth
from components.sidebar import render_sidebar

st.set_page_config(page_title="Alerts - EDQMP", page_icon="🔔", layout="wide")

# Enforce Authentication
require_auth()

# Render Sidebar
render_sidebar()

st.title("🔔 Alert Management")
st.markdown("View, acknowledge, and resolve data quality alerts")

# Alert summary
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Open Alerts", "3", "⚠️")
with col2:
    st.metric("Critical", "1", "🚨")
with col3:
    st.metric("Warnings", "2", "⚡")
with col4:
    st.metric("Resolved Today", "8", "✅")

st.markdown("---")

# Active alerts
st.subheader("🚨 Active Alerts")

alerts = pd.DataFrame({
    "Time": ["10 min ago", "25 min ago", "1 hour ago"],
    "Severity": ["🔴 Critical", "🟡 Warning", "🟡 Warning"],
    "Source": ["Market Data Feed", "KYC API", "Trade Settlement"],
    "Rule": ["Anomaly Detection", "Freshness Check", "Completeness"],
    "Message": [
        "Price spike detected: 3.2σ deviation",
        "Data not refreshed in 2+ hours",
        "5% missing values in account_id"
    ],
    "Status": ["Open", "Open", "Open"]
})

for idx, row in alerts.iterrows():
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{row['Severity']}** | {row['Source']} - {row['Rule']}")
            st.caption(f"{row['Message']} • {row['Time']}")
        with col2:
            if st.button("Acknowledge", key=f"ack_{idx}"):
                st.success("Alert acknowledged")
        with col3:
            if st.button("Resolve", key=f"res_{idx}"):
                st.success("Alert resolved")
        st.markdown("---")

# Alert history
st.subheader("📜 Alert History")
history = pd.DataFrame({
    "Time": pd.date_range(end=datetime.now(), periods=10, freq='H'),
    "Source": ["Trade DB"] * 5 + ["KYC API"] * 5,
    "Severity": ["warning", "critical", "warning", "info", "warning"] * 2,
    "Status": ["resolved"] * 10
})
st.dataframe(history, use_container_width=True)

# Configure alerts
st.subheader("⚙️ Configure Alert Channels")
col1, col2 = st.columns(2)
with col1:
    slack_enabled = st.toggle("Slack Notifications", value=True)
    email_enabled = st.toggle("Email Notifications", value=True)
with col2:
    webhook_enabled = st.toggle("Webhook Integration", value=False)
    pagerduty_enabled = st.toggle("PagerDuty", value=False)
