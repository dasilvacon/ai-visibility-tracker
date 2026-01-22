# Authentication Setup Guide

This guide explains how to set up client authentication for your Streamlit dashboard.

## Overview

The authenticated dashboard (`streamlit_app_auth.py`) provides:
- **Secure login** for each client
- **Brand-specific access** - clients only see their own report
- **Simple password protection** without complex setup
- **Easy credential management** via Streamlit secrets

---

## Local Testing

### Step 1: Create Local Secrets File

Copy the example file and add your credentials:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

### Step 2: Edit secrets.toml

Open `.streamlit/secrets.toml` and add your client credentials:

```toml
[passwords]
natasha_denona = "SecurePassword123"
client2 = "AnotherPassword456"

[brands]
natasha_denona = "Natasha Denona"
client2 = "Brand Name 2"
```

**Important**:
- Usernames should match the report file names (use underscores)
- Brand names must exactly match the report file names
- Use strong, unique passwords for each client

### Step 3: Test Locally

```bash
streamlit run streamlit_app_auth.py
```

Try logging in with:
- **Username**: `natasha_denona`
- **Password**: (whatever you set in secrets.toml)

---

## Deploying to Streamlit Cloud

### Step 1: Push Code to GitHub

Make sure your authenticated app is pushed:

```bash
git add streamlit_app_auth.py .streamlit/secrets.toml.example AUTHENTICATION_SETUP.md
git commit -m "Add authentication for client dashboard"
git push
```

**Note**: `.streamlit/secrets.toml` is automatically ignored by git (it's in `.gitignore`)

### Step 2: Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. **Repository**: `dasilvacon/ai-visibility-tracker`
4. **Branch**: `main`
5. **Main file path**: `streamlit_app_auth.py` (NOT streamlit_app.py)
6. Click "Advanced settings"

### Step 3: Add Secrets to Streamlit Cloud

In the "Secrets" section, paste your credentials:

```toml
[passwords]
natasha_denona = "SecurePassword123"
client2 = "AnotherPassword456"

[brands]
natasha_denona = "Natasha Denona"
client2 = "Brand Name 2"
```

**Important Security Notes**:
- Never commit `secrets.toml` to GitHub
- Use different passwords than your examples
- Change passwords regularly
- Use strong passwords (12+ characters, mix of letters/numbers/symbols)

### Step 4: Deploy

Click "Deploy" and wait 2-3 minutes for the app to build.

---

## Adding New Clients

### For Local Testing

Edit `.streamlit/secrets.toml`:

```toml
[passwords]
natasha_denona = "password1"
new_client = "password2"

[brands]
natasha_denona = "Natasha Denona"
new_client = "New Client Brand Name"
```

Restart Streamlit to apply changes.

### For Streamlit Cloud

1. Go to your app on https://share.streamlit.io
2. Click ⚙️ Settings → Secrets
3. Add the new client credentials:

```toml
[passwords]
new_client = "password2"

[brands]
new_client = "New Client Brand Name"
```

4. Click "Save"
5. App will automatically restart with new credentials

---

## Username and Brand Mapping

The system maps usernames to brand names:

```
Username (login)     →  Brand Name (report)
natasha_denona       →  Natasha Denona
rare_beauty          →  Rare Beauty
charlotte_tilbury    →  Charlotte Tilbury
```

**Rules**:
- Username uses underscores: `natasha_denona`
- Brand name matches report files: `Natasha_Denona` or `Natasha Denona`
- Report files: `sources_Natasha_Denona.csv`, `action_plan_Natasha_Denona.csv`, etc.

---

## Security Best Practices

### 1. Strong Passwords

Generate secure passwords:

```python
import secrets
import string

def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

print(generate_password())  # Example: "k9$mP2@xL5#nQ8&w"
```

### 2. Password Sharing with Clients

**Option A: Secure Email**
```
Subject: Your AI Visibility Dashboard Access

Hi [Client Name],

Your dashboard is ready at: https://your-app.streamlit.app

Login credentials:
Username: natasha_denona
Password: [SecurePassword]

Please change your password after first login.

Best regards,
Tiffany
```

**Option B: Password Manager**
- Share via 1Password, LastPass, or similar
- Generate temporary link that expires

**Option C: Temporary Passwords**
- Give client temporary password
- Have them contact you to set permanent one

### 3. Regular Security Maintenance

- Change passwords every 90 days
- Remove access for inactive clients
- Monitor login attempts (check Streamlit logs)
- Keep backup of client credentials (encrypted)

---

## Troubleshooting

### "Invalid username or password"

**Cause**: Credentials don't match secrets.toml

**Solution**:
1. Check username spelling (case-sensitive)
2. Verify password matches exactly
3. Ensure secrets.toml is properly formatted (TOML syntax)
4. Restart Streamlit after changing secrets

### "Brand not found" after login

**Cause**: Brand name doesn't match report files

**Solution**:
1. Check brand name in `[brands]` section
2. Verify report files exist: `ls data/reports/`
3. Ensure brand name matches file naming: `sources_Brand_Name.csv`
4. Check for spaces vs underscores

### Secrets not working on Streamlit Cloud

**Cause**: Secrets not saved properly

**Solution**:
1. Go to app Settings → Secrets
2. Verify TOML syntax (no extra quotes, proper brackets)
3. Click "Save" (not just close)
4. Wait for app to restart (watch status indicator)

---

## Upgrading to Advanced Authentication

For more advanced needs, consider:

### 1. Hash Passwords

Instead of plaintext passwords, use hashed versions:

```python
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# In secrets.toml
[passwords]
client1 = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # hashed
```

Update `check_password()` in `streamlit_app_auth.py`:

```python
def check_password(username: str, password: str) -> bool:
    try:
        if hasattr(st, 'secrets') and 'passwords' in st.secrets:
            stored_hash = st.secrets['passwords'].get(username)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if stored_hash and stored_hash == password_hash:
                return True
    except Exception:
        pass
    return False
```

### 2. Session Timeout

Add automatic logout after inactivity:

```python
from datetime import datetime, timedelta

if 'last_activity' not in st.session_state:
    st.session_state.last_activity = datetime.now()

# Check timeout (30 minutes)
if datetime.now() - st.session_state.last_activity > timedelta(minutes=30):
    logout()

# Update activity timestamp
st.session_state.last_activity = datetime.now()
```

### 3. Multi-Factor Authentication

For high-security needs:
- Use `streamlit-authenticator` package
- Implement email verification
- Add SMS/TOTP codes

---

## FAQ

**Q: Can multiple clients share the same dashboard?**
A: Yes! Each client logs in with their own credentials and sees only their brand's data.

**Q: Can a client see multiple brands?**
A: Currently, each username maps to one brand. To give access to multiple brands, create multiple usernames for that client.

**Q: How do I remove a client's access?**
A: Simply delete their entry from `secrets.toml` (local) or Streamlit Cloud secrets.

**Q: Can I use OAuth (Google, GitHub login)?**
A: Yes, but requires additional setup with `streamlit-oauth` package. The current system is simpler for small client numbers.

**Q: Is this secure enough for sensitive data?**
A: For basic client reports, yes. For highly sensitive data, consider adding:
- Password hashing
- HTTPS (automatic on Streamlit Cloud)
- Session management
- Audit logging

---

## Example: Complete Setup for New Client

Let's add "Rare Beauty" as a new client:

### 1. Generate Reports

```bash
python main.py --analyze --brand-config data/rare_beauty_brand_config.json
```

This creates:
- `data/reports/sources_Rare_Beauty.csv`
- `data/reports/action_plan_Rare_Beauty.csv`
- etc.

### 2. Add Credentials

In `.streamlit/secrets.toml`:

```toml
[passwords]
rare_beauty = "RareBeauty2024!Secure"

[brands]
rare_beauty = "Rare Beauty"
```

### 3. Test Locally

```bash
streamlit run streamlit_app_auth.py
```

Login with `rare_beauty` / `RareBeauty2024!Secure`

### 4. Deploy to Streamlit Cloud

Update secrets in Streamlit Cloud settings, save, and share URL with client.

---

## Next Steps

- ✅ Test authentication locally
- ✅ Deploy to Streamlit Cloud
- ✅ Add your client credentials
- ✅ Share login details with client
- 📧 Set up email notifications (optional)
- 🎨 Customize branding (optional)
- 🔒 Implement password hashing (optional)

---

## Support

Need help? Check:
- Streamlit Docs: https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management
- Authentication Guide: https://blog.streamlit.io/streamlit-authenticator-part-1-adding-an-authentication-component-to-your-app/

---

**Your authenticated dashboard is ready!** 🎉

Share the URL with your client along with their login credentials, and they can securely access their AI visibility report.
