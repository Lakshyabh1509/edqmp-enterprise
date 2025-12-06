"""
EDQMP Authentication Utilities
Centralized Supabase authentication and session management
"""
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Try to initialize Supabase client
_supabase_client = None

def get_supabase_client():
    """Get or create Supabase client singleton"""
    global _supabase_client
    
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            return None
        try:
            from supabase import create_client, Client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except ImportError:
            st.warning("Supabase library not installed. Running in demo mode only.")
            return None
        except Exception as e:
            st.error(f"Failed to connect to Supabase: {e}")
            return None
    
    return _supabase_client


def is_demo_mode() -> bool:
    """Check if current session is in demo mode"""
    return st.session_state.get("is_demo", False)


def get_current_user() -> dict | None:
    """Get the current authenticated user"""
    return st.session_state.get("user", None)


def get_current_user_id() -> str | None:
    """Get authenticated user's ID for data filtering"""
    user = get_current_user()
    if user:
        return user.get("id") or user.get("email")
    return None


def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)


def sign_up(email: str, password: str, full_name: str = "") -> tuple[bool, str]:
    """
    Register a new user with Supabase
    Returns (success, message)
    """
    client = get_supabase_client()
    
    if not client:
        # Fallback: Allow signup without Supabase (demo mode)
        return True, "Account created! (Demo mode - no email verification)"
    
    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })
        
        if response.user:
            # Check if email confirmation is required
            if response.user.email_confirmed_at is None:
                return True, "Account created! Please check your email to verify your account."
            else:
                return True, "Account created and verified! You can now log in."
        else:
            return False, "Failed to create account. Please try again."
            
    except Exception as e:
        error_msg = str(e)
        if "already registered" in error_msg.lower():
            return False, "An account with this email already exists."
        return False, f"Sign up failed: {error_msg}"


def sign_in(email: str, password: str) -> tuple[bool, str, dict | None]:
    """
    Sign in with email and password
    Returns (success, message, user_data)
    """
    client = get_supabase_client()
    
    if not client:
        # Fallback: Demo mode login (any credentials work)
        user_data = {
            "id": f"demo_{email}",
            "email": email,
            "role": "user",
            "is_demo": False,
            "email_verified": True  # Skip verification in demo mode
        }
        return True, "Login successful! (Demo mode)", user_data
    
    try:
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Check email verification status
            is_verified = response.user.email_confirmed_at is not None
            
            if not is_verified:
                return False, "Please verify your email before logging in. Check your inbox for the verification link.", None
            
            user_data = {
                "id": response.user.id,
                "email": response.user.email,
                "role": response.user.user_metadata.get("role", "user"),
                "full_name": response.user.user_metadata.get("full_name", ""),
                "is_demo": False,
                "email_verified": True,
                "access_token": response.session.access_token if response.session else None
            }
            return True, "Login successful!", user_data
        else:
            return False, "Invalid credentials. Please check your email and password.", None
            
    except Exception as e:
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
            return False, "Invalid email or password. Please try again."
        return False, f"Login failed: {error_msg}"


def sign_out():
    """Sign out the current user"""
    client = get_supabase_client()
    
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass  # Ignore sign out errors
    
    # Clear session state
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.is_demo = False
    if "access_token" in st.session_state:
        del st.session_state["access_token"]


def start_demo_session():
    """Start a demo session with sample data access"""
    st.session_state.authenticated = True
    st.session_state.is_demo = True
    st.session_state.user = {
        "id": "demo_user",
        "email": "demo@edqmp.com",
        "role": "viewer",
        "full_name": "Demo User",
        "is_demo": True,
        "email_verified": True
    }


def resend_verification_email(email: str) -> tuple[bool, str]:
    """Resend the verification email"""
    client = get_supabase_client()
    
    if not client:
        return False, "Email verification not available in demo mode."
    
    try:
        client.auth.resend({
            "type": "signup",
            "email": email
        })
        return True, "Verification email sent! Please check your inbox."
    except Exception as e:
        return False, f"Failed to resend verification email: {e}"


# Empty state helper for pages
def show_empty_state(title: str, message: str, cta_label: str = None, cta_callback = None):
    """Display a beautiful empty state for new users"""
    st.markdown(f"""
    <div style='
        text-align: center; 
        padding: 4rem 2rem; 
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        border: 1px dashed #334155;
        margin: 2rem 0;
    '>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>📊</div>
        <h2 style='color: #f8fafc; margin-bottom: 0.5rem;'>{title}</h2>
        <p style='color: #94a3b8; max-width: 400px; margin: 0 auto 1.5rem;'>{message}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if cta_label and cta_callback:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(cta_label, type="primary", use_container_width=True):
                cta_callback()
