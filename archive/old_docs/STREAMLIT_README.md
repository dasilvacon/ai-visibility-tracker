# 🎯 AI Visibility Dashboard - Quick Start

## What is This?

An interactive web dashboard for exploring your AI visibility analysis. No technical knowledge required - just click and explore!

## Features

### 📊 Overview
- Key metrics at a glance
- Competitive landscape charts
- Top priority actions
- Download all reports

### 🎯 Sources & Citations
- See where you're being mentioned (Sephora, Reddit, etc.)
- Interactive opportunity matrix
- Filter by priority (HIGH/MEDIUM/LOW)
- PR target list with recommended actions

### ✅ Action Plan
- Task checklist for your content team
- Filter by priority and category
- Add assignees and due dates
- Export as CSV or Markdown

### 🏆 Competitor Analysis
- Detailed competitive positioning
- Gap analysis for each competitor
- Market share visualization
- Performance matrix

## How to Use

### 1. Access the Dashboard

**Local (On Your Computer)**:
```bash
cd /Users/tiffanydasilva/Claude-Projects/ai-visibility-tracker
source venv/bin/activate
streamlit run streamlit_app.py
```

Opens at: http://localhost:8501

**Online (Hosted)**:
Visit: https://your-dashboard-url.streamlit.app

### 2. Navigate

Use the sidebar to switch between pages:
- 📊 Overview → Start here
- 🎯 Sources & Citations → PR targets
- ✅ Action Plan → Task management
- 🏆 Competitor Analysis → Competitive intel

### 3. Filter & Sort

Each page has filters:
- **Priority**: HIGH, MEDIUM, LOW
- **Category**: Content, Audience
- **Sort by**: Opportunity Score, Gap, etc.

### 4. Download Reports

Click download buttons to get:
- PDF Executive Summary
- Full HTML Report
- CSV exports
- Markdown task lists

### 5. Task Management (Action Plan)

- Check boxes to mark tasks complete
- Add assignee names
- Set due dates
- Export updated list

## Tips

💡 **Start with Overview** - Get the big picture first

💡 **Focus on HIGH Priority** - Filter by HIGH in Action Plan

💡 **Target Zone = Opportunity** - In Sources page, look for red "Target Zone" on chart

💡 **Download CSV** - Export filtered lists for your team

💡 **Mobile Friendly** - Works on phone/tablet

## Keyboard Shortcuts

- `/` - Focus search
- `R` - Rerun app
- `Ctrl+S` - Save/screenshot

## Troubleshooting

**"No reports found"**
→ Make sure analysis has been run first
→ Check `data/reports/` folder exists

**Charts not showing**
→ Refresh browser (Ctrl+R or Cmd+R)
→ Clear cache (Ctrl+Shift+R or Cmd+Shift+R)

**Slow loading**
→ First load takes ~10 seconds (normal)
→ Subsequent loads are cached (fast)

## Need Help?

- Check tooltips (ℹ️ icons)
- Review deployment guide: `STREAMLIT_DEPLOYMENT_GUIDE.md`
- Contact your account manager

## What's Next?

1. ✅ Review Overview metrics
2. ✅ Check Sources for PR opportunities
3. ✅ Assign tasks from Action Plan
4. ✅ Download reports for your team
5. ✅ Schedule monthly updates

---

Powered by Streamlit | DaSilva Branding
