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

### Phase 1: Generate Prompts (Port 8502)
1. Open **Prompt Generator** at http://localhost:8502
2. Go to **Generate** page
3. Choose how many prompts (e.g., 100)
4. Click "Generate Prompts"
5. Go to **Review & Approve** page
6. Filter and approve prompts
7. Go to **Export** page
8. Export to `data/generated_prompts.csv` (append mode)

### Phase 2: Track & Analyze (Port 8501)
1. Open **Main Dashboard** at http://localhost:8501
2. Select brand
3. Run tracking tests on new prompts
4. View results and generate reports
5. Export client reports

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
├── prompt_generator_pages/           # Prompt generator UI pages
├── data/
│   ├── generated_prompts.csv         # Shared by both apps
│   └── prompt_generation/            # Prompt generator staging area
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

## Next Steps

1. **Start with Prompt Generator** to create your prompt library
2. **Export approved prompts** to the main database
3. **Switch to Main Dashboard** to run tracking tests
4. **Generate reports** for clients

Enjoy using both apps! 🚀
