# AI Visibility Tracker - Quick Start Guide

## 🎯 One Integrated App

This project now has **ONE integrated Streamlit app** with role-based access:

---

## 📊 Integrated App
**File:** `streamlit_app_html.py`
**Purpose:** Dashboard + Prompt Generator (role-based)
**Who:** All users (features based on role)

### How to Run:
```bash
streamlit run streamlit_app_html.py
```

### What Admin Users See:
- **Dashboard** → View reports for any client
- **Prompt Generator** → Full access to:
  - Client Manager
  - Generate (with quality scoring)
  - Review & Approve
  - Export
  - Prompt Library

### What Client Users See:
- **Dashboard** → View their own reports only
- **No access** to prompt generation features

### Workflow:
1. **Login** with credentials
2. **Navigate** using sidebar
3. **Admin:** Access all features
4. **Clients:** View their reports only

---

## 🔄 Complete End-to-End Workflow

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  1. CREATE      │      │  2. TEST        │      │  3. VIEW        │
│  PROMPTS        │  →   │  PROMPTS        │  →   │  RESULTS        │
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│                 │      │                 │      │                 │
│ Integrated App  │      │ CLI Tool        │      │ Integrated App  │
│ (Admin Only)    │      │ (main.py)       │      │ (All Users)     │
│                 │      │                 │      │                 │
│ Output:         │      │ Input:          │      │ Input:          │
│ prompts.csv     │  →   │ prompts.csv     │  →   │ results HTML    │
│                 │      │                 │      │                 │
│ 100-300 prompts │      │ Test against:   │      │ View metrics    │
│ Quality scored  │      │ - ChatGPT       │      │ Share w/clients │
│ Approved only   │      │ - Claude        │      │                 │
│                 │      │ - Perplexity    │      │                 │
│                 │      │ - Gemini        │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

---

## 📝 Step-by-Step: Create Your First Prompts

### Step 1: Set Up Client

```bash
streamlit run streamlit_app_html.py
```

1. **Login as admin**
2. Click **"Client Manager"** in sidebar
3. Click **"Add New Client"**
4. Fill in:
   - Client name (e.g., "Say I Do")
   - Industry (e.g., "Wedding")
   - Keywords file (upload CSV or use template)
   - Personas file (upload JSON or use template)
5. Click **"Save Client"**

### Step 2: Generate Prompts

1. Click **"Generate"** in sidebar
2. Verify client is selected (top banner)
3. Configure settings:
   - **Batch Name:** "Initial Baseline" (for first batch)
   - **Total Prompts:** 293 (or 100-300)
   - **Competitor Mentions:** 30%
   - **Deduplication:** High Similarity (90%)
4. Click **"🚀 Generate Prompts"**

**You'll see:**
```
✅ Generation complete!

Quality Scores:
├─ Average Quality: 85.2/100
├─ Excellent (90-100): 127 prompts
├─ Good (75-89): 120 prompts
├─ Fair (60-74): 25 prompts
└─ Poor (<60): 21 prompts

Quality Dimensions (Average):
├─ Naturalness: 92.3
├─ Clarity: 84.1
├─ Length: 88.5
├─ Relevance: 81.2
└─ Diversity: 79.8
```

### Step 3: Review & Approve

1. Click **"Review & Approve"** in sidebar
2. Use filters to find high-quality prompts:
   - **Quality Score Range:** 75-100 (Good to Excellent only)
   - **Quality Level:** Check "Excellent" and "Good"
3. Review the filtered list
4. Click **"✓ Approve All Visible"**
5. Review any "Fair" or "Poor" prompts manually

### Step 4: Export for Testing

1. Click **"Export"** in sidebar
2. Select **"Export Approved Prompts"**
3. Choose format: **CSV** (for testing)
4. Click **"Download CSV"**
5. Save as: `say_i_do_prompts.csv`

### Step 5: Run Tests (CLI)

```bash
# Navigate to project directory
cd /path/to/ai-visibility-tracker

# Run tests with your prompts
python main.py --client "Say I Do" --prompts say_i_do_prompts.csv

# This will:
# 1. Load your prompts
# 2. Test against ChatGPT, Claude, Perplexity, Gemini
# 3. Generate HTML report
# 4. Save results to data/results/
```

### Step 6: View Results

```bash
# App is already running
```

1. Navigate to **"Dashboard"** in sidebar
2. Select client to view their report
3. See visibility scores for each AI platform
4. Share dashboard URL with client (they'll only see their own report)

---

## 🎓 Best Practices

### Prompt Generation:
- **Initial batch:** Generate 200-300 prompts for baseline
- **Quality target:** 80%+ should be Excellent or Good
- **Approve only high-quality:** Filter out Fair/Poor prompts
- **Diversity:** Use various personas and intent types
- **Save batches:** Name batches clearly (e.g., "Q1 2026 Baseline")

### Testing:
- **Test monthly:** Run same prompts each month to track improvement
- **Don't regenerate:** Reuse same prompts for consistent tracking
- **Archive results:** Keep all monthly reports for comparison

### Client Management:
- **One client per instance:** Don't mix prompts from different clients
- **Clear naming:** Use descriptive batch names
- **Regular exports:** Export approved prompts after each review session

---

## 🆘 Troubleshooting

### Problem: "I don't see the Prompt Generator in the sidebar"
**Solution:** Make sure you're logged in as admin. Client users don't have access to prompt generation.

### Problem: "I don't see quality scores"
**Solution:**
1. Make sure you're in the "Generate" page (admin only)
2. Restart the app if you recently updated the code: `Ctrl+C` then `streamlit run streamlit_app_html.py`
3. Regenerate prompts (old prompts don't have quality scores)

### Problem: "My client disappeared"
**Solution:** Check `data/clients.json` - clients are now persisted. If missing, re-create via Client Manager.

### Problem: "Prompts were lost after I closed the app"
**Solution:** Fixed as of Feb 10! Prompts now save to `data/prompt_generation/drafts/` automatically.

### Problem: "How do I get prompts into the dashboard?"
**Solution:** Export CSV from Prompt Generator → Export, then run tests via CLI. Results auto-appear in dashboard.

---

## 📂 File Structure

```
ai-visibility-tracker/
├── streamlit_app_html.py            ← MAIN APP - Dashboard + Prompt Generator
├── main.py                          ← CLI tool for running tests
│
├── data/
│   ├── clients.json                 ← Client registry
│   ├── prompt_generation/
│   │   ├── drafts/                  ← Auto-saved prompts (persistent!)
│   │   ├── approved/                ← Approved prompts
│   │   └── exported/                ← Archived exports
│   └── results/                     ← Test results (HTML reports)
│
├── src/
│   ├── prompt_generator/
│   │   ├── generator.py             ← Core generation logic
│   │   ├── quality_scorer.py        ← Quality scoring system
│   │   └── approval_manager.py
│   └── authentication.py
│
├── prompt_generator_pages/          ← Admin pages (integrated into main app)
│   ├── generate.py
│   ├── review.py
│   ├── export_page.py
│   ├── library.py
│   └── settings.py (Client Manager)
│
└── docs/
    ├── QUALITY_SCORING.md           ← Quality system details
    └── PROMPT_GENERATOR_REVIEW.md   ← Full technical review
```

---

## 🚀 Quick Command Reference

```bash
# Start integrated app (dashboard + prompt generator)
streamlit run streamlit_app_html.py

# Run tests via CLI
python main.py --client "Client Name" --prompts prompts.csv

# Run quality scorer tests
python3 test_quality_scorer.py

# Check git status
git status

# Deploy changes to Streamlit Cloud
git add .
git commit -m "Your message"
git push origin main
```

---

## 📞 Need Help?

1. Check `docs/QUALITY_SCORING.md` for quality system details
2. Check `docs/PROMPT_GENERATOR_REVIEW.md` for technical review
3. Review this guide
4. Check error messages in terminal (not just Streamlit UI)

---

## 🎉 You're Ready!

You now know:
- ✅ Which app to use for what
- ✅ How to create and manage prompts
- ✅ How to use quality scoring
- ✅ How to export and test prompts
- ✅ How to view results in the dashboard

**Next:** Generate your first batch of prompts with quality scoring!
