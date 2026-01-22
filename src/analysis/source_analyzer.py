"""
Source analyzer for understanding where brands are being mentioned.

Identifies which third-party sites (Sephora, Reddit, beauty blogs, etc.)
are citing which brands, revealing opportunities for outreach and visibility improvement.
"""

from collections import defaultdict
from typing import Dict, List, Any


class SourceAnalyzer:
    """Analyzes which sources drive brand mentions in AI responses."""

    def analyze_sources(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze which sources mention which brands.

        This reveals:
        - Top sources overall
        - Sources that mention your brand
        - Sources that mention competitors but not you (targeting opportunities)
        - Recommended sources for outreach

        Args:
            scored_results: List of scored visibility results

        Returns:
            Dictionary with source analysis including:
            - all_sources: Complete list of sources with stats
            - sources_with_your_brand: Sources mentioning your brand
            - sources_with_competitors_only: Gap opportunities
            - recommended_targets: Top sources to target for outreach
        """
        if not scored_results:
            return {
                'all_sources': [],
                'sources_with_your_brand': [],
                'sources_with_competitors_only': [],
                'recommended_targets': []
            }

        # Collect source statistics
        source_stats = defaultdict(lambda: {
            'total_mentions': 0,
            'brand_mentions': 0,
            'competitor_mentions': defaultdict(int),
            'example_urls': [],
            'example_attributions': []
        })

        for result in scored_results:
            sources = result.get('visibility', {}).get('sources', [])
            visibility = result.get('visibility', {})

            brand_mentioned = visibility.get('brand_mentioned', False)
            competitors = visibility.get('competitors_mentioned', [])

            for source in sources:
                # Get source key (domain or name)
                source_key = source.get('domain') or source.get('source_name')
                if not source_key:
                    continue

                stats = source_stats[source_key]
                stats['total_mentions'] += 1

                # Track brand mentions
                if brand_mentioned:
                    stats['brand_mentions'] += 1

                # Track competitor mentions
                for comp in competitors:
                    stats['competitor_mentions'][comp] += 1

                # Store example URLs (max 3 per source)
                if source.get('full_url') and len(stats['example_urls']) < 3:
                    stats['example_urls'].append(source['full_url'])

                # Store example attributions (max 3 per source)
                if source.get('type') == 'attribution' and len(stats['example_attributions']) < 3:
                    context = result.get('visibility', {}).get('context_snippets', [])
                    if context:
                        stats['example_attributions'].append(context[0])

        # Calculate metrics for each source
        sources_list = []
        for source_name, stats in source_stats.items():
            total = stats['total_mentions']
            brand_mentions = stats['brand_mentions']

            # Calculate brand mention rate
            brand_rate = (brand_mentions / total * 100) if total > 0 else 0

            # Find top competitor mentioned at this source
            top_competitor = None
            top_competitor_count = 0
            if stats['competitor_mentions']:
                top_competitor, top_competitor_count = max(
                    stats['competitor_mentions'].items(),
                    key=lambda x: x[1]
                )

            # Total competitor mentions
            total_competitor_mentions = sum(stats['competitor_mentions'].values())
            competitor_rate = (total_competitor_mentions / total * 100) if total > 0 else 0

            # Should we target this source? (competitors appear but we don't)
            should_target = total_competitor_mentions > 0 and brand_mentions == 0

            sources_list.append({
                'source': source_name,
                'total_appearances': total,
                'mentions_your_brand': brand_mentions,
                'brand_mention_rate': round(brand_rate, 1),
                'top_competitor': top_competitor,
                'top_competitor_mentions': top_competitor_count,
                'competitor_count': total_competitor_mentions,
                'competitor_rate': round(competitor_rate, 1),
                'example_urls': stats['example_urls'],
                'example_attributions': stats['example_attributions'],
                'should_target': should_target,
                'opportunity_score': self._calculate_opportunity_score(
                    total, brand_mentions, total_competitor_mentions
                )
            })

        # Sort by total appearances (most influential sources first)
        sources_list.sort(key=lambda x: x['total_appearances'], reverse=True)

        # Create filtered lists
        sources_with_brand = [s for s in sources_list if s['mentions_your_brand'] > 0]
        sources_with_competitors_only = [s for s in sources_list if s['should_target']]

        # Recommended targets: sort by opportunity score
        recommended_targets = sorted(
            sources_with_competitors_only,
            key=lambda x: x['opportunity_score'],
            reverse=True
        )[:10]

        return {
            'all_sources': sources_list,
            'sources_with_your_brand': sources_with_brand,
            'sources_with_competitors_only': sources_with_competitors_only,
            'recommended_targets': recommended_targets,
            'total_unique_sources': len(sources_list),
            'sources_mentioning_brand': len(sources_with_brand),
            'gap_opportunities': len(sources_with_competitors_only)
        }

    def _calculate_opportunity_score(self, total_appearances: int,
                                     brand_mentions: int,
                                     competitor_mentions: int) -> float:
        """
        Calculate opportunity score for a source (0-100).

        Higher score = better opportunity for outreach.

        Factors:
        - High total appearances (influential source)
        - High competitor mentions (they're getting featured)
        - Low/zero brand mentions (gap to fill)

        Args:
            total_appearances: Total times source appeared
            brand_mentions: Times your brand was mentioned
            competitor_mentions: Times competitors were mentioned

        Returns:
            Opportunity score from 0-100
        """
        if total_appearances == 0:
            return 0.0

        score = 0.0

        # Weight for influence (total appearances)
        # Max 40 points for being a frequently-cited source
        influence_score = min(40, total_appearances * 4)
        score += influence_score

        # Weight for competitor presence
        # Max 40 points if competitors are heavily featured
        competitor_score = min(40, competitor_mentions * 4)
        score += competitor_score

        # Penalty for existing brand presence (we want gaps)
        # -50 points if you're already mentioned
        if brand_mentions > 0:
            score -= 50

        # Bonus if it's a complete gap (competitors but not you)
        if competitor_mentions > 0 and brand_mentions == 0:
            score += 20

        return max(0.0, min(100.0, score))

    def get_source_summary(self, source_analysis: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of source analysis.

        Args:
            source_analysis: Result from analyze_sources()

        Returns:
            Formatted text summary
        """
        summary_lines = []

        total_sources = source_analysis.get('total_unique_sources', 0)
        brand_sources = source_analysis.get('sources_mentioning_brand', 0)
        gap_opportunities = source_analysis.get('gap_opportunities', 0)

        summary_lines.append(f"=== SOURCE ANALYSIS SUMMARY ===\n")
        summary_lines.append(f"Total unique sources found: {total_sources}")
        summary_lines.append(f"Sources mentioning your brand: {brand_sources}")
        summary_lines.append(f"Gap opportunities (competitors only): {gap_opportunities}\n")

        # Top sources with your brand
        sources_with_brand = source_analysis.get('sources_with_your_brand', [])
        if sources_with_brand:
            summary_lines.append("Top sources mentioning your brand:")
            for i, source in enumerate(sources_with_brand[:5], 1):
                rate = source['brand_mention_rate']
                total = source['total_appearances']
                summary_lines.append(
                    f"  {i}. {source['source']} - {rate}% brand mention rate "
                    f"({source['mentions_your_brand']}/{total} appearances)"
                )
            summary_lines.append("")

        # Recommended targets
        targets = source_analysis.get('recommended_targets', [])
        if targets:
            summary_lines.append("TOP TARGETS FOR OUTREACH:")
            for i, target in enumerate(targets[:10], 1):
                summary_lines.append(
                    f"\n  {i}. {target['source']}"
                )
                summary_lines.append(
                    f"     Your brand: {target['mentions_your_brand']} mentions "
                    f"({target['brand_mention_rate']}%)"
                )
                summary_lines.append(
                    f"     Competitors: {target['competitor_count']} mentions "
                    f"({target['competitor_rate']}%)"
                )
                if target['top_competitor']:
                    summary_lines.append(
                        f"     Top competitor: {target['top_competitor']} "
                        f"({target['top_competitor_mentions']} mentions)"
                    )
                if target['example_urls']:
                    summary_lines.append(f"     Example: {target['example_urls'][0]}")
                summary_lines.append(
                    f"     Opportunity Score: {target['opportunity_score']:.0f}/100"
                )

        return "\n".join(summary_lines)

    def export_to_csv_data(self, source_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Prepare source data for CSV export.

        Args:
            source_analysis: Result from analyze_sources()

        Returns:
            List of dictionaries ready for CSV writing
        """
        csv_data = []

        for source in source_analysis.get('all_sources', []):
            csv_data.append({
                'Source': source['source'],
                'Total Appearances': source['total_appearances'],
                'Your Brand Mentions': source['mentions_your_brand'],
                'Your Brand %': f"{source['brand_mention_rate']}%",
                'Top Competitor': source.get('top_competitor', ''),
                'Competitor Mentions': source['competitor_count'],
                'Competitor %': f"{source['competitor_rate']}%",
                'Should Target': 'YES' if source['should_target'] else 'No',
                'Opportunity Score': f"{source['opportunity_score']:.0f}",
                'Example URLs': '; '.join(source['example_urls'])
            })

        return csv_data
