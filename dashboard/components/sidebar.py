"""
Shared Sidebar Component
"""
import streamlit as st

def render_sidebar():
    """
    Renders the consistent sidebar navigation for all pages.
    """
    with st.sidebar:
        st.markdown("### 🛡️ EDQMP Enterprise")
        
        # User Info
        if "user" in st.session_state and st.session_state.user:
            email = st.session_state.user.get('email', 'Unknown')
            st.caption(f"Logged in as: {email}")
        
        st.markdown("---")
        
        st.markdown("#### 📍 Command Center")
        
        # Navigation Links
        # Note: We use page_link which requires Streamlit 1.31+ or late 1.30
        # The paths must be relative to the main app.py
        
        st.page_link("app.py", label="Overview", icon="📊")
        st.page_link("pages/1_✅_Data_Quality.py", label="Quality Control", icon="✅")
        st.page_link("pages/2_🔄_Pipelines.py", label="Pipeline Monitor", icon="🔄")
        st.page_link("pages/3_🔔_Alerts.py", label="Alert Manager", icon="🔔")
        st.page_link("pages/4_📋_Reports.py", label="Compliance Reports", icon="📋")
        
        st.markdown("---")
        
        # Sign Out Button
        if st.button("Sign Out", key="sidebar_signout"):
            st.session_state.authenticated = False
            st.session_state.user = {}
            st.rerun()
