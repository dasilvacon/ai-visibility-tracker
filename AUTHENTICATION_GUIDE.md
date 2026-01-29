# Authentication & Multi-Client Access Guide

## Current State: No Authentication ⚠️

Both apps (Main Dashboard and Prompt Generator) are currently **public** - anyone with the URL can access them.

---

## Authentication Options

### Option 1: Streamlit Built-in Authentication (Recommended for Start)

Streamlit Community Cloud has simple built-in auth:

**How it works:**
- User enters email or Google login
- You whitelist specific email addresses
- Only whitelisted users can access

**Setup:**

1. **In Streamlit Cloud Dashboard:**
   - Go to your app settings
   - Click "Sharing"
   - Enable "Restrict app access"
   - Add allowed email addresses

2. **No code changes needed!**

**Pros:**
✅ Super easy to set up (no coding)
✅ Free on Streamlit Cloud
✅ Google SSO supported

**Cons:**
⚠️ No client-specific customization
⚠️ All authenticated users see same content
⚠️ No multi-tenancy

---

### Option 2: Custom Password Authentication

Add a simple login page with username/password.

**Implementation:**

Add this to the **top** of both `streamlit_app.py` and `prompt_generator_app.py`:

```python
import streamlit as st
import hmac

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # First run, show login
    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False

    # Password not correct, show input + error
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False

    # Password correct
    else:
        return True

# Add this check at the start of your app
if not check_password():
    st.stop()  # Don't run the rest of the app

# Rest of your app code continues here...
```

**In Streamlit Cloud, add secrets:**
1. Go to app settings
2. Click "Secrets"
3. Add:
```toml
password = "your_secure_password_here"
```

**Pros:**
✅ Simple to implement
✅ Works for single password access
✅ No external dependencies

**Cons:**
⚠️ Single password for everyone
⚠️ No user management
⚠️ No client-specific views

---

### Option 3: Multi-Client Authentication with Client-Specific Data

**This is what you probably want** - different clients see different dashboards/data.

**Implementation:**

#### Step 1: Define Users & Clients in Secrets

In Streamlit Cloud secrets (`.streamlit/secrets.toml`):

```toml
# Client credentials
[passwords]
"natasha.denona@example.com" = "nd_password_123"
"client2@example.com" = "client2_password_456"
"admin@dasilva.com" = "admin_password_789"

# Client to brand mapping
[clients]
"natasha.denona@example.com" = "Natasha Denona"
"client2@example.com" = "Client Brand 2"
"admin@dasilva.com" = "ALL"  # Admin sees all brands
```

#### Step 2: Add Login Function

Create `src/authentication.py`:

```python
import streamlit as st
import hmac

def check_credentials(username, password):
    """Check if username/password combination is valid."""
    if username in st.secrets["passwords"]:
        return hmac.compare_digest(
            password,
            st.secrets["passwords"][username]
        )
    return False

def get_client_brand(username):
    """Get the brand this client has access to."""
    return st.secrets["clients"].get(username, None)

def login_page():
    """Display login page and handle authentication."""

    st.title("🔐 AI Visibility Tracker - Login")

    with st.form("login_form"):
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if check_credentials(username, password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["client_brand"] = get_client_brand(username)
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.markdown("---")
    st.caption("© 2026 DaSilva Consulting")

def logout():
    """Logout user."""
    st.session_state["authenticated"] = False
    st.session_state["username"] = None
    st.session_state["client_brand"] = None
    st.rerun()

def require_authentication():
    """Check if user is authenticated, show login if not."""
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        login_page()
        st.stop()  # Don't run rest of app

    # Show logout button in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"👤 Logged in as: {st.session_state['username']}")
        if st.button("Logout"):
            logout()
```

#### Step 3: Update Main App

In `streamlit_app.py` (Main Dashboard):

```python
import streamlit as st
import sys
sys.path.insert(0, 'src')

from authentication import require_authentication

# Set page config
st.set_page_config(...)

# Require authentication BEFORE anything else
require_authentication()

# Now get client brand
client_brand = st.session_state["client_brand"]

# Filter data based on client
if client_brand == "ALL":
    # Admin sees all brands
    available_brands = ["Natasha Denona", "Client Brand 2", "All brands..."]
else:
    # Regular client sees only their brand
    available_brands = [client_brand]

# Rest of your dashboard code...
# Use `client_brand` to filter reports, data, etc.
```

#### Step 4: Update Prompt Generator

In `prompt_generator_app.py`:

```python
import streamlit as st
import sys
sys.path.insert(0, 'src')

from authentication import require_authentication

# Set page config
st.set_page_config(...)

# Require authentication
require_authentication()

# Get client brand
client_brand = st.session_state["client_brand"]

# Load personas/keywords for this client
if client_brand == "ALL":
    # Admin can select any brand
    personas_file = st.sidebar.selectbox(
        "Select Brand",
        ["natasha_denona", "client2", ...]
    )
else:
    # Client sees only their brand's data
    brand_slug = client_brand.lower().replace(" ", "_")
    personas_file = f"data/{brand_slug}_personas.json"

# Rest of your prompt generator code...
```

---

## Recommended Setup for Client Access

### Phase 1: Simple Password (Quick Start)
Use **Option 2** (Custom Password) to lock down your apps immediately.

### Phase 2: Multi-Client (When You Have Multiple Clients)
Implement **Option 3** (Multi-Client Auth) with:
- Email-based login
- Client-specific brand access
- Admin account sees everything

---

## File Structure for Multi-Client

Organize data files by client:

```
data/
├── natasha_denona_personas.json
├── natasha_denona_keywords.csv
├── natasha_denona_generated_prompts.csv
├── client2_personas.json
├── client2_keywords.csv
├── client2_generated_prompts.csv
└── reports/
    ├── natasha_denona/
    │   └── report_20260129.json
    └── client2/
        └── report_20260129.json
```

In your code:
```python
client_slug = client_brand.lower().replace(" ", "_")
personas_file = f"data/{client_slug}_personas.json"
keywords_file = f"data/{client_slug}_keywords.csv"
prompts_file = f"data/{client_slug}_generated_prompts.csv"
```

---

## Security Best Practices

1. **Always use secrets management**
   - Never hardcode passwords in code
   - Use Streamlit Cloud secrets or environment variables

2. **Use HTTPS**
   - Streamlit Cloud provides this automatically

3. **Hash passwords properly**
   - Use `hmac.compare_digest()` for password comparison
   - Store password hashes, not plain text

4. **Session management**
   - Streamlit handles sessions automatically
   - Use `st.session_state` for user data

5. **Input validation**
   - Sanitize user inputs
   - Prevent SQL injection (if using databases)

---

## Quick Decision Guide

**"I just want to lock down the apps"**
→ Use **Option 1** (Streamlit built-in auth)

**"I need a simple password for my team"**
→ Use **Option 2** (Custom password)

**"I have multiple clients who should see different data"**
→ Use **Option 3** (Multi-client auth)

**"I need enterprise-grade auth with SSO"**
→ Consider using authentication services like Auth0, or upgrade to Streamlit Enterprise

---

## Implementation Steps

Want me to implement authentication for you? Let me know:

1. Which option do you want? (1, 2, or 3)
2. Do you have multiple clients now, or planning for future?
3. Should clients have separate data files, or same data filtered differently?

I can add the authentication code to your apps right now!
