# AI Visibility Tracker - Quick Start Guide

## 🎯 Which App Should I Use?

This project has **TWO separate Streamlit apps**. Use the right one for your task:

---

## 🎨 App 1: Prompt Generator
**File:** `prompt_generator_app.py`
**Purpose:** CREATE and MANAGE test prompts
**Who:** Admin only (agency staff)

### How to Run:
```bash
streamlit run prompt_generator_app.py
```

### What It Does:
- Create and manage clients
- Generate test prompts with AI quality scoring
- Review and approve prompts before testing
- Export approved prompts to CSV
- Manage prompt library

### Workflow:
1. **Client Manager** → Set up new client or select existing
2. **Generate** → Create 100-300 prompts with quality scores
3. **Review & Approve** → Filter by quality, approve best prompts
4. **Export** → Download CSV of approved prompts
5. Use CSV for testing (see below)

---

## 📊 App 2: AI Visibility Dashboard
**File:** `streamlit_app_html.py`
**Purpose:** VIEW test results and reports
**Who:** Clients and admin

### How to Run:
```bash
streamlit run streamlit_app_html.py
```

### What It Does:
- Display HTML reports from completed tests
- Show visibility scores and metrics
- Client-facing dashboard with authentication
- Monthly progress tracking

### Workflow:
1. **Login** with credentials
2. **View Reports** - Interactive HTML reports
3. **Track Progress** - See visibility improvements

---

## 🔄 Complete End-to-End Workflow

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  1. CREATE      │      │  2. TEST        │      │  3. VIEW        │
│  PROMPTS        │  →   │  PROMPTS        │  →   │  RESULTS        │
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│                 │      │                 │      │                 │
│ Prompt          │      │ CLI Tool        │      │ AI Visibility   │
│ Generator       │      │ (main.py)       │      │ Dashboard       │
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
streamlit run prompt_generator_app.py
```

1. Click **"Client Manager"** in sidebar
2. Click **"Add New Client"**
3. Fill in:
   - Client name (e.g., "Say I Do")
   - Industry (e.g., "Wedding")
   - Keywords file (upload CSV or use template)
   - Personas file (upload JSON or use template)
4. Click **"Save Client"**

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
streamlit run streamlit_app_html.py
```

1. Login with client credentials
2. View the generated HTML report
3. See visibility scores for each AI platform
4. Share dashboard URL with client

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

### Problem: "I don't see quality scores"
**Solution:** Make sure you're running `prompt_generator_app.py`, NOT `streamlit_app_html.py`

### Problem: "My client disappeared"
**Solution:** Check `data/clients.json` - clients are now persisted. If missing, re-create via Client Manager.

### Problem: "Prompts were lost after I closed the app"
**Solution:** Fixed as of Feb 10! Prompts now save to `data/prompt_generation/drafts/` automatically.

### Problem: "Can't see quality columns in Review page"
**Solution:**
1. Stop the Streamlit app (Ctrl+C)
2. Restart: `streamlit run prompt_generator_app.py`
3. Regenerate prompts (old prompts don't have quality scores)

### Problem: "How do I get prompts into the main dashboard?"
**Solution:** Currently manual - export CSV from Prompt Generator, then run tests via CLI. Results auto-appear in dashboard.

---

## 📂 File Structure

```
ai-visibility-tracker/
├── prompt_generator_app.py          ← RUN THIS to create prompts
├── streamlit_app_html.py            ← RUN THIS to view results
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
├── prompt_generator_pages/          ← Pages for prompt generator app
│   ├── generate.py
│   ├── review.py
│   ├── export_page.py
│   └── settings.py (Client Manager)
│
└── docs/
    ├── QUALITY_SCORING.md           ← Quality system details
    └── PROMPT_GENERATOR_REVIEW.md   ← Full technical review
```

---

## 🚀 Quick Command Reference

```bash
# Start prompt generator (create prompts)
streamlit run prompt_generator_app.py

# Start dashboard (view results)
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
