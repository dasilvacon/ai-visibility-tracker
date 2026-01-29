# 📋 Deployment Checklist - Prompt Generator

Use this checklist to deploy the Prompt Generator as a separate app on Streamlit Community Cloud.

---

## ☑️ Pre-Deployment Checklist

### 1. Verify Files Exist

```bash
# Run this to check all required files
ls -lh prompt_generator_app.py
ls -lh prompt_generator_pages/*.py
ls -lh src/prompt_generator/*.py
ls -lh data/natasha_denona_personas.json
ls -lh data/natasha_denona_keywords.csv
ls -lh requirements.txt
ls -lh .streamlit/config.toml
```

Expected output:
- ✅ `prompt_generator_app.py` exists
- ✅ 5 files in `prompt_generator_pages/`
- ✅ 3+ files in `src/prompt_generator/`
- ✅ Personas and keywords files exist
- ✅ `requirements.txt` exists
- ✅ `.streamlit/config.toml` exists

### 2. Test Locally First

```bash
streamlit run prompt_generator_app.py --server.port 8502
```

Verify:
- [ ] App opens at http://localhost:8502
- [ ] Generate page loads
- [ ] Can generate prompts (try 10 prompts)
- [ ] Review & Approve page shows prompts
- [ ] Can approve/reject prompts
- [ ] Export page shows approved prompts
- [ ] Settings page loads

### 3. Commit Everything to Git

```bash
git status  # Check what needs to be committed

git add prompt_generator_app.py
git add prompt_generator_pages/
git add src/prompt_generator/
git add .streamlit/
git add requirements.txt
git add DEPLOYMENT_GUIDE.md
git add PROMPT_GENERATOR_GUIDE.md

git commit -m "Add Prompt Generator & Approval Tool"
git push origin main
```

Verify:
- [ ] All prompt generator files committed
- [ ] Pushed to GitHub successfully
- [ ] No merge conflicts

---

## ☑️ Deployment Steps

### Step 1: Open Streamlit Cloud
- [ ] Go to https://share.streamlit.io
- [ ] Sign in with GitHub account
- [ ] See your dashboard

### Step 2: Create New App
- [ ] Click "New app" button
- [ ] See deployment form

### Step 3: Fill Deployment Form

**Repository:**
- [ ] Select your repo: `tiffanydasilva/ai-visibility-tracker` (or your path)

**Branch:**
- [ ] Select: `main`

**Main file path:**
- [ ] Enter: `prompt_generator_app.py` ⭐ (NOT streamlit_app.py)

**App URL:**
- [ ] Choose custom URL: `_________________` (e.g., "prompt-generator")

### Step 4: Deploy
- [ ] Click "Deploy!" button
- [ ] Wait for deployment (1-3 minutes)
- [ ] See "Your app is live!" message

---

## ☑️ Post-Deployment Verification

### Access Your App
- [ ] Open the provided URL: `https://[your-slug].streamlit.app`
- [ ] App loads without errors

### Test Core Features

**Generate Page:**
- [ ] Slider for prompt count visible (10-1000)
- [ ] Can see persona/keyword file status
- [ ] Settings show correct values
- [ ] Generate button works (test with 20 prompts)
- [ ] Stats display after generation
- [ ] Sample prompts show

**Review & Approve Page:**
- [ ] Generated prompts appear in table
- [ ] Filters work (persona, category, intent)
- [ ] Can approve individual prompts
- [ ] Bulk approve works
- [ ] Stats update correctly

**Export Page:**
- [ ] Approved prompts count correct
- [ ] Breakdown charts display
- [ ] Can download CSV
- [ ] Can download JSON

**Settings Page:**
- [ ] Personas file path correct
- [ ] Keywords file path correct
- [ ] Can view file previews

### Branding Check
- [ ] Deep plum colors visible
- [ ] Off-white background
- [ ] DaSilva branding in sidebar footer
- [ ] Buttons styled correctly

---

## ☑️ Final Steps

### Share Your App
- [ ] Copy app URL
- [ ] Share with team members
- [ ] Add URL to documentation

### Set Up Both Apps

You now have TWO apps:

**Main Dashboard:**
- File: `streamlit_app.py`
- URL: `https://[dashboard-url].streamlit.app`
- Purpose: View reports, track visibility

**Prompt Generator:**
- File: `prompt_generator_app.py`
- URL: `https://[generator-url].streamlit.app`
- Purpose: Generate & approve prompts

### Document URLs

Save your URLs here:

```
Main Dashboard URL: ________________________________

Prompt Generator URL: ________________________________
```

---

## ☑️ Troubleshooting (If Needed)

### If app fails to deploy:

1. **Check logs:**
   - [ ] Click "Manage app" in Streamlit Cloud
   - [ ] View logs for errors

2. **Common fixes:**
   - [ ] Verify `prompt_generator_app.py` path is correct
   - [ ] Check `requirements.txt` has all dependencies
   - [ ] Ensure data files are committed to repo
   - [ ] Try restarting the app

3. **Test locally again:**
   - [ ] Pull latest from GitHub
   - [ ] Run locally: `streamlit run prompt_generator_app.py --server.port 8502`
   - [ ] Fix any errors
   - [ ] Commit and push fixes

---

## ✅ Success Criteria

Your deployment is successful when:

- ✅ App loads at public URL
- ✅ Can generate 50 prompts without errors
- ✅ Can approve/reject prompts using filters
- ✅ Can export approved prompts to CSV
- ✅ Settings page shows correct file paths
- ✅ Deduplication removes duplicates during generation
- ✅ Branding looks correct (DaSilva colors)

---

## 🎉 You're Done!

Congratulations! You now have a deployed Prompt Generator tool.

**Next steps:**
1. Generate your first batch of prompts in production
2. Share the URL with your team
3. Use the exported prompts in your main dashboard

**Need help?** See `DEPLOYMENT_GUIDE.md` for detailed troubleshooting.
