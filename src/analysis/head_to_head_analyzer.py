"""
Head-to-head competitive comparison analyzer.
Detects comparison queries and determines win/loss/tie outcomes.
"""

import re
from typing import Dict, List, Any, Optional
from collections import defaultdict


class HeadToHeadAnalyzer:
    """Analyzes direct competitive comparisons and determines outcomes."""

    def __init__(self, brand_name: str, competitor_names: List[str]):
        """
        Initialize the head-to-head analyzer.

        Args:
            brand_name: Primary brand name
            competitor_names: List of competitor brand names
        """
        self.brand_name = brand_name
        self.competitor_names = competitor_names

    def is_comparison_query(self, prompt_text: str) -> Dict[str, Any]:
        """
        Detect if a prompt is a head-to-head comparison query.

        Args:
            prompt_text: The prompt text

        Returns:
            Dictionary with:
            - is_comparison: Boolean
            - comparison_type: 'explicit', 'implicit', or None
            - competitors_in_query: List of competitors mentioned in prompt
        """
        prompt_lower = prompt_text.lower()
        brand_lower = self.brand_name.lower()

        # Check if brand is in the query
        brand_in_query = brand_lower in prompt_lower

        # Find competitors mentioned in query
        competitors_in_query = [
            comp for comp in self.competitor_names
            if comp.lower() in prompt_lower
        ]

        # Explicit comparison patterns
        explicit_patterns = [
            r'\b(vs\.?|versus|compared?\s+to|vs|or)\b',
            r'\b(better|which|difference|choose\s+between)\b',
            r'\b(growclass\s+and\s+\w+|growclass\s+or\s+\w+)\b',
        ]

        is_explicit = any(
            re.search(pattern, prompt_lower)
            for pattern in explicit_patterns
        )

        # Determine if it's a comparison
        is_comparison = False
        comparison_type = None

        if brand_in_query and competitors_in_query:
            if is_explicit:
                is_comparison = True
                comparison_type = 'explicit'
            else:
                # Brand + competitor mentioned but not explicit comparison
                is_comparison = True
                comparison_type = 'implicit'

        return {
            'is_comparison': is_comparison,
            'comparison_type': comparison_type,
            'competitors_in_query': competitors_in_query,
            'brand_in_query': brand_in_query
        }

    def determine_outcome(self, response_text: str, prompt_text: str,
                         visibility_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the outcome of a head-to-head comparison.

        Args:
            response_text: The AI's response
            prompt_text: The original prompt
            visibility_data: Visibility scoring data

        Returns:
            Dictionary with outcome analysis
        """
        # Check if this is a comparison query
        comparison_check = self.is_comparison_query(prompt_text)
        if not comparison_check['is_comparison']:
            return {'is_comparison': False}

        brand_mentioned = visibility_data.get('brand_mentioned', False)
        competitors_mentioned = visibility_data.get('competitors_mentioned', [])
        competitor_details = visibility_data.get('competitor_details', {})

        # Get competitors that were actually in the query
        query_competitors = comparison_check['competitors_in_query']

        outcomes = {}

        for competitor in query_competitors:
            if competitor not in competitors_mentioned:
                # Competitor was in query but not mentioned in response
                # This is likely a win for us if we were mentioned
                if brand_mentioned:
                    outcomes[competitor] = 'win'
                else:
                    outcomes[competitor] = 'unknown'
                continue

            # Both brand and competitor mentioned - analyze who won
            outcome = self._analyze_recommendation(
                response_text,
                self.brand_name,
                competitor,
                visibility_data
            )
            outcomes[competitor] = outcome

        return {
            'is_comparison': True,
            'comparison_type': comparison_check['comparison_type'],
            'competitors_compared': query_competitors,
            'outcomes': outcomes,
            'overall_win': self._calculate_overall_outcome(outcomes)
        }

    def _analyze_recommendation(self, response_text: str, brand: str,
                               competitor: str, visibility_data: Dict[str, Any]) -> str:
        """
        Analyze who AI recommends in the response.

        Args:
            response_text: The AI's response
            brand: Brand name
            competitor: Competitor name
            visibility_data: Visibility scoring data

        Returns:
            'win', 'loss', 'tie', or 'unclear'
        """
        response_lower = response_text.lower()
        brand_lower = brand.lower()
        comp_lower = competitor.lower()

        # Strong recommendation patterns (definitive win/loss)
        strong_win_patterns = [
            rf'\b{re.escape(brand_lower)}\s+(?:is|would be)\s+(?:the\s+)?better\b',
            rf'\brecommend\s+{re.escape(brand_lower)}\b',
            rf'\b{re.escape(brand_lower)}\s+stands out\b',
            rf'\b{re.escape(brand_lower)}\s+(?:is|offers)\s+superior\b',
            rf'\bgo with\s+{re.escape(brand_lower)}\b',
            rf'\bchoose\s+{re.escape(brand_lower)}\b',
        ]

        strong_loss_patterns = [
            rf'\b{re.escape(comp_lower)}\s+(?:is|would be)\s+(?:the\s+)?better\b',
            rf'\brecommend\s+{re.escape(comp_lower)}\b',
            rf'\b{re.escape(comp_lower)}\s+stands out\b',
            rf'\b{re.escape(comp_lower)}\s+(?:is|offers)\s+superior\b',
            rf'\bgo with\s+{re.escape(comp_lower)}\b',
            rf'\bchoose\s+{re.escape(comp_lower)}\b',
        ]

        # Check strong patterns
        for pattern in strong_win_patterns:
            if re.search(pattern, response_lower):
                return 'win'

        for pattern in strong_loss_patterns:
            if re.search(pattern, response_lower):
                return 'loss'

        # Check positioning - who is mentioned first
        brand_pos = visibility_data.get('citation_position')
        competitor_details = visibility_data.get('competitor_details', {})

        if competitor in competitor_details:
            comp_positions = competitor_details[competitor].get('positions', [])
            if comp_positions and brand_pos:
                comp_first_pos = comp_positions[0]

                # First mention advantage (unless contradicted by strong language)
                if comp_first_pos < brand_pos:
                    # Check for hedging language that might indicate tie
                    if self._has_hedging_language(response_text):
                        return 'tie'
                    return 'loss'
                elif brand_pos < comp_first_pos:
                    if self._has_hedging_language(response_text):
                        return 'tie'
                    return 'win'

        # Check for tie language
        tie_patterns = [
            r'\bboth\s+(?:are\s+)?(?:good|great|excellent|strong)\b',
            r'\bdepends\s+on\s+your\b',
            r'\beach\s+has\s+(?:its\s+)?(?:advantages|strengths)\b',
            r'\bno\s+clear\s+winner\b',
            r'\bequally\b',
        ]

        for pattern in tie_patterns:
            if re.search(pattern, response_lower):
                return 'tie'

        # Default to unclear if we can't determine
        return 'unclear'

    def _has_hedging_language(self, response_text: str) -> bool:
        """Check if response has hedging/balancing language suggesting a tie."""
        response_lower = response_text.lower()

        hedging_patterns = [
            r'\bhowever\b',
            r'\bon the other hand\b',
            r'\bthat said\b',
            r'\bboth\s+offer\b',
            r'\beach\s+provides\b',
        ]

        hedge_count = sum(
            1 for pattern in hedging_patterns
            if re.search(pattern, response_lower)
        )

        return hedge_count >= 2  # Multiple hedges suggest balanced comparison

    def _calculate_overall_outcome(self, outcomes: Dict[str, str]) -> str:
        """Calculate overall outcome from individual competitor outcomes."""
        if not outcomes:
            return 'unclear'

        wins = sum(1 for o in outcomes.values() if o == 'win')
        losses = sum(1 for o in outcomes.values() if o == 'loss')
        ties = sum(1 for o in outcomes.values() if o == 'tie')

        if wins > losses:
            return 'win'
        elif losses > wins:
            return 'loss'
        elif wins == losses and ties > 0:
            return 'tie'
        else:
            return 'unclear'

    def aggregate_head_to_head_results(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate all head-to-head comparison results.

        Args:
            scored_results: List of results with visibility scores

        Returns:
            Dictionary with aggregated head-to-head statistics
        """
        competitor_records = defaultdict(lambda: {
            'wins': 0,
            'losses': 0,
            'ties': 0,
            'unclear': 0,
            'total_comparisons': 0,
            'prompts': []
        })

        total_comparisons = 0
        comparison_prompts = []

        for result in scored_results:
            prompt_text = result.get('prompt_text', '')
            response_text = result.get('response_text', '')
            visibility = result.get('visibility', {})

            # Determine outcome for this result
            outcome_data = self.determine_outcome(response_text, prompt_text, visibility)

            if not outcome_data.get('is_comparison'):
                continue

            total_comparisons += 1
            comparison_prompts.append({
                'prompt': prompt_text,
                'platform': result.get('platform'),
                'outcomes': outcome_data.get('outcomes', {}),
                'overall': outcome_data.get('overall_win')
            })

            # Track per-competitor
            for competitor, outcome in outcome_data.get('outcomes', {}).items():
                competitor_records[competitor]['total_comparisons'] += 1

                if outcome == 'win':
                    competitor_records[competitor]['wins'] += 1
                elif outcome == 'loss':
                    competitor_records[competitor]['losses'] += 1
                elif outcome == 'tie':
                    competitor_records[competitor]['ties'] += 1
                else:
                    competitor_records[competitor]['unclear'] += 1

                competitor_records[competitor]['prompts'].append({
                    'prompt': prompt_text,
                    'outcome': outcome,
                    'platform': result.get('platform')
                })

        # Calculate win rates and status
        battlecard = []
        for competitor, record in competitor_records.items():
            total = record['total_comparisons']
            if total == 0:
                continue

            wins = record['wins']
            losses = record['losses']
            ties = record['ties']

            # Calculate win rate (ties count as 0.5)
            win_rate = ((wins + (ties * 0.5)) / total * 100) if total > 0 else 0

            # Determine status
            if wins > losses:
                status = 'winning'
            elif losses > wins:
                status = 'losing'
            else:
                status = 'tied'

            battlecard.append({
                'competitor': competitor,
                'wins': wins,
                'losses': losses,
                'ties': ties,
                'unclear': record['unclear'],
                'total_comparisons': total,
                'win_rate': round(win_rate, 1),
                'status': status,
                'sample_prompts': record['prompts'][:3]  # Top 3 examples
            })

        # Sort by total comparisons (most compared competitors first)
        battlecard.sort(key=lambda x: x['total_comparisons'], reverse=True)

        return {
            'total_comparison_queries': total_comparisons,
            'total_wins': sum(b['wins'] for b in battlecard),
            'total_losses': sum(b['losses'] for b in battlecard),
            'total_ties': sum(b['ties'] for b in battlecard),
            'overall_win_rate': self._calculate_overall_win_rate(battlecard),
            'battlecard': battlecard,
            'comparison_prompts': comparison_prompts[:10]  # Top 10 examples
        }

    def _calculate_overall_win_rate(self, battlecard: List[Dict[str, Any]]) -> float:
        """Calculate overall win rate across all competitors."""
        total_wins = sum(b['wins'] for b in battlecard)
        total_losses = sum(b['losses'] for b in battlecard)
        total_ties = sum(b['ties'] for b in battlecard)

        total_comparisons = total_wins + total_losses + total_ties

        if total_comparisons == 0:
            return 0.0

        # Ties count as 0.5 wins
        effective_wins = total_wins + (total_ties * 0.5)
        return round((effective_wins / total_comparisons) * 100, 1)
