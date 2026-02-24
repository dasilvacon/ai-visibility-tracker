"""
Composite scoring system that combines multiple metrics into a single grade.
"""

from typing import Dict, List, Any, Optional


class CompositeScorer:
    """Creates composite scores and letter grades from multiple visibility metrics."""

    # Default weights for scoring dimensions
    DEFAULT_WEIGHTS = {
        'visibility': 0.30,           # 30% - How often brand appears
        'prominence': 0.20,            # 20% - Position/prominence when mentioned
        'competitive_win_rate': 0.25,  # 25% - Win/loss in head-to-head
        'citation_authority': 0.15,    # 15% - Control of narrative via citations
        'positioning_quality': 0.10,   # 10% - Quality of AI descriptions
    }

    MATURITY_THRESHOLDS = {
        'Market Leader': 80,
        'Established': 60,
        'Growing': 30,
        'Emerging': 0,
    }

    MATURITY_DESCRIPTIONS = {
        'Market Leader': 'You are a dominant force in AI conversations about your space',
        'Established': 'You have strong AI visibility with room to optimize',
        'Growing': 'You are building meaningful AI presence',
        'Emerging': 'You are in early stages of AI visibility - significant opportunity ahead',
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the composite scorer.

        Args:
            weights: Custom weights for each dimension (must sum to 1.0)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS

        # Validate weights
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

    def calculate_dimension_scores(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate individual dimension scores (0-100).

        Args:
            metrics: Dictionary containing all raw metrics

        Returns:
            Dictionary with scored dimensions
        """
        scores = {}

        # 1. Visibility Score (based on visibility rate)
        visibility_rate = metrics.get('visibility_rate', 0)
        scores['visibility'] = self._score_visibility(visibility_rate)

        # 2. Prominence Score (based on average prominence)
        prominence_rate = metrics.get('prominence_rate', 0)
        scores['prominence'] = self._score_prominence(prominence_rate)

        # 3. Competitive Win Rate Score
        competitive_win_rate = metrics.get('competitive_win_rate', 0)
        scores['competitive_win_rate'] = self._score_competitive(competitive_win_rate)

        # 4. Citation Authority Score
        citation_authority = metrics.get('citation_authority_score', 0)
        scores['citation_authority'] = citation_authority  # Already 0-100

        # 5. Positioning Quality Score (if available)
        positioning_quality = metrics.get('positioning_quality_score', 70)  # Default to C
        scores['positioning_quality'] = positioning_quality

        return scores

    def _score_visibility(self, visibility_rate: float) -> float:
        """
        Convert visibility rate to 0-100 score.

        Visibility rate is % of prompts where brand appears.
        80%+ is excellent (A), 50-80% is good (B), etc.
        """
        # Direct mapping - visibility rate is already a percentage
        return min(visibility_rate, 100.0)

    def _score_prominence(self, prominence_rate: float) -> float:
        """
        Convert prominence rate (avg citation position) to 0-100 score.

        Lower prominence rate (closer to 1) is better.
        Transform so that position 1 = 100, position 10 = 0.
        """
        # Prominence rate is average position (1-10+)
        # Invert: position 1 = 100, position 2 = 88.9, position 3 = 77.8, etc.
        if prominence_rate <= 0:
            return 100.0

        # Score decreases as position gets worse
        score = max(0, 100 - ((prominence_rate - 1) * 11.1))
        return min(score, 100.0)

    def _score_competitive(self, win_rate: float) -> float:
        """
        Convert competitive win rate to 0-100 score.

        Win rate is % of head-to-head comparisons won.
        70%+ is excellent, 50% is tied, <30% is poor.
        """
        # Amplify the competitive dimension
        # 50% win rate (tied) = 50 score
        # 100% win rate = 100 score
        # 0% win rate = 0 score
        return min(win_rate, 100.0)

    def calculate_composite_score(self, dimension_scores: Dict[str, float],
                                  metrics: Dict[str, Any]) -> tuple[float, Dict[str, float]]:
        """
        Calculate weighted composite score, adjusting weights when data is missing.

        Args:
            dimension_scores: Individual dimension scores (0-100)
            metrics: Raw metrics to check data availability

        Returns:
            Tuple of (composite_score, adjusted_weights)
        """
        # Check which dimensions have actual data
        has_competitive_data = metrics.get('competitive_win_rate', -1) >= 0 and metrics.get('total_comparison_queries', 0) > 0
        has_citation_data = metrics.get('citation_authority_score', -1) > 0 and metrics.get('total_citations', 0) > 0

        # Adjust weights if data is missing
        adjusted_weights = self.weights.copy()

        if not has_competitive_data or not has_citation_data:
            # Redistribute missing weights to visibility and prominence
            missing_weight = 0
            if not has_competitive_data:
                missing_weight += adjusted_weights['competitive_win_rate']
                adjusted_weights['competitive_win_rate'] = 0
            if not has_citation_data:
                missing_weight += adjusted_weights['citation_authority']
                adjusted_weights['citation_authority'] = 0

            # Add missing weight proportionally to visibility and prominence
            adjusted_weights['visibility'] += missing_weight * 0.6
            adjusted_weights['prominence'] += missing_weight * 0.4

        # Calculate composite score with adjusted weights
        composite = 0.0
        for dimension, weight in adjusted_weights.items():
            score = dimension_scores.get(dimension, 0)
            composite += score * weight

        return round(composite, 1), adjusted_weights

    def assign_maturity_stage(self, score: float) -> str:
        """
        Assign maturity stage based on score.

        Args:
            score: Composite score (0-100)

        Returns:
            Maturity stage (Market Leader, Established, Growing, Emerging)
        """
        for stage, threshold in self.MATURITY_THRESHOLDS.items():
            if score >= threshold:
                return stage

        return 'Emerging'

    def get_maturity_description(self, stage: str) -> Dict[str, Any]:
        """Get description and color for a maturity stage."""
        descriptions = {
            'Market Leader': {
                'label': 'Market Leader',
                'description': self.MATURITY_DESCRIPTIONS['Market Leader'],
                'color': '#10b981',  # Green
                'emoji': '🏆'
            },
            'Established': {
                'label': 'Established',
                'description': self.MATURITY_DESCRIPTIONS['Established'],
                'color': '#3b82f6',  # Blue
                'emoji': '📈'
            },
            'Growing': {
                'label': 'Growing',
                'description': self.MATURITY_DESCRIPTIONS['Growing'],
                'color': '#f59e0b',  # Amber
                'emoji': '🌱'
            },
            'Emerging': {
                'label': 'Emerging',
                'description': self.MATURITY_DESCRIPTIONS['Emerging'],
                'color': '#8b5cf6',  # Purple
                'emoji': '🚀'
            }
        }

        return descriptions.get(stage, descriptions['Emerging'])

    def create_full_scorecard(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create complete scorecard with all dimensions, composite score, and maturity stage.

        Args:
            metrics: Raw metrics from analysis

        Returns:
            Complete scorecard dictionary
        """
        # Calculate dimension scores
        dimension_scores = self.calculate_dimension_scores(metrics)

        # Calculate composite score with adjusted weights
        composite_score, adjusted_weights = self.calculate_composite_score(dimension_scores, metrics)

        # Assign maturity stage (replaces letter grade)
        maturity_stage = self.assign_maturity_stage(composite_score)
        stage_info = self.get_maturity_description(maturity_stage)

        # Check data availability for context
        has_competitive_data = metrics.get('total_comparison_queries', 0) > 0
        has_citation_data = metrics.get('total_citations', 0) > 0

        # Format dimension breakdown
        dimension_breakdown = []
        for dimension, score in dimension_scores.items():
            individual_stage = self.assign_maturity_stage(score)
            weight = adjusted_weights.get(dimension, 0)

            # Skip dimensions with 0 weight (no data)
            if weight == 0:
                continue

            dimension_breakdown.append({
                'dimension': self._format_dimension_name(dimension),
                'name': self._format_dimension_name(dimension),
                'score': round(score, 1),
                'grade': individual_stage,  # Use maturity stage for individual dimensions too
                'weight': f'{weight * 100:.0f}%',
                'contribution': round(score * weight, 1),
                'weighted_contribution': round(score * weight, 1),
                'description': self._get_dimension_description(dimension)
            })

        # Sort by weight (most important first)
        dimension_breakdown.sort(key=lambda x: adjusted_weights.get(
            self._unformat_dimension_name(x['dimension']), 0
        ), reverse=True)

        # Renumber dimension_scores for output
        dimension_scores_output = []
        for dim in dimension_breakdown:
            dimension_scores_output.append({
                'dimension': dim['dimension'],
                'name': dim['name'],
                'score': dim['score'],
                'grade': dim['grade'],
                'contribution': dim['contribution']
            })

        return {
            'composite_score': composite_score,
            'letter_grade': maturity_stage,  # Keep key for backward compatibility
            'maturity_stage': maturity_stage,
            'grade_label': stage_info['label'],
            'grade_description': stage_info['description'],
            'grade_color': stage_info['color'],
            'grade_emoji': stage_info['emoji'],
            'dimension_breakdown': dimension_breakdown,
            'dimension_scores': dimension_scores_output,
            'weights_used': adjusted_weights,
            'original_weights': self.weights,
            'has_competitive_data': has_competitive_data,
            'has_citation_data': has_citation_data,
            'strengths': self._identify_strengths(dimension_scores),
            'weaknesses': self._identify_weaknesses(dimension_scores),
        }

    def _format_dimension_name(self, dimension: str) -> str:
        """Format dimension name for display."""
        names = {
            'visibility': 'Visibility',
            'prominence': 'Prominence',
            'competitive_win_rate': 'Competitive Win Rate',
            'citation_authority': 'Citation Authority',
            'positioning_quality': 'Positioning Quality',
        }
        return names.get(dimension, dimension.replace('_', ' ').title())

    def _unformat_dimension_name(self, formatted_name: str) -> str:
        """Convert formatted name back to key."""
        reverse_map = {
            'Visibility': 'visibility',
            'Prominence': 'prominence',
            'Competitive Win Rate': 'competitive_win_rate',
            'Citation Authority': 'citation_authority',
            'Positioning Quality': 'positioning_quality',
        }
        return reverse_map.get(formatted_name, formatted_name.lower().replace(' ', '_'))

    def _get_dimension_description(self, dimension: str) -> str:
        """Get description for a dimension."""
        descriptions = {
            'visibility': 'How often your brand appears in AI responses',
            'prominence': 'Position and prominence when mentioned',
            'competitive_win_rate': 'Win rate in head-to-head comparisons',
            'citation_authority': 'Control of narrative through owned citations',
            'positioning_quality': 'Quality and differentiation of AI descriptions',
        }
        return descriptions.get(dimension, '')

    def _identify_strengths(self, dimension_scores: Dict[str, float]) -> List[str]:
        """Identify strong dimensions (score >= 75)."""
        strengths = []
        for dimension, score in dimension_scores.items():
            if score >= 75:
                strengths.append(self._format_dimension_name(dimension))
        return strengths

    def _identify_weaknesses(self, dimension_scores: Dict[str, float]) -> List[str]:
        """Identify weak dimensions (score < 60)."""
        weaknesses = []
        for dimension, score in dimension_scores.items():
            if score < 60:
                weaknesses.append(self._format_dimension_name(dimension))
        return weaknesses

    def compare_to_benchmark(self, composite_score: float,
                            industry_avg: Optional[float] = None) -> Dict[str, Any]:
        """
        Compare score to industry benchmark.

        Args:
            composite_score: Your composite score
            industry_avg: Industry average (if known)

        Returns:
            Comparison analysis
        """
        # Default industry benchmarks by category
        default_benchmarks = {
            'excellent': 85,
            'good': 70,
            'average': 55,
            'poor': 40,
        }

        industry_avg = industry_avg or default_benchmarks['average']

        diff = composite_score - industry_avg
        percentile = self._estimate_percentile(composite_score)

        return {
            'your_score': composite_score,
            'industry_average': industry_avg,
            'difference': round(diff, 1),
            'better_than_average': diff > 0,
            'estimated_percentile': percentile,
            'benchmark_context': self._get_benchmark_context(composite_score),
        }

    def _estimate_percentile(self, score: float) -> int:
        """Estimate percentile based on score."""
        # Rough estimates
        if score >= 90:
            return 95
        elif score >= 75:
            return 75
        elif score >= 60:
            return 50
        elif score >= 45:
            return 25
        else:
            return 10

    def _get_benchmark_context(self, score: float) -> str:
        """Get contextual description of score."""
        if score >= 85:
            return "Top tier - among the best in AI visibility"
        elif score >= 70:
            return "Above average - strong competitive position"
        elif score >= 55:
            return "Average - maintaining baseline visibility"
        elif score >= 40:
            return "Below average - significant improvement needed"
        else:
            return "Critical - fundamental visibility challenges"
