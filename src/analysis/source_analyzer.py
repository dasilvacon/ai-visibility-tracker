"""
Source analyzer for understanding where brands are being mentioned.

Identifies which third-party sites are citing which brands,
revealing opportunities for outreach and visibility improvement.
Uses enriched source data with context snippets for accurate co-mention tracking.
"""

import json
from collections import defaultdict
from typing import Dict, List, Any, Optional


class SourceAnalyzer:
    """Analyzes which sources drive brand mentions in AI responses."""

    def analyze_sources(self, scored_results: List[Dict[str, Any]],
                       brand_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze which sources mention which brands using enriched source data.

        Uses the new context-aware source data to determine actual co-mentions
        (brand appearing IN THE SAME CONTEXT as the source), not just in the same response.

        Args:
            scored_results: List of scored visibility results
            brand_config: Client's brand config with known_sources, source_categories,
                         and irrelevant_sources

        Returns:
            Dictionary with source analysis including:
            - all_sources: Complete list of sources with detailed stats
            - sources_with_brand_co_mentions: Sources where brand appears in context
            - gap_opportunities: Sources with competitors but no brand co-mention
            - recommended_targets: Top sources to target for outreach
        """
        if not scored_results:
            return {
                'all_sources': [],
                'sources_with_brand_co_mentions': [],
                'gap_opportunities': [],
                'recommended_targets': [],
                'total_unique_sources': 0,
                'sources_with_brand_co_mentions_count': 0,
                'gap_opportunities_count': 0
            }

        # Load config data
        known_sources = set()
        source_categories = {}
        irrelevant_sources = set()

        if brand_config:
            known_sources = set(s.lower() for s in brand_config.get('known_sources', []))
            source_categories = brand_config.get('source_categories', {})
            irrelevant_sources = set(s.lower() for s in brand_config.get('irrelevant_sources', []))

        # Build reverse lookup for source_categories
        category_lookup = {}
        for category, sources in source_categories.items():
            for source in sources:
                category_lookup[source.lower()] = category

        # Collect source statistics
        source_stats = defaultdict(lambda: {
            'total_appearances': 0,
            'brand_co_mentions': 0,
            'competitor_co_mentions': defaultdict(int),
            'positions': [],
            'prompt_ids': [],
            'context_samples': [],
            'brand_context_samples': [],
            'example_urls': []
        })

        for result in scored_results:
            sources = result.get('visibility', {}).get('sources', [])
            prompt_id = result.get('prompt_id', '')

            for source in sources:
                # Get source key (domain)
                source_key = source.get('domain', '').lower()
                if not source_key:
                    continue

                # Skip irrelevant sources
                if source_key in irrelevant_sources:
                    continue

                stats = source_stats[source_key]
                stats['total_appearances'] += 1

                # Track brand co-mentions (using enriched context data)
                if source.get('brand_in_context', False):
                    stats['brand_co_mentions'] += 1
                    # Prioritize brand context samples
                    if len(stats['brand_context_samples']) < 5:
                        snippet = source.get('context_snippet', '')
                        if snippet:
                            stats['brand_context_samples'].append(snippet)

                # Track competitor co-mentions (using enriched context data)
                for comp in source.get('competitors_in_context', []):
                    stats['competitor_co_mentions'][comp] += 1

                # Track position in response
                position = source.get('position_in_response')
                if position is not None:
                    stats['positions'].append(position)

                # Track prompt IDs for drill-down
                if prompt_id and prompt_id not in stats['prompt_ids']:
                    stats['prompt_ids'].append(prompt_id)

                # Store context samples (prioritize brand context)
                if len(stats['context_samples']) < 5:
                    snippet = source.get('context_snippet', '')
                    if snippet:
                        stats['context_samples'].append(snippet)

                # Store example URLs
                if source.get('full_url') and len(stats['example_urls']) < 3:
                    stats['example_urls'].append(source['full_url'])

        # Calculate metrics for each source
        sources_list = []
        for source_domain, stats in source_stats.items():
            total = stats['total_appearances']
            brand_co_mentions = stats['brand_co_mentions']

            # Calculate brand co-mention rate
            brand_co_mention_rate = (brand_co_mentions / total * 100) if total > 0 else 0

            # Find top competitor at this source
            top_competitor = None
            top_competitor_count = 0
            if stats['competitor_co_mentions']:
                top_competitor, top_competitor_count = max(
                    stats['competitor_co_mentions'].items(),
                    key=lambda x: x[1]
                )

            # Total competitor co-mentions
            total_competitor_co_mentions = sum(stats['competitor_co_mentions'].values())

            # Calculate average position (lower = earlier = more authoritative)
            avg_position = (sum(stats['positions']) / len(stats['positions'])) if stats['positions'] else 0.5

            # Determine source category
            source_category = category_lookup.get(source_domain, 'uncategorized')

            # Check if it's a known source
            is_known_source = source_domain in known_sources or any(
                source_domain.endswith(ks) or ks in source_domain
                for ks in known_sources
            )

            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(
                is_known_source=is_known_source,
                has_category=(source_category != 'uncategorized'),
                brand_co_mention_rate=brand_co_mention_rate,
                avg_position=avg_position,
                total_appearances=total
            )

            # Use brand context samples first, then regular context samples
            context_samples = stats['brand_context_samples']
            if len(context_samples) < 5:
                for sample in stats['context_samples']:
                    if sample not in context_samples and len(context_samples) < 5:
                        context_samples.append(sample)

            sources_list.append({
                'source': source_domain,
                'domain': source_domain,
                'total_appearances': total,
                'brand_co_mentions': brand_co_mentions,
                'brand_co_mention_rate': round(brand_co_mention_rate, 1),
                'competitor_co_mentions': dict(stats['competitor_co_mentions']),
                'top_competitor': top_competitor,
                'top_competitor_count': top_competitor_count,
                'avg_position': round(avg_position, 3),
                'prompt_ids': stats['prompt_ids'],
                'context_samples': context_samples,
                'example_urls': stats['example_urls'],
                'source_category': source_category,
                'relevance_score': relevance_score,
                # Legacy fields for backwards compatibility
                'mentions_your_brand': brand_co_mentions,
                'brand_mention_rate': round(brand_co_mention_rate, 1),
                'competitor_count': total_competitor_co_mentions,
                'competitor_rate': round((total_competitor_co_mentions / total * 100) if total > 0 else 0, 1),
                'should_target': total_competitor_co_mentions > 0 and brand_co_mentions == 0,
                'opportunity_score': self._calculate_opportunity_score(
                    total, brand_co_mentions, total_competitor_co_mentions
                )
            })

        # Sort by relevance score (most relevant first)
        sources_list.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Create filtered lists
        sources_with_brand_co_mentions = [s for s in sources_list if s['brand_co_mentions'] > 0]

        # Gap opportunities: relevant sources with competitors but no brand
        gap_opportunities = [
            s for s in sources_list
            if s['should_target'] and s['relevance_score'] > 30
        ]
        gap_opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)

        # Recommended targets: top gap opportunities
        recommended_targets = gap_opportunities[:10]

        return {
            'all_sources': sources_list,
            'sources_with_brand_co_mentions': sources_with_brand_co_mentions,
            'sources_with_your_brand': sources_with_brand_co_mentions,  # Legacy alias
            'gap_opportunities': gap_opportunities,
            'sources_with_competitors_only': gap_opportunities,  # Legacy alias
            'recommended_targets': recommended_targets,
            'total_unique_sources': len(sources_list),
            'sources_with_brand_co_mentions_count': len(sources_with_brand_co_mentions),
            'sources_mentioning_brand': len(sources_with_brand_co_mentions),  # Legacy alias
            'gap_opportunities_count': len(gap_opportunities)
        }

    def _calculate_relevance_score(self, is_known_source: bool,
                                   has_category: bool,
                                   brand_co_mention_rate: float,
                                   avg_position: float,
                                   total_appearances: int) -> int:
        """
        Calculate relevance score for a source (0-100).

        Based on:
        - Is it in the client's known_sources? (+30)
        - Is it in the client's source_categories? (+20)
        - brand_co_mention_rate > 0? (+25)
        - avg_position < 0.3 (cited early)? (+15)
        - total_appearances > 3? (+10)

        Args:
            is_known_source: Whether source is in known_sources
            has_category: Whether source has a category
            brand_co_mention_rate: Rate of brand co-mentions
            avg_position: Average position in response
            total_appearances: Total times source appeared

        Returns:
            Relevance score from 0-100
        """
        score = 0

        if is_known_source:
            score += 30

        if has_category:
            score += 20

        if brand_co_mention_rate > 0:
            score += 25

        if avg_position < 0.3:
            score += 15

        if total_appearances > 3:
            score += 10

        return min(100, score)

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

    def flag_irrelevant_source(self, source_domain: str,
                               brand_config_path: str) -> bool:
        """
        Flag a source as irrelevant by adding it to the client's brand_config.json.

        Args:
            source_domain: The domain to flag as irrelevant
            brand_config_path: Path to the client's brand_config.json

        Returns:
            True if successfully flagged, False otherwise
        """
        try:
            with open(brand_config_path, 'r') as f:
                config = json.load(f)

            # Initialize irrelevant_sources if not present
            if 'irrelevant_sources' not in config:
                config['irrelevant_sources'] = []

            # Add source if not already present
            source_lower = source_domain.lower()
            if source_lower not in config['irrelevant_sources']:
                config['irrelevant_sources'].append(source_lower)

            # Save updated config
            with open(brand_config_path, 'w') as f:
                json.dump(config, f, indent=2)

            return True
        except Exception as e:
            print(f"Error flagging irrelevant source: {e}")
            return False

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
        brand_sources = source_analysis.get('sources_with_brand_co_mentions_count', 0)
        gap_opportunities = source_analysis.get('gap_opportunities_count', 0)

        summary_lines.append("=== SOURCE ANALYSIS SUMMARY ===\n")
        summary_lines.append(f"Total unique sources found: {total_sources}")
        summary_lines.append(f"Sources with brand co-mentions: {brand_sources}")
        summary_lines.append(f"Gap opportunities: {gap_opportunities}\n")

        # Top sources with your brand
        sources_with_brand = source_analysis.get('sources_with_brand_co_mentions', [])
        if sources_with_brand:
            summary_lines.append("Top sources with brand co-mentions:")
            for i, source in enumerate(sources_with_brand[:5], 1):
                rate = source['brand_co_mention_rate']
                total = source['total_appearances']
                category = source.get('source_category', 'uncategorized')
                summary_lines.append(
                    f"  {i}. {source['source']} [{category}] - {rate}% co-mention rate "
                    f"({source['brand_co_mentions']}/{total} appearances)"
                )
            summary_lines.append("")

        # Recommended targets
        targets = source_analysis.get('recommended_targets', [])
        if targets:
            summary_lines.append("TOP TARGETS FOR OUTREACH:")
            for i, target in enumerate(targets[:10], 1):
                category = target.get('source_category', 'uncategorized')
                summary_lines.append(
                    f"\n  {i}. {target['source']} [{category}]"
                )
                summary_lines.append(
                    f"     Relevance: {target['relevance_score']}/100"
                )
                summary_lines.append(
                    f"     Your brand: {target['brand_co_mentions']} co-mentions "
                    f"({target['brand_co_mention_rate']}%)"
                )
                summary_lines.append(
                    f"     Competitors: {target['competitor_count']} co-mentions"
                )
                if target['top_competitor']:
                    summary_lines.append(
                        f"     Top competitor: {target['top_competitor']} "
                        f"({target['top_competitor_count']} co-mentions)"
                    )
                if target['example_urls']:
                    summary_lines.append(f"     Example: {target['example_urls'][0]}")

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
                'Category': source.get('source_category', 'uncategorized'),
                'Total Appearances': source['total_appearances'],
                'Brand Co-mentions': source['brand_co_mentions'],
                'Brand Co-mention %': f"{source['brand_co_mention_rate']}%",
                'Top Competitor': source.get('top_competitor', ''),
                'Competitor Co-mentions': source.get('competitor_count', 0),
                'Avg Position': source.get('avg_position', 0),
                'Relevance Score': source['relevance_score'],
                'Opportunity Score': f"{source['opportunity_score']:.0f}",
                'Should Target': 'YES' if source['should_target'] else 'No',
                'Example URLs': '; '.join(source['example_urls'])
            })

        return csv_data
