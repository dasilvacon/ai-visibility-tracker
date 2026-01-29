# 🚀 Quick Start Guide

## ✅ The Prompt Generator App is Ready!

All files have been created and validated. Here's how to launch it:

---

## Step 1: Open Terminal

Open your terminal and navigate to the project directory:

```bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker
```

---

## Step 2: Launch the Prompt Generator

Run this command:

```bash
streamlit run prompt_generator_app.py --server.port 8502
```

You should see output like:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8502
  Network URL: http://192.168.x.x:8502
```

---

## Step 3: Open in Browser

Click the URL or open your browser to:

**http://localhost:8502**

---

## What You'll See

### 1. Generate Page (Default)
- **Prominent slider**: Choose 10-1000 prompts
- Configure competitor ratio (0-50%)
- Select deduplication mode
- Click "🚀 Generate Prompts"

### 2. Review & Approve Page
- Filter by persona, category, intent, score
- Bulk approve/reject with filters
- Edit individual prompts
- Track approval stats

### 3. Export Page
- View breakdown by persona/category/intent
- Export to CSV (append or replace)
- Download JSON with full metadata
- Access previous exports

### 4. Settings Page
- Configure data sources
- Set generation defaults
- Adjust pagination

---

## Running Both Apps

### Option 1: Two Terminal Windows

**Terminal 1 - Main Dashboard:**
```bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker
streamlit run streamlit_app.py --server.port 8501
```
Open: http://localhost:8501

**Terminal 2 - Prompt Generator:**
```bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker
streamlit run prompt_generator_app.py --server.port 8502
```
Open: http://localhost:8502

### Option 2: Use Launch Scripts

```bash
# Launch main dashboard
./launch_main_dashboard.sh

# In another terminal, launch prompt generator
./launch_prompt_generator.sh
```

---

## Quick Test Workflow

Once the app opens at http://localhost:8502:

1. **Generate Tab**
   - Set slider to **30 prompts**
   - Keep defaults (30% competitors, High Similarity deduplication)
   - Click **"🚀 Generate Prompts"**
   - Wait ~30 seconds
   - See stats and sample prompts

2. **Review & Approve Tab**
   - See all 30 prompts in table
   - Filter by "Luxury Beauty Enthusiast"
   - Click **"✓ Approve All Visible"**
   - Filter by "Professional Makeup Artist"
   - Click **"✓ Approve All Visible"**

3. **Export Tab**
   - See breakdown charts
   - Choose "Append to existing generated_prompts.csv"
   - Click **"📥 Export CSV"**
   - Success! Prompts are now in the main database

---

## Troubleshooting

### "streamlit: command not found"
Make sure Streamlit is installed:
```bash
pip install streamlit
```

### "Address already in use"
Another app is using that port. Either:
- Stop the other app: `pkill -f streamlit`
- Use a different port: `--server.port 8503`

### "ModuleNotFoundError"
Make sure you're in the project directory:
```bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker
```

---

## Files Created

✅ All these files are ready:

```
prompt_generator_app.py                    # Main entry point
prompt_generator_pages/
  ├── generate.py                         # Generation UI
  ├── review.py                           # Approval workflow
  ├── export_page.py                      # Export options
  └── settings.py                         # Configuration
src/prompt_generator/
  ├── deduplicator.py                     # Deduplication logic
  └── approval_manager.py                 # Approval management
launch_prompt_generator.sh                # Launch script
PROMPT_GENERATOR_GUIDE.md                 # Full documentation
```

---

## Ready to Go! 🎉

Just run:
```bash
streamlit run prompt_generator_app.py --server.port 8502
```

Then open **http://localhost:8502** in your browser!
