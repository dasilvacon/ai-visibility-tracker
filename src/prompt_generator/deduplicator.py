"""
Prompt deduplication module for real-time duplicate detection.
"""

import re
from difflib import SequenceMatcher
from typing import Dict, List, Any, Tuple, Set


class PromptDeduplicator:
    """Real-time deduplication for prompt generation."""

    def __init__(self, exact_match: bool = True,
                 similarity_threshold: float = 0.90,
                 use_semantic: bool = False):
        """
        Initialize the deduplicator.

        Args:
            exact_match: Enable exact match detection (case-insensitive)
            similarity_threshold: Threshold for similarity matching (0.0-1.0)
            use_semantic: Enable semantic similarity (requires sentence-transformers)
        """
        self.exact_match = exact_match
        self.similarity_threshold = similarity_threshold
        self.use_semantic = use_semantic

        # Tracking sets
        self.seen_exact: Set[str] = set()
        self.prompt_history: List[str] = []

        # Statistics
        self.stats = {
            'total_checked': 0,
            'exact_duplicates': 0,
            'similar_duplicates': 0,
            'semantic_duplicates': 0
        }

    def clean_prompt_for_comparison(self, text: str) -> str:
        """
        Clean and normalize prompt text for comparison.
        Extracted from html_report_generator.py:_clean_query_for_display

        Examples:
        - "Compare how to apply eyeshadow for beginners to Pat McGrath Labs"
          -> "how to apply eyeshadow for beginners"
        - "Help me learn about cruelty free luxury eyeshadow"
          -> "cruelty free luxury eyeshadow"
        """
        # Pattern: "Compare [content/how-to topic] to [Brand]"
        match = re.match(r'^Compare (how to .+?|.+?) to [A-Z][a-zA-Z\s]+$', text, re.IGNORECASE)
        if match:
            text = match.group(1).strip()

        # Pattern: "Help me learn about X"
        if text.lower().startswith('help me learn about'):
            text = text[19:].strip()

        # Pattern: "What should I know about X"
        if text.lower().startswith('what should i know about'):
            text = text[24:].strip()

        # Normalize whitespace and case
        text = ' '.join(text.split())  # Collapse multiple spaces
        text = text.lower()

        # Remove punctuation at the end
        text = text.rstrip('?!.,;:')

        return text

    def check_duplicate(self, prompt_text: str) -> Dict[str, Any]:
        """
        Check if a prompt is a duplicate.

        Args:
            prompt_text: The prompt text to check

        Returns:
            Dict with keys:
                - is_duplicate: bool
                - duplicate_type: str ('exact', 'similar', 'semantic', or None)
                - similar_to: str (the similar prompt, if any)
                - similarity_score: float (if similar duplicate)
        """
        self.stats['total_checked'] += 1

        # Clean the prompt
        cleaned = self.clean_prompt_for_comparison(prompt_text)

        # Check exact match
        if self.exact_match and cleaned in self.seen_exact:
            self.stats['exact_duplicates'] += 1
            return {
                'is_duplicate': True,
                'duplicate_type': 'exact',
                'similar_to': None,
                'similarity_score': 1.0
            }

        # Check similarity match
        if self.similarity_threshold > 0:
            similar = self._find_similar_prompt(cleaned)
            if similar:
                self.stats['similar_duplicates'] += 1
                return {
                    'is_duplicate': True,
                    'duplicate_type': 'similar',
                    'similar_to': similar['prompt'],
                    'similarity_score': similar['score']
                }

        # Not a duplicate - add to tracking
        self.seen_exact.add(cleaned)
        self.prompt_history.append(cleaned)

        return {
            'is_duplicate': False,
            'duplicate_type': None,
            'similar_to': None,
            'similarity_score': 0.0
        }

    def _find_similar_prompt(self, cleaned_prompt: str) -> Dict[str, Any]:
        """
        Find similar prompts in history using string similarity.

        Args:
            cleaned_prompt: Cleaned prompt text

        Returns:
            Dict with 'prompt' and 'score' if found, None otherwise
        """
        for existing in self.prompt_history:
            similarity = self._calculate_similarity(cleaned_prompt, existing)
            if similarity >= self.similarity_threshold:
                return {
                    'prompt': existing,
                    'score': similarity
                }
        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using SequenceMatcher.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0-1.0)
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def deduplicate_batch(self, prompts: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Deduplicate a batch of prompts.

        Args:
            prompts: List of prompt dicts with 'prompt_text' key

        Returns:
            Tuple of (unique_prompts, duplicates_removed, stats)
        """
        unique = []
        duplicates = []

        for prompt in prompts:
            result = self.check_duplicate(prompt['prompt_text'])
            if result['is_duplicate']:
                duplicates.append({
                    **prompt,
                    'duplicate_info': result
                })
            else:
                unique.append(prompt)

        stats = {
            'total_input': len(prompts),
            'unique': len(unique),
            'duplicates': len(duplicates),
            'duplicate_rate': len(duplicates) / len(prompts) if prompts else 0,
            **self.stats
        }

        return unique, duplicates, stats

    def get_stats(self) -> Dict[str, Any]:
        """Get current deduplication statistics."""
        return {
            **self.stats,
            'unique_prompts': len(self.seen_exact)
        }

    def reset(self):
        """Reset the deduplicator state."""
        self.seen_exact.clear()
        self.prompt_history.clear()
        self.stats = {
            'total_checked': 0,
            'exact_duplicates': 0,
            'similar_duplicates': 0,
            'semantic_duplicates': 0
        }
