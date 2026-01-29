"""
Authentication system for AI Visibility Tracker.
Supports admin (full access) and client-specific access.
"""

import streamlit as st
import hmac


def check_credentials(username: str, password: str) -> bool:
    """
    Check if username/password combination is valid.

    Args:
        username: User's email
        password: User's password

    Returns:
        True if credentials are valid
    """
    if username not in st.secrets.get("passwords", {}):
        return False

    return hmac.compare_digest(
        password,
        st.secrets["passwords"][username]
    )


def get_user_role(username: str) -> str:
    """
    Get user role (admin or client).

    Args:
        username: User's email

    Returns:
        'admin' or 'client'
    """
    return st.secrets.get("roles", {}).get(username, "client")


def get_client_brand(username: str) -> str:
    """
    Get the brand this user has access to.

    Args:
        username: User's email

    Returns:
        Brand name or "ALL" for admin
    """
    return st.secrets.get("clients", {}).get(username, None)


def is_admin(username: str) -> bool:
    """Check if user is admin."""
    return get_user_role(username) == "admin"


def login_page():
    """Display login page and handle authentication."""

    # DaSilva brand colors
    DEEP_PLUM = '#402E3A'
    OFF_WHITE = '#FBFBEF'

    st.markdown(f"""
    <style>
        .login-container {{
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .login-title {{
            color: {DEEP_PLUM};
            text-align: center;
            margin-bottom: 30px;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<h1 class='login-title'>🔐 AI Visibility Tracker</h1>", unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Email", placeholder="your@email.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if username and password:
                if check_credentials(username, password):
                    # Set session state
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["role"] = get_user_role(username)
                    st.session_state["client_brand"] = get_client_brand(username)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
            else:
                st.warning("Please enter both email and password")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.caption("© 2026 DaSilva Consulting")


def logout():
    """Logout user and clear session."""
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None
    st.session_state["client_brand"] = None
    st.rerun()


def require_authentication(allow_clients: bool = True):
    """
    Require authentication to access app.

    Args:
        allow_clients: If False, only admin can access (blocks clients)
    """
    # Check if authenticated
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        login_page()
        st.stop()

    # Check if clients are allowed
    if not allow_clients:
        if st.session_state["role"] != "admin":
            st.error("🚫 Access Denied")
            st.warning("This tool is only available to administrators.")
            st.markdown("---")
            if st.button("Logout"):
                logout()
            st.stop()


def show_user_info():
    """Display user info and logout button in sidebar."""
    with st.sidebar:
        st.markdown("---")

        role_emoji = "👑" if st.session_state["role"] == "admin" else "👤"
        st.markdown(f"{role_emoji} **{st.session_state['username']}**")

        if st.session_state["role"] == "admin":
            st.caption("Administrator")
        else:
            st.caption(f"Client: {st.session_state['client_brand']}")

        if st.button("🚪 Logout", use_container_width=True):
            logout()


def get_available_brands(all_brands: list) -> list:
    """
    Get list of brands user can access.

    Args:
        all_brands: List of all available brands

    Returns:
        Filtered list based on user role
    """
    if st.session_state["role"] == "admin":
        # Admin sees all brands
        return all_brands
    else:
        # Client sees only their brand
        client_brand = st.session_state["client_brand"]
        return [b for b in all_brands if b == client_brand]


def filter_by_brand(data: list, brand_field: str = "brand") -> list:
    """
    Filter data list by user's accessible brands.

    Args:
        data: List of dictionaries with brand field
        brand_field: Name of the brand field in data

    Returns:
        Filtered data list
    """
    if st.session_state["role"] == "admin":
        # Admin sees all data
        return data
    else:
        # Client sees only their brand
        client_brand = st.session_state["client_brand"]
        return [item for item in data if item.get(brand_field) == client_brand]
