# 🚀 Deploy Prompt Generator - Quick Start

**Status: ✅ ALL CHECKS PASSED - READY TO DEPLOY**

---

## What You're Deploying

A **separate Streamlit app** for generating and approving prompts before they go into your main dashboard.

**Current Setup:**
- ✅ Main Dashboard: `streamlit_app.py` (already deployed?)
- ✅ Prompt Generator: `prompt_generator_app.py` (ready to deploy)

---

## 5-Minute Deployment Steps

### Step 1: Commit & Push (2 min)

Open your terminal and run:

```bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker

# Check what needs to be committed
git status

# Add all prompt generator files
git add prompt_generator_app.py
git add prompt_generator_pages/
git add src/prompt_generator/
git add .streamlit/config.toml
git add DEPLOYMENT_GUIDE.md
git add DEPLOYMENT_CHECKLIST.md

# Commit
git commit -m "Add Prompt Generator & Approval Tool for deployment"

# Push
git push origin main
```

### Step 2: Deploy on Streamlit Cloud (3 min)

1. **Go to:** https://share.streamlit.io

2. **Click:** "New app" button (top right, like in your screenshot)

3. **Fill in the form:**
   ```
   Repository: tiffanydasilva/ai-visibility-tracker
   Branch: main
   Main file path: prompt_generator_app.py  ← IMPORTANT!
   App URL: prompt-generator  (or choose your own)
   ```

4. **Click:** "Deploy!" button

5. **Wait:** 1-3 minutes for deployment

6. **Done!** You'll get a URL like: `https://prompt-generator.streamlit.app`

---

## What Happens Next

### You'll Have TWO Separate Apps:

| App | File | Purpose | URL |
|-----|------|---------|-----|
| **Main Dashboard** | `streamlit_app.py` | View reports, track visibility | Your current URL |
| **Prompt Generator** | `prompt_generator_app.py` | Generate & approve prompts | New URL you just created |

Both apps:
- ✅ Share the same GitHub repo
- ✅ Run independently on different URLs
- ✅ Can be updated separately
- ✅ Can run at the same time

---

## After Deployment - Quick Test

Once your app is live:

1. **Open the URL** (e.g., `https://prompt-generator.streamlit.app`)

2. **Generate Page** (default)
   - Move slider to **30 prompts**
   - Click "🚀 Generate Prompts"
   - Wait ~30 seconds
   - See stats and sample prompts

3. **Review & Approve Page**
   - See all 30 prompts in table
   - Click **"✓ Approve All Visible"**
   - Stats show approved count

4. **Export Page**
   - See breakdown charts
   - Click **"📥 Export CSV"**
   - Download the CSV file

✅ If all these work, your deployment is successful!

---

## File Synchronization (Important!)

Since both apps are on Streamlit Cloud, they have **ephemeral storage**:

### Recommended Workflow:

1. **Generate prompts** in Prompt Generator (cloud)
2. **Approve prompts** using filters
3. **Export & Download CSV**
4. **Commit to GitHub:**
   ```bash
   git add data/generated_prompts.csv
   git commit -m "Add approved prompts"
   git push
   ```
5. **Main Dashboard** will pick up changes on next load

### Alternative (Simpler):

- Run Prompt Generator **locally only**: `streamlit run prompt_generator_app.py --server.port 8502`
- Export and commit prompts
- Deploy **only Main Dashboard** to cloud

---

## Troubleshooting

### "ModuleNotFoundError" during deployment

**Fix:** Make sure `requirements.txt` includes:
```txt
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.17.0
```

Commit and push if you added anything.

### "File not found: data/..."

**Fix:** Make sure data files are committed:
```bash
git add data/natasha_denona_personas.json
git add data/natasha_denona_keywords.csv
git push
```

### App loads but pages are blank

**Fix:** Check that all page files are committed:
```bash
git add prompt_generator_pages/*.py
git push
```

### Need to see logs

1. Go to https://share.streamlit.io
2. Click on your app
3. Click "Manage app" → "Logs"

---

## Your Deployment URLs

Once deployed, save your URLs here for reference:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Main Dashboard URL:                                        │
│  https://________________________________.streamlit.app     │
│                                                             │
│  Prompt Generator URL:                                      │
│  https://________________________________.streamlit.app     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Need More Help?

📖 **Detailed guides:**
- `DEPLOYMENT_GUIDE.md` - Complete deployment documentation
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist
- `PROMPT_GENERATOR_GUIDE.md` - How to use the tool

🆘 **Support:**
- Streamlit Docs: https://docs.streamlit.io/streamlit-community-cloud
- Streamlit Forum: https://discuss.streamlit.io

---

## Ready? Let's Deploy! 🚀

Just follow **Step 1** (commit & push) and **Step 2** (deploy on Streamlit Cloud) above.

You'll have your separate Prompt Generator app live in about 5 minutes!
