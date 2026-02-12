# 🚀 START HERE - AI Visibility Tracker

## Quick Start

There is now **ONE integrated app** for everything:

```bash
streamlit run app.py
```

That's it! The app automatically shows different features based on who logs in.

---

## What You'll See

### 👑 When YOU log in (Admin):
```
📊 Dashboard
   └─ View Reports (see client results)

✨ Prompt Generator (Admin Only)
   ├─ Client Manager
   ├─ Generate
   ├─ Review & Approve
   ├─ Export
   └─ Prompt Library
```

**You get everything** - both the dashboard AND the prompt generator tools.

### 👤 When clients log in:
```
📊 Dashboard
   └─ View Reports (their brand only)
```

**Clients only see** their own visibility reports. No access to prompt generation.

---

## Complete Workflow

### 1. Create Prompts (Admin Only)

```bash
# Start the app
streamlit run app.py

# Login as admin
# Navigate to: Prompt Generator → Client Manager
# Create or select client

# Navigate to: Prompt Generator → Generate
# Generate 100-300 prompts with quality scoring
# Review quality metrics

# Navigate to: Prompt Generator → Review & Approve
# Filter by quality (75-100 range)
# Approve high-quality prompts

# Navigate to: Prompt Generator → Export
# Download CSV of approved prompts
```

### 2. Run Tests (CLI)

```bash
# Use the exported CSV
python main.py --client "Client Name" --prompts approved_prompts.csv

# Tests run against ChatGPT, Claude, Perplexity, Gemini
# Results saved to data/results/
```

### 3. View Results (Dashboard)

```bash
# Already running app.py
# Navigate to: Dashboard → View Reports
# Select client
# See visibility scores and metrics
```

---

## Features by Role

| Feature | Admin | Client |
|---------|-------|--------|
| View all client dashboards | ✅ | ❌ |
| View own dashboard | ✅ | ✅ |
| Create/manage clients | ✅ | ❌ |
| Generate prompts | ✅ | ❌ |
| Quality scoring | ✅ | ❌ |
| Review & approve | ✅ | ❌ |
| Export prompts | ✅ | ❌ |
| Prompt library | ✅ | ❌ |

---

## Old Apps (Deprecated)

These are no longer needed:
- ~~`streamlit_app_html.py`~~ → Use `app.py` instead
- ~~`prompt_generator_app.py`~~ → Use `app.py` instead

Everything is now integrated into `app.py`.

---

## Next Steps

1. **Start the app:** `streamlit run app.py`
2. **Login as admin**
3. **Go to Prompt Generator → Generate**
4. **Generate 50-100 test prompts**
5. **See quality scores in action!** 🎉

---

## Need Help?

- **Full guide:** See `HOW_TO_USE.md`
- **Quality scoring:** See `docs/QUALITY_SCORING.md`
- **Technical review:** See `docs/PROMPT_GENERATOR_REVIEW.md`

---

## Quick Commands

```bash
# Start integrated app
streamlit run app.py

# Run tests via CLI
python main.py --client "Client Name" --prompts prompts.csv

# Test quality scorer
python3 test_quality_scorer.py

# Deploy to Streamlit Cloud
git add .
git commit -m "Integrated app with role-based access"
git push origin main
```

---

**You're all set! Just run `streamlit run app.py` and everything works together.**
