#!/usr/bin/env python3
"""
Save Historical Data Script

Run this after completing CLI tests to save monthly metrics to historical tracking.
This allows you to track visibility trends over time.

Usage:
    python save_historical_data.py --client "Client Name" --report path/to/report.html

The script will extract metrics from the HTML report and save them to monthly_scores.json
"""

import argparse
import sys
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

# Add src to path
sys.path.insert(0, 'src')

from tracking.historical_tracker import HistoricalTracker


def extract_metrics_from_html(html_path: Path) -> dict:
    """
    Extract visibility metrics from HTML report.

    Args:
        html_path: Path to HTML report file

    Returns:
        Dict with visibility metrics
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    metrics = {}

    # Try to find metrics in the HTML
    # This is a simple parser - adjust based on your actual HTML structure
    text = soup.get_text()

    # Extract visibility rate
    visibility_match = re.search(r'Visibility Rate:\s*(\d+\.?\d*)%', text, re.IGNORECASE)
    if visibility_match:
        metrics['brand_visibility_rate'] = float(visibility_match.group(1))

    # Extract prominence/position
    position_match = re.search(r'Average.*Position:\s*(\d+\.?\d*)', text, re.IGNORECASE)
    if position_match:
        metrics['average_citation_position'] = float(position_match.group(1))

    # Extract mention counts
    brand_mentions_match = re.search(r'Brand Mentions:\s*(\d+)', text, re.IGNORECASE)
    if brand_mentions_match:
        metrics['brand_mentions'] = int(brand_mentions_match.group(1))

    competitor_mentions_match = re.search(r'Competitor Mentions:\s*(\d+)', text, re.IGNORECASE)
    if competitor_mentions_match:
        metrics['total_competitor_mentions'] = int(competitor_mentions_match.group(1))

    total_prompts_match = re.search(r'Total Prompts.*?:\s*(\d+)', text, re.IGNORECASE)
    if total_prompts_match:
        metrics['total_prompts_tested'] = int(total_prompts_match.group(1))

    return metrics


def main():
    parser = argparse.ArgumentParser(
        description='Save historical visibility data from test results'
    )
    parser.add_argument(
        '--client',
        required=True,
        help='Client name (e.g., "Natasha Denona")'
    )
    parser.add_argument(
        '--report',
        required=False,
        help='Path to HTML report (auto-detects if not provided)'
    )
    parser.add_argument(
        '--month',
        required=False,
        help='Month to save data for (YYYY-MM), defaults to current month'
    )
    parser.add_argument(
        '--visibility-rate',
        type=float,
        help='Manual visibility rate (%%)'
    )
    parser.add_argument(
        '--prominence',
        type=float,
        help='Manual prominence rate (average position)'
    )
    parser.add_argument(
        '--brand-mentions',
        type=int,
        help='Manual brand mention count'
    )
    parser.add_argument(
        '--competitor-mentions',
        type=int,
        help='Manual competitor mention count'
    )
    parser.add_argument(
        '--total-prompts',
        type=int,
        help='Manual total prompt count'
    )

    args = parser.parse_args()

    # Initialize historical tracker
    tracker = HistoricalTracker()

    # Get metrics - either from HTML report or manual input
    if args.report:
        report_path = Path(args.report)
        if not report_path.exists():
            print(f"❌ Error: Report file not found: {args.report}")
            sys.exit(1)

        print(f"📊 Extracting metrics from {args.report}...")
        metrics = extract_metrics_from_html(report_path)

    elif (args.visibility_rate is not None and args.prominence is not None and
          args.brand_mentions is not None and args.competitor_mentions is not None):
        # Manual input
        metrics = {
            'brand_visibility_rate': args.visibility_rate,
            'average_citation_position': args.prominence,
            'brand_mentions': args.brand_mentions,
            'total_competitor_mentions': args.competitor_mentions,
            'total_prompts_tested': args.total_prompts or (args.brand_mentions + args.competitor_mentions)
        }
    else:
        # Auto-detect report path
        client_slug = args.client.lower().replace(' ', '_')
        auto_report_path = Path(f'data/reports/visibility_report_{client_slug}.html')

        if auto_report_path.exists():
            print(f"📊 Found report: {auto_report_path}")
            print(f"📊 Extracting metrics...")
            metrics = extract_metrics_from_html(auto_report_path)
        else:
            print(f"❌ Error: Could not find report at {auto_report_path}")
            print(f"   Please provide metrics manually or specify --report path")
            sys.exit(1)

    if not metrics:
        print("❌ Error: Could not extract metrics from report")
        print("   Try providing metrics manually with --visibility-rate, --prominence, etc.")
        sys.exit(1)

    # Display metrics
    print(f"\n✅ Extracted Metrics for {args.client}:")
    print(f"   Visibility Rate: {metrics.get('brand_visibility_rate', 'N/A')}%")
    print(f"   Prominence: Position #{metrics.get('average_citation_position', 'N/A')}")
    print(f"   Brand Mentions: {metrics.get('brand_mentions', 'N/A')}")
    print(f"   Competitor Mentions: {metrics.get('total_competitor_mentions', 'N/A')}")
    print(f"   Total Prompts: {metrics.get('total_prompts_tested', 'N/A')}")

    # Calculate share of voice
    brand_mentions = metrics.get('brand_mentions', 0)
    competitor_mentions = metrics.get('total_competitor_mentions', 0)
    if brand_mentions + competitor_mentions > 0:
        sov = (brand_mentions / (brand_mentions + competitor_mentions)) * 100
        print(f"   Share of Voice: {sov:.1f}%")

    # Save to historical tracker
    print(f"\n💾 Saving to historical tracking...")
    tracker.save_monthly_scores(
        client_name=args.client,
        visibility_summary=metrics,
        month=args.month
    )

    month = args.month or tracker.get_all_months(args.client)[-1]
    print(f"✅ Saved historical data for {args.client} - {month}")
    print(f"\n📈 View trends in the dashboard: Historical Trends page")


if __name__ == '__main__':
    main()
