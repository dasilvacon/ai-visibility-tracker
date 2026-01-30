# Deploy Step-by-Step Guide

✅ **Code pushed to GitHub!** Now let's deploy both apps.

---

## Step 2: Deploy Main Dashboard on Streamlit Cloud

### 2A. Go to Streamlit Cloud

1. Open: **https://share.streamlit.io**
2. Sign in with your GitHub account

### 2B. Create New App (Main Dashboard)

1. Click **"New app"** button (top right)

2. Fill in the form:
   ```
   Repository:    dasilvacon/ai-visibility-tracker
   Branch:        main
   Main file:     streamlit_app.py
   App URL:       ai-visibility-dashboard (or choose your own)
   ```

3. Click **"Deploy!"**

4. **Wait ~2 minutes** for deployment

5. ⚠️ **DON'T TEST YET** - Need to add secrets first!

---

## Step 3: Add Secrets to Main Dashboard

### 3A. Open App Settings

1. In Streamlit Cloud dashboard, click on your **Main Dashboard** app
2. Click **"Settings"** button (⚙️ icon in top right)
3. Click **"Secrets"** tab

### 3B. Copy This Template

Replace with YOUR actual credentials:

```toml
# YOUR ADMIN ACCOUNT (replace with your real email and password)
[passwords]
"your.email@dasilva.com" = "YourSecurePassword123!"

# EXAMPLE CLIENT ACCOUNT (add real client info)
[passwords."natasha.denona@example.com"]
password = "ClientPassword456!"

# USER ROLES
[roles]
"your.email@dasilva.com" = "admin"
"natasha.denona@example.com" = "client"

# BRAND ACCESS
[clients]
"your.email@dasilva.com" = "ALL"
"natasha.denona@example.com" = "Natasha Denona"
```

### 3C. Paste and Save

1. Paste the config (with your actual credentials)
2. Click **"Save"**
3. App will automatically restart
4. Close the settings panel

---

## Step 4: Test Main Dashboard

1. Click on your app URL (or visit the app)
2. You should see a **login page** 🔐
3. **Test admin login:**
   - Enter your admin email and password
   - Click "Login"
   - ✅ Should see ALL brands in dropdown
4. Click **"Logout"** (in sidebar)
5. **Test client login:**
   - Enter client email and password
   - Click "Login"
   - ✅ Should see ONLY their brand in dropdown

**If both work, proceed to deploy Prompt Generator!**

---

## Step 5: Deploy Prompt Generator

### 5A. Create Second App

1. In Streamlit Cloud, click **"New app"** again
2. Fill in the form:
   ```
   Repository:    dasilvacon/ai-visibility-tracker  (same repo!)
   Branch:        main
   Main file:     prompt_generator_app.py  ⭐ DIFFERENT FILE
   App URL:       prompt-generator (or choose your own)
   ```

3. Click **"Deploy!"**

4. **Wait ~2 minutes** for deployment

5. ⚠️ **DON'T TEST YET** - Need to add secrets!

---

## Step 6: Add Secrets to Prompt Generator

### 6A. Open Prompt Generator Settings

1. Click on your **Prompt Generator** app
2. Click **"Settings"** button (⚙️ icon)
3. Click **"Secrets"** tab

### 6B. Copy THE SAME Secrets

**Important:** Use the EXACT SAME secrets as Main Dashboard!

```toml
# Paste the same configuration you used for Main Dashboard
[passwords]
"your.email@dasilva.com" = "YourSecurePassword123!"
"natasha.denona@example.com" = "ClientPassword456!"

[roles]
"your.email@dasilva.com" = "admin"
"natasha.denona@example.com" = "client"

[clients]
"your.email@dasilva.com" = "ALL"
"natasha.denona@example.com" = "Natasha Denona"
```

### 6C. Save

1. Click **"Save"**
2. App restarts
3. Close settings

---

## Step 7: Test Prompt Generator

1. Visit your Prompt Generator app URL
2. Should see **login page** 🔐
3. **Test admin login:**
   - Enter your admin email and password
   - ✅ Should see the Generate page (full access)
4. Click **"Logout"** (in sidebar)
5. **Test client login:**
   - Enter client email and password
   - ✅ Should see **"Access Denied"** message
   - ✅ Can only logout (clients blocked!)

---

## Step 8: Save Your URLs

Write down both app URLs for reference:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Main Dashboard:                                            │
│  https://________________________________.streamlit.app     │
│                                                             │
│  Prompt Generator:                                          │
│  https://________________________________.streamlit.app     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Success Checklist

Your deployment is complete when:

- [ ] Main Dashboard deployed
- [ ] Main Dashboard has secrets configured
- [ ] Admin can see ALL brands in Main Dashboard
- [ ] Client can see ONLY their brand in Main Dashboard
- [ ] Prompt Generator deployed
- [ ] Prompt Generator has secrets configured
- [ ] Admin can access Prompt Generator
- [ ] Client is BLOCKED from Prompt Generator
- [ ] Both URLs saved for reference

---

## 🎉 You're Done!

You now have:
- ✅ Two separate apps from one repository
- ✅ Role-based authentication
- ✅ Admin sees everything
- ✅ Clients see only their brand
- ✅ Prompt Generator is admin-only

---

## Next Steps

### To Add a New Client:

1. Go to **both apps** in Streamlit Cloud
2. Settings > Secrets
3. Add new credentials:
   ```toml
   [passwords]
   # ... existing ...
   "newclient@example.com" = "TheirPassword789"

   [roles]
   # ... existing ...
   "newclient@example.com" = "client"

   [clients]
   # ... existing ...
   "newclient@example.com" = "Their Brand Name"
   ```
4. Save (both apps restart automatically)

### To Use Prompt Generator:

1. Visit your Prompt Generator URL
2. Login with your admin credentials
3. Go to "Generate" page
4. Set slider to desired number of prompts
5. Click "Generate Prompts"
6. Review and approve in "Review & Approve" page
7. Export to CSV in "Export" page

---

## Troubleshooting

### "Can't find secrets" error
- Make sure you clicked "Save" after pasting secrets
- Check both apps have secrets configured
- Restart the app manually if needed

### Login doesn't work
- Check email spelling (case-sensitive)
- Verify password is correct
- No extra spaces in secrets configuration

### Client sees all brands
- Make sure role is "client" not "admin"
- Check brand name matches exactly
- Restart app after changing secrets

---

**Need help?** Check these files in your repo:
- `AUTHENTICATION_SETUP.md` - Detailed auth guide
- `DEPLOYMENT_WITH_AUTH.md` - Complete deployment reference
- `PROMPT_GENERATOR_GUIDE.md` - How to use the tool

🚀 Happy deploying!
