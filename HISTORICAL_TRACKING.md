# 📈 Historical Tracking Guide

Track your AI visibility metrics over time to measure improvement month-over-month.

## 🎯 Three Key Metrics

1. **Visibility Rate** - % of prompts where your brand is mentioned
2. **Prominence Rate** - Average position in AI responses (1st, 2nd, 3rd, etc.)
3. **Share of Voice** - Your brand mentions vs. competitor mentions

## 📅 Monthly Workflow

### Step 1: Run Tests (Monthly)

Use the **same prompts** each month to track consistent improvements:

```bash
# Month 1 (Baseline)
python main.py --client "Natasha Denona" --prompts natasha_denona_baseline.csv

# Month 2 (Use SAME CSV)
python main.py --client "Natasha Denona" --prompts natasha_denona_baseline.csv

# Month 3 (Use SAME CSV again)
python main.py --client "Natasha Denona" --prompts natasha_denona_baseline.csv
```

**Important:** Reuse the same CSV every month! This ensures you're measuring genuine visibility improvements, not prompt variation.

### Step 2: Save Historical Data

After tests complete, save the metrics for historical tracking:

```bash
python save_historical_data.py --client "Natasha Denona"
```

This will:
- Auto-detect your latest report
- Extract the three key metrics
- Save to `data/results/monthly_scores.json`
- Make data available in Historical Trends dashboard

### Step 3: View Trends in Dashboard

1. Open your dashboard: `streamlit run streamlit_app_html.py`
2. Login
3. Click **"📈 Historical Trends"** in the sidebar
4. See your month-over-month progress!

## 📊 What You'll See

### Month-over-Month Comparison
```
Visibility Rate:     75% (↑ +5%)  🟢
Prominence Rate:     #2  (↑ -0.5) 🟢 (lower is better!)
Share of Voice:      38% (↑ +3%)  🟢
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Trend: Improving! 🎉
```

### Trend Charts

Interactive charts showing each metric over time, with:
- Line graphs for visual trends
- Data tables for exact values
- Month-by-month breakdown

### Historical Archive

All past test runs with:
- Date and time of each test
- Full metrics for each month
- Platform-specific breakdowns (ChatGPT, Claude, Perplexity, Gemini)

## 🔧 Manual Data Entry

If you need to manually enter historical data:

```bash
python save_historical_data.py \
  --client "Natasha Denona" \
  --visibility-rate 75.5 \
  --prominence 2.3 \
  --brand-mentions 85 \
  --competitor-mentions 138 \
  --total-prompts 100 \
  --month "2026-02"
```

## 📁 Data Storage

Historical data is saved to:
```
data/results/monthly_scores.json
```

Format:
```json
{
  "natasha_denona": {
    "2026-02": {
      "test_date": "2026-02-13T10:30:00",
      "total_prompts": 100,
      "metrics": {
        "visibility_rate": 75.0,
        "prominence_rate": 2.3,
        "share_of_voice": 38.0
      },
      "detailed_stats": {
        "brand_mentions": 85,
        "competitor_mentions": 138
      }
    },
    "2026-03": { ... }
  }
}
```

## 🗓️ Best Practices

### Consistent Testing Schedule
- Set a monthly reminder (e.g., 1st of each month)
- Use the same day each month for consistency
- Run tests at similar times (AI models can vary by time of day)

### Reuse Same Prompts
- Generate a baseline set of 100-300 prompts
- Save the CSV file securely
- Use the **exact same file** every month
- This ensures you're measuring visibility changes, not prompt quality changes

### Track Alongside SEO Efforts
- Note when you make content changes
- Track which actions led to visibility improvements
- Correlate with other marketing metrics

### Archive Everything
- Keep all monthly CSV files
- Save all HTML reports
- Back up `monthly_scores.json` regularly

## 🎯 What Defines Success?

### Good Trends
- **Visibility Rate increasing** (60% → 70% → 80%)
- **Prominence improving** (Position #3 → #2 → #1)
- **Share of Voice growing** (30% → 35% → 42%)

### Concerning Trends
- Visibility Rate declining
- Position getting worse (moving from #1 to #3)
- Share of Voice shrinking vs. competitors

### Take Action When:
- You see 2+ months of declining metrics
- Competitors are gaining share of voice
- Specific platforms show low visibility

## 🚀 Quick Start Checklist

- [ ] Generate baseline prompts (100-300)
- [ ] Export to CSV and save securely
- [ ] Run first test: `python main.py --client "YourClient" --prompts baseline.csv`
- [ ] Save historical data: `python save_historical_data.py --client "YourClient"`
- [ ] View in dashboard: Historical Trends page
- [ ] Set calendar reminder for next month
- [ ] Repeat monthly with **same CSV**!

## 💡 Pro Tips

1. **Baseline First**: Your first month establishes the baseline - subsequent months show improvement
2. **Seasonal Variations**: Some months may naturally vary (holidays, industry trends)
3. **Platform Differences**: Track which AI platforms improve most
4. **Competitor Tracking**: Watch how competitor mentions trend over time
5. **Content Correlation**: Note when you publish new content or update SEO

---

**Questions?** Check `docs/QUALITY_SCORING.md` and `HOW_TO_USE.md` for more information.
