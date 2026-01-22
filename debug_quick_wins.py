#!/usr/bin/env python3
"""
Debug script to check why generate_geo_aeo_quick_wins returns empty.
"""

import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analysis.visibility_scorer import VisibilityScorer
from analysis.gap_analyzer import GapAnalyzer
from tracking.results_tracker import ResultsTracker

# Load brand config
with open('data/natasha_denona_brand_config.json', 'r') as f:
    brand_config = json.load(f)

brand_name = brand_config['brand']['name']
brand_aliases = brand_config['brand'].get('aliases', [])
competitors = brand_config.get('competitors', [])

print(f"Brand: {brand_name}")
print(f"Competitors: {competitors}\n")

# Load test results
results_tracker = ResultsTracker('data/results')
results = results_tracker.load_results_summary()

# Load full results
full_results = []
for result in results:  # Load ALL results
    test_id = result.get('test_id')
    if test_id:
        try:
            full_result = results_tracker.load_full_result(test_id)
            full_results.append(full_result)
        except:
            pass

print(f"Loaded {len(full_results)} results\n")

# Score results with new visibility scorer
scorer = VisibilityScorer(
    brand_name=brand_name,
    brand_aliases=brand_aliases,
    competitor_names=competitors
)

scored_results = scorer.score_all_results(full_results)

# Check for competitor mentions
print("=" * 60)
print("Checking all competitor mentions:")
print("=" * 60)

high_prom_count = 0
all_comp_mentions = 0
brand_absent_comp_present = 0

for i, result in enumerate(scored_results):
    visibility = result.get('visibility', {})
    brand_mentioned = visibility.get('brand_mentioned', False)
    competitor_details = visibility.get('competitor_details', {})

    if competitor_details:
        all_comp_mentions += 1

        if not brand_mentioned:
            brand_absent_comp_present += 1

            # Show first few examples with prominence scores
            if brand_absent_comp_present <= 5:
                prompt = result.get('prompt_text', '')[:60]
                print(f"\nExample {brand_absent_comp_present}:")
                print(f"  Prompt: {prompt}...")
                for comp_name, comp_data in competitor_details.items():
                    prom = comp_data.get('prominence_score', 0)
                    positions = comp_data.get('positions', [])
                    print(f"  {comp_name}: prominence={prom:.1f}, positions={positions[:3]}")

                    if prom >= 7:
                        high_prom_count += 1

print(f"\n" + "=" * 60)
print(f"Stats from {len(scored_results)} results:")
print(f"  - Results with any competitor mention: {all_comp_mentions}")
print(f"  - Results where brand absent but competitor present: {brand_absent_comp_present}")
print(f"  - High-prominence misses (prominence >= 7): {high_prom_count}")
print("=" * 60)

# Now test generate_geo_aeo_quick_wins
print("\nTesting generate_geo_aeo_quick_wins()...")
gap_analyzer = GapAnalyzer(brand_name)
geo_aeo_wins = gap_analyzer.generate_geo_aeo_quick_wins(scored_results)

print(f"\nReturned {len(geo_aeo_wins)} recommendations:")
for i, win in enumerate(geo_aeo_wins, 1):
    print(f"\n{i}. {win['title']}")
    print(f"   What: {win['what'][:100]}...")
    print(f"   Why: {win['why'][:100]}...")
