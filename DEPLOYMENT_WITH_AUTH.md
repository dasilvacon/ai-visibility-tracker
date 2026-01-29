# Complete Deployment Guide with Authentication

## What You Now Have

✅ **Two Separate Apps (Same Repo):**
1. **Main Dashboard** (`streamlit_app.py`) - Admin sees all brands, clients see only theirs
2. **Prompt Generator** (`prompt_generator_app.py`) - **Admin only** (clients blocked)

✅ **Authentication System:**
- Login page for both apps
- Role-based access (admin vs client)
- Brand-specific filtering for clients
- Logout functionality

---

## Quick Start: Deploy with Authentication

### Step 1: Set Up Local Secrets for Testing

Create file: `.streamlit/secrets.toml`

```toml
# YOUR admin account
[passwords]
"your.email@dasilva.com" = "YourSecurePassword123!"

# Example client account
[passwords."natasha.denona@example.com"]
password = "ClientPassword456!"

# Roles
[roles]
"your.email@dasilva.com" = "admin"
"natasha.denona@example.com" = "client"

# Brand access
[clients]
"your.email@dasilva.com" = "ALL"
"natasha.denona@example.com" = "Natasha Denona"
```

**Note:** Replace emails and passwords with real ones!

---

### Step 2: Test Locally

```bash
# Test Main Dashboard (admin sees all, client sees only their brand)
streamlit run streamlit_app.py --server.port 8501

# Test Prompt Generator (only admin can access)
streamlit run prompt_generator_app.py --server.port 8502
```

**Test both:**
1. Login as admin → Should see everything
2. Logout
3. Login as client → Should see limited access
4. Try prompt generator as client → Should be blocked ✅

---

### Step 3: Commit and Push

```bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker

git add .
git commit -m "Add authentication system with admin/client roles"
git push origin main
```

---

### Step 4: Deploy on Streamlit Cloud

#### Deploy Main Dashboard

1. Go to https://share.streamlit.io
2. Click "New app"
3. Fill in:
   - Repository: `ai-visibility-tracker`
   - Branch: `main`
   - Main file: `streamlit_app.py`
   - App URL: Choose like `ai-dashboard`
4. Click "Deploy!"
5. **Before testing, add secrets (Step 5 below)**

#### Deploy Prompt Generator

1. Click "New app" again
2. Fill in:
   - Repository: `ai-visibility-tracker` (same repo!)
   - Branch: `main`
   - Main file: `prompt_generator_app.py` ⭐
   - App URL: Choose like `prompt-generator`
3. Click "Deploy!"
4. **Before testing, add secrets (Step 5 below)**

---

### Step 5: Add Secrets to Streamlit Cloud

**Do this for BOTH apps:**

1. Click on your app in Streamlit Cloud
2. Click "Settings" (⚙️ icon)
3. Click "Secrets"
4. Paste:

```toml
# Replace with YOUR real credentials!
[passwords]
"your.email@dasilva.com" = "YourSecurePassword123!"
"client@example.com" = "ClientPassword456!"

[roles]
"your.email@dasilva.com" = "admin"
"client@example.com" = "client"

[clients]
"your.email@dasilva.com" = "ALL"
"client@example.com" = "Their Brand Name"
```

5. Click "Save"
6. App will automatically restart

**Important:** Add the SAME secrets to BOTH apps!

---

### Step 6: Test Your Deployment

#### Test Main Dashboard

1. Visit your dashboard URL: `https://[your-dashboard-slug].streamlit.app`
2. Should see **login page** 🔐
3. Login with admin credentials
   - ✅ Should see ALL brands in dropdown
   - ✅ Can view any report
4. Logout
5. Login with client credentials
   - ✅ Should see ONLY their brand
   - ✅ Can view only their reports

#### Test Prompt Generator

1. Visit: `https://[your-generator-slug].streamlit.app`
2. Should see **login page** 🔐
3. Login with admin credentials
   - ✅ Full access to generate/review/export
4. Logout
5. Try client credentials
   - ✅ Should see "Access Denied" message
   - ✅ Can only logout

---

## User Access Matrix

| User | Main Dashboard | Prompt Generator |
|------|---------------|------------------|
| **You (Admin)** | ✅ All brands | ✅ Full access |
| **Clients** | ✅ Only their brand | ❌ Blocked |

---

## Adding New Clients

### Step 1: Get Client Info
- Email address
- Brand name (must match report files exactly)
- Generate secure password

### Step 2: Update Secrets

In Streamlit Cloud, go to **BOTH apps** > Settings > Secrets:

```toml
# Add to existing sections:
[passwords]
# ... existing ...
"newclient@example.com" = "NewPassword789!"

[roles]
# ... existing ...
"newclient@example.com" = "client"

[clients]
# ... existing ...
"newclient@example.com" = "New Brand Name"
```

### Step 3: Save and Test
- Click "Save" (app auto-restarts)
- Test login with new credentials
- Verify they see only their brand

---

## Brand Name Mapping

**Important:** Brand names must match across:

1. **Report files:**
   ```
   data/reports/visibility_report_natasha_denona.html
   ```

2. **Secrets configuration:**
   ```toml
   [clients]
   "client@example.com" = "Natasha Denona"
   ```

3. **Code expects:**
   - File: `natasha_denona` (lowercase, underscores)
   - Display: `"Natasha Denona"` (proper case, spaces)

The code automatically converts between formats.

---

## Security Checklist

Before sharing with clients:

- [ ] Changed all default passwords in secrets
- [ ] Used strong passwords (12+ characters, mixed case, symbols)
- [ ] Added secrets to BOTH apps on Streamlit Cloud
- [ ] Tested admin login (sees all brands)
- [ ] Tested client login (sees only their brand)
- [ ] Verified client blocked from prompt generator
- [ ] `.streamlit/secrets.toml` in `.gitignore`
- [ ] Not committed secrets to GitHub

---

## Troubleshooting

### Login page doesn't show
- Make sure you pushed latest code
- Check that `src/authentication.py` exists in repo
- Restart the app in Streamlit Cloud

### "Invalid credentials"
- Check spelling of email (case-sensitive)
- Verify no extra spaces in secrets
- Make sure secrets saved in Streamlit Cloud
- Restart app after saving secrets

### Client sees wrong brand
- Brand name must match exactly (case-sensitive)
- Check report file name matches secrets config
- Verify report exists in `data/reports/`

### Client can access Prompt Generator
- Check role is "client" not "admin"
- Verify secrets in prompt generator app
- Restart app after secrets change

---

## Your Two App URLs

Once deployed, save these:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Main Dashboard (all users):                                │
│  https://________________________________.streamlit.app     │
│                                                             │
│  Prompt Generator (admin only):                             │
│  https://________________________________.streamlit.app     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Changed

New files:
- ✅ `src/authentication.py` - Auth logic
- ✅ `.streamlit/secrets.toml.template` - Secrets template
- ✅ `AUTHENTICATION_SETUP.md` - Detailed auth guide
- ✅ `DEPLOYMENT_WITH_AUTH.md` - This guide

Updated files:
- ✅ `streamlit_app.py` - Added auth (clients allowed)
- ✅ `prompt_generator_app.py` - Added auth (admin only)
- ✅ `.gitignore` - Added secrets.toml

---

## Ready to Deploy!

Follow Steps 1-6 above and you'll have two authenticated apps with role-based access in about 15 minutes! 🚀

Need help? Check `AUTHENTICATION_SETUP.md` for detailed troubleshooting.
