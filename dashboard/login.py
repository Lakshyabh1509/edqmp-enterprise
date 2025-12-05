"""
EDQMP Login Page
"""
import streamlit as st
import httpx
import os

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")

def login_page():
    st.markdown("""
        <style>
        .stTextInput input {
            background-color: #1e293b;
            color: white;
            border: 1px solid #334155;
        }
        .stButton button {
            width: 100%;
            padding: 0.5rem;
            font-weight: bold;
            border: none;
        }
        /* Primary Button (Sign In) */
        div[data-testid="stForm"] button {
            background: linear-gradient(90deg, #6366f1, #8b5cf6);
            color: white;
        }
        /* Secondary Button (Demo) */
        button[kind="secondary"] {
            background-color: #334155;
            color: #f8fafc;
            border: 1px solid #475569;
        }
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background: #0f172a;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #6366f1;'>EDQMP</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Enterprise Data Quality & Monitoring</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Tabs for Login / Sign Up
        tab_login, tab_signup = st.tabs(["🔐 Login", "👤 Sign Up"])
        
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Email", placeholder="admin@edqmp.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Sign In")
                
                if submit:
                    with st.spinner("Authenticating..."):
                        try:
                            # For MVP demo, simulate successful login for admin
                            if username and password:
                                st.session_state.authenticated = True
                                st.session_state.user = {"email": username, "role": "admin"}
                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error("Please enter credentials")
                        except Exception as e:
                            st.error(f"Login failed: {str(e)}")
            
            st.markdown("---")
            st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.9rem;'>Don't have an account?</p>", unsafe_allow_html=True)
            
            if st.button("🚀 Try Demo Account", type="secondary"):
                st.session_state.authenticated = True
                st.session_state.user = {"email": "demo@edqmp.com", "role": "viewer"}
                st.success("Welcome, Demo User!")
                st.rerun()

        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("Email Address")
                new_name = st.text_input("Full Name")
                new_pass = st.text_input("Create Password", type="password")
                confirm_pass = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("Create Account"):
                    if new_pass != confirm_pass:
                        st.error("Passwords do not match")
                    elif not new_email or not new_pass:
                        st.error("Please fill all fields")
                    else:
                        with st.spinner("Creating account..."):
                            # Simulate signup
                            st.session_state.authenticated = True
                            st.session_state.user = {"email": new_email, "role": "user", "name": new_name}
                            st.success("Account created successfully!")
                            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 0.8rem; color: #64748b;'>Protected System. Authorized Access Only.</p>", unsafe_allow_html=True)

def require_auth():
    """
    Gatekeeper function for internal pages.
    If user is not authenticated, stop execution and redirect to login.
    """
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        st.warning("⚠️ Unauthorized Access")
        st.error("You must log in to view this page.")
        if st.button("Go to Login Page"):
            st.switch_page("app.py")
        st.stop()
