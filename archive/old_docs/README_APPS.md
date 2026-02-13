# AI Visibility Tracker - Running the Apps

## Two Separate Streamlit Apps

This project now has **two separate Streamlit applications** that run independently:

### 1. 🎯 Main AI Visibility Dashboard (Port 8501)
The main dashboard for viewing reports and tracking AI visibility.

**Launch:**
```bash
./launch_main_dashboard.sh
```
Or:
```bash
streamlit run streamlit_app.py --server.port 8501
```

**Access:** http://localhost:8501

**Use for:**
- Viewing generated reports
- Analyzing AI visibility results
- Tracking prompt performance
- Exporting final client reports

---

### 2. ✨ Prompt Generator & Approval Tool (Port 8502)
Standalone tool for generating, reviewing, and approving prompts **before** adding them to the dashboard.

**Launch:**
```bash
./launch_prompt_generator.sh
```
Or:
```bash
streamlit run prompt_generator_app.py --server.port 8502
```

**Access:** http://localhost:8502

**Use for:**
- Generating new prompts (10-1000 at a time)
- Reviewing prompts with filters (by persona, category, intent)
- Bulk approving/rejecting prompts
- Exporting approved prompts to CSV

---

## Running Both Apps Simultaneously

You can run **both apps at the same time** since they use different ports:

### Option 1: Two Terminal Windows
1. **Terminal 1:**
   ```bash
   ./launch_main_dashboard.sh
   ```
   Opens on http://localhost:8501

2. **Terminal 2:**
   ```bash
   ./launch_prompt_generator.sh
   ```
   Opens on http://localhost:8502

### Option 2: Background Processes
```bash
# Run main dashboard in background
streamlit run streamlit_app.py --server.port 8501 &

# Run prompt generator in background
streamlit run prompt_generator_app.py --server.port 8502 &
```

To stop background processes:
```bash
# Find and kill Streamlit processes
pkill -f streamlit
```

---

## Recommended Workflow

### 🎯 Complete Workflow: From Prompts to Reports

#### Phase 1: Set Up Client (Port 8502 - Prompt Generator)
1. Open **Prompt Generator** at http://localhost:8502
2. Go to **Client Manager** page
3. Select existing client OR add new client (upload personas JSON + keywords CSV)
4. Active client shows at top with stats

#### Phase 2: Generate Prompts (Port 8502 - Prompt Generator)
1. Go to **Generate** page
2. Choose how many prompts (10-1000)
3. Adjust settings (competitor ratio, deduplication mode)
4. Click "Generate Prompts"
5. Wait for generation to complete

#### Phase 3: Review & Approve (Port 8502 - Prompt Generator)
1. Go to **Review & Approve** page
2. Filter by persona, category, or intent type
3. Review individual prompts
4. Bulk approve/reject prompts
5. Adjust expected visibility scores if needed

#### Phase 4: Export Prompts (Port 8502 - Prompt Generator)
1. Go to **Export** page
2. Choose export mode:
   - **Append mode** (recommended) - adds to existing prompts
   - **Replace mode** - starts fresh (use carefully!)
   - **Custom location** - download for manual import
3. Export creates timestamped backup in `data/prompt_generation/approved/`
4. Prompts are ready for AI Visibility Tracker

#### Phase 5: Run AI Visibility Tests (Port 8501 - Main Dashboard)
1. Open **Main Dashboard** at http://localhost:8501
2. Select brand/client
3. Run tracking tests on new prompts
4. AI tools will test each prompt
5. View results in real-time

#### Phase 6: Generate Reports (Port 8501 - Main Dashboard)
1. View **Overview** page for summary metrics
2. Check **Sources & Citations** for where brand appeared
3. Review **Action Plan** for recommendations
4. Analyze **Competitor Analysis** for market position
5. Export final client reports (HTML, PDF)

---

## Quick Reference

| App | Port | URL | Purpose |
|-----|------|-----|---------|
| Main Dashboard | 8501 | http://localhost:8501 | View reports, track results |
| Prompt Generator | 8502 | http://localhost:8502 | Generate & approve prompts |

---

## File Organization

```
ai-visibility-tracker/
├── streamlit_app.py                  # Main dashboard app
├── prompt_generator_app.py           # Prompt generator app
├── launch_main_dashboard.sh          # Launch script for main app
├── launch_prompt_generator.sh        # Launch script for prompt generator
├── dashboard_pages/                  # Main dashboard UI pages (overview, sources, etc.)
├── prompt_generator_pages/           # Prompt generator UI pages (generate, review, export)
├── data/
│   ├── generated_prompts.csv         # Shared by both apps
│   ├── prompt_generation/            # Prompt generator staging area
│   └── [client]_personas.json        # Client persona files
│   └── [client]_keywords.csv         # Client keyword files
└── src/                              # Shared modules
```

---

## Troubleshooting

### Port Already in Use
If you see "Address already in use" error:

```bash
# Check what's running on port 8501
lsof -i :8501

# Check what's running on port 8502
lsof -i :8502

# Kill specific process
kill -9 <PID>

# Or kill all Streamlit processes
pkill -f streamlit
```

### Can't Access Apps
- Check that your firewall allows localhost connections
- Verify the apps are running: `ps aux | grep streamlit`
- Try restarting: Stop all processes and relaunch

### Import Errors
Make sure you're in the project root directory:
```bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker
```

---

## 📅 Monthly Reports: How to Track Your Work Effectiveness

### The Right Approach for Tracking Improvement

**To measure if your content/SEO work is improving AI visibility, you need to test the SAME prompts each month.**

### Standard Monthly Workflow (Recommended)

#### Initial Setup - Month 1
1. Open **Prompt Generator**
2. Generate a strong set of 100-200 prompts
3. Review and approve them carefully
4. Export to `data/generated_prompts.csv`
5. Run tests in Main Dashboard
6. **This is your baseline** - save this report!

#### Monthly Tracking - Month 2, 3, 4...
1. **Skip the Prompt Generator** (you already have your prompts!)
2. Open **Main Dashboard** directly
3. Run tests using the SAME prompts from Month 1
4. Compare results to previous months
5. Track visibility score improvements

**This shows:** "Is our work moving the needle on these key searches?"

### When to Generate Fresh Prompts

**Generate new prompts only when:**

#### Scenario 1: New Product/Service Launch
**Trigger:** Client launches new product line

**Action:**
- Generate 25-50 new prompts for new offerings
- Export with **"Append"** mode
- Adds to existing prompt library
- Track both old and new prompts going forward

#### Scenario 2: Campaign-Specific Testing
**Trigger:** Running specific marketing campaign

**Action:**
- Generate campaign-specific prompts temporarily
- Export to custom location (don't append)
- Test during campaign period
- Compare campaign prompts vs. core prompts

#### Scenario 3: Quarterly Expansion
**Trigger:** Want to test new angles/personas

**Action:**
- Generate 20-30 new prompts exploring different angles
- Export with **"Append"** mode
- Expand your tracking set gradually
- Keep core prompts for consistency

#### Scenario 4: Annual Refresh
**Trigger:** Client business has significantly evolved

**Action:**
- Review all existing prompts
- Retire outdated ones
- Generate fresh set aligned with new strategy
- This resets your baseline

### File Management for Monthly Reports

**The system keeps everything organized:**

```
data/
├── generated_prompts.csv                    # All prompts (evergreen + new)
├── prompt_generation/
│   └── approved/
│       ├── approved_20260130_143022.csv    # Jan export
│       ├── approved_20260228_102045.csv    # Feb export
│       ├── approved_20260330_155512.csv    # Mar export
│       └── ...                              # Each export timestamped
```

**Each export is timestamped, so you can:**
- See which prompts were used in which report
- Roll back if needed
- Track prompt evolution over time
- Audit what was sent to clients

### Best Practice Workflow

**Month 1 (January):** Generate 100 prompts → Approve → Export → Run tests → Baseline report
**Month 2 (February):** Reuse same 100 prompts → Run tests → Compare to January → Show improvement
**Month 3 (March):** Reuse same 100 prompts → Run tests → Compare to Jan/Feb → Track progress
**Month 4 (April):** Reuse same 100 prompts → Run tests → Quarterly comparison report

**OR with expansion:**

**Month 1 (January):** Generate 100 prompts → Baseline
**Month 2 (February):** Reuse 100 prompts + add 25 new for new product launch (125 total going forward)
**Month 3 (March):** Reuse all 125 prompts → Track both original and new
**Month 4 (April):** Reuse all 125 prompts → Show 3-month trend

This gives you:
- ✅ Consistent measurement of your work's impact
- ✅ Clear month-over-month improvement tracking
- ✅ Ability to expand prompt library strategically
- ✅ Full audit trail of what was tested when

---

## 💭 The Right Mindset: Prompts as Your Testing Framework

### Think of Prompts Like Scientific Experiments

**Your prompts are your control variables.** To measure if your work is effective, you need to test the SAME prompts repeatedly.

**Analogy:**
- ❌ **Wrong:** Testing different thermometers each time to see if the room is getting warmer
- ✅ **Right:** Using the same thermometer each time to accurately measure temperature change

**Your Workflow:**
- ❌ **Wrong:** Generate new prompts every month → Can't tell if improvement is due to your work or just different prompts
- ✅ **Right:** Test same prompts every month → Clear signal if your content/SEO is working

### When Each App Gets Used

**Prompt Generator (Used Rarely):**
- Week 1: Set up new client
- Week 1: Generate initial prompt library
- Week 1: Review and export
- Month 3: Add 25 prompts for new product
- Month 6: Add 30 prompts for campaign
- Month 12: Possible refresh if business changed significantly

**Main Dashboard (Used Monthly):**
- Week 2: Run initial tests (baseline)
- Month 2: Retest same prompts
- Month 3: Retest same prompts
- Month 4: Retest same prompts
- Month 5: Retest same prompts
- *(Every month, same prompts, measuring improvement)*

### The Value Proposition

**What you're selling to clients:**
"We will track your AI visibility on 100 key search queries each month and show you month-over-month improvement."

**NOT:**
"We will test 100 random queries each month and show you some results."

**Clients want to see:**
- "In January, ChatGPT mentioned you 15% of the time"
- "In February, ChatGPT mentioned you 22% of the time"
- "In March, ChatGPT mentioned you 31% of the time"
- **"Your visibility is improving because of our work!"**

This ONLY works if you're testing the same prompts.

---

## Next Steps

1. **Set up your first client** in Client Manager
2. **Generate your core prompt library** (100-200 prompts)
3. **Export once** to the main database
4. **Run tests monthly** in Main Dashboard with those same prompts
5. **Show clients improvement** with month-over-month comparisons
6. **Only generate new prompts** when business needs change

Enjoy tracking real improvement! 🚀
