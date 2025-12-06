"""
EDQMP Login Page
Real authentication with Supabase + Demo mode
"""
import streamlit as st
from auth_utils import (
    sign_in, sign_up, start_demo_session, 
    resend_verification_email, is_authenticated
)

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
        .verification-box {
            background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%);
            border: 1px solid #3b82f6;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #6366f1;'>EDQMP</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Enterprise Data Quality & Monitoring</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Check for pending verification
        if st.session_state.get("pending_verification"):
            show_verification_pending()
            return
        
        # Tabs for Login / Sign Up
        tab_login, tab_signup = st.tabs(["🔐 Login", "👤 Sign Up"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@company.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Sign In")
                
                if submit:
                    if not email or not password:
                        st.error("Please enter your email and password")
                    else:
                        with st.spinner("Authenticating..."):
                            success, message, user_data = sign_in(email, password)
                            
                            if success and user_data:
                                st.session_state.authenticated = True
                                st.session_state.user = user_data
                                st.session_state.is_demo = False
                                if user_data.get("access_token"):
                                    st.session_state.access_token = user_data["access_token"]
                                st.success(message)
                                st.rerun()
                            else:
                                if "verify your email" in message.lower():
                                    st.session_state.pending_verification = True
                                    st.session_state.pending_email = email
                                    st.rerun()
                                else:
                                    st.error(message)
            
            st.markdown("---")
            st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.9rem;'>Want to explore first?</p>", unsafe_allow_html=True)
            
            if st.button("🚀 Try Demo Account", type="secondary", use_container_width=True):
                start_demo_session()
                st.success("Welcome to the Demo! Explore the platform with sample data.")
                st.rerun()

        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("Email Address", placeholder="you@company.com")
                new_name = st.text_input("Full Name", placeholder="John Doe")
                new_pass = st.text_input("Create Password", type="password", placeholder="Min. 6 characters")
                confirm_pass = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
                
                # Password requirements hint
                st.caption("🔒 Password must be at least 6 characters")
                
                if st.form_submit_button("Create Account"):
                    # Validation
                    if not new_email or not new_pass or not new_name:
                        st.error("Please fill in all fields")
                    elif len(new_pass) < 6:
                        st.error("Password must be at least 6 characters")
                    elif new_pass != confirm_pass:
                        st.error("Passwords do not match")
                    elif "@" not in new_email or "." not in new_email:
                        st.error("Please enter a valid email address")
                    else:
                        with st.spinner("Creating your account..."):
                            success, message = sign_up(new_email, new_pass, new_name)
                            
                            if success:
                                if "verify" in message.lower() or "check your email" in message.lower():
                                    st.session_state.pending_verification = True
                                    st.session_state.pending_email = new_email
                                    st.rerun()
                                else:
                                    # Demo mode or auto-verified
                                    st.success(message)
                                    st.info("You can now log in with your credentials.")
                            else:
                                st.error(message)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 0.8rem; color: #64748b;'>Protected System. Authorized Access Only.</p>", unsafe_allow_html=True)


def show_verification_pending():
    """Show email verification pending screen"""
    email = st.session_state.get("pending_email", "your email")
    
    st.markdown(f"""
    <div class='verification-box'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>📧</div>
        <h2 style='color: #f8fafc; margin-bottom: 0.5rem;'>Verify Your Email</h2>
        <p style='color: #94a3b8; margin-bottom: 1rem;'>
            We've sent a verification link to<br>
            <strong style='color: #3b82f6;'>{email}</strong>
        </p>
        <p style='color: #64748b; font-size: 0.9rem;'>
            Click the link in your email to activate your account.
            <br>Check your spam folder if you don't see it.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Resend Email", use_container_width=True):
            success, message = resend_verification_email(email)
            if success:
                st.success(message)
            else:
                st.error(message)
    
    with col2:
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.pending_verification = False
            st.session_state.pending_email = None
            st.rerun()
    
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #64748b;'>Already verified? Try logging in again.</p>", unsafe_allow_html=True)
    
    if st.button("🔐 Try Logging In", type="primary", use_container_width=True):
        st.session_state.pending_verification = False
        st.rerun()


def require_auth():
    """
    Gatekeeper function for internal pages.
    If user is not authenticated, stop execution and redirect to login.
    """
    if not is_authenticated():
        st.warning("⚠️ Unauthorized Access")
        st.error("You must log in to view this page.")
        if st.button("Go to Login Page"):
            st.switch_page("app.py")
        st.stop()
