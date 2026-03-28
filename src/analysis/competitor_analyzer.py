"""
Competitor analyzer for comparing brand visibility vs competitors.
"""

from typing import Dict, List, Any, Set
from collections import defaultdict
import re


class CompetitorAnalyzer:
    """Analyzes brand performance relative to competitors."""

    # Category keyword patterns for brand classification
    CATEGORY_PATTERNS = {
        'retailer': {
            'keywords': [
                'buy', 'shop', 'store', 'purchase', 'order', 'checkout',
                'cart', 'shipping', 'delivery', 'retail', 'sells', 'marketplace',
                'e-commerce', 'ecommerce', 'amazon', 'walmart', 'target',
                'available at', 'sold at', 'find at', 'get it at'
            ],
            'domains': ['amazon.', 'walmart.', 'target.', 'shopify.', 'etsy.'],
            'weight': 1.0
        },
        'media': {
            'keywords': [
                'review', 'article', 'according to', 'reported', 'writes',
                'published', 'magazine', 'blog', 'news', 'journalist',
                'editor', 'coverage', 'featured in', 'wrote about', 'says',
                'media', 'publication', 'press', 'outlet', 'interviewed'
            ],
            'domains': ['.blog', 'news.', 'magazine.', 'times.', 'post.'],
            'weight': 1.0
        },
        'government': {
            'keywords': [
                '.gov', 'ministry', 'government', 'federal', 'provincial',
                'state', 'municipal', 'funded by', 'grant', 'regulation',
                'policy', 'legislation', 'public health', 'official',
                'department of', 'agency', 'bureau', 'commission'
            ],
            'domains': ['.gov', '.gc.ca', '.on.ca', '.ca/en/'],
            'weight': 1.2  # Higher weight - government mentions are distinctive
        },
        'resource': {
            'keywords': [
                'directory', 'list of', 'database', 'resource', 'guide',
                'information', 'wiki', 'encyclopedia', 'reference',
                'handbook', 'portal', 'hub', 'finder', 'locator', 'index'
            ],
            'domains': ['wiki', 'directory.', 'finder.', 'guide.'],
            'weight': 0.9
        },
        'adjacent': {
            'keywords': [
                'similar', 'related', 'also offers', 'alternative',
                'complements', 'works with', 'integrates', 'partnership',
                'affiliated', 'associated', 'sister organization'
            ],
            'domains': [],
            'weight': 0.8
        },
        'direct_competitor': {
            'keywords': [
                'competitor', 'competing', 'versus', 'vs', 'compared to',
                'instead of', 'rather than', 'alternative to', 'better than',
                'same service', 'also provides', 'similar to'
            ],
            'domains': [],
            'weight': 0.9
        }
    }

    # Confidence thresholds
    HIGH_CONFIDENCE = 0.7
    MEDIUM_CONFIDENCE = 0.4

    def __init__(self, brand_name: str):
        """
        Initialize the competitor analyzer.

        Args:
            brand_name: Primary brand name
        """
        self.brand_name = brand_name

    def categorize_brand(self, brand_name: str, context_text: str,
                         category_overrides: dict = None) -> dict:
        """
        Categorize a brand based on surrounding context in AI responses.

        Args:
            brand_name: The brand/organization name to categorize
            context_text: The surrounding text where the brand was mentioned
            category_overrides: Manual overrides from brand_config.json

        Returns:
            Dictionary with 'category' and 'confidence' keys
        """
        # Check for manual override first - these always win
        if category_overrides and brand_name in category_overrides:
            return {
                'category': category_overrides[brand_name],
                'confidence': 1.0,
                'source': 'manual_override'
            }

        # Also check case-insensitive
        if category_overrides:
            for override_name, override_cat in category_overrides.items():
                if override_name.lower() == brand_name.lower():
                    return {
                        'category': override_cat,
                        'confidence': 1.0,
                        'source': 'manual_override'
                    }

        # Extract context window around brand mention (200 chars before/after)
        context_lower = context_text.lower()
        brand_lower = brand_name.lower()

        # Find all positions where brand is mentioned
        positions = []
        start = 0
        while True:
            pos = context_lower.find(brand_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1

        # If brand not found in context, use full context
        if not positions:
            context_window = context_lower
        else:
            # Build context window from all mentions
            context_parts = []
            for pos in positions:
                window_start = max(0, pos - 200)
                window_end = min(len(context_lower), pos + len(brand_lower) + 200)
                context_parts.append(context_lower[window_start:window_end])
            context_window = ' '.join(context_parts)

        # Score each category based on keyword matches
        category_scores = {}

        for category, patterns in self.CATEGORY_PATTERNS.items():
            score = 0.0

            # Check keywords
            for keyword in patterns['keywords']:
                if keyword in context_window:
                    score += patterns['weight']

            # Check domains (if brand looks like a domain)
            for domain in patterns['domains']:
                if domain in brand_lower or domain in context_window:
                    score += patterns['weight'] * 1.5

            category_scores[category] = score

        # Find best matching category
        if not category_scores or max(category_scores.values()) == 0:
            return {
                'category': 'uncategorized',
                'confidence': 0.0,
                'source': 'no_match'
            }

        best_category = max(category_scores, key=category_scores.get)
        best_score = category_scores[best_category]

        # Calculate confidence based on score magnitude and differentiation
        total_score = sum(category_scores.values())
        if total_score > 0:
            # How dominant is the best category?
            dominance = best_score / total_score
            # Scale by absolute score (more matches = more confident)
            confidence = min(1.0, dominance * min(1.0, best_score / 3.0))
        else:
            confidence = 0.0

        # Apply thresholds
        if confidence < self.MEDIUM_CONFIDENCE:
            return {
                'category': 'uncategorized',
                'confidence': confidence,
                'source': 'low_confidence',
                'scores': category_scores
            }

        return {
            'category': best_category,
            'confidence': round(confidence, 2),
            'source': 'keyword_match',
            'scores': category_scores
        }

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
                                   listed_competitors: List[str],
                                   category_overrides: dict = None) -> Dict[str, Any]:
        """
        Find every brand mentioned in responses, not just listed competitors.
        Uses industry-agnostic patterns to detect brand names.
        Now includes automatic categorization of discovered brands.

        Args:
            scored_results: List of results with visibility scores
            listed_competitors: List of competitors you're explicitly tracking
            category_overrides: Manual category assignments from brand_config.json

        Returns:
            Dictionary with all brands found, separated by listed vs unlisted,
            now including category information for each brand
        """
        all_brands = defaultdict(int)
        brand_contexts = defaultdict(list)  # Store context for categorization
        listed_competitor_set = set(c.lower() for c in listed_competitors)
        brand_name_lower = self.brand_name.lower()

        # Also add brand aliases to skip list
        brand_aliases_lower = set()
        for word in brand_name_lower.split():
            if len(word) > 2:
                brand_aliases_lower.add(word)

        # Common words to exclude (not brand names)
        common_words = {
            # Generic words
            'the', 'and', 'for', 'with', 'your', 'this', 'that', 'they', 'their',
            'what', 'when', 'where', 'which', 'who', 'how', 'why', 'can', 'will',
            'should', 'would', 'could', 'have', 'has', 'had', 'been', 'being',
            'some', 'most', 'many', 'much', 'more', 'other', 'another', 'each',
            'every', 'both', 'all', 'any', 'few', 'several', 'such', 'only',
            # Common nouns often capitalized
            'company', 'brand', 'service', 'product', 'platform', 'website',
            'organization', 'business', 'solution', 'option', 'alternative',
            'provider', 'tool', 'app', 'application', 'software', 'system',
            # Action words
            'offers', 'provides', 'includes', 'features', 'supports', 'enables',
            'helps', 'allows', 'makes', 'creates', 'delivers', 'gives',
            # Adjectives
            'best', 'top', 'great', 'good', 'new', 'free', 'easy', 'simple',
            'popular', 'leading', 'major', 'main', 'key', 'primary', 'first',
            # Time/location
            'today', 'here', 'there', 'now', 'then', 'often', 'always', 'never',
            # Articles and prepositions
            'also', 'just', 'like', 'about', 'into', 'over', 'after', 'before',
            # Common sentence starters
            'however', 'therefore', 'additionally', 'furthermore', 'moreover',
            'meanwhile', 'finally', 'overall', 'generally', 'typically',
            # Generic category words (often appear capitalized in lists)
            'services', 'products', 'options', 'features', 'benefits', 'tools',
            'resources', 'solutions', 'alternatives', 'providers', 'platforms',
        }

        for result in scored_results:
            response_text = result.get('response', '') or result.get('response_text', '')
            if not response_text:
                continue

            # PATTERN 1: Capitalized multi-word phrases (2-4 words)
            # Matches things like "The Knot", "Home Instead", "Ontario Caregiver Organization"
            multi_word_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
            matches = re.findall(multi_word_pattern, response_text)
            for match in matches:
                brand = match.strip()
                brand_lower = brand.lower()

                # Skip if common phrase or already tracked
                words = brand_lower.split()
                if any(w in common_words for w in words):
                    continue
                if brand_lower == brand_name_lower or brand_lower in listed_competitor_set:
                    continue
                if brand_lower in brand_aliases_lower:
                    continue

                all_brands[brand] += 1
                brand_contexts[brand].append(response_text)

            # PATTERN 2: Single capitalized words that look like brand names
            # (followed by context clues like "offers", "provides", ".com", etc.)
            brand_context_pattern = r'\b([A-Z][a-z]{2,})\b(?:\s+(?:offers|provides|is|has|allows|lets|helps|enables|\.com|website|platform|app))'
            matches = re.findall(brand_context_pattern, response_text)
            for match in matches:
                brand = match.strip()
                brand_lower = brand.lower()

                if brand_lower in common_words:
                    continue
                if brand_lower == brand_name_lower or brand_lower in listed_competitor_set:
                    continue
                if brand_lower in brand_aliases_lower:
                    continue
                if len(brand) < 3:
                    continue

                all_brands[brand] += 1
                brand_contexts[brand].append(response_text)

            # PATTERN 3: Names in list contexts
            # "options include X, Y, and Z" or "such as X, Y, Z" or "like X, Y, and Z"
            list_pattern = r'(?:such as|like|including|options include|consider|try|check out|look at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)*(?:\s*,?\s*(?:and|or)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)?)'
            matches = re.findall(list_pattern, response_text, re.IGNORECASE)
            for match in matches:
                # Split by comma, "and", "or"
                items = re.split(r'\s*,\s*|\s+and\s+|\s+or\s+', match)
                for item in items:
                    brand = item.strip()
                    brand_lower = brand.lower()

                    if brand_lower in common_words:
                        continue
                    if brand_lower == brand_name_lower or brand_lower in listed_competitor_set:
                        continue
                    if brand_lower in brand_aliases_lower:
                        continue
                    if len(brand) < 2:
                        continue
                    # Must start with capital
                    if not brand[0].isupper():
                        continue

                    all_brands[brand] += 1
                    brand_contexts[brand].append(response_text)

            # PATTERN 4: Domains/URLs mentioned
            # Extract brand names from URLs like "theknot.com" or "withjoy.com"
            url_pattern = r'(?:https?://)?(?:www\.)?([a-z]+)\.(?:com|org|net|io|co)\b'
            matches = re.findall(url_pattern, response_text, re.IGNORECASE)
            for match in matches:
                brand = match.strip().title()  # Convert to title case
                brand_lower = brand.lower()

                if brand_lower in common_words:
                    continue
                if brand_lower == brand_name_lower or brand_lower in listed_competitor_set:
                    continue
                if brand_lower in brand_aliases_lower:
                    continue
                if len(brand) < 3:
                    continue

                all_brands[brand] += 1
                brand_contexts[brand].append(response_text)

            # Also check visibility data for competitors already found by scorer
            visibility = result.get('visibility', {})
            competitors = visibility.get('competitors_mentioned', [])
            for comp in competitors:
                comp_lower = comp.lower()
                if comp_lower not in listed_competitor_set and comp_lower != brand_name_lower:
                    all_brands[comp] += 1
                    brand_contexts[comp].append(response_text)

        # Calculate total responses
        total_responses = len(scored_results)

        # Sort by frequency
        sorted_brands = sorted(all_brands.items(), key=lambda x: x[1], reverse=True)

        # Filter out low-quality matches and calculate mention rates
        unlisted_brands = []
        for brand, count in sorted_brands:
            # Skip if only mentioned once (likely noise)
            if count < 2:
                continue

            mention_rate = (count / total_responses * 100) if total_responses > 0 else 0

            # Categorize the brand using collected context
            combined_context = ' '.join(brand_contexts.get(brand, []))
            category_result = self.categorize_brand(
                brand,
                combined_context,
                category_overrides
            )

            unlisted_brands.append({
                'name': brand,
                'mentions': count,
                'mention_rate': round(mention_rate, 1),
                'should_track': count >= 5,  # Recommend tracking if mentioned 5+ times
                'category': category_result['category'],
                'category_confidence': category_result['confidence'],
                'category_source': category_result.get('source', 'unknown')
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
                'category': brand_data['category'],
                'category_confidence': brand_data['category_confidence'],
                'first_seen': datetime.utcnow().strftime('%Y-%m-%d'),
                'promoted_to_expected': False
            })

        # Calculate category breakdown
        category_counts = defaultdict(lambda: {'count': 0, 'brands': []})
        for brand_data in unlisted_brands:
            cat = brand_data['category']
            category_counts[cat]['count'] += 1
            category_counts[cat]['brands'].append({
                'name': brand_data['name'],
                'mentions': brand_data['mentions'],
                'confidence': brand_data['category_confidence']
            })

        return {
            'unlisted_brands': unlisted_brands[:15],  # Top 15
            'total_unlisted_found': len(unlisted_brands),
            'recommendations': [
                b for b in unlisted_brands if b['should_track']
            ][:5],  # Top 5 recommendations
            'for_brand_config': for_brand_config[:15],  # Ready for brand_config.json
            'by_category': dict(category_counts)  # Brands grouped by category
        }
