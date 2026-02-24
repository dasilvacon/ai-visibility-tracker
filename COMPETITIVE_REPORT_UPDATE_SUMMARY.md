# Competitive Report Update - Implementation Plan

## What We're Adding to the HTML Report

### 1. Composite Score Badge (Header Section)
- Large letter grade display (A, B, C, D, F)
- Overall score out of 100
- Color-coded by grade
- One-sentence summary

### 2. Score Breakdown Section (After Executive Summary)
Shows all 5 weighted dimensions:
- Visibility (30%)
- Competitive Win Rate (25%)
- Prominence (20%)
- Citation Authority (15%)
- Positioning Quality (10%)

Each with:
- Individual scores
- Letter grades
- Visual indicators

### 3. Competitive Battlecard (New Section)
- Head-to-head results table
- Win/Loss/Tie counts per competitor
- Status indicators (Winning/Losing/Tied)
- Win rate percentages

### 4. High-Intent Prompts You're Losing
- List of comparison queries where competitors win
- Platform breakdown
- Sources cited

### 5. Citation Analysis (Enhanced Sources Tab)
- Owned vs Third-party vs Competitor breakdown
- Citation authority score
- Top domains by type
- Narrative control insights

## Files Modified
1. `/src/reporting/html_report_generator.py`
   - Updated `generate_report()` signature
   - Updated `_build_html()` signature
   - Added new helper methods:
     * `_build_composite_score_badge()`
     * `_build_score_breakdown()`
     * `_build_competitive_battlecard()`
     * `_build_high_intent_losses()`
     * `_build_citation_analysis()`

## Integration Points

The new sections will be integrated as follows:

### Executive Summary Tab:
```
Header with Brand Name
↓
**[NEW]** Composite Score Badge  <-- Big grade badge
↓
Top Executive Summary
↓
**[NEW]** Score Breakdown Table  <-- 5 dimensions
↓
Executive Summary Details
↓
**[NEW]** Competitive Battlecard  <-- Head-to-head results
↓
Competitive Landscape Visual
↓
Brief Priorities
```

### Sources & Citations Tab:
```
**[ENHANCED]** Citation Analysis  <-- Owned/Third-party/Competitor breakdown
↓
Existing source tables
```

### Action Plan Tab:
```
Quick Wins
↓
**[NEW]** High-Intent Prompts You're Losing  <-- Comparison queries lost
↓
Content Gap Analysis
↓
(rest of action plan)
```

## Data Flow

When generating a report, you'll now pass:

```python
report_generator.generate_report(
    brand_name=brand_name,
    visibility_summary=visibility_summary,
    competitive_analysis=competitive_analysis,
    gap_analysis=gap_analysis,
    action_plan=action_plan,
    scored_results=scored_results,

    # NEW PARAMETERS:
    composite_scorecard=scorecard,           # From CompositeScorer
    head_to_head_results=h2h_results,        # From HeadToHeadAnalyzer
    citation_stats=citation_stats,           # From CitationClassifier

    source_analysis=source_analysis
)
```

## Next Steps

1. ✅ Update method signatures (DONE)
2. ⏳ Add CSS styles for new components
3. ⏳ Implement helper methods
4. ⏳ Integrate into existing report structure
5. ⏳ Test with sample data

## Visual Design

Following DaSilva Consulting brand:
- Colors: `#4D2E3A` (primary), `#6B5660` (secondary), `#A7868F` (muted)
- Grade colors:
  - A: Green `#10b981`
  - B: Blue `#3b82f6`
  - C: Amber `#f59e0b`
  - D/F: Red `#ef4444`
- Clean, professional tables
- Card-based layouts
- Subtle shadows and borders
