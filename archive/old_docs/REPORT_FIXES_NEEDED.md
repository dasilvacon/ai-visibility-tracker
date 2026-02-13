# AI Visibility Report Fixes - Implementation Guide

## Issues Identified

### 1. PROMPT COUNT MISMATCH (362 vs 300)
**Location:** HTML report shows 362 prompts
**Expected:** 150 prompts × 2 platforms = 300
**Root Cause:** Need to investigate if:
- There are duplicate test results
- More than 2 platforms are being tested
- Some prompts have multiple test runs

**Files to check:**
- `main.py` line 291: `len(full_results)`
- Results loading logic in ResultsTracker

**Fix needed:**
```python
# Add platform and prompt deduplication or clearly document:
# "Testing 150 unique prompts across ChatGPT and Claude (N platforms) = X total tests"
# If there are legitimately more tests, explain why in the report
```

### 2. EMPTY "START THIS WEEK" SECTION
**Location:** `src/reporting/html_report_generator.py`
**Current:** Shows "No immediate priorities identified"
**Fix:** Generate 2-3 GEO/AEO quick wins based on actual gaps

**New method needed in gap_analyzer.py:**
```python
def generate_geo_aeo_quick_wins(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate 2-3 actionable GEO/AEO recommendations based on actual gaps.

    Returns list of recommendations with:
    - title: What to do
    - why: The gap it addresses
    - how: Specific GEO/AEO tactic (schema, content structure, entity signals)
    - expected_impact: Estimated queries affected
    """
    recommendations = []

    # Analyze query types where competitors win
    query_types = self._analyze_query_type_gaps(scored_results)

    # Generate schema recommendations for how-to/FAQ gaps
    if query_types.get('how_to_gap', 0) > 20:
        recommendations.append({
            'title': 'Add HowTo Schema to Tutorial Content',
            'why': f"You're missing {query_types['how_to_count']} how-to queries where competitors appear",
            'how': 'Implement schema.org/HowTo markup on product application guides. Include step-by-step instructions, tools needed, and estimated time.',
            'tactical': 'Start with your top 5 products. Add JSON-LD schema with @type: HowTo',
            'expected_impact': f"~{query_types['how_to_count'] * 0.3:.0f} additional mentions/month"
        })

    # Generate FAQ schema recommendations for question queries
    if query_types.get('question_gap', 0) > 15:
        recommendations.append({
            'title': 'Implement FAQ Schema on Product Pages',
            'why': f"You're losing {query_types['question_count']} question-based queries",
            'how': 'Add schema.org/FAQPage markup answering common questions like "Does this work for oily lids?", "How long does it last?"',
            'tactical': 'Create 5-8 Q&A pairs per product page with Question/Answer schema',
            'expected_impact': f"~{query_types['question_count'] * 0.25:.0f} additional mentions/month"
        })

    # Generate comparison content recommendation
    if query_types.get('comparison_gap', 0) > 10:
        recommendations.append({
            'title': 'Create Competitor Comparison Landing Pages',
            'why': f"You're absent from {query_types['comparison_count']} comparison queries",
            'how': 'Build "[Your Brand] vs [Top Competitor]" pages with detailed feature comparison tables, honest pros/cons, and use/case recommendations',
            'tactical': f"Start with: {', '.join(query_types['top_competitors'][:3])}",
            'expected_impact': f"~{query_types['comparison_count'] * 0.4:.0f} additional mentions/month"
        })

    return recommendations[:3]  # Top 3 quick wins
```

### 3. BIGGEST MISSED OPPORTUNITIES SECTION
**Add new section showing 5 specific prompts where:**
- Competitor had high prominence (7+)
- Client brand was absent
- Include GEO/AEO recommendation for each

**New method in gap_analyzer.py:**
```python
def get_biggest_missed_opportunities(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find 5 specific prompts where competitors dominated and client was absent.

    Returns list with:
    - prompt: Exact prompt text
    - competitor_who_won: Which competitor appeared
    - their_prominence: Score 1-10
    - query_type: informational/comparison/how-to/etc
    - geo_aeo_fix: Specific recommendation
    """
    missed = []

    for result in scored_results:
        visibility = result.get('visibility', {})

        # Client not mentioned, competitor was
        if not visibility.get('brand_mentioned') and visibility.get('competitors_mentioned'):
            competitors = visibility.get('competitor_details', {})

            # Find competitor with highest prominence
            top_comp = None
            top_prominence = 0
            for comp_name, comp_data in competitors.items():
                prom = comp_data.get('prominence_score', 0)
                if prom > top_prominence:
                    top_prominence = prom
                    top_comp = comp_name

            # Only include if competitor had high prominence (7+)
            if top_prominence >= 7:
                missed.append({
                    'prompt': result.get('prompt_text', ''),
                    'competitor_who_won': top_comp,
                    'their_prominence': top_prominence,
                    'query_type': result.get('metadata', {}).get('intent_type', 'Unknown'),
                    'category': result.get('metadata', {}).get('category', 'Unknown'),
                    'geo_aeo_fix': self._generate_geo_aeo_fix(result)
                })

    # Sort by prominence, return top 5
    missed.sort(key=lambda x: x['their_prominence'], reverse=True)
    return missed[:5]

def _generate_geo_aeo_fix(self, result: Dict[str, Any]) -> str:
    """Generate specific GEO/AEO recommendation for a missed query."""
    query_type = result.get('metadata', {}).get('intent_type', '')
    category = result.get('metadata', {}).get('category', '')
    prompt = result.get('prompt_text', '').lower()

    # How-to queries -> HowTo schema
    if 'how to' in prompt or query_type == 'how_to':
        return "This is a how-to query. Create a tutorial page with HowTo schema markup including step-by-step instructions."

    # Question queries -> FAQ schema
    elif '?' in prompt or 'what' in prompt or 'which' in prompt:
        return "This is a question query. Add this Q&A to your FAQ page with FAQPage schema markup."

    # Comparison queries -> comparison content
    elif 'vs' in prompt or 'compare' in prompt or 'difference' in prompt:
        return "This is a comparison query. Create a dedicated comparison page with a feature table and honest head-to-head analysis."

    # Product queries -> Product schema + reviews
    elif category == 'transactional':
        return "This is a product query. Enhance your product page with Product schema, aggregate ratings, and customer reviews."

    # Default
    return "Create targeted content for this query type with appropriate schema markup and entity optimization."
```

### 4. "WHY YOU'RE LOSING" NARRATIVE
**Add 2-3 sentence analysis explaining visibility gap from GEO/AEO perspective**

**New method in gap_analyzer.py:**
```python
def generate_why_losing_narrative(self, scored_results: List[Dict[str, Any]],
                                 competitive_analysis: Dict[str, Any]) -> str:
    """
    Generate narrative explaining why brand is losing from GEO/AEO perspective.

    Analyzes:
    - Content type gaps (missing tutorials, comparisons, FAQs)
    - Entity authority signals
    - Query type patterns
    """
    # Analyze what content types competitors have
    missing_content = []
    educational_gap = self._count_gap_by_category(scored_results, 'educational')
    if educational_gap > 20:
        missing_content.append("how-to tutorials and educational content")

    comparison_gap = self._count_gap_by_intent(scored_results, 'comparison')
    if comparison_gap > 15:
        missing_content.append("competitor comparison pages")

    question_gap = self._count_question_queries(scored_results)
    if question_gap > 20:
        missing_content.append("FAQ pages with structured Q&A")

    # Build narrative
    narrative = []

    if missing_content:
        content_list = ', '.join(missing_content[:-1]) + (' and ' + missing_content[-1] if len(missing_content) > 1 else missing_content[0])
        narrative.append(f"Your competitors appear more often because they have {content_list} that AI models preferentially cite.")

    # Check entity strength
    top_comp = competitive_analysis.get('top_competitors', [{}])[0]
    if top_comp:
        comp_name = top_comp.get('name', 'competitors')
        comp_rate = top_comp.get('mention_rate', 0)
        narrative.append(f"{comp_name} dominates with {comp_rate:.0f}% visibility, likely due to stronger entity signals (more Wikipedia citations, industry mentions, and consistent NAP data).")

    # Query type analysis
    your_rate = competitive_analysis.get('brand_share_of_voice', 0)
    if your_rate < 30:
        narrative.append("You're particularly weak in informational and comparison queries, which represent the majority of AI-driven searches.")

    return " ".join(narrative)
```

### 5. FIX COMPETITOR BASELINE
**Location:** `_build_top_competitors()` in html_report_generator.py
**Issue:** Brand row shows 0% and 0 mentions
**Fix:** Already implemented in line 976-987 but may have bug

**Verify:**
```python
# Check that visibility_summary contains correct data
brand_rate = visibility_summary.get('visibility_rate', 0)  # Should be 16.3
brand_mentions = visibility_summary.get('total_mentions', 0)  # Should be 59
```

If still showing 0, check that `visibility_summary` is being passed correctly.

### 6. SMART DEFAULT FILTER
**Location:** HTML template in _build_prompt_viewer()
**Current:** Defaults to "All"
**Fix:** Default to "High Priority Gaps" (competitor mentioned, client not mentioned)

```html
<select id="status-filter" onchange="filterTable()">
    <option value="high_priority_gaps" selected>High Priority Gaps</option>
    <option value="all">All ({total})</option>
    <option value="mentioned">Brand Mentions</option>
    <option value="not_mentioned">No Mentions</option>
    <option value="with_competitors">With Competitors</option>
</select>
```

Add JavaScript:
```javascript
// On page load, apply high priority gaps filter
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('status-filter').value = 'high_priority_gaps';
    filterTable();
});
```

### 7. EXPLAIN IMPACT SCORES
**Location:** Opportunities table
**Current:** Shows raw number like "7154"
**Fix:** Either:
1. Add tooltip: "Impact Score = (Gap %) × (Sample Size) × 100"
2. Replace with "Estimated missed impressions: ~310/month"

## Implementation Priority

1. **HIGH:** Fix "Start This Week" with GEO/AEO quick wins
2. **HIGH:** Add "Biggest Missed Opportunities" section
3. **HIGH:** Add "Why You're Losing" narrative
4. **MEDIUM:** Fix competitor baseline (verify data flow)
5. **MEDIUM:** Set smart default filter
6. **LOW:** Document/fix prompt count mismatch
7. **LOW:** Explain or replace impact scores

## Testing Checklist

After implementing:
- [ ] "Start This Week" shows 2-3 GEO/AEO recommendations
- [ ] "Biggest Missed Opportunities" shows 5 specific prompts with GEO/AEO fixes
- [ ] "Why You're Losing" narrative appears with entity/content analysis
- [ ] Competitor table shows client brand with actual 16.3% rate
- [ ] Prompts tab defaults to "High Priority Gaps"
- [ ] Report clearly documents total prompt count
