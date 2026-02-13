# Deployment Guide - Prompt Generator on Streamlit Cloud

## Overview

This guide shows you how to deploy the **Prompt Generator & Approval Tool** as a **separate app** on Streamlit Community Cloud, independent from your main AI Visibility Dashboard.

---

## Prerequisites

- ✅ GitHub account with repository access
- ✅ Streamlit Community Cloud account (https://share.streamlit.io)
- ✅ Your repository pushed to GitHub

---

## Step 1: Push Code to GitHub

Make sure all the prompt generator files are committed and pushed:

```bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker

git add .
git commit -m "Add Prompt Generator & Approval Tool"
git push origin main
```

**Important files to include:**
- `prompt_generator_app.py` (main entry point)
- `prompt_generator_pages/` (all UI pages)
- `src/prompt_generator/` (deduplicator, approval manager)
- `data/natasha_denona_personas.json`
- `data/natasha_denona_keywords.csv`
- `requirements.txt`
- `.streamlit/config.toml`

---

## Step 2: Deploy on Streamlit Cloud

### 2.1 Go to Streamlit Cloud
1. Open https://share.streamlit.io
2. Sign in with your GitHub account

### 2.2 Create New App
1. Click **"New app"** button (top right)
2. You'll see a deployment form like this:

```
Repository: [dropdown]
Branch: [dropdown]
Main file path: [text input]
App URL (optional): [text input]
```

### 2.3 Fill in Deployment Form

**Repository:**
- Select your repository (e.g., `tiffanydasilva/ai-visibility-tracker`)

**Branch:**
- Select `main` (or your default branch)

**Main file path:**
- Enter: `prompt_generator_app.py` ⭐ **This is the key difference!**
- NOT `streamlit_app.py` (that's your main dashboard)

**App URL:**
- Choose a custom URL slug like:
  - `prompt-generator`
  - `ai-prompt-tool`
  - `nd-prompt-generator`
- This will be: `https://[your-slug].streamlit.app`

### 2.4 Advanced Settings (Optional)

Click "Advanced settings" if you need to:
- Set Python version (3.10+ recommended)
- Add secrets (not needed for prompt generator)
- Configure environment variables

### 2.5 Deploy!

Click **"Deploy!"** button

Streamlit will:
- Clone your repository
- Install dependencies from `requirements.txt`
- Start the app from `prompt_generator_app.py`
- Provide you with a public URL

---

## Step 3: Verify Deployment

Once deployed, you should see:

✅ **App URL:** `https://[your-slug].streamlit.app`

✅ **Four Pages:**
- Generate (with prompt count slider)
- Review & Approve (with filters)
- Export (CSV/JSON export)
- Settings (configuration)

✅ **DaSilva Branding:**
- Deep plum colors
- Off-white background
- Proper styling

---

## Step 4: You Now Have Two Apps!

| App | Repository File | URL |
|-----|----------------|-----|
| **Main Dashboard** | `streamlit_app.py` | `https://[dashboard-url].streamlit.app` |
| **Prompt Generator** | `prompt_generator_app.py` | `https://[generator-url].streamlit.app` |

Both apps:
- Share the same GitHub repository
- Run independently
- Have separate URLs
- Can be updated separately

---

## Data Management for Cloud Deployment

### Important: File Storage Limitation

Streamlit Community Cloud apps have **ephemeral file systems** - any files created during runtime are lost when the app restarts.

### Solution: GitHub as Source of Truth

**Workflow for Cloud-Deployed Apps:**

1. **Generate prompts** in Prompt Generator app (cloud)
2. **Approve prompts** using filters and bulk actions
3. **Export to CSV** - download the file
4. **Commit to GitHub:**
   ```bash
   git add data/generated_prompts.csv
   git commit -m "Add approved prompts"
   git push
   ```
5. **Main Dashboard** will pick up changes on next reload

### Alternative: Keep Prompt Generator Local

For a simpler workflow, you can:

1. **Run Prompt Generator locally only:**
   ```bash
   streamlit run prompt_generator_app.py --server.port 8502
   ```

2. **Export and commit prompts** to GitHub

3. **Deploy only Main Dashboard** to cloud

This avoids the file sync complexity entirely.

---

## Updating Your Deployed Apps

### Update Prompt Generator

1. Make changes to code locally
2. Commit and push to GitHub:
   ```bash
   git add prompt_generator_app.py prompt_generator_pages/
   git commit -m "Update prompt generator"
   git push
   ```
3. Streamlit Cloud will **auto-redeploy** (within ~1 minute)

### Update Main Dashboard

1. Make changes to `streamlit_app.py`
2. Commit and push
3. Main dashboard auto-redeploys

Each app redeploys independently!

---

## Managing Multiple Deployments

### In Streamlit Cloud Dashboard

You'll see both apps listed:

```
My apps
├── ai-visibility-dashboard
│   └── streamlit_app.py
│   └── Status: Running ✓
│   └── URL: https://dashboard.streamlit.app
│
└── prompt-generator
    └── prompt_generator_app.py
    └── Status: Running ✓
    └── URL: https://prompt-generator.streamlit.app
```

You can:
- ⏸️ Pause/resume each app
- 🔄 Restart apps
- ⚙️ Edit settings
- 📊 View logs
- 🗑️ Delete apps

---

## Troubleshooting

### "App failed to load"

**Check the logs:**
1. Go to Streamlit Cloud dashboard
2. Click on your app
3. Click "Manage app" → "Logs"
4. Look for error messages

**Common issues:**
- Missing dependencies in `requirements.txt`
- Wrong main file path
- Missing data files

### "Module not found" errors

Make sure `requirements.txt` includes:
```txt
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.17.0
```

### Data files not found

Verify these files exist in your repo:
- `data/natasha_denona_personas.json`
- `data/natasha_denona_keywords.csv`

### App runs but pages don't load

Check that all page files exist:
- `prompt_generator_pages/__init__.py`
- `prompt_generator_pages/generate.py`
- `prompt_generator_pages/review.py`
- `prompt_generator_pages/export_page.py`
- `prompt_generator_pages/settings.py`

---

## Cost & Limits

Streamlit Community Cloud (Free Tier):
- ✅ Unlimited public apps
- ✅ 1 GB RAM per app
- ✅ Auto-sleep after inactivity
- ✅ GitHub integration

For private apps or more resources, upgrade to Streamlit Cloud Premium.

---

## Security Note

Since the prompt generator doesn't need API keys (currently template-based only), you don't need to configure secrets. If you enable AI generation later:

1. Go to app settings in Streamlit Cloud
2. Add secrets:
   ```toml
   OPENAI_API_KEY = "your-key"
   ANTHROPIC_API_KEY = "your-key"
   ```
3. Access in code: `st.secrets["OPENAI_API_KEY"]`

---

## Next Steps After Deployment

1. ✅ Test the deployed app at your URL
2. ✅ Generate a small batch (30 prompts) to verify functionality
3. ✅ Test the review/approve workflow
4. ✅ Export prompts and download CSV
5. ✅ Share the URL with team members

---

## Support

- Streamlit Cloud Docs: https://docs.streamlit.io/streamlit-community-cloud
- Streamlit Forum: https://discuss.streamlit.io
- GitHub Issues: Use your repository's issue tracker

---

**Ready to deploy?** Follow Step 2 above and you'll have your separate Prompt Generator app live in minutes! 🚀
