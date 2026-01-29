# Authentication Setup Guide

## Overview

I've implemented multi-user authentication with two access levels:

✅ **Admin (You):**
- Access to ALL brands in Main Dashboard
- Full access to Prompt Generator
- Can see everything

✅ **Clients:**
- Access ONLY to their brand in Main Dashboard
- **BLOCKED** from Prompt Generator (admin only)
- Limited view

---

## Step 1: Set Up Secrets (Required!)

### For Local Testing

Create a file: `.streamlit/secrets.toml` (local only, don't commit!)

```toml
# User passwords
[passwords]
"tiffany@dasilva.com" = "your_secure_password"
"natasha.denona@example.com" = "client_password_123"

# User roles
[roles]
"tiffany@dasilva.com" = "admin"
"natasha.denona@example.com" = "client"

# Brand access
[clients]
"tiffany@dasilva.com" = "ALL"
"natasha.denona@example.com" = "Natasha Denona"
```

**Important:** Add to `.gitignore`:
```bash
echo ".streamlit/secrets.toml" >> .gitignore
```

### For Streamlit Cloud (Production)

1. **Go to Streamlit Cloud:** https://share.streamlit.io

2. **For EACH app (Main Dashboard + Prompt Generator):**
   - Click on your app
   - Click **"Settings"** (⚙️ icon)
   - Click **"Secrets"**
   - Paste this (replace with real emails/passwords):

```toml
# Admin account (YOU)
[passwords]
"your@email.com" = "your_secure_password_here"

# Client accounts
"natasha.denona@example.com" = "nd_password_123"

# Roles (admin or client)
[roles]
"your@email.com" = "admin"
"natasha.denona@example.com" = "client"

# Brand access (admin gets "ALL", clients get specific brand)
[clients]
"your@email.com" = "ALL"
"natasha.denona@example.com" = "Natasha Denona"
```

3. **Click "Save"**

4. **Repeat for both apps**

---

## Step 2: Add Secrets to .gitignore

```bash
echo ".streamlit/secrets.toml" >> .gitignore
```

---

## Step 3: Test Locally

Create `.streamlit/secrets.toml` and test both apps:

```bash
# Test Main Dashboard
streamlit run streamlit_app.py --server.port 8501

# Test Prompt Generator
streamlit run prompt_generator_app.py --server.port 8502
```

**Expected behavior:**
- Login page appears first
- Admin sees all brands / full prompt generator access
- Client sees only their brand / blocked from prompt generator

---

## Adding New Clients

Update secrets and add:

```toml
[passwords]
"newclient@example.com" = "secure_password"

[roles]
"newclient@example.com" = "client"

[clients]
"newclient@example.com" = "Their Brand Name"
```

---

See full guide in repository for complete details.
