#!/usr/bin/env python3
"""
Website Content Verification Tool

Analyzes brand and competitor websites to verify actual content gaps
vs AI-perceived gaps.

Usage:
    python verify_websites.py --brand-config data/natasha_denona_brand_config.json
"""

import argparse
import json
import os
from src.analysis.website_analyzer import analyze_brand_and_competitors


def main():
    parser = argparse.ArgumentParser(
        description="Verify website content gaps by analyzing actual websites"
    )
    parser.add_argument(
        '--brand-config',
        required=True,
        help='Path to brand configuration JSON file'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=50,
        help='Maximum pages to crawl per website (default: 50)'
    )
    parser.add_argument(
        '--output',
        default='data/reports',
        help='Output directory for verification report (default: data/reports)'
    )

    args = parser.parse_args()

    # Load brand config
    if not os.path.exists(args.brand_config):
        print(f"❌ Error: Brand config file not found at {args.brand_config}")
        return

    with open(args.brand_config, 'r') as f:
        brand_config = json.load(f)

    # Extract URLs
    brand_name = brand_config['brand']['name']
    brand_url = brand_config['brand'].get('website')

    if not brand_url:
        print(f"❌ Error: No website URL found in brand config.")
        print("Please add 'website' field to brand config:")
        print('  "brand": {')
        print('    "name": "Your Brand",')
        print('    "website": "https://yourbrand.com"')
        print('  }')
        return

    # Get competitor URLs
    competitor_urls = []
    for comp in brand_config.get('competitors', []):
        if isinstance(comp, dict) and 'website' in comp:
            competitor_urls.append(comp['website'])
        elif isinstance(comp, str):
            print(f"⚠️  Warning: Competitor '{comp}' has no website URL in config")

    if not competitor_urls:
        print("⚠️  Warning: No competitor website URLs found in config.")
        print("Add website URLs to competitors:")
        print('  "competitors": [')
        print('    {"name": "Competitor Name", "website": "https://competitor.com"}')
        print('  ]')
        return

    print(f"\n🔍 Website Content Verification")
    print(f"  Brand: {brand_name} ({brand_url})")
    print(f"  Competitors: {len(competitor_urls)} websites")
    print(f"  Max pages per site: {args.max_pages}")
    print()

    # Run analysis
    try:
        results = analyze_brand_and_competitors(
            brand_url=brand_url,
            competitor_urls=competitor_urls,
            max_pages=args.max_pages
        )

        # Save detailed results
        os.makedirs(args.output, exist_ok=True)
        output_file = os.path.join(
            args.output,
            f'website_verification_{brand_name.replace(" ", "_")}.json'
        )

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Detailed results saved to: {output_file}")

        # Generate human-readable summary
        summary_file = os.path.join(
            args.output,
            f'website_verification_{brand_name.replace(" ", "_")}.txt'
        )

        with open(summary_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"WEBSITE CONTENT VERIFICATION - {brand_name}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {results['timestamp']}\n\n")

            f.write("YOUR WEBSITE CONTENT INVENTORY\n")
            f.write("-" * 80 + "\n")
            for content_type, data in results['brand_analysis']['summary'].items():
                status = "✓ EXISTS" if data['exists'] else "✗ MISSING"
                f.write(f"{content_type.replace('_', ' ').title()}: {status}")
                if data['exists']:
                    f.write(f" ({data['page_count']} pages)")
                f.write("\n")
                if data['example_urls']:
                    for url in data['example_urls'][:2]:
                        f.write(f"  - {url}\n")
            f.write("\n")

            f.write("VERIFIED CONTENT GAPS\n")
            f.write("-" * 80 + "\n")

            verified_gaps = results['comparison']['verified_gaps']
            if not verified_gaps:
                f.write("No verified gaps found! Your content coverage matches competitors.\n")
            else:
                for i, gap in enumerate(verified_gaps, 1):
                    if gap['status'] == 'verified_gap':
                        f.write(f"\n{i}. {gap['content_type'].replace('_', ' ').title()} [{gap['priority'].upper()}]\n")
                        f.write(f"   Status: MISSING from your site\n")
                        f.write(f"   Competitors with this: {gap['competitors_with']}/{gap['total_competitors']}\n")
                        f.write(f"   Recommendation: {gap['recommendation']}\n")
                        f.write("   Competitor examples:\n")
                        for comp in gap['competitor_examples']:
                            f.write(f"     - {comp['url']} ({comp['page_count']} pages)\n")
                            for ex_url in comp['examples'][:2]:
                                f.write(f"       → {ex_url}\n")

            f.write("\n")
            f.write("EXPANSION OPPORTUNITIES\n")
            f.write("-" * 80 + "\n")

            expansion_opps = [g for g in verified_gaps if g['status'] == 'expansion_opportunity']
            if not expansion_opps:
                f.write("None found.\n")
            else:
                for gap in expansion_opps:
                    f.write(f"\n• {gap['content_type'].replace('_', ' ').title()}\n")
                    f.write(f"  You have: {gap['brand_count']} pages\n")
                    f.write(f"  Competitors with more: {gap['competitors_with']}\n")
                    f.write(f"  Recommendation: {gap['recommendation']}\n")

            f.write("\n")
            f.write("FALSE POSITIVES (NOT REAL GAPS)\n")
            f.write("-" * 80 + "\n")

            false_positives = results['comparison']['false_positives']
            if not false_positives:
                f.write("None identified.\n")
            else:
                for fp in false_positives:
                    f.write(f"\n• {fp['content_type'].replace('_', ' ').title()}\n")
                    f.write(f"  Status: {fp['status'].replace('_', ' ').title()}\n")
                    f.write(f"  Reason: {fp['reason']}\n")
                    f.write(f"  Recommendation: {fp['recommendation']}\n")

        print(f"✓ Summary report saved to: {summary_file}")

        # Print key findings
        print("\n" + "=" * 80)
        print("KEY FINDINGS")
        print("=" * 80)

        verified = results['comparison']['verified_gap_count']
        expansion = results['comparison']['expansion_opportunity_count']

        print(f"\n✓ Verified Content Gaps: {verified}")
        if verified > 0:
            print("\nTop priorities:")
            for gap in results['comparison']['verified_gaps'][:3]:
                if gap['status'] == 'verified_gap':
                    print(f"  • {gap['content_type'].replace('_', ' ').title()} - {gap['competitors_with']} competitors have it")

        print(f"\n✓ Expansion Opportunities: {expansion}")
        if expansion > 0:
            print("\nAreas to expand:")
            for gap in [g for g in results['comparison']['verified_gaps'] if g['status'] == 'expansion_opportunity'][:3]:
                print(f"  • {gap['content_type'].replace('_', ' ').title()} - expand from {gap['brand_count']} pages")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
