"""
Gap analyzer for identifying visibility opportunities.
"""

from typing import Dict, List, Any
from collections import defaultdict, Counter


class GapAnalyzer:
    """Identifies gaps and opportunities in brand visibility."""

    def __init__(self, brand_name: str):
        """
        Initialize the gap analyzer.

        Args:
            brand_name: Primary brand name
        """
        self.brand_name = brand_name

    def identify_gaps(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify all types of visibility gaps.

        Args:
            scored_results: List of results with visibility scores

        Returns:
            Dictionary with gap analysis
        """
        return {
            'persona_gaps': self._analyze_persona_gaps(scored_results),
            'category_gaps': self._analyze_category_gaps(scored_results),
            'intent_gaps': self._analyze_intent_gaps(scored_results),
            'platform_gaps': self._analyze_platform_gaps(scored_results),
            'priority_opportunities': self._rank_opportunities(scored_results)
        }

    def _analyze_persona_gaps(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze gaps by persona."""
        persona_stats = defaultdict(lambda: {'total': 0, 'mentions': 0, 'avg_prominence': []})

        for result in scored_results:
            persona = result.get('metadata', {}).get('persona', 'Unknown')
            visibility = result.get('visibility', {})

            persona_stats[persona]['total'] += 1
            if visibility.get('brand_mentioned'):
                persona_stats[persona]['mentions'] += 1
            persona_stats[persona]['avg_prominence'].append(visibility.get('prominence_score', 0))

        gaps = []
        for persona, stats in persona_stats.items():
            mention_rate = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_prominence = sum(stats['avg_prominence']) / len(stats['avg_prominence']) if stats['avg_prominence'] else 0

            if mention_rate < 60:  # Flag as gap if <60% visibility
                gaps.append({
                    'persona': persona,
                    'visibility_rate': round(mention_rate, 1),
                    'avg_prominence': round(avg_prominence, 1),
                    'sample_size': stats['total'],
                    'gap_severity': 'high' if mention_rate < 30 else 'medium'
                })

        return sorted(gaps, key=lambda x: x['visibility_rate'])

    def _analyze_category_gaps(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze gaps by category."""
        category_stats = defaultdict(lambda: {'total': 0, 'mentions': 0})

        for result in scored_results:
            category = result.get('metadata', {}).get('category') or result.get('category', 'Unknown')
            visibility = result.get('visibility', {})

            category_stats[category]['total'] += 1
            if visibility.get('brand_mentioned'):
                category_stats[category]['mentions'] += 1

        gaps = []
        for category, stats in category_stats.items():
            mention_rate = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0

            if mention_rate < 60:
                gaps.append({
                    'category': category,
                    'visibility_rate': round(mention_rate, 1),
                    'sample_size': stats['total']
                })

        return sorted(gaps, key=lambda x: x['visibility_rate'])

    def _analyze_intent_gaps(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze gaps by intent type."""
        intent_stats = defaultdict(lambda: {'total': 0, 'mentions': 0})

        for result in scored_results:
            intent = result.get('metadata', {}).get('intent_type') or result.get('intent_type', 'Unknown')
            visibility = result.get('visibility', {})

            intent_stats[intent]['total'] += 1
            if visibility.get('brand_mentioned'):
                intent_stats[intent]['mentions'] += 1

        gaps = []
        for intent, stats in intent_stats.items():
            mention_rate = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0

            if mention_rate < 60:
                gaps.append({
                    'intent_type': intent,
                    'visibility_rate': round(mention_rate, 1),
                    'sample_size': stats['total']
                })

        return sorted(gaps, key=lambda x: x['visibility_rate'])

    def _analyze_platform_gaps(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze gaps by platform."""
        platform_stats = defaultdict(lambda: {'total': 0, 'mentions': 0})

        for result in scored_results:
            platform = result.get('platform', 'Unknown')
            visibility = result.get('visibility', {})

            platform_stats[platform]['total'] += 1
            if visibility.get('brand_mentioned'):
                platform_stats[platform]['mentions'] += 1

        gaps = []
        for platform, stats in platform_stats.items():
            mention_rate = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0

            gaps.append({
                'platform': platform,
                'visibility_rate': round(mention_rate, 1),
                'sample_size': stats['total']
            })

        return sorted(gaps, key=lambda x: x['visibility_rate'])

    def _rank_opportunities(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank top opportunities for improvement with detailed recommendations.

        Args:
            scored_results: List of results with visibility scores

        Returns:
            List of opportunities ranked by impact potential with priorities
        """
        opportunities = []

        # Calculate competitor average visibility
        total_with_competitors = sum(1 for r in scored_results if r.get('visibility', {}).get('competitors_mentioned'))
        competitor_avg = (total_with_competitors / len(scored_results) * 100) if scored_results else 0

        # Analyze each dimension
        persona_gaps = self._analyze_persona_gaps(scored_results)
        category_gaps = self._analyze_category_gaps(scored_results)
        intent_gaps = self._analyze_intent_gaps(scored_results)

        # Convert persona gaps to opportunities
        for gap in persona_gaps:
            impact_score = (100 - gap['visibility_rate']) * (gap['sample_size'] / len(scored_results)) * 100
            gap_points = max(0, competitor_avg - gap['visibility_rate'])
            missed_monthly = round((gap_points * gap['sample_size'] / 100) * 4 / 5) * 5  # Round to nearest 5

            # Get actual example prompts
            example_prompts = self._get_example_prompts_for_gap('Persona', gap['persona'], scored_results)
            competitor_who_won = self._get_competitor_who_won(example_prompts)

            opportunities.append({
                'type': 'Persona',
                'target': gap['persona'],
                'current_visibility': gap['visibility_rate'],
                'competitor_avg': round(competitor_avg, 1),
                'gap_points': round(gap_points, 1),
                'sample_size': gap['sample_size'],
                'impact_score': round(impact_score, 1),
                'missed_monthly': max(5, missed_monthly),  # Minimum 5
                'recommendation': self._generate_persona_recommendation(gap, scored_results),
                'value_prop': self._get_persona_value_prop(gap['persona']),
                'specific_actions': self._generate_specific_actions('Persona', gap['persona']),
                'where_to_implement': 'Product pages, Blog, YouTube, Social media',
                'target_keywords': self._extract_keywords_for_persona(gap['persona']),
                'example_prompts': example_prompts,
                'competitor_who_won': competitor_who_won
            })

        # Convert category gaps to opportunities
        for gap in category_gaps:
            impact_score = (100 - gap['visibility_rate']) * (gap['sample_size'] / len(scored_results)) * 100
            gap_points = max(0, competitor_avg - gap['visibility_rate'])
            missed_monthly = round((gap_points * gap['sample_size'] / 100) * 4 / 5) * 5

            # Get actual example prompts
            example_prompts = self._get_example_prompts_for_gap('Category', gap['category'], scored_results)
            competitor_who_won = self._get_competitor_who_won(example_prompts)

            opportunities.append({
                'type': 'Category',
                'target': gap['category'],
                'current_visibility': gap['visibility_rate'],
                'competitor_avg': round(competitor_avg, 1),
                'gap_points': round(gap_points, 1),
                'sample_size': gap['sample_size'],
                'impact_score': round(impact_score, 1),
                'missed_monthly': max(5, missed_monthly),
                'recommendation': self._generate_category_recommendation(gap),
                'specific_actions': self._generate_specific_actions('Category', gap['category']),
                'where_to_implement': 'Blog, Resource center, FAQ pages',
                'target_keywords': self._extract_keywords_for_category(gap['category']),
                'example_prompts': example_prompts,
                'competitor_who_won': competitor_who_won
            })

        # Convert intent gaps to opportunities
        for gap in intent_gaps:
            impact_score = (100 - gap['visibility_rate']) * (gap['sample_size'] / len(scored_results)) * 100
            gap_points = max(0, competitor_avg - gap['visibility_rate'])
            missed_monthly = round((gap_points * gap['sample_size'] / 100) * 4 / 5) * 5

            # Get actual example prompts
            example_prompts = self._get_example_prompts_for_gap('Intent Type', gap['intent_type'], scored_results)
            competitor_who_won = self._get_competitor_who_won(example_prompts)

            opportunities.append({
                'type': 'Intent Type',
                'target': gap['intent_type'],
                'current_visibility': gap['visibility_rate'],
                'competitor_avg': round(competitor_avg, 1),
                'gap_points': round(gap_points, 1),
                'sample_size': gap['sample_size'],
                'impact_score': round(impact_score, 1),
                'missed_monthly': max(5, missed_monthly),
                'recommendation': self._generate_intent_recommendation(gap),
                'specific_actions': self._generate_specific_actions('Intent', gap['intent_type']),
                'where_to_implement': 'Landing pages, Blog, Product descriptions',
                'target_keywords': self._extract_keywords_for_intent(gap['intent_type']),
                'example_prompts': example_prompts,
                'competitor_who_won': competitor_who_won
            })

        # Sort by impact score
        opportunities.sort(key=lambda x: x['impact_score'], reverse=True)

        # Add priority badges
        for i, opp in enumerate(opportunities[:10]):
            if i < 3:
                opp['priority'] = 'HIGH'
                opp['priority_emoji'] = '🔴'
            elif i < 8:
                opp['priority'] = 'MEDIUM'
                opp['priority_emoji'] = '🟡'
            else:
                opp['priority'] = 'LOW'
                opp['priority_emoji'] = '🟢'

            # Add user-friendly category grouping
            if opp['type'] == 'Persona':
                opp['group'] = 'audience'
                opp['group_label'] = 'Audience to Target'
            else:  # Category or Intent Type
                opp['group'] = 'content'
                opp['group_label'] = 'Content to Create'
                # Add user-friendly content type names
                opp['content_type'] = self._get_content_type_name(opp['type'], opp['target'])

        return opportunities[:10]

    def _get_content_type_name(self, opp_type: str, target: str) -> str:
        """Convert opportunity type/target to user-friendly content type name."""
        content_type_map = {
            'educational': 'Educational/How-To Content',
            'technical': 'Technical Guides',
            'business': 'Business/Professional Content',
            'informational': 'Informational Content',
            'transactional': 'Product/Purchase Pages',
            'comparison': 'Comparison Content',
        }

        if opp_type == 'Category':
            return content_type_map.get(target.lower(), f'{target} Content')
        elif opp_type == 'Intent Type':
            return content_type_map.get(target.lower(), f'{target.title()} Content')
        return target

    def get_organized_opportunities(self, scored_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get opportunities organized by type (Content vs Audience).

        Args:
            scored_results: List of results with visibility scores

        Returns:
            Dictionary with 'content' and 'audience' opportunity lists
        """
        all_opportunities = self._rank_opportunities(scored_results)

        content_opps = [opp for opp in all_opportunities if opp['group'] == 'content']
        audience_opps = [opp for opp in all_opportunities if opp['group'] == 'audience']

        return {
            'content_opportunities': content_opps,
            'audience_opportunities': audience_opps
        }

    def get_prioritized_audiences(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get prioritized audience opportunities with business context and actionable recommendations.

        Returns:
            List of audience opportunities with enriched data for marketing decision-making
        """
        from collections import Counter

        persona_gaps = self._analyze_persona_gaps(scored_results)

        # Calculate overall competitor average for benchmarking
        competitor_mention_rates = []
        for result in scored_results:
            visibility = result.get('visibility', {})
            if visibility.get('competitors_mentioned'):
                competitor_mention_rates.append(1)
            else:
                competitor_mention_rates.append(0)
        competitor_avg = (sum(competitor_mention_rates) / len(competitor_mention_rates) * 100) if competitor_mention_rates else 0

        prioritized_audiences = []

        for gap in persona_gaps:
            persona = gap['persona']
            current_vis = gap['visibility_rate']
            sample_size = gap['sample_size']

            # Calculate competitor performance for this persona
            persona_results = [r for r in scored_results if r.get('metadata', {}).get('persona') == persona]
            persona_comp_mentions = sum(1 for r in persona_results if r.get('visibility', {}).get('competitors_mentioned'))
            persona_comp_rate = (persona_comp_mentions / len(persona_results) * 100) if persona_results else 0

            gap_percentage = persona_comp_rate - current_vis

            # Get example queries (deduplicated)
            example_prompts = self._get_example_prompts_for_gap('Persona', persona, scored_results)
            all_prompts = [ex['prompt'] for ex in example_prompts]
            example_queries = list(dict.fromkeys(all_prompts))[:5]  # Remove duplicates, keep order

            # Find which competitor dominates this persona
            top_competitor = self._get_competitor_who_won(example_prompts)

            # Calculate effort (based on # of content pieces needed)
            effort_estimate = "High" if sample_size > 100 else "Medium" if sample_size > 50 else "Low"
            content_pieces_needed = max(5, int(sample_size * gap_percentage / 1000))  # Rough estimate

            # Determine priority based on gap and value
            if gap_percentage > 30 and persona in ['Professional Makeup Artist', 'Luxury Beauty Enthusiast']:
                priority_level = "CRITICAL"
                priority_emoji = "🔥"
            elif gap_percentage > 20:
                priority_level = "HIGH"
                priority_emoji = "⚡"
            else:
                priority_level = "MEDIUM"
                priority_emoji = "⏳"

            # Business value context
            value_context = self._get_persona_value_prop(persona)

            # Calculate estimated monthly impressions lost
            total_prompts = len(scored_results)
            monthly_multiplier = 4  # Assuming weekly testing = 4x per month
            missed_impressions = int((gap_percentage / 100) * sample_size * monthly_multiplier)

            prioritized_audiences.append({
                'persona': persona,
                'current_visibility': current_vis,
                'competitor_average': round(persona_comp_rate, 1),
                'gap_percentage': round(gap_percentage, 1),
                'sample_size': sample_size,
                'priority_level': priority_level,
                'priority_emoji': priority_emoji,
                'business_context': value_context,
                'top_competitor': top_competitor,
                'competitor_rate': round(persona_comp_rate, 1),
                'example_queries': example_queries,
                'effort_estimate': effort_estimate,
                'content_pieces_needed': content_pieces_needed,
                'missed_monthly_impressions': missed_impressions,
                'action_items': self._generate_specific_actions('Persona', persona)[:3],
                'quick_win': gap_percentage > 25 and effort_estimate == "Low"
            })

        # Sort by gap percentage (biggest opportunity first)
        prioritized_audiences.sort(key=lambda x: x['gap_percentage'], reverse=True)

        return prioritized_audiences[:5]  # Top 5 audiences

    def get_prioritized_content_gaps(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get prioritized content gap opportunities with competitive analysis.

        Returns:
            List of content gaps with specific recommendations and competitor benchmarks
        """
        from collections import Counter

        category_gaps = self._analyze_category_gaps(scored_results)
        intent_gaps = self._analyze_intent_gaps(scored_results)

        # Calculate overall competitor average
        competitor_mention_rates = []
        for result in scored_results:
            visibility = result.get('visibility', {})
            if visibility.get('competitors_mentioned'):
                competitor_mention_rates.append(1)
            else:
                competitor_mention_rates.append(0)
        competitor_avg = (sum(competitor_mention_rates) / len(competitor_mention_rates) * 100) if competitor_mention_rates else 0

        prioritized_content = []

        # Process category gaps
        for gap in category_gaps:
            category = gap['category']
            current_vis = gap['visibility_rate']
            sample_size = gap['sample_size']

            # Calculate competitor performance for this category
            category_results = [r for r in scored_results if r.get('metadata', {}).get('category') == category]
            category_comp_mentions = sum(1 for r in category_results if r.get('visibility', {}).get('competitors_mentioned'))
            category_comp_rate = (category_comp_mentions / len(category_results) * 100) if category_results else 0

            gap_percentage = category_comp_rate - current_vis

            # Get example queries (deduplicated)
            example_prompts = self._get_example_prompts_for_gap('Category', category, scored_results)
            all_prompts = [ex['prompt'] for ex in example_prompts]
            example_queries = list(dict.fromkeys(all_prompts))[:5]  # Remove duplicates, keep order

            # Find which competitor dominates
            top_competitor = self._get_competitor_who_won(example_prompts)

            # Determine priority
            if gap_percentage > 30:
                priority_level = "CRITICAL"
                priority_emoji = "🔥"
            elif gap_percentage > 20:
                priority_level = "HIGH"
                priority_emoji = "⚡"
            else:
                priority_level = "MEDIUM"
                priority_emoji = "⏳"

            # Content type mapping
            content_type_name = self._get_content_type_name('Category', category)

            # Effort estimate
            effort_estimate = "High" if sample_size > 100 else "Medium" if sample_size > 50 else "Low"
            content_pieces_needed = max(5, int(sample_size * gap_percentage / 1000))

            # Monthly impressions lost
            monthly_multiplier = 4
            missed_impressions = int((gap_percentage / 100) * sample_size * monthly_multiplier)

            prioritized_content.append({
                'content_type': content_type_name,
                'category': category,
                'current_coverage': current_vis,
                'competitor_average': round(category_comp_rate, 1),
                'gap_percentage': round(gap_percentage, 1),
                'queries_missing': sample_size,
                'priority_level': priority_level,
                'priority_emoji': priority_emoji,
                'top_competitor': top_competitor,
                'example_queries': example_queries,
                'effort_estimate': effort_estimate,
                'content_pieces_needed': content_pieces_needed,
                'missed_monthly_impressions': missed_impressions,
                'specific_content_to_create': self._generate_specific_actions('Category', category)[:3],
                'quick_win': gap_percentage > 25 and effort_estimate == "Low"
            })

        # Process intent gaps (similar logic)
        for gap in intent_gaps:
            intent = gap['intent_type']
            current_vis = gap['visibility_rate']
            sample_size = gap['sample_size']

            intent_results = [r for r in scored_results if r.get('metadata', {}).get('intent_type') == intent]
            intent_comp_mentions = sum(1 for r in intent_results if r.get('visibility', {}).get('competitors_mentioned'))
            intent_comp_rate = (intent_comp_mentions / len(intent_results) * 100) if intent_results else 0

            gap_percentage = intent_comp_rate - current_vis

            # Get example queries (deduplicated)
            example_prompts = self._get_example_prompts_for_gap('Intent Type', intent, scored_results)
            all_prompts = [ex['prompt'] for ex in example_prompts]
            example_queries = list(dict.fromkeys(all_prompts))[:5]  # Remove duplicates, keep order
            top_competitor = self._get_competitor_who_won(example_prompts)

            if gap_percentage > 30:
                priority_level = "CRITICAL"
                priority_emoji = "🔥"
            elif gap_percentage > 20:
                priority_level = "HIGH"
                priority_emoji = "⚡"
            else:
                priority_level = "MEDIUM"
                priority_emoji = "⏳"

            content_type_name = self._get_content_type_name('Intent Type', intent)
            effort_estimate = "High" if sample_size > 100 else "Medium" if sample_size > 50 else "Low"
            content_pieces_needed = max(5, int(sample_size * gap_percentage / 1000))
            monthly_multiplier = 4
            missed_impressions = int((gap_percentage / 100) * sample_size * monthly_multiplier)

            prioritized_content.append({
                'content_type': content_type_name,
                'category': intent,
                'current_coverage': current_vis,
                'competitor_average': round(intent_comp_rate, 1),
                'gap_percentage': round(gap_percentage, 1),
                'queries_missing': sample_size,
                'priority_level': priority_level,
                'priority_emoji': priority_emoji,
                'top_competitor': top_competitor,
                'example_queries': example_queries,
                'effort_estimate': effort_estimate,
                'content_pieces_needed': content_pieces_needed,
                'missed_monthly_impressions': missed_impressions,
                'specific_content_to_create': self._generate_specific_actions('Intent', intent)[:3],
                'quick_win': gap_percentage > 25 and effort_estimate == "Low"
            })

        # Sort by gap percentage
        prioritized_content.sort(key=lambda x: x['gap_percentage'], reverse=True)

        return prioritized_content[:5]  # Top 5 content gaps

    def _get_persona_value_prop(self, persona: str) -> str:
        """Get why this persona matters."""
        value_props = {
            'Professional Makeup Artist': 'High-value buyers, frequent purchases, recommend to clients',
            'Luxury Beauty Enthusiast': 'Premium buyers, brand advocates, high lifetime value',
            'Specific Need Shopper': 'High intent, specific problems to solve, ready to buy',
            'Beauty Beginner': 'First luxury purchase, brand loyalty potential, growing segment',
        }
        return value_props.get(persona, 'Key target audience for your brand')

    def _get_example_prompts_for_gap(self, gap_type: str, target: str, scored_results: List[Dict[str, Any]]) -> List[str]:
        """
        Get 3-5 actual prompts from the test that fit this gap.

        Args:
            gap_type: Type of gap (Persona, Category, Intent Type)
            target: Specific target (persona name, category name, etc.)
            scored_results: List of all scored results

        Returns:
            List of actual prompt texts where competitors appeared but brand didn't
        """
        examples = []

        for result in scored_results:
            metadata = result.get('metadata', {})
            visibility = result.get('visibility', {})
            prompt_text = result.get('prompt_text', '').strip()

            if not prompt_text:
                continue

            # Must have competitors mentioned but NOT brand
            if not visibility.get('competitors_mentioned') or visibility.get('brand_mentioned'):
                continue

            # Match the gap criteria
            matches = False
            if gap_type == 'Persona' and metadata.get('persona') == target:
                matches = True
            elif gap_type == 'Category' and metadata.get('category') == target:
                matches = True
            elif gap_type == 'Intent Type' and metadata.get('intent_type') == target:
                matches = True

            if matches:
                # Get which competitor was mentioned
                competitors = visibility.get('competitors_mentioned', [])
                examples.append({
                    'prompt': prompt_text,
                    'competitors': competitors
                })

            if len(examples) >= 5:
                break

        return examples[:3]  # Return top 3 examples

    def _get_competitor_who_won(self, examples: List[Dict[str, Any]]) -> str:
        """Get the most common competitor from examples."""
        from collections import Counter

        if not examples:
            return "competitors"

        all_competitors = []
        for ex in examples:
            all_competitors.extend(ex.get('competitors', []))

        if not all_competitors:
            return "competitors"

        most_common = Counter(all_competitors).most_common(1)[0][0]
        return most_common

    def _generate_persona_recommendation(self, gap: Dict[str, Any], scored_results: List[Dict[str, Any]]) -> str:
        """Generate detailed recommendation for persona gap."""
        persona = gap['persona']
        vis_rate = gap['visibility_rate']

        if vis_rate < 15:
            return f"You're missing from conversations with {persona}."
        elif vis_rate < 30:
            return f"{persona} sees you occasionally, but not enough."
        else:
            return f"You show up for {persona}, but competitors appear more often."

    def _generate_category_recommendation(self, gap: Dict[str, Any]) -> str:
        """Generate detailed recommendation for category gap."""
        category = gap['category']
        vis_rate = gap['visibility_rate']

        if vis_rate < 15:
            return f"You're missing from {category} conversations."
        elif vis_rate < 30:
            return f"You appear occasionally in {category} content, but competitors dominate."
        else:
            return f"You show up in {category} content, but need stronger presence."

    def _generate_intent_recommendation(self, gap: Dict[str, Any]) -> str:
        """Generate detailed recommendation for intent gap."""
        intent = gap['intent_type']
        vis_rate = gap['visibility_rate']

        if vis_rate < 15:
            return f"You're invisible when people ask {intent} questions."
        elif vis_rate < 30:
            return f"You appear occasionally in {intent} queries, but competitors appear more."
        else:
            return f"You show up for {intent} queries, but competitors have stronger presence."

    def _generate_specific_actions(self, opp_type: str, target: str) -> List[str]:
        """Generate specific actionable steps."""
        actions = {
            'Persona': {
                'Professional Makeup Artist': [
                    "Create '/for-professionals' landing page with pro-focused product info",
                    "Write case studies from working MUAs with before/after photos",
                    "Add professional use cases to product pages: '12-hour wear for bridal work'",
                    "Feature pro discount and bulk ordering information"
                ],
                'Luxury Beauty Enthusiast': [
                    "Write detailed product comparison guides: luxury vs drugstore",
                    "Create 'Investment Pieces' collection featuring top luxury items",
                    "Add ingredient breakdowns and formulation details to product pages",
                    "Film luxury unboxing and first impressions videos"
                ],
                'Specific Need Shopper': [
                    "Add FAQ sections to product pages addressing specific concerns (oily lids, hooded eyes, etc.)",
                    "Create collection pages: 'Best for Hooded Eyes', 'Best for Oily Lids'",
                    "Write problem-solution format guides: 'If you have X, use Y'",
                    "Add before/after photos for specific skin concerns"
                ],
                'Beauty Beginner': [
                    "Create 'Beginner's Guide to Luxury Eyeshadow' on blog",
                    "Add 'Is this good for beginners?' FAQ on product pages",
                    "Film simple tutorial videos for first-time users",
                    "Create 'Starter Kit' bundles with beginner-friendly products"
                ],
                'default': [
                    f"Write content targeting {target}",
                    f"Add {target}-focused sections to product pages",
                    f"Create case studies featuring {target} customers"
                ]
            },
            'Category': {
                'educational': [
                    "Create how-to guides and tutorials for your products",
                    "Add FAQ sections to product pages",
                    "Film application videos and post on YouTube"
                ],
                'business': [
                    "Write business case studies showing ROI",
                    "Create professional buyer guides",
                    "Add bulk ordering and professional discount information"
                ],
                'technical': [
                    "Add technical specifications to all product pages",
                    "Create ingredient breakdowns and formulation guides",
                    "Write technical comparison charts vs competitors"
                ],
                'default': [
                    f"Create comprehensive content library for {target}",
                    f"Add dedicated {target} section to website",
                    f"Publish weekly {target} content"
                ]
            },
            'Intent': {
                'informational': [
                    "Create detailed guides and explainers",
                    "Add comprehensive product information pages",
                    "Write comparison articles and buying guides"
                ],
                'transactional': [
                    "Optimize product pages with clear CTAs",
                    "Add reviews and social proof to purchase pages",
                    "Create special offer and bundle pages"
                ],
                'comparison': [
                    "Create 'vs competitor' comparison pages",
                    "Add feature comparison charts",
                    "Write honest head-to-head reviews"
                ],
                'default': [
                    f"Create content targeting {target} intent",
                    f"Optimize existing pages for {target} queries",
                    f"Add {target}-focused landing pages"
                ]
            }
        }

        if opp_type in actions and target in actions[opp_type]:
            return actions[opp_type][target]
        elif opp_type in actions:
            return actions[opp_type].get('default', [])
        return [f"Create targeted content for {target}"]

    def _extract_keywords_for_persona(self, persona: str) -> List[str]:
        """Extract relevant keywords for persona."""
        keywords = {
            'Luxury Beauty Enthusiast': ['luxury eyeshadow', 'high-end makeup', 'premium beauty products'],
            'Professional Makeup Artist': ['professional makeup', 'pro artist', 'makeup for work'],
            'Beauty Beginner': ['beginner makeup', 'easy eyeshadow', 'makeup tutorial for beginners'],
            'default': [f'{persona} makeup', f'{persona} beauty', f'{persona} products']
        }
        return keywords.get(persona, keywords['default'])

    def _extract_keywords_for_category(self, category: str) -> List[str]:
        """Extract relevant keywords for category."""
        keywords = {
            'educational': ['how to apply', 'tutorial', 'guide', 'tips'],
            'business': ['professional', 'bulk order', 'business account'],
            'technical': ['ingredients', 'formulation', 'specifications'],
            'default': [f'{category} content', f'{category} information']
        }
        return keywords.get(category, keywords['default'])

    def _extract_keywords_for_intent(self, intent: str) -> List[str]:
        """Extract relevant keywords for intent type."""
        keywords = {
            'informational': ['what is', 'how does', 'guide to'],
            'transactional': ['buy', 'purchase', 'order', 'shop'],
            'comparison': ['vs', 'versus', 'compare', 'difference between'],
            'default': [f'{intent} queries']
        }
        return keywords.get(intent, keywords['default'])

    def generate_action_plan(self, scored_results: List[Dict[str, Any]],
                            website_verification: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate actionable recommendations.

        Args:
            scored_results: List of results with visibility scores
            website_verification: Optional website verification results

        Returns:
            Dictionary with action plan
        """
        gaps = self.identify_gaps(scored_results)
        opportunities = gaps['priority_opportunities']

        # Add verification status to each opportunity
        if website_verification:
            opportunities = self._add_verification_status(opportunities, website_verification)

        # Group opportunities by type
        quick_wins = []
        medium_term = []
        long_term = []

        for opp in opportunities:
            # Prioritize verified gaps over assumed gaps
            impact_multiplier = 1.5 if opp.get('verification_status') == 'verified' else 1.0
            adjusted_impact = opp['impact_score'] * impact_multiplier

            if adjusted_impact > 50 and opp['sample_size'] < 20:
                quick_wins.append(opp)
            elif adjusted_impact > 30:
                medium_term.append(opp)
            else:
                long_term.append(opp)

        # Sort each by verification status (verified first), then by impact
        quick_wins = sorted(quick_wins,
                          key=lambda x: (x.get('verification_status') == 'verified', x['impact_score']),
                          reverse=True)
        medium_term = sorted(medium_term,
                           key=lambda x: (x.get('verification_status') == 'verified', x['impact_score']),
                           reverse=True)

        return {
            'quick_wins': quick_wins[:5],
            'medium_term_priorities': medium_term[:5],
            'long_term_strategy': long_term[:5],
            'overall_recommendation': self._generate_summary_recommendation(scored_results, gaps),
            'website_verification': website_verification
        }

    def _add_verification_status(self, opportunities: List[Dict[str, Any]],
                                 website_verification: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Add verification status to opportunities based on website analysis.

        Args:
            opportunities: List of gap opportunities
            website_verification: Results from website verification

        Returns:
            Opportunities with verification status added
        """
        if not website_verification or 'comparison' not in website_verification:
            # Mark all as assumed if no verification data
            for opp in opportunities:
                opp['verification_status'] = 'assumed'
                opp['competitor_examples'] = []
            return opportunities

        verified_gaps = website_verification.get('comparison', {}).get('verified_gaps', [])

        # Create lookup for verified content types
        verified_lookup = {}
        for gap in verified_gaps:
            content_type = gap.get('content_type', '').replace('_', ' ').lower()
            verified_lookup[content_type] = gap

        # Tag each opportunity
        for opp in opportunities:
            # Get content type, removing ' Content' suffix if present
            opp_type = opp.get('content_type', opp.get('type', '')).replace(' Content', '').lower()

            # Check if this opportunity matches a verified gap
            if opp_type in verified_lookup:
                gap = verified_lookup[opp_type]
                opp['verification_status'] = 'verified'
                opp['competitor_examples'] = gap.get('competitor_examples', [])
                opp['competitors_with_content'] = gap.get('competitors_with', 0)
            else:
                opp['verification_status'] = 'assumed'
                opp['competitor_examples'] = []

        return opportunities

    def _generate_summary_recommendation(self, scored_results: List[Dict[str, Any]],
                                        gaps: Dict[str, Any]) -> str:
        """Generate overall recommendation summary."""
        total_results = len(scored_results)
        brand_mentions = sum(1 for r in scored_results
                            if r.get('visibility', {}).get('brand_mentioned', False))
        visibility_rate = (brand_mentions / total_results * 100) if total_results > 0 else 0

        if visibility_rate >= 80:
            return "Brand has strong visibility. Focus on maintaining prominence and expanding to new query types."
        elif visibility_rate >= 60:
            return "Brand has moderate visibility. Prioritize addressing persona and category gaps to improve coverage."
        elif visibility_rate >= 40:
            return "Brand has low visibility. Immediate action needed across multiple dimensions. Start with quick wins."
        else:
            return "Brand visibility is critically low. Comprehensive content strategy overhaul recommended."

    def generate_geo_aeo_quick_wins(self, scored_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate 2-3 actionable content recommendations based on high-prominence competitor wins.

        Returns:
            List of actionable content briefs with full examples
        """
        from collections import defaultdict, Counter

        # Find prompts where competitors scored 7+ and client scored 0
        high_priority_misses = []
        for result in scored_results:
            visibility = result.get('visibility', {})

            # Client not mentioned
            if visibility.get('brand_mentioned'):
                continue

            # Find competitors with 7+ prominence
            competitor_details = visibility.get('competitor_details', {})
            for comp_name, comp_data in competitor_details.items():
                if comp_data.get('prominence_score', 0) >= 7:
                    high_priority_misses.append({
                        'prompt': result.get('prompt_text', ''),
                        'competitor': comp_name,
                        'prominence': comp_data.get('prominence_score', 0),
                        'intent_type': result.get('metadata', {}).get('intent_type', 'Unknown'),
                        'category': result.get('metadata', {}).get('category', 'Unknown'),
                        'persona': result.get('metadata', {}).get('persona', 'Unknown')
                    })
                    break  # Only count once per prompt

        if not high_priority_misses:
            return []

        # Group by query type
        query_type_groups = defaultdict(list)
        for miss in high_priority_misses:
            intent = miss['intent_type']
            category = miss['category']
            prompt = miss['prompt'].lower()

            # Classify query type
            if 'how to' in prompt or intent == 'how_to':
                query_type_groups['how_to'].append(miss)
            elif '?' in prompt or 'what' in prompt or 'which' in prompt:
                query_type_groups['question'].append(miss)
            elif 'vs' in prompt or 'compare' in prompt or 'difference' in prompt or intent == 'comparison':
                query_type_groups['comparison'].append(miss)
            elif category == 'educational':
                query_type_groups['tutorial'].append(miss)
            else:
                query_type_groups['general'].append(miss)

        # Generate recommendations
        recommendations = []

        # How-to/Tutorial queries -> Create tutorial content
        how_to_count = len(query_type_groups['how_to']) + len(query_type_groups['tutorial'])
        if how_to_count >= 3:
            top_competitor = Counter([m['competitor'] for m in query_type_groups['how_to'] + query_type_groups['tutorial']]).most_common(1)[0][0]
            # Deduplicate prompts
            all_prompts = [m['prompt'] for m in (query_type_groups['how_to'] + query_type_groups['tutorial'])]
            example_prompts = list(dict.fromkeys(all_prompts))[:5]  # Keep order, remove duplicates
            top_persona = Counter([m['persona'] for m in (query_type_groups['how_to'] + query_type_groups['tutorial'])]).most_common(1)[0][0]

            recommendations.append({
                'title': 'Create Step-by-Step Tutorial Content',
                'content_type': 'Tutorial/How-To Content',
                'priority': 'HIGH',
                'what': f"Create 3-5 tutorial articles or videos targeting {top_persona}. Example topics your audience is searching for:",
                'example_queries': example_prompts[:5],  # Full queries, not truncated
                'why': f"{top_competitor} dominates {how_to_count} tutorial queries where you're absent. They're being featured prominently (7+ score) while you're invisible.",
                'content_brief': f"Write comprehensive how-to guides with clear step-by-step instructions, images/screenshots, and expected outcomes. Format with numbered steps, bullet points for tips, and FAQ section at bottom.",
                'distribution': 'Blog + YouTube video + social snippets + email newsletter feature',
                'seo_technical': 'Add HowTo schema markup to help AI platforms parse your content structure',
                'estimated_impact': f"Close {int(how_to_count * 0.4)} gap queries (~{int(how_to_count * 0.4 * 4)} monthly impressions)",
                'timeline': 'Week 1-2'
            })

        # Question queries -> Create FAQ/Q&A content
        question_count = len(query_type_groups['question'])
        if question_count >= 3:
            top_competitor = Counter([m['competitor'] for m in query_type_groups['question']]).most_common(1)[0][0]
            # Deduplicate prompts
            all_prompts = [m['prompt'] for m in query_type_groups['question']]
            example_prompts = list(dict.fromkeys(all_prompts))[:5]  # Keep order, remove duplicates
            top_persona = Counter([m['persona'] for m in query_type_groups['question']]).most_common(1)[0][0]

            recommendations.append({
                'title': 'Build Comprehensive FAQ Content',
                'content_type': 'FAQ/Q&A Content',
                'priority': 'HIGH',
                'what': f"Create FAQ pages answering common {top_persona} questions. Real questions your audience is asking:",
                'example_queries': example_prompts[:5],  # Full queries
                'why': f"{top_competitor} appears in {question_count} question-based queries where you're invisible. AI platforms prefer well-structured Q&A content.",
                'content_brief': f"Create dedicated FAQ pages organized by topic. Each Q&A should be 150-300 words with clear, direct answers. Include 'People also ask' sections linking related questions.",
                'distribution': 'Dedicated FAQ pages + embed Q&As in relevant product/service pages + create social Q&A posts',
                'seo_technical': 'Implement FAQPage schema markup so AI can easily extract Q&A pairs',
                'estimated_impact': f"Close {int(question_count * 0.35)} gap queries (~{int(question_count * 0.35 * 4)} monthly impressions)",
                'timeline': 'Week 2-3'
            })

        # Comparison queries -> Create comparison content
        comparison_count = len(query_type_groups['comparison'])
        if comparison_count >= 3:
            competitors_mentioned = Counter([m['competitor'] for m in query_type_groups['comparison']]).most_common(3)
            top_competitors = [c[0] for c in competitors_mentioned]
            # Deduplicate prompts
            all_prompts = [m['prompt'] for m in query_type_groups['comparison']]
            example_prompts = list(dict.fromkeys(all_prompts))[:5]  # Keep order, remove duplicates

            recommendations.append({
                'title': 'Create Competitor Comparison Content',
                'content_type': 'Comparison Content',
                'priority': 'HIGH',
                'what': f"Build comparison articles/pages for your top competitors. Queries you're missing:",
                'example_queries': example_prompts[:5],  # Full queries
                'why': f"You're absent from {comparison_count} comparison queries. When users compare you to competitors, you need to control the narrative.",
                'content_brief': f"Create honest comparison articles: '[Your Brand] vs {top_competitors[0]}', '[Your Brand] vs {top_competitors[1] if len(top_competitors) > 1 else top_competitors[0]}'. Include: side-by-side feature table, pricing comparison, pros/cons for each, use-case recommendations ('Choose X if...'), and user testimonials.",
                'distribution': 'Dedicated comparison landing pages + blog posts + social media graphics with key comparisons',
                'seo_technical': 'Use comparison tables with Product schema for each brand compared',
                'estimated_impact': f"Close {int(comparison_count * 0.45)} gap queries (~{int(comparison_count * 0.45 * 4)} monthly impressions)",
                'timeline': 'Week 3-4'
            })

        return recommendations[:3]  # Top 3 quick wins
