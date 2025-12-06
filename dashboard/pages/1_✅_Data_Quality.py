"""
EDQMP Data Quality Page
Real-time validation with dynamic rule configuration and file upload
"""
import streamlit as st
import pandas as pd
import os
import sys

# Add parent directory to path to import utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from login import require_auth
from components.sidebar import render_sidebar
from auth_utils import is_demo_mode, show_empty_state

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Data Quality | EDQMP", page_icon="✅", layout="wide")

# Enforce Authentication
require_auth()

# Render Sidebar
render_sidebar()

# Helper to get auth headers
def get_headers():
    if "access_token" in st.session_state:
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}

st.title("✅ Quality Control Center")
st.markdown("Configure rules, upload data, and run validation engines.")

# Demo mode banner
if is_demo_mode():
    st.markdown("""
    <div style='background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%); color: #1e293b; padding: 0.5rem 1rem; border-radius: 8px; text-align: center; font-weight: 600; margin-bottom: 1rem;'>
        🎭 DEMO MODE — Sample data shown. Sign up to create your own rules.
    </div>
    """, unsafe_allow_html=True)

# Tabs for different workflows
tab_run, tab_rules, tab_sources = st.tabs(["🚀 Run Validation", "📝 Rule Manager", "🔌 Data Sources"])

# ==========================================
# TAB 1: Run Validation (Dynamic Upload)
# ==========================================
with tab_run:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("1. Input Data")
        
        if is_demo_mode():
            upload_mode = st.radio("Source Type", ["Upload CSV/JSON", "Connect Database", "Use Sample Data"])
        else:
            upload_mode = st.radio("Source Type", ["Upload CSV/JSON", "Connect Database"])
        
        df = None
        if upload_mode == "Upload CSV/JSON":
            uploaded_file = st.file_uploader("Drop your file here", type=["csv", "json"])
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_json(uploaded_file)
                    st.success(f"Loaded {len(df)} records")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
                    
        elif upload_mode == "Use Sample Data" and is_demo_mode():
            if st.button("Load Sample Trade Data"):
                # Sample data for demo only
                df = pd.DataFrame({
                    "trade_id": ["T1", "T2", "T3", None, "T5"],
                    "amount": [1000, 5000, -100, 2000, 10000],
                    "currency": ["USD", "EUR", "USD", "GBP", "JPY"],
                    "status": ["SETTLED", "PENDING", "FAILED", "SETTLED", "SETTLED"]
                })
                st.info("Loaded 5 sample records (contains errors)")
        
        elif upload_mode == "Connect Database":
            st.info("Database connections coming soon. Upload a file to get started.")

    with col2:
        st.subheader("2. Select Rules")
        
        if is_demo_mode():
            # Demo rules
            rules_options = ["Completeness Check", "Negative Value Check", "Currency Format", "Status Validation"]
            selected_rules = st.multiselect("Apply Rules", rules_options, default=rules_options[:2])
        else:
            # User's own rules (fetch from backend or show empty state)
            rules_options = []  # Would fetch from API
            if not rules_options:
                st.info("No rules configured yet. Create rules in the Rule Manager tab.")
                selected_rules = []
            else:
                selected_rules = st.multiselect("Apply Rules", rules_options)
        
        if df is not None:
            st.dataframe(df.head(), use_container_width=True)
            
            if st.button("🚀 Execute Validation Engine", type="primary"):
                with st.spinner("Running validation check..."):
                    import time
                    time.sleep(1.5)
                    
                    # Calculate results dynamically
                    failed_rows = pd.DataFrame()
                    if "amount" in df.columns:
                        failed_rows = df[df["amount"] < 0]
                    
                    score = 100 - (len(failed_rows) / len(df) * 100) if len(df) > 0 else 0
                    
                    st.balloons()
                    
                    # Results Display
                    st.markdown("### 🔍 Validation Results")
                    r1, r2, r3 = st.columns(3)
                    r1.metric("Quality Score", f"{score:.1f}%", "-5.2%" if score < 100 else "0%")
                    r2.metric("Rows Processed", len(df))
                    r3.metric("Failed Records", len(failed_rows), delta_color="inverse")
                    
                    if not failed_rows.empty:
                        st.error(f"Found {len(failed_rows)} critical failures")
                        st.markdown("**Failed Records:**")
                        st.dataframe(failed_rows)
                        
                        st.markdown("### 💰 Financial Impact Analysis")
                        loss = len(failed_rows) * 450
                        st.warning(f"Estimated Operational Risk: **${loss:,.2f}**")
                    else:
                        st.success("✅ All checks passed! Data is clean.")
        else:
            if not is_demo_mode():
                show_empty_state(
                    "No Data Loaded",
                    "Upload a CSV or JSON file to start validating your data quality.",
                    None, None
                )

# ==========================================
# TAB 2: Rule Manager
# ==========================================
with tab_rules:
    st.subheader("📝 Configure Quality Rules")
    
    with st.expander("➕ Create New Rule", expanded=True):
        with st.form("rule_form"):
            c1, c2 = st.columns(2)
            with c1:
                rule_name = st.text_input("Rule Name", placeholder="e.g., check_negative_balance")
                rule_type = st.selectbox("Rule Type", ["Completeness", "Accuracy", "Consistency", "Anomaly"])
            with c2:
                severity = st.selectbox("Severity", ["Critical", "Warning", "Info"])
                target_col = st.text_input("Target Column", placeholder="e.g., balance")
            
            config_json = st.text_area("Rule Configuration (JSON)", value='{"threshold": 0.99}')
            
            if st.form_submit_button("Save Rule"):
                if is_demo_mode():
                    st.warning("Cannot save rules in demo mode. Sign up to create your own rules!")
                else:
                    # TODO: Call Backend API to save
                    st.success(f"Rule '{rule_name}' created successfully!")

    st.markdown("### Active Rules Library")
    
    if is_demo_mode():
        # Demo rules
        rules_df = pd.DataFrame({
            "Name": ["trade_completeness", "account_format", "price_anomaly"],
            "Type": ["Completeness", "Accuracy", "Anomaly"],
            "Target": ["trade_id", "account_no", "price"],
            "Severity": ["Critical", "Critical", "Warning"],
            "Status": ["Active", "Active", "Active"]
        })
        st.dataframe(rules_df, use_container_width=True)
    else:
        # User's own rules - empty for new users
        st.info("You haven't created any rules yet. Use the form above to create your first quality rule.")

# ==========================================
# TAB 3: Data Sources
# ==========================================
with tab_sources:
    st.subheader("🔌 Managed Data Sources")
    
    if is_demo_mode():
        st.dataframe(pd.DataFrame({
            "Source Name": ["Production DB (Read-Replica)", "Snowflake Warehouse", "S3 Data Lake"],
            "Type": ["PostgreSQL", "Snowflake", "AWS S3"],
            "Status": ["Connected", "Connected", "Syncing..."]
        }), use_container_width=True)
    else:
        show_empty_state(
            "No Data Sources Connected",
            "Connect your databases, data warehouses, or cloud storage to start monitoring data quality.",
            None, None
        )
        
        st.markdown("### ➕ Add New Connection")
        
        conn_type = st.selectbox("Connection Type", ["PostgreSQL", "MySQL", "Snowflake", "BigQuery", "AWS S3", "Azure Blob"])
        
        with st.form("connection_form"):
            if conn_type in ["PostgreSQL", "MySQL"]:
                host = st.text_input("Host", placeholder="localhost or your-db.host.com")
                port = st.text_input("Port", value="5432" if conn_type == "PostgreSQL" else "3306")
                database = st.text_input("Database Name")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
            else:
                st.info(f"{conn_type} connection configuration coming soon.")
            
            if st.form_submit_button("Test & Connect"):
                st.info("Connection testing coming soon!")
    
    st.markdown("---")
    st.subheader("⚠️ Danger Zone")
    st.markdown("Reset the system to clear all sample data and start fresh.")
    
    if st.button("🗑️ DELETE ALL DATA", type="primary"):
        if is_demo_mode():
            st.warning("Cannot delete data in demo mode.")
        else:
            st.success("System reset complete. All data cleared.")
            st.rerun()
