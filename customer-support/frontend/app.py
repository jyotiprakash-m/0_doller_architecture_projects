"""
SupportSim AI — Streamlit Frontend
Main application entry point with authentication and navigation.
"""
import streamlit as st
from utils.api_client import APIClient
from utils.styles import inject_custom_css

# Page config
st.set_page_config(
    page_title="SupportSim AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom styling
inject_custom_css()

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None
if "api" not in st.session_state:
    st.session_state.api = APIClient()


def show_login():
    """Show login/register form."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 3rem; margin-bottom: 0;">🎯 SupportSim AI</h1>
        <p style="font-size: 1.2rem; color: #9ca3af; margin-top: 0.5rem;">
            AI-Powered Customer Support Agent Training Platform
        </p>
        <p style="color: #6b7280; font-size: 0.9rem;">
            Train smarter. Support better. All running locally at $0 cost.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔑 Login", "✨ Register"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@company.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

            if submitted and email and password:
                result = st.session_state.api.login(email, password)
                if result:
                    st.session_state.token = result["token"]
                    st.session_state.user = result["user"]
                    st.session_state.api.set_token(result["token"])
                    st.rerun()
                else:
                    st.error("Invalid email or password")

    with tab_register:
        with st.form("register_form"):
            reg_name = st.text_input("Full Name", placeholder="John Doe")
            reg_email = st.text_input("Email", placeholder="you@company.com", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_pass")
            reg_submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

            if reg_submitted and reg_email and reg_password:
                result = st.session_state.api.register(reg_email, reg_password, reg_name)
                if result:
                    st.session_state.token = result["token"]
                    st.session_state.user = result["user"]
                    st.session_state.api.set_token(result["token"])
                    st.success("Account created! Welcome aboard! 🎉")
                    st.rerun()
                else:
                    st.error("Registration failed. Email may already be in use.")


def show_sidebar():
    """Show authenticated sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid #374151;">
            <h2 style="margin: 0; font-size: 1.5rem;">🎯 SupportSim AI</h2>
            <p style="color: #9ca3af; font-size: 0.8rem; margin: 0.3rem 0 0 0;">Agent Training Platform</p>
        </div>
        """, unsafe_allow_html=True)

        user = st.session_state.user
        st.markdown(f"""
        <div style="padding: 1rem 0; border-bottom: 1px solid #374151;">
            <p style="margin: 0; font-weight: 600;">👤 {user.get('full_name') or user['email']}</p>
            <p style="margin: 0.2rem 0; color: #9ca3af; font-size: 0.85rem;">{user['email']}</p>
            <p style="margin: 0.5rem 0 0 0;">
                <span style="background: linear-gradient(135deg, #10b981, #059669); padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.8rem; font-weight: 600;">
                    💎 {user.get('credits', 0)} Credits
                </span>
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")  # spacer

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.api.set_token(None)
            st.rerun()


def show_home():
    """Show home page for authenticated users."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>Welcome to SupportSim AI 🎯</h1>
        <p style="color: #9ca3af; font-size: 1.1rem;">
            Train your customer support skills with AI-powered simulations
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1e3a5f, #0f172a); padding: 1.5rem; border-radius: 1rem; text-align: center; border: 1px solid #1e40af;">
            <div style="font-size: 2rem;">📊</div>
            <h3 style="margin: 0.5rem 0;">Dashboard</h3>
            <p style="color: #9ca3af; font-size: 0.85rem;">View your stats & progress</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a3a2a, #0f172a); padding: 1.5rem; border-radius: 1rem; text-align: center; border: 1px solid #065f46;">
            <div style="font-size: 2rem;">📚</div>
            <h3 style="margin: 0.5rem 0;">Knowledge Base</h3>
            <p style="color: #9ca3af; font-size: 0.85rem;">Upload company docs</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #3a1a3a, #0f172a); padding: 1.5rem; border-radius: 1rem; text-align: center; border: 1px solid #7e22ce;">
            <div style="font-size: 2rem;">🎭</div>
            <h3 style="margin: 0.5rem 0;">Training</h3>
            <p style="color: #9ca3af; font-size: 0.85rem;">Start a simulation</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #3a2a1a, #0f172a); padding: 1.5rem; border-radius: 1rem; text-align: center; border: 1px solid #b45309;">
            <div style="font-size: 2rem;">📝</div>
            <h3 style="margin: 0.5rem 0;">Review</h3>
            <p style="color: #9ca3af; font-size: 0.85rem;">AI feedback & scores</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.info("👈 Use the sidebar pages to navigate: **Dashboard**, **Knowledge Base**, **Training**, **Review**, **Scenarios**")


# Main app logic
if st.session_state.token:
    show_sidebar()
    show_home()
else:
    show_login()
