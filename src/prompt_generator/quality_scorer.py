"""
Quality scoring system for evaluating prompt effectiveness.

Scores prompts across multiple dimensions:
- Naturalness: Does it sound like a real search query?
- Clarity: Is the intent clear and specific?
- Length: Is it an appropriate length?
- Keyword Relevance: Does it align with the client's business?
- Diversity: Is it unique from other prompts?
"""

import re
from typing import Dict, List, Any, Tuple, Optional


class PromptQualityScorer:
    """Evaluates prompt quality across multiple dimensions."""

    # Anti-patterns that hurt naturalness
    GREETINGS = ['hi', 'hey', 'hello', 'greetings', 'good morning', 'good afternoon']
    PLEASANTRIES = ['thanks', 'thank you', 'appreciate', 'cheers', 'regards']
    FILLER_PHRASES = [
        'quick question', 'can anyone help', 'i was wondering', 'any advice',
        'any help', 'can someone', 'does anyone know', 'just curious'
    ]

    # Quality indicators
    QUESTION_WORDS = ['how', 'what', 'why', 'when', 'where', 'which', 'who']
    ACTION_WORDS = ['compare', 'find', 'looking', 'need', 'want', 'best', 'top']

    # Optimal length ranges (in words)
    IDEAL_MIN_LENGTH = 3
    IDEAL_MAX_LENGTH = 25
    TOO_SHORT = 2
    TOO_LONG = 35

    def __init__(self):
        """Initialize the quality scorer."""
        self.score_history = []

    def score_prompt(self, prompt_text: str,
                     context: Optional[Dict[str, Any]] = None,
                     existing_prompts: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Score a prompt across all quality dimensions.

        Args:
            prompt_text: The prompt text to score
            context: Optional context with persona, intent, keywords
            existing_prompts: Optional list of existing prompts for diversity check

        Returns:
            Dictionary with overall score and dimension breakdowns
        """
        scores = {
            'naturalness': self._score_naturalness(prompt_text),
            'clarity': self._score_clarity(prompt_text),
            'length': self._score_length(prompt_text),
            'keyword_relevance': self._score_keyword_relevance(prompt_text, context),
            'diversity': self._score_diversity(prompt_text, existing_prompts)
        }

        # Weighted overall score (0-100)
        overall = (
            scores['naturalness'] * 0.30 +
            scores['clarity'] * 0.25 +
            scores['length'] * 0.15 +
            scores['keyword_relevance'] * 0.20 +
            scores['diversity'] * 0.10
        )

        # Round to 1 decimal
        overall = round(overall, 1)

        # Classify quality level
        quality_level = self._classify_quality(overall)

        # Get quality issues and recommendations
        issues = self._identify_issues(prompt_text, scores)
        recommendations = self._get_recommendations(issues, scores)

        result = {
            'overall_score': overall,
            'quality_level': quality_level,
            'dimension_scores': scores,
            'issues': issues,
            'recommendations': recommendations,
            'word_count': len(prompt_text.split())
        }

        # Track for analytics
        self.score_history.append(result)

        return result

    def _score_naturalness(self, prompt_text: str) -> float:
        """
        Score how natural the prompt sounds (0-100).

        A natural prompt:
        - Has NO greetings or pleasantries
        - Has NO conversational filler
        - Sounds like a real search query
        - Is direct and to-the-point

        Args:
            prompt_text: The prompt text

        Returns:
            Naturalness score (0-100)
        """
        score = 100.0
        text_lower = prompt_text.lower()
        infractions = 0

        # Check for greetings (severe penalty - ruins naturalness)
        for greeting in self.GREETINGS:
            if re.search(r'\b' + greeting + r'\b', text_lower):
                score -= 40
                infractions += 1
                break

        # Check for pleasantries (severe penalty)
        for pleasantry in self.PLEASANTRIES:
            if re.search(r'\b' + pleasantry + r'\b', text_lower):
                score -= 35
                infractions += 1
                break

        # Check for filler phrases (major penalty)
        for filler in self.FILLER_PHRASES:
            if filler in text_lower:
                score -= 30
                infractions += 1
                break

        # Multiple infractions = even worse (stacking penalty)
        if infractions >= 2:
            score -= 15  # Additional penalty for multiple issues

        # Check for excessive punctuation (!!! or ???)
        if '!!' in prompt_text or '??' in prompt_text:
            score -= 10

        # Check for ALL CAPS (unnatural)
        caps_words = [w for w in prompt_text.split() if w.isupper() and len(w) > 2]
        if len(caps_words) > 1:
            score -= 15

        # Bonus for natural structure
        has_question_word = any(w in text_lower for w in self.QUESTION_WORDS)
        has_action_word = any(w in text_lower for w in self.ACTION_WORDS)
        if has_question_word or has_action_word:
            score += 5

        return max(0, min(100, score))

    def _score_clarity(self, prompt_text: str) -> float:
        """
        Score how clear and specific the prompt is (0-100).

        A clear prompt:
        - Has a specific topic/keyword
        - Intent is understandable
        - Not too vague or generic

        Args:
            prompt_text: The prompt text

        Returns:
            Clarity score (0-100)
        """
        score = 70.0  # Start at a reasonable baseline
        text_lower = prompt_text.lower()

        # Too vague (single-word or very short)
        word_count = len(prompt_text.split())
        if word_count <= 2:
            score -= 30
        elif word_count == 3:
            score -= 10

        # Contains specific product/topic indicators (good)
        specific_indicators = ['for', 'with', 'on', 'vs', 'compared', 'between']
        if any(ind in text_lower for ind in specific_indicators):
            score += 10

        # Has clear question structure
        if '?' in prompt_text:
            score += 5

        # Contains comparison language (very specific)
        comparison_words = ['vs', 'versus', 'compared to', 'or', 'between']
        if any(comp in text_lower for comp in comparison_words):
            score += 10

        # Too many questions (confusing)
        question_count = prompt_text.count('?')
        if question_count > 2:
            score -= 15

        # Generic words that reduce specificity
        generic_words = ['something', 'anything', 'stuff', 'things', 'whatever']
        if any(gen in text_lower for gen in generic_words):
            score -= 20

        return max(0, min(100, score))

    def _score_length(self, prompt_text: str) -> float:
        """
        Score whether the prompt length is appropriate (0-100).

        Ideal length: 3-25 words
        Acceptable: 2-35 words

        Args:
            prompt_text: The prompt text

        Returns:
            Length score (0-100)
        """
        word_count = len(prompt_text.split())

        # Ideal range
        if self.IDEAL_MIN_LENGTH <= word_count <= self.IDEAL_MAX_LENGTH:
            # Perfect range, slight bonus for sweet spot (5-15 words)
            if 5 <= word_count <= 15:
                return 100.0
            return 95.0

        # Too short
        if word_count < self.IDEAL_MIN_LENGTH:
            if word_count <= self.TOO_SHORT:
                return 40.0  # Very short
            return 70.0  # Slightly short

        # Too long
        if word_count > self.IDEAL_MAX_LENGTH:
            if word_count >= self.TOO_LONG:
                return 30.0  # Way too long
            # Gradual penalty
            excess = word_count - self.IDEAL_MAX_LENGTH
            penalty = excess * 6  # 6 points per excess word
            return max(40, 95 - penalty)

        return 85.0  # Default for edge cases

    def _score_keyword_relevance(self, prompt_text: str,
                                  context: Optional[Dict[str, Any]] = None) -> float:
        """
        Score how well the prompt aligns with the client's business (0-100).

        Uses context if provided (persona, intent, keywords).

        Args:
            prompt_text: The prompt text
            context: Optional context dictionary

        Returns:
            Keyword relevance score (0-100)
        """
        # Without context, we can only do basic checks
        if not context:
            # Basic heuristic: longer prompts with specific terms score higher
            word_count = len(prompt_text.split())
            if word_count >= 5:
                return 80.0
            return 70.0

        score = 70.0  # Baseline
        text_lower = prompt_text.lower()

        # Check if main keyword is present
        if 'keyword' in context:
            keyword = context['keyword'].lower()
            if keyword in text_lower:
                score += 20

        # Check if it matches the intent type
        if 'intent_type' in context:
            intent = context['intent_type']

            # Verify intent alignment
            if intent == 'comparison' and any(w in text_lower for w in ['vs', 'versus', 'compared', 'or', 'between']):
                score += 10
            elif intent == 'how_to' and 'how' in text_lower:
                score += 10
            elif intent == 'recommendation' and any(w in text_lower for w in ['best', 'top', 'recommend']):
                score += 10
            elif intent == 'review' and any(w in text_lower for w in ['review', 'worth', 'quality']):
                score += 10

        # Check persona alignment (if provided) — generic, works for any industry
        if 'persona' in context:
            persona = context['persona'].lower()
            # Extract meaningful words from persona name (skip filler words)
            skip_words = {'the', 'a', 'an', 'of', 'for', 'and', 'or', 'with', 'in', 'on', 'to'}
            persona_words = [w for w in persona.split() if w not in skip_words and len(w) > 2]
            # Check if any persona-identifying word appears in the prompt
            if any(pw in text_lower for pw in persona_words):
                score += 10
            # Also check priority_topics if provided in context
            elif 'priority_topics' in context:
                topics = context['priority_topics'] if isinstance(context['priority_topics'], list) else []
                for topic in topics[:3]:
                    if topic.lower() in text_lower:
                        score += 8
                        break

        return max(0, min(100, score))

    def _score_diversity(self, prompt_text: str,
                        existing_prompts: Optional[List[str]] = None) -> float:
        """
        Score how unique this prompt is compared to existing ones (0-100).

        Uses simple similarity heuristics without heavy NLP.

        Args:
            prompt_text: The prompt text
            existing_prompts: List of existing prompt texts

        Returns:
            Diversity score (0-100)
        """
        # If no existing prompts, it's perfectly diverse
        if not existing_prompts:
            return 100.0

        # Simple word-based similarity
        words_set = set(prompt_text.lower().split())

        # Find max similarity with any existing prompt
        max_similarity = 0.0
        for existing in existing_prompts:
            existing_words = set(existing.lower().split())

            # Jaccard similarity
            intersection = words_set & existing_words
            union = words_set | existing_words

            if union:
                similarity = len(intersection) / len(union)
                max_similarity = max(max_similarity, similarity)

        # Convert similarity to diversity score
        # High similarity = low diversity
        diversity_score = (1 - max_similarity) * 100

        return round(diversity_score, 1)

    def _classify_quality(self, overall_score: float) -> str:
        """
        Classify quality level based on overall score.

        Args:
            overall_score: The overall quality score (0-100)

        Returns:
            Quality level string
        """
        if overall_score >= 90:
            return "Excellent"
        elif overall_score >= 75:
            return "Good"
        elif overall_score >= 60:
            return "Fair"
        else:
            return "Poor"

    def _identify_issues(self, prompt_text: str, scores: Dict[str, float]) -> List[str]:
        """
        Identify specific quality issues with the prompt.

        Args:
            prompt_text: The prompt text
            scores: Dictionary of dimension scores

        Returns:
            List of issue descriptions
        """
        issues = []
        text_lower = prompt_text.lower()

        # Naturalness issues
        if scores['naturalness'] < 70:
            if any(g in text_lower for g in self.GREETINGS):
                issues.append("Contains greetings (e.g., 'Hi', 'Hey')")
            if any(p in text_lower for p in self.PLEASANTRIES):
                issues.append("Contains pleasantries (e.g., 'Thanks', 'Appreciate')")
            if any(f in text_lower for f in self.FILLER_PHRASES):
                issues.append("Contains conversational filler")

        # Clarity issues
        if scores['clarity'] < 60:
            word_count = len(prompt_text.split())
            if word_count <= 2:
                issues.append("Too vague - needs more context")
            if any(g in text_lower for g in ['something', 'anything', 'stuff']):
                issues.append("Uses generic language")

        # Length issues
        word_count = len(prompt_text.split())
        if scores['length'] < 70:
            if word_count < self.IDEAL_MIN_LENGTH:
                issues.append(f"Too short ({word_count} words)")
            elif word_count > self.TOO_LONG:
                issues.append(f"Too long ({word_count} words)")

        # Diversity issues
        if scores['diversity'] < 60:
            issues.append("Very similar to existing prompts")

        return issues

    def _get_recommendations(self, issues: List[str], scores: Dict[str, float]) -> List[str]:
        """
        Generate recommendations for improving the prompt.

        Args:
            issues: List of identified issues
            scores: Dictionary of dimension scores

        Returns:
            List of recommendations
        """
        recommendations = []

        # Naturalness recommendations
        if scores['naturalness'] < 70:
            recommendations.append("Remove greetings and pleasantries - make it direct")
            recommendations.append("Phrase it like a real search query")

        # Clarity recommendations
        if scores['clarity'] < 60:
            recommendations.append("Add more specific details about what you're looking for")
            recommendations.append("Include the product/topic name clearly")

        # Length recommendations
        if scores['length'] < 70:
            if len(issues) > 0 and "Too short" in issues[0]:
                recommendations.append("Add more context - aim for 5-15 words")
            elif len(issues) > 0 and "Too long" in issues[0]:
                recommendations.append("Simplify - remove unnecessary words")

        # Diversity recommendations
        if scores['diversity'] < 60:
            recommendations.append("Try a different angle or phrasing to increase uniqueness")

        return recommendations

    def get_batch_statistics(self, prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate aggregate quality statistics for a batch of prompts.

        Args:
            prompts: List of prompt dictionaries with quality scores

        Returns:
            Dictionary with batch statistics
        """
        if not prompts:
            return {}

        # Extract overall scores
        overall_scores = [p.get('quality_score', {}).get('overall_score', 0) for p in prompts]
        quality_levels = [p.get('quality_score', {}).get('quality_level', 'Unknown') for p in prompts]

        # Calculate stats
        stats = {
            'total_prompts': len(prompts),
            'average_score': round(sum(overall_scores) / len(overall_scores), 1) if overall_scores else 0,
            'min_score': min(overall_scores) if overall_scores else 0,
            'max_score': max(overall_scores) if overall_scores else 0,
            'quality_distribution': {
                'Excellent': quality_levels.count('Excellent'),
                'Good': quality_levels.count('Good'),
                'Fair': quality_levels.count('Fair'),
                'Poor': quality_levels.count('Poor')
            },
            'excellent_percentage': round(quality_levels.count('Excellent') / len(quality_levels) * 100, 1) if quality_levels else 0
        }

        # Dimension averages
        dimension_totals = {'naturalness': 0, 'clarity': 0, 'length': 0, 'keyword_relevance': 0, 'diversity': 0}
        count = 0

        for prompt in prompts:
            if 'quality_score' in prompt and 'dimension_scores' in prompt['quality_score']:
                dims = prompt['quality_score']['dimension_scores']
                for dim in dimension_totals:
                    dimension_totals[dim] += dims.get(dim, 0)
                count += 1

        if count > 0:
            stats['dimension_averages'] = {
                dim: round(total / count, 1) for dim, total in dimension_totals.items()
            }

        return stats
