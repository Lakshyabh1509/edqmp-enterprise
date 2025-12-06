"""Alerts Management Page"""
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

st.set_page_config(page_title="Alerts - EDQMP", page_icon="🔔", layout="wide")

# Enforce Authentication
require_auth()

# Render Sidebar
render_sidebar()

st.title("🔔 Alert Management")
st.markdown("View, acknowledge, and resolve data quality alerts")

# Demo mode banner
if is_demo_mode():
    st.markdown("""
    <div style='background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%); color: #1e293b; padding: 0.5rem 1rem; border-radius: 8px; text-align: center; font-weight: 600; margin-bottom: 1rem;'>
        🎭 DEMO MODE — Sample alerts shown. Sign up to configure your own alerts.
    </div>
    """, unsafe_allow_html=True)

if is_demo_mode():
    # Demo data - Alert summary
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
                    st.success("Alert acknowledged (demo)")
            with col3:
                if st.button("Resolve", key=f"res_{idx}"):
                    st.success("Alert resolved (demo)")
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

else:
    # Real user - empty state
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Open Alerts", "0", help="No alerts yet")
    with col2:
        st.metric("Critical", "0")
    with col3:
        st.metric("Warnings", "0")
    with col4:
        st.metric("Resolved Today", "0")

    st.markdown("---")

    show_empty_state(
        "No Alerts Configured",
        "Set up alert rules to get notified when data quality issues are detected in your pipelines.",
        None, None
    )

# Configure alerts section (shown for both demo and real users)
st.markdown("---")
st.subheader("⚙️ Configure Alert Channels")

col1, col2 = st.columns(2)
with col1:
    slack_enabled = st.toggle("Slack Notifications", value=is_demo_mode())
    email_enabled = st.toggle("Email Notifications", value=is_demo_mode())
with col2:
    webhook_enabled = st.toggle("Webhook Integration", value=False)
    pagerduty_enabled = st.toggle("PagerDuty", value=False)

if not is_demo_mode():
    st.markdown("### ➕ Create Alert Rule")
    
    with st.form("alert_rule_form"):
        col1, col2 = st.columns(2)
        with col1:
            rule_name = st.text_input("Rule Name", placeholder="e.g., High Error Rate Alert")
            trigger_type = st.selectbox("Trigger Type", ["Threshold", "Anomaly Detection", "Missing Data", "Freshness"])
        with col2:
            severity = st.selectbox("Severity", ["Critical", "Warning", "Info"])
            threshold = st.number_input("Threshold Value", min_value=0.0, value=0.95)
        
        channels = st.multiselect("Notification Channels", ["Email", "Slack", "Webhook", "PagerDuty"])
        
        if st.form_submit_button("Create Alert Rule"):
            if not slack_enabled and not email_enabled:
                st.warning("Please enable at least one notification channel above first.")
            else:
                st.success(f"Alert rule '{rule_name}' created successfully!")
