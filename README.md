# 🎯 AI Visibility Tracker

Track your brand's visibility across AI platforms (ChatGPT, Claude, Perplexity, Gemini) with monthly trend analysis.

## 🚀 Quick Start

```bash
# Start the integrated app
streamlit run streamlit_app_html.py
```

**That's it!** One app for everything:
- **Admin:** Dashboard + Prompt Generator + Historical Trends
- **Clients:** Dashboard only (their brand)

For complete instructions, see **[START_HERE.md](START_HERE.md)**

---

## 📊 What This Does

### 1. Generate Test Prompts (Admin Only)
- Create 100-300 AI-optimized prompts
- Quality scoring system (naturalness, clarity, relevance)
- Review and approve before testing
- Export to CSV

### 2. Test Across AI Platforms (CLI)
```bash
python main.py --client "Client Name" --prompts prompts.csv
```
Tests your prompts against:
- ChatGPT
- Claude
- Perplexity
- Gemini

### 3. Track Monthly Trends (Dashboard)
Three key metrics:
- **Visibility Rate** - % of prompts where your brand appears
- **Prominence Rate** - Average citation position (lower is better)
- **Share of Voice** - Your mentions vs. competitors

See [HISTORICAL_TRACKING.md](HISTORICAL_TRACKING.md) for details.

---

## 📁 Project Structure

```
ai-visibility-tracker/
├── streamlit_app_html.py          # Main integrated app
├── main.py                        # CLI tool for running tests
├── save_historical_data.py        # Save monthly metrics
│
├── src/                           # Core functionality
│   ├── api_clients/              # AI platform API clients
│   ├── analysis/                 # Visibility scoring
│   ├── authentication.py         # User authentication
│   ├── prompt_generator/         # Prompt generation + quality scoring
│   ├── reporting/                # Report generation
│   └── tracking/                 # Historical tracking
│
├── prompt_generator_pages/        # Admin pages
│   ├── settings.py               # Client Manager
│   ├── generate.py               # Generate prompts
│   ├── review.py                 # Review & approve
│   ├── export_page.py            # Export
│   └── library.py                # Library
│
├── dashboard_pages/               # Dashboard pages
│   ├── overview.py               # Main dashboard
│   ├── historical_trends.py      # Monthly trends
│   ├── competitors.py            # Competitor analysis
│   └── sources.py                # Source analysis
│
├── data/                          # Data storage
│   ├── clients.json              # Client registry
│   ├── prompt_generation/        # Prompts
│   ├── results/                  # Test results
│   │   └── monthly_scores.json   # Historical metrics
│   └── reports/                  # HTML reports
│
├── docs/                          # Documentation
│
└── archive/                       # Old/deprecated files
```

---

## 🔑 Key Files

### Main Application
- **`streamlit_app_html.py`** - Integrated app with role-based access

### CLI Tools
- **`main.py`** - Run AI visibility tests
- **`save_historical_data.py`** - Save monthly metrics

### Documentation
- **`START_HERE.md`** - Quick start guide
- **`HOW_TO_USE.md`** - Complete user guide
- **`HISTORICAL_TRACKING.md`** - Monthly tracking workflow

---

## 🎯 Complete Workflow

### 1. Admin: Create Prompts
1. Login as admin
2. **Client Manager** → Create/select client
3. **Generate** → Create 100-300 prompts with quality scoring
4. **Review & Approve** → Filter by quality (75-100)
5. **Export** → Download CSV

### 2. Run Tests (CLI)
```bash
python main.py --client "Client Name" --prompts approved_prompts.csv
```

### 3. Save Historical Data
```bash
python save_historical_data.py --client "Client Name"
```

### 4. View Trends
- Navigate to **Historical Trends** page
- See month-over-month improvements

---

## 🔐 Authentication

Role-based access in `.streamlit/secrets.toml`:
```toml
[passwords]
admin = "your-admin-password"
client_name = "client-password"

[roles]
admin = "admin"
client_name = "client"

[clients]
admin = "ALL"
client_name = "Client Display Name"
```

---

## 📈 Monthly Tracking

1. **Generate baseline prompts** (100-300)
2. **Save the CSV** - reuse every month
3. **Run tests monthly** with same CSV
4. **Save historical data** after each test
5. **Track improvements** in dashboard

**Why same prompts?** Measures genuine visibility improvement, not prompt variation.

---

## 📞 Support

- **Quick Start:** [START_HERE.md](START_HERE.md)
- **Full Guide:** [HOW_TO_USE.md](HOW_TO_USE.md)
- **Monthly Tracking:** [HISTORICAL_TRACKING.md](HISTORICAL_TRACKING.md)
- **Quality Scoring:** [docs/QUALITY_SCORING.md](docs/QUALITY_SCORING.md)

---

**Built with ❤️ for tracking AI visibility**
