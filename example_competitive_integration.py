#!/usr/bin/env python3
"""
Example integration of competitive features into existing visibility tracker.
This shows how to wire up the new analyzers with your existing workflow.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analysis.head_to_head_analyzer import HeadToHeadAnalyzer
from analysis.citation_classifier import CitationClassifier
from analysis.composite_scorer import CompositeScorer


def run_competitive_analysis(brand_name: str,
                             scored_results: list,
                             visibility_summary: dict,
                             brand_config: dict) -> dict:
    """
    Run all competitive analyses and return enhanced results.

    Args:
        brand_name: Your brand name
        scored_results: List of scored test results (from existing workflow)
        visibility_summary: Visibility summary stats (from existing workflow)
        brand_config: Brand configuration with domains and competitors

    Returns:
        Dictionary with all competitive analysis results
    """
    print("\n" + "="*60)
    print("Running Competitive Analysis Enhancements")
    print("="*60)

    # Extract configuration
    competitors = list(brand_config.get('competitors', {}).keys())
    brand_domains = brand_config.get('brand_domains', [])
    competitor_domains = {
        comp: config.get('domains', [])
        for comp, config in brand_config.get('competitors', {}).items()
    }

    # 1. HEAD-TO-HEAD ANALYSIS
    print("\n1. Analyzing head-to-head comparisons...")
    h2h_analyzer = HeadToHeadAnalyzer(
        brand_name=brand_name,
        competitor_names=competitors
    )
    h2h_results = h2h_analyzer.aggregate_head_to_head_results(scored_results)

    print(f"   ✓ Found {h2h_results['total_comparison_queries']} comparison queries")
    print(f"   ✓ Overall win rate: {h2h_results['overall_win_rate']}%")
    print(f"   ✓ Wins: {h2h_results['total_wins']}, Losses: {h2h_results['total_losses']}, Ties: {h2h_results['total_ties']}")

    # 2. CITATION CLASSIFICATION
    print("\n2. Classifying citations...")
    citation_classifier = CitationClassifier(
        brand_domains=brand_domains,
        competitor_domains=competitor_domains
    )
    citation_stats = citation_classifier.classify_all_sources(scored_results)
    citation_gaps = citation_classifier.get_citation_gap_analysis(
        scored_results,
        citation_stats
    )

    print(f"   ✓ Total citations analyzed: {citation_stats['total_citations']}")
    print(f"   ✓ Owned: {citation_stats['owned_percentage']}%")
    print(f"   ✓ Third-party: {citation_stats['third_party_percentage']}%")
    print(f"   ✓ Competitor: {citation_stats['competitor_percentage']}%")
    print(f"   ✓ Citation Authority Score: {citation_stats['citation_authority_score']}/100")

    # 3. COMPOSITE SCORING
    print("\n3. Calculating composite score...")
    composite_scorer = CompositeScorer()

    composite_metrics = {
        'visibility_rate': visibility_summary.get('brand_visibility_rate', 0),
        'prominence_rate': visibility_summary.get('average_prominence', 0),
        'competitive_win_rate': h2h_results.get('overall_win_rate', 0),
        'citation_authority_score': citation_stats.get('citation_authority_score', 0),
        'positioning_quality_score': 70  # Default - can be calculated separately
    }

    scorecard = composite_scorer.create_full_scorecard(composite_metrics)

    print(f"   ✓ Overall Grade: {scorecard['letter_grade']} ({scorecard['composite_score']}/100)")
    print(f"   ✓ Status: {scorecard['grade_label']}")
    print(f"   ✓ Strengths: {', '.join(scorecard['strengths']) if scorecard['strengths'] else 'None identified'}")
    print(f"   ✓ Weaknesses: {', '.join(scorecard['weaknesses']) if scorecard['weaknesses'] else 'None identified'}")

    # 4. PRINT COMPETITIVE BATTLECARD
    print("\n" + "="*60)
    print("COMPETITIVE BATTLECARD")
    print("="*60)

    for competitor_data in h2h_results.get('battlecard', [])[:5]:
        comp_name = competitor_data['competitor']
        wins = competitor_data['wins']
        losses = competitor_data['losses']
        ties = competitor_data['ties']
        status = competitor_data['status']
        win_rate = competitor_data['win_rate']

        status_emoji = {
            'winning': '✅',
            'losing': '❌',
            'tied': '⚖️'
        }.get(status, '❓')

        print(f"\n{status_emoji} {comp_name}")
        print(f"   You: {wins} wins | Them: {losses} losses | Tied: {ties}")
        print(f"   Win Rate: {win_rate}% | Status: {status.upper()}")

    # 5. CITATION INSIGHTS
    print("\n" + "="*60)
    print("CITATION INSIGHTS")
    print("="*60)

    print(f"\nNarrative Control:")
    print(f"  • {citation_stats['owned_percentage']:.0f}% of citations are YOUR content")
    print(f"  • {citation_stats['third_party_percentage']:.0f}% are third-party sites")
    print(f"  • {citation_stats['competitor_percentage']:.0f}% are competitor sites")

    print(f"\nTop Cited Domains:")
    for i, domain_data in enumerate(citation_stats.get('top_domains', [])[:5], 1):
        domain = domain_data['domain']
        count = domain_data['citations']
        dtype = domain_data['classification']
        print(f"  {i}. {domain} - {count} citations ({dtype})")

    # 6. RECOMMENDATIONS
    print("\n" + "="*60)
    print("KEY RECOMMENDATIONS")
    print("="*60)

    recommendations = []

    # Based on weaknesses
    if 'Competitive Win Rate' in scorecard['weaknesses']:
        recommendations.append({
            'priority': 'HIGH',
            'area': 'Competitive Positioning',
            'action': 'Create comparison content highlighting your advantages vs top competitors',
            'competitors': [b['competitor'] for b in h2h_results['battlecard'][:3] if b['status'] == 'losing']
        })

    if 'Visibility' in scorecard['weaknesses']:
        recommendations.append({
            'priority': 'HIGH',
            'area': 'Content Production',
            'action': 'Increase content covering high-value buyer queries where you\'re absent'
        })

    # Based on citation gaps
    if citation_stats['third_party_percentage'] > 50:
        recommendations.append({
            'priority': 'MEDIUM',
            'area': 'Citation Building',
            'action': f'Build owned content - third parties control {citation_stats["third_party_percentage"]:.0f}% of your narrative',
            'goal': 'Target 50%+ owned citations'
        })

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. [{rec['priority']}] {rec['area']}")
        print(f"   → {rec['action']}")
        if 'goal' in rec:
            print(f"   → Goal: {rec['goal']}")
        if 'competitors' in rec and rec['competitors']:
            print(f"   → Focus on: {', '.join(rec['competitors'])}")

    print("\n" + "="*60)

    # Return all results for report generation
    return {
        'composite_scorecard': scorecard,
        'head_to_head_results': h2h_results,
        'citation_stats': citation_stats,
        'citation_gaps': citation_gaps,
        'recommendations': recommendations
    }


def example_usage():
    """Example showing how to use the competitive analysis."""

    # Example brand configuration
    brand_config = {
        'brand_name': 'Growclass',
        'brand_domains': ['growclass.co', 'learning.growclass.co'],
        'competitors': {
            'Reforge': {
                'domains': ['reforge.com']
            },
            'CXL': {
                'domains': ['cxl.com']
            },
            'Demand Curve': {
                'domains': ['demandcurve.com']
            }
        }
    }

    # Example visibility summary (from your existing workflow)
    visibility_summary = {
        'brand_visibility_rate': 75.0,
        'average_prominence': 2.3,
        'share_of_voice': 38.0
    }

    # Example scored results (from your existing workflow)
    # In real usage, this would be your actual scored_results list
    scored_results = []  # Your actual results here

    print("="*60)
    print("Competitive Analysis Integration Example")
    print("="*60)
    print("\nThis example shows how to integrate the new competitive")
    print("features into your existing visibility tracking workflow.")
    print("\nIn practice, you would:")
    print("1. Run your existing visibility tests (main.py)")
    print("2. Get scored_results and visibility_summary")
    print("3. Pass them to run_competitive_analysis()")
    print("4. Add results to your HTML report")
    print("\nFor a real demo, add this to your main.py after scoring:")
    print("\ncompetitive_results = run_competitive_analysis(")
    print("    brand_name=brand_name,")
    print("    scored_results=scored_results,")
    print("    visibility_summary=visibility_summary,")
    print("    brand_config=load_brand_config()")
    print(")")
    print("\n" + "="*60)


if __name__ == '__main__':
    example_usage()
