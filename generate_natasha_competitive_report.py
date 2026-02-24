#!/usr/bin/env python3
"""
Generate Natasha Denona competitive analysis report.
Run this after visibility tests complete.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.db_manager import DatabaseManager
from analysis.visibility_calculator import VisibilityCalculator
from analysis.competitive_analyzer import CompetitiveAnalyzer
from analysis.gap_analyzer import GapAnalyzer
from analysis.action_plan_generator import ActionPlanGenerator
from analysis.source_analyzer import SourceAnalyzer
from analysis.head_to_head_analyzer import HeadToHeadAnalyzer
from analysis.citation_classifier import CitationClassifier
from analysis.composite_scorer import CompositeScorer
from reporting.html_report_generator import HTMLReportGenerator


def load_brand_config():
    """Load Natasha Denona brand configuration."""
    with open('data/natasha_denona_brand_config.json', 'r') as f:
        return json.load(f)


def extract_brand_domains_and_competitors(brand_config):
    """Extract domains from brand config v2.0 format."""

    # Extract brand domain from website URL
    brand_website = brand_config['brand']['website']
    brand_domains = [brand_website.replace('https://', '').replace('http://', '')]

    # Extract competitor info
    competitors_dict = {}
    for comp in brand_config['competitors']['expected']:
        comp_name = comp['name']
        comp_website = comp['website']
        comp_domain = comp_website.replace('https://', '').replace('http://', '')
        competitors_dict[comp_name] = {
            'domains': [comp_domain]
        }

    return brand_domains, competitors_dict


def main():
    """Generate competitive analysis report for Natasha Denona."""

    print("="*60)
    print("Natasha Denona Competitive Analysis Report")
    print("="*60)

    # Load brand configuration
    print("\n1. Loading brand configuration...")
    brand_config = load_brand_config()
    brand_name = brand_config['brand']['name']
    brand_domains, competitors_dict = extract_brand_domains_and_competitors(brand_config)
    competitor_names = list(competitors_dict.keys())

    print(f"   ✓ Brand: {brand_name}")
    print(f"   ✓ Competitors: {', '.join(competitor_names)}")

    # Get latest test results from database
    print("\n2. Loading test results from database...")
    db = DatabaseManager()

    # Get all results (no date filter to get latest batch)
    results = db.get_all_results()

    if not results:
        print("   ✗ No test results found in database")
        print("   → Run: python3 main.py --platforms openai anthropic perplexity gemini --prompts data/generated_prompts.csv")
        return 1

    print(f"   ✓ Loaded {len(results)} test results")

    # Get prompts
    prompts = db.get_all_prompts()
    prompts_dict = {p['prompt_id']: p for p in prompts}

    # Attach prompt text to results
    scored_results = []
    for result in results:
        prompt_data = prompts_dict.get(result['prompt_id'])
        if prompt_data:
            result['prompt_text'] = prompt_data['prompt_text']
            result['prompt_category'] = prompt_data.get('category', 'unknown')
            scored_results.append(result)

    print(f"   ✓ Matched {len(scored_results)} results with prompts")

    # 3. Run visibility analysis
    print("\n3. Calculating visibility metrics...")
    vis_calc = VisibilityCalculator(brand_name=brand_name)
    visibility_summary = vis_calc.calculate_visibility_summary(scored_results)

    print(f"   ✓ Brand Visibility Rate: {visibility_summary['brand_visibility_rate']:.1f}%")
    print(f"   ✓ Share of Voice: {visibility_summary.get('share_of_voice', 0):.1f}%")

    # 4. Run competitive analysis
    print("\n4. Running competitive analysis...")
    comp_analyzer = CompetitiveAnalyzer(
        brand_name=brand_name,
        competitor_names=competitor_names
    )
    competitive_analysis = comp_analyzer.analyze_competitive_landscape(scored_results)

    print(f"   ✓ Analyzed competitive landscape")

    # 5. Run gap analysis
    print("\n5. Analyzing content gaps...")
    gap_analyzer = GapAnalyzer(brand_name=brand_name)
    gap_analysis = gap_analyzer.analyze_gaps(scored_results)

    print(f"   ✓ Identified content gaps")

    # 6. Generate action plan
    print("\n6. Generating action plan...")
    action_planner = ActionPlanGenerator(brand_name=brand_name)
    action_plan = action_planner.generate_action_plan(
        visibility_summary=visibility_summary,
        gap_analysis=gap_analysis,
        competitive_analysis=competitive_analysis
    )

    print(f"   ✓ Generated action plan")

    # 7. Analyze sources
    print("\n7. Analyzing sources...")
    source_analyzer = SourceAnalyzer()
    source_analysis = source_analyzer.analyze_sources(scored_results)

    print(f"   ✓ Analyzed sources")

    # 8. HEAD-TO-HEAD ANALYSIS
    print("\n8. Running head-to-head competitive analysis...")
    h2h_analyzer = HeadToHeadAnalyzer(
        brand_name=brand_name,
        competitor_names=competitor_names
    )
    h2h_results = h2h_analyzer.aggregate_head_to_head_results(scored_results)

    print(f"   ✓ Found {h2h_results['total_comparison_queries']} comparison queries")
    print(f"   ✓ Overall win rate: {h2h_results['overall_win_rate']:.1f}%")
    print(f"   ✓ Wins: {h2h_results['total_wins']}, Losses: {h2h_results['total_losses']}, Ties: {h2h_results['total_ties']}")

    # 9. CITATION CLASSIFICATION
    print("\n9. Classifying citations...")
    citation_classifier = CitationClassifier(
        brand_domains=brand_domains,
        competitor_domains=competitors_dict
    )
    citation_stats = citation_classifier.classify_all_sources(scored_results)

    print(f"   ✓ Total citations: {citation_stats['total_citations']}")
    print(f"   ✓ Owned: {citation_stats['owned_percentage']:.1f}%")
    print(f"   ✓ Third-party: {citation_stats['third_party_percentage']:.1f}%")
    print(f"   ✓ Competitor: {citation_stats['competitor_percentage']:.1f}%")
    print(f"   ✓ Citation Authority Score: {citation_stats['citation_authority_score']:.1f}/100")

    # 10. COMPOSITE SCORING
    print("\n10. Calculating composite score...")
    composite_scorer = CompositeScorer()

    composite_metrics = {
        'visibility_rate': visibility_summary.get('brand_visibility_rate', 0),
        'prominence_rate': visibility_summary.get('average_prominence', 0) * 10,  # Scale to 0-100
        'competitive_win_rate': h2h_results.get('overall_win_rate', 0),
        'citation_authority_score': citation_stats.get('citation_authority_score', 0),
        'positioning_quality_score': 70  # Default
    }

    scorecard = composite_scorer.create_full_scorecard(composite_metrics)

    print(f"   ✓ Overall Grade: {scorecard['letter_grade']} ({scorecard['composite_score']:.1f}/100)")
    print(f"   ✓ Status: {scorecard['grade_label']}")
    if scorecard['strengths']:
        print(f"   ✓ Strengths: {', '.join(scorecard['strengths'])}")
    if scorecard['weaknesses']:
        print(f"   ⚠ Weaknesses: {', '.join(scorecard['weaknesses'])}")

    # 11. GENERATE HTML REPORT
    print("\n11. Generating HTML report with competitive features...")
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

    print(f"   ✓ Report generated: {report_path}")

    # 12. PRINT SUMMARY
    print("\n" + "="*60)
    print("COMPETITIVE ANALYSIS SUMMARY")
    print("="*60)

    print(f"\n📊 Overall Grade: {scorecard['letter_grade']} ({scorecard['composite_score']:.0f}/100)")
    print(f"   Status: {scorecard['grade_label']}")

    print("\n📈 Score Breakdown:")
    for dim in scorecard['dimension_scores']:
        print(f"   • {dim['name']}: {dim['score']:.0f}/100 ({dim['grade']}) - {dim['contribution']:.0f} points")

    print(f"\n🥊 Competitive Battlecard:")
    for comp_data in h2h_results.get('battlecard', [])[:5]:
        status_emoji = {'winning': '✅', 'losing': '❌', 'tied': '⚖️'}.get(comp_data['status'], '❓')
        print(f"   {status_emoji} vs {comp_data['competitor']}: {comp_data['wins']}W-{comp_data['losses']}L-{comp_data['ties']}T ({comp_data['win_rate']:.0f}%)")

    print(f"\n📰 Citation Control:")
    print(f"   • Owned: {citation_stats['owned_percentage']:.0f}%")
    print(f"   • Third-party: {citation_stats['third_party_percentage']:.0f}%")
    print(f"   • Competitor: {citation_stats['competitor_percentage']:.0f}%")

    print("\n" + "="*60)
    print(f"✓ Full report: {report_path}")
    print("="*60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
