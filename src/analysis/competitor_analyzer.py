"""
Competitor analyzer for comparing brand visibility vs competitors.
"""

from typing import Dict, List, Any, Set
from collections import defaultdict
import re


class CompetitorAnalyzer:
    """Analyzes brand performance relative to competitors."""

    def __init__(self, brand_name: str):
        """
        Initialize the competitor analyzer.

        Args:
            brand_name: Primary brand name
        """
        self.brand_name = brand_name

    def analyze_competitive_landscape(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze competitive landscape across all results.

        Args:
            scored_results: List of results with visibility scores

        Returns:
            Dictionary with competitive analysis
        """
        total_results = len(scored_results)
        if total_results == 0:
            return {'error': 'No results to analyze'}

        # Track competitor mentions
        competitor_stats = defaultdict(lambda: {
            'mention_count': 0,
            'co_mention_with_brand': 0,
            'mentioned_before_brand': 0,
            'mentioned_alone': 0
        })

        brand_only = 0
        brand_with_competitors = 0
        competitors_only = 0
        none_mentioned = 0

        for result in scored_results:
            visibility = result.get('visibility', {})
            brand_mentioned = visibility.get('brand_mentioned', False)
            competitors = visibility.get('competitors_mentioned', [])
            competitor_details = visibility.get('competitor_details', {})

            # Categorize this result
            if brand_mentioned and not competitors:
                brand_only += 1
            elif brand_mentioned and competitors:
                brand_with_competitors += 1
            elif not brand_mentioned and competitors:
                competitors_only += 1
            elif not brand_mentioned and not competitors:
                none_mentioned += 1

            # Track each competitor
            for comp in competitors:
                competitor_stats[comp]['mention_count'] += 1

                if brand_mentioned:
                    competitor_stats[comp]['co_mention_with_brand'] += 1

                    # Check if competitor was mentioned before brand
                    comp_pos = competitor_details[comp]['positions'][0]
                    brand_pos = visibility.get('citation_position')
                    if comp_pos and brand_pos and comp_pos < brand_pos:
                        competitor_stats[comp]['mentioned_before_brand'] += 1
                else:
                    competitor_stats[comp]['mentioned_alone'] += 1

        # Calculate competitive metrics
        competitive_metrics = {
            'total_prompts': total_results,
            'brand_only_mentions': brand_only,
            'brand_with_competitors': brand_with_competitors,
            'competitors_only': competitors_only,
            'none_mentioned': none_mentioned,
            'brand_share_of_voice': (brand_only + brand_with_competitors) / total_results * 100,
            'competitor_stats': dict(competitor_stats)
        }

        # Rank competitors by dominance
        ranked_competitors = sorted(
            competitor_stats.items(),
            key=lambda x: x[1]['mention_count'],
            reverse=True
        )

        competitive_metrics['top_competitors'] = [
            {
                'name': comp,
                'mentions': stats['mention_count'],
                'mention_rate': stats['mention_count'] / total_results * 100,
                'dominance_score': self._calculate_dominance_score(stats, total_results)
            }
            for comp, stats in ranked_competitors[:5]
        ]

        return competitive_metrics

    def _calculate_dominance_score(self, competitor_stats: Dict[str, int],
                                   total_results: int) -> float:
        """
        Calculate competitor dominance score.

        Args:
            competitor_stats: Statistics for a competitor
            total_results: Total number of results

        Returns:
            Dominance score (0-100)
        """
        # Weight different factors
        mention_score = (competitor_stats['mention_count'] / total_results) * 40
        alone_score = (competitor_stats['mentioned_alone'] / max(total_results, 1)) * 30
        first_score = (competitor_stats['mentioned_before_brand'] / max(total_results, 1)) * 30

        return round(mention_score + alone_score + first_score, 1)

    def compare_by_dimension(self, scored_results: List[Dict[str, Any]],
                            dimension: str) -> Dict[str, Any]:
        """
        Compare brand vs competitors by a specific dimension.

        Args:
            scored_results: List of results with visibility scores
            dimension: Dimension to compare by (persona, platform, category, intent_type)

        Returns:
            Dictionary with comparison data
        """
        dimension_stats = defaultdict(lambda: {
            'brand_mentions': 0,
            'competitor_mentions': 0,
            'total': 0,
            'brand_rate': 0.0
        })

        for result in scored_results:
            # Get dimension value
            dim_value = result.get('metadata', {}).get(dimension) or result.get(dimension, 'Unknown')

            visibility = result.get('visibility', {})
            brand_mentioned = visibility.get('brand_mentioned', False)
            has_competitors = len(visibility.get('competitors_mentioned', [])) > 0

            dimension_stats[dim_value]['total'] += 1
            if brand_mentioned:
                dimension_stats[dim_value]['brand_mentions'] += 1
            if has_competitors:
                dimension_stats[dim_value]['competitor_mentions'] += 1

        # Calculate rates
        for dim_value, stats in dimension_stats.items():
            if stats['total'] > 0:
                stats['brand_rate'] = (stats['brand_mentions'] / stats['total']) * 100

        # Sort by brand_rate descending
        sorted_dims = sorted(
            dimension_stats.items(),
            key=lambda x: x[1]['brand_rate'],
            reverse=True
        )

        return {
            'dimension': dimension,
            'breakdown': dict(sorted_dims),
            'best_performing': sorted_dims[0] if sorted_dims else None,
            'worst_performing': sorted_dims[-1] if sorted_dims else None
        }

    def identify_competitive_gaps(self, scored_results: List[Dict[str, Any]],
                                  threshold: float = 50.0) -> List[Dict[str, Any]]:
        """
        Identify areas where competitors dominate over brand.

        Args:
            scored_results: List of results with visibility scores
            threshold: Minimum competitor dominance % to flag as gap

        Returns:
            List of competitive gap opportunities
        """
        # Analyze by persona
        persona_analysis = self.compare_by_dimension(scored_results, 'persona')

        # Analyze by category
        category_analysis = self.compare_by_dimension(scored_results, 'category')

        # Analyze by intent
        intent_analysis = self.compare_by_dimension(scored_results, 'intent_type')

        gaps = []

        # Find gaps in personas
        for persona, stats in persona_analysis['breakdown']:
            competitor_rate = (stats['competitor_mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
            brand_rate = stats['brand_rate']

            if competitor_rate > threshold and brand_rate < 50:
                gaps.append({
                    'type': 'persona',
                    'value': persona,
                    'brand_rate': round(brand_rate, 1),
                    'competitor_rate': round(competitor_rate, 1),
                    'gap_score': round(competitor_rate - brand_rate, 1),
                    'sample_size': stats['total']
                })

        # Find gaps in categories
        for category, stats in category_analysis['breakdown']:
            competitor_rate = (stats['competitor_mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
            brand_rate = stats['brand_rate']

            if competitor_rate > threshold and brand_rate < 50:
                gaps.append({
                    'type': 'category',
                    'value': category,
                    'brand_rate': round(brand_rate, 1),
                    'competitor_rate': round(competitor_rate, 1),
                    'gap_score': round(competitor_rate - brand_rate, 1),
                    'sample_size': stats['total']
                })

        # Sort by gap score
        gaps.sort(key=lambda x: x['gap_score'], reverse=True)

        return gaps[:10]  # Top 10 gaps

    def find_all_brands_mentioned(self, scored_results: List[Dict[str, Any]],
                                   listed_competitors: List[str]) -> Dict[str, Any]:
        """
        Find every brand mentioned in responses, not just listed competitors.

        Args:
            scored_results: List of results with visibility scores
            listed_competitors: List of competitors you're explicitly tracking

        Returns:
            Dictionary with all brands found, separated by listed vs unlisted
        """
        all_brands = defaultdict(int)
        listed_competitor_set = set(c.lower() for c in listed_competitors)
        brand_name_lower = self.brand_name.lower()

        # Common beauty/makeup brand patterns
        beauty_brand_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+(?:Beauty|Cosmetics|Makeup|Labs?)\b',
            r'\b(?:Urban Decay|MAC|NARS|Fenty Beauty|Rare Beauty|Ilia|Glossier|Milk Makeup)\b',
            r'\b(?:Bobbi Brown|Laura Mercier|Hourglass|Benefit|Too Faced|Tarte|Smashbox)\b',
            r'\b(?:Maybelline|L\'Or[eé]al|NYX|e\.l\.f\.|ColourPop|Revlon|CoverGirl)\b',
            r'\b(?:Dior|Chanel|YSL|Givenchy|Guerlain|Lancome|Armani)\b',
            r'\b(?:Estee Lauder|Clinique|MAC|Bobbi Brown)\b',
        ]

        for result in scored_results:
            response_text = result.get('response', '')
            if not response_text:
                continue

            # Try pattern matching for brand names
            for pattern in beauty_brand_patterns:
                matches = re.finditer(pattern, response_text, re.IGNORECASE)
                for match in matches:
                    brand = match.group(0).strip()
                    brand_lower = brand.lower()

                    # Skip if it's the main brand or already in competitors
                    if brand_lower == brand_name_lower:
                        continue
                    if brand_lower in listed_competitor_set:
                        continue

                    all_brands[brand] += 1

            # Also check visibility data for competitors already found
            visibility = result.get('visibility', {})
            competitors = visibility.get('competitors_mentioned', [])
            for comp in competitors:
                comp_lower = comp.lower()
                if comp_lower not in listed_competitor_set and comp_lower != brand_name_lower:
                    all_brands[comp] += 1

        # Calculate total responses
        total_responses = len(scored_results)

        # Sort by frequency
        sorted_brands = sorted(all_brands.items(), key=lambda x: x[1], reverse=True)

        # Calculate mention rates
        unlisted_brands = []
        for brand, count in sorted_brands:
            mention_rate = (count / total_responses * 100) if total_responses > 0 else 0
            unlisted_brands.append({
                'name': brand,
                'mentions': count,
                'mention_rate': round(mention_rate, 1),
                'should_track': count >= 5  # Recommend tracking if mentioned 5+ times
            })

        # Prepare data for brand_config.json (discovered competitors)
        from datetime import datetime
        for_brand_config = []
        for brand_data in unlisted_brands:
            # Determine status based on mention count
            status = 'emerging_threat' if brand_data['mentions'] >= 5 else 'occasional_mention'

            for_brand_config.append({
                'name': brand_data['name'],
                'mention_count': brand_data['mentions'],
                'mention_rate': brand_data['mention_rate'],
                'status': status,
                'first_seen': datetime.utcnow().strftime('%Y-%m-%d'),
                'promoted_to_expected': False
            })

        return {
            'unlisted_brands': unlisted_brands[:15],  # Top 15
            'total_unlisted_found': len(unlisted_brands),
            'recommendations': [
                b for b in unlisted_brands if b['should_track']
            ][:5],  # Top 5 recommendations
            'for_brand_config': for_brand_config[:15]  # NEW: Ready for brand_config.json
        }
