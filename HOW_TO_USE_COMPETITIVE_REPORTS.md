# How to Use Competitive Reports

## ✅ What's Been Added

Your HTML report generator now includes 5 new competitive analysis sections:

### 1. **Composite Score Badge** (Executive Summary Tab)
- Large letter grade (A-F)
- Overall score out of 100
- Color-coded status

### 2. **Score Breakdown** (Executive Summary Tab)
- All 5 weighted dimensions
- Individual scores and grades
- Strengths and weaknesses

### 3. **Competitive Battlecard** (Executive Summary Tab)
- Head-to-head win/loss records
- Status vs each competitor (Winning/Losing/Tied)
- Overall win rate

### 4. **High-Intent Prompts You're Losing** (Action Plan Tab)
- Comparison queries where competitors win
- Example prompts by competitor
- Platforms where you're losing

### 5. **Citation Analysis** (Sources Tab)
- Owned vs Third-party vs Competitor breakdown
- Citation authority score
- Top cited domains

## 🚀 How to Generate Reports with Competitive Features

### Step 1: Run Your Visibility Tests

```bash
python3 main.py --platforms openai anthropic perplexity gemini --prompts data/prompts.csv
```

### Step 2: Update Your Report Generation Code

Add competitive analysis to your report generation workflow:

```python
from src.analysis.head_to_head_analyzer import HeadToHeadAnalyzer
from src.analysis.citation_classifier import CitationClassifier
from src.analysis.composite_scorer import CompositeScorer

# After running tests and getting scored_results...

# 1. HEAD-TO-HEAD ANALYSIS
h2h_analyzer = HeadToHeadAnalyzer(
    brand_name=brand_name,
    competitor_names=list(competitors.keys())
)
h2h_results = h2h_analyzer.aggregate_head_to_head_results(scored_results)

# 2. CITATION CLASSIFICATION
citation_classifier = CitationClassifier(
    brand_domains=brand_config['brand_domains'],
    competitor_domains={
        comp: config['domains']
        for comp, config in brand_config['competitors'].items()
    }
)
citation_stats = citation_classifier.classify_all_sources(scored_results)

# 3. COMPOSITE SCORING
composite_scorer = CompositeScorer()
composite_metrics = {
    'visibility_rate': visibility_summary['brand_visibility_rate'],
    'prominence_rate': visibility_summary.get('average_prominence', 0),
    'competitive_win_rate': h2h_results.get('overall_win_rate', 0),
    'citation_authority_score': citation_stats.get('citation_authority_score', 0),
    'positioning_quality_score': 70  # Default or calculate separately
}
scorecard = composite_scorer.create_full_scorecard(composite_metrics)

# 4. GENERATE REPORT WITH COMPETITIVE DATA
from src.reporting.html_report_generator import HTMLReportGenerator

report_gen = HTMLReportGenerator('data/reports')
report_path = report_gen.generate_report(
    brand_name=brand_name,
    visibility_summary=visibility_summary,
    competitive_analysis=competitive_analysis,
    gap_analysis=gap_analysis,
    action_plan=action_plan,
    scored_results=scored_results,

    # NEW: Competitive parameters
    composite_scorecard=scorecard,
    head_to_head_results=h2h_results,
    citation_stats=citation_stats,

    source_analysis=source_analysis
)

print(f"Report generated: {report_path}")
```

### Step 3: Configure Your Brand Settings

Make sure `data/brand_config.json` has:

```json
{
  "brand_name": "YourBrand",
  "brand_domains": [
    "yourbrand.com",
    "blog.yourbrand.com"
  ],
  "competitors": {
    "Competitor1": {
      "domains": ["competitor1.com"]
    },
    "Competitor2": {
      "domains": ["competitor2.com"]
    }
  }
}
```

## 📊 What You'll See in Reports

### Executive Summary Tab
- **Top**: Big grade badge (e.g., "B 72/100")
- **After summary**: Score breakdown table with 5 dimensions
- **Middle**: Competitive battlecard showing who you're winning/losing against

### Action Plan Tab
- **After Quick Wins**: High-intent comparison queries you're losing
- Prioritized by competitor threat level

### Sources Tab
- **Top**: Citation analysis showing narrative control
- Owned vs third-party vs competitor percentages
- Top cited domains

## 🎯 Example Output

When you run a report with competitive features, you'll see:

```
Overall Grade: B (72/100)

Score Breakdown:
- Visibility: 75/100 (B) - Strong
- Competitive Win Rate: 60/100 (C) - Needs improvement
- Prominence: 80/100 (A) - Strong
- Citation Authority: 72/100 (A) - Strong
- Positioning Quality: 70/100 (B)

Strengths: Visibility, Prominence, Citation Authority
Weaknesses: Competitive Win Rate

Competitive Battlecard:
- vs Competitor1: 7 wins, 5 losses, 1 tie (WINNING)
- vs Competitor2: 3 wins, 8 losses, 0 ties (LOSING) ⚠️

Citation Control:
- 45% Owned
- 40% Third-party
- 15% Competitor
```

## 💡 Tips

1. **Run tests monthly** to track competitive progress over time
2. **Focus on weaknesses** - If competitive win rate is low, prioritize comparison content
3. **Monitor citation authority** - Aim for 50%+ owned citations
4. **Watch high-intent losses** - These are your highest priority fixes

## 🔧 Troubleshooting

**Q: Competitive sections not showing in report?**
- Make sure you're passing the competitive parameters when calling `generate_report()`
- Check that competitive analysis ran successfully (no errors)

**Q: All scores showing as 0?**
- Verify your brand_config.json has correct domains
- Check that competitor names match those in your prompts

**Q: Citation analysis showing 0%?**
- Ensure brand_domains are correctly configured
- Check that sources are being extracted (look at raw results)

## 📚 Reference

- `example_competitive_integration.py` - Full working example
- `COMPETITIVE_FEATURES_SUMMARY.md` - Detailed feature documentation
- `test_api_keys.py` - Verify platforms are working

## Next Steps

1. Run your first test with all 4 platforms
2. Generate a report with competitive features
3. Review the competitive battlecard to identify priorities
4. Create content targeting your biggest competitive losses
