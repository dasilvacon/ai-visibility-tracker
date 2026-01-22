# AI Visibility Tracker - Analysis Guide

## 🎯 Complete Analysis System

The AI Visibility Tracker now includes a comprehensive visibility scoring and reporting system that automatically analyzes brand mentions in AI responses.

## ✅ What's Included

### Analysis Modules (`src/analysis/`)

1. **`visibility_scorer.py`**
   - Detects brand mentions using regex patterns
   - Scores prominence (0-10 scale)
   - Tracks competitor mentions
   - Extracts context snippets

2. **`competitor_analyzer.py`**
   - Calculates brand share of voice
   - Ranks competitors by dominance
   - Identifies competitive gaps
   - Compares by dimension (persona, category, platform)

3. **`gap_analyzer.py`**
   - Identifies visibility gaps
   - Ranks opportunities by impact
   - Creates prioritized action plans
   - Generates strategic recommendations

4. **`html_report_generator.py`**
   - Generates professional HTML reports
   - Interactive metrics dashboard
   - Visibility breakdowns by persona/platform
   - Top competitors and opportunities
   - Action plan with recommendations

## 🚀 Usage

### 1. Configure Your Brand

Copy and edit the brand configuration template:

```bash
cp data/brand_config_template.json data/my_brand_config.json
```

Edit `my_brand_config.json`:

```json
{
  "brand": {
    "name": "Your Brand Name",
    "aliases": ["YBN", "Your Brand", "Brand Name Inc"],
    "description": "Your brand description"
  },
  "competitors": [
    "Competitor A",
    "Competitor B",
    "Competitor C"
  ]
}
```

### 2. Run Complete Pipeline with Analysis

**Full workflow - Generate, Test, and Analyze:**

```bash
python main.py --full-pipeline \
  --count 100 \
  --brand-config data/my_brand_config.json \
  --analyze \
  --platforms openai anthropic
```

This will:
1. Generate 100 natural prompts
2. Test them on OpenAI and Anthropic
3. Score brand visibility
4. Analyze competitors
5. Identify gaps
6. Generate reports (text + HTML)

### 3. Analyze Existing Test Results

If you already have test results:

```bash
python main.py --analyze --brand-config data/my_brand_config.json
```

### 4. Test Then Analyze

Run tests first, then analyze separately:

```bash
# Step 1: Run tests
python main.py --prompts data/my_prompts.csv --platforms openai anthropic

# Step 2: Analyze results
python main.py --analyze --brand-config data/my_brand_config.json
```

## 📊 Reports Generated

### Text Report
**Location:** `data/reports/visibility_analysis_{Brand_Name}.txt`

Contains:
- Executive summary with key metrics
- Prominence distribution
- Competitive analysis
- Top 10 opportunities ranked by impact
- Action plan (Quick Wins, Medium-term, Long-term)
- Overall strategic recommendation

### HTML Report
**Location:** `data/reports/visibility_report_{Brand_Name}.html`

Interactive report with:
- 📊 Executive summary dashboard
- 👥 Visibility by persona (table)
- 🖥️ Visibility by platform (table)
- 🏆 Top 10 competitors mentioned
- 💡 Top 10 gap opportunities
- 🎯 Action plan with recommendations

**Open in browser to view:**
```bash
open data/reports/visibility_report_Your_Brand_Name.html
```

## 📈 Metrics Explained

### Brand Visibility Rate
Percentage of prompts where your brand was mentioned.
- **High (>60%)**: Strong visibility
- **Medium (30-60%)**: Moderate visibility
- **Low (<30%)**: Weak visibility

### Prominence Score (0-10)
How prominently your brand is featured in responses:
- **10**: Mentioned first, prominently featured
- **7-9**: Mentioned clearly but not first
- **4-6**: Mentioned briefly or in passing
- **1-3**: Mentioned minimally
- **0**: Not mentioned

### Share of Voice
Brand mentions as percentage of all mentions (brand + competitors).

### Dominance Score
Competitor strength calculated from:
- Mention frequency (40%)
- Solo mentions without brand (30%)
- Mentioned before brand (30%)

### Impact Score
Opportunity impact based on:
- Gap severity (100 - current visibility %)
- Prompt volume in category
- Weighted by category importance

## 🎯 Reading the Action Plan

### Quick Wins (Start Immediately)
- High impact opportunities
- Small sample sizes
- Can be addressed quickly
- Focus here first

### Medium-Term Priorities (3 Months)
- Significant impact
- Larger effort required
- Strategic importance
- Plan and execute systematically

### Long-Term Strategy (6+ Months)
- Foundational changes
- Comprehensive initiatives
- Sustained effort required
- Build into roadmap

## 🔍 Example Workflow

### Scenario: New Brand Launch

```bash
# 1. Create brand config
cp data/brand_config_template.json data/mybrand.json
# Edit mybrand.json with your brand details

# 2. Run initial baseline test (small sample)
python main.py --full-pipeline \
  --count 50 \
  --brand-config data/mybrand.json \
  --analyze \
  --platforms openai anthropic

# 3. Review HTML report
open data/reports/visibility_report_MyBrand.html

# 4. Identify top 3 opportunities from Quick Wins

# 5. Create targeted content for those gaps

# 6. Re-test after 1 month with larger sample
python main.py --full-pipeline \
  --count 200 \
  --brand-config data/mybrand.json \
  --analyze \
  --platforms openai anthropic

# 7. Compare reports to measure improvement
```

### Scenario: Competitor Analysis

```bash
# 1. Add all major competitors to brand config
# Edit competitors list in brand_config.json

# 2. Generate prompts in your category
# Customize personas and keywords for your industry

# 3. Run comprehensive test
python main.py --full-pipeline \
  --count 500 \
  --brand-config data/mybrand.json \
  --analyze \
  --platforms openai anthropic

# 4. Review competitive analysis in HTML report
# Check "Top 10 Competitors" section

# 5. Identify where competitors dominate
# Review competitive gaps

# 6. Create content strategy to address gaps
```

## 💡 Tips for Best Results

1. **Use Realistic Brand Names**: The scorer uses exact matching, so use your actual brand name and common variations

2. **Include Common Aliases**: Add acronyms, short forms, and common misspellings to `aliases`

3. **List Real Competitors**: Use actual competitor names for accurate competitive analysis

4. **Test Regularly**: Run monthly or quarterly to track progress

5. **Use Sufficient Sample Size**:
   - Baseline: 50-100 prompts
   - Quarterly: 200-500 prompts
   - Annual: 1000+ prompts

6. **Diversify Prompts**: Use varied personas, intents, and categories for comprehensive coverage

7. **Customize Keywords**: Update `keywords_template.csv` with SEO data from your industry

8. **Test Multiple Platforms**: Different AI platforms may have different training data

## 🐛 Troubleshooting

### "No results found"
- Run tests first before analysis
- Check that test results exist in `data/results/`

### "Brand Visibility Rate: 0%"
- Verify brand name spelling in config
- Check that prompts are relevant to your brand
- Ensure aliases include common variations
- Generate more targeted prompts

### "No competitors mentioned"
- Competitors may not be relevant to test prompts
- Add competitor mentions to keywords file
- Increase competitor_ratio in prompt generation

### HTML report not opening
- Check file permissions
- Try opening directly: `python -m webbrowser data/reports/visibility_report_Brand.html`
- View in any modern browser

## 📚 Advanced Usage

### Custom Prompt Sets

Create focused prompt sets for specific analysis:

```bash
# SEO keyword test
python main.py --prompts data/seo_prompts.csv \
  --brand-config data/mybrand.json \
  --analyze

# Competitor comparison test
python main.py --prompts data/competitor_prompts.csv \
  --brand-config data/mybrand.json \
  --analyze

# Persona-specific test
python main.py --prompts data/persona_prompts.csv \
  --brand-config data/mybrand.json \
  --analyze
```

### Batch Analysis

Analyze multiple brands:

```bash
for brand in brand1 brand2 brand3; do
  python main.py --analyze --brand-config data/${brand}_config.json
done
```

### Export Results

Results are saved as JSON for further analysis:
- Individual test results: `data/results/test_*.json`
- Summary CSV: `data/results/results_summary.csv`

Load in Python for custom analysis:
```python
import json
with open('data/results/test_12345.json') as f:
    result = json.load(f)
    print(result['visibility'])
```

## 🎓 Understanding the Scoring Algorithm

### Brand Detection
1. Exact match with word boundaries
2. Case-insensitive
3. Matches all aliases
4. Counts multiple mentions

### Prominence Calculation
- Base score: 3 points for being mentioned
- Position bonus: +4 points if in first 20% of response
- Multiple mentions: +1-2 points
- Competitor penalty: -0.5 to -1.5 points
- Final score: Clamped to 0-10 range

### Gap Identification
Gaps identified when:
- Visibility rate < 60%
- High competitor presence
- Low prominence scores
- Large sample size

## 🔐 Privacy & Security

- All analysis runs locally
- No data sent externally
- API keys stored in gitignored config
- Reports contain only aggregated data
- Safe to share HTML reports (no sensitive info)

## 📞 Support

For issues or questions:
1. Check this guide
2. Review README.md
3. Check example_usage.py for code samples
4. Create an issue in the repository

## 🎉 Success Metrics

Track these over time:
- ✅ Increasing visibility rate
- ✅ Rising prominence scores
- ✅ Growing share of voice
- ✅ Closing gap opportunities
- ✅ Beating competitor dominance

**Goal**: Achieve 60%+ visibility rate with 7+ average prominence score.
