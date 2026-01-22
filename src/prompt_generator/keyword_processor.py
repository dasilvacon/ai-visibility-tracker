"""
Keyword processor for loading and processing SEO data and keywords.
"""

import csv
import os
from typing import Dict, List, Any, Optional
from collections import defaultdict


class KeywordProcessor:
    """Processes keywords and SEO data for prompt generation."""

    def __init__(self, keywords_file: str):
        """
        Initialize the keyword processor.

        Args:
            keywords_file: Path to keywords CSV file
        """
        self.keywords_file = keywords_file
        self.keywords = []
        self.keywords_by_intent = defaultdict(list)
        self._load_keywords()

    def _load_keywords(self) -> None:
        """Load keywords from CSV file."""
        if not os.path.exists(self.keywords_file):
            raise FileNotFoundError(f"Keywords file not found: {self.keywords_file}")

        with open(self.keywords_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                keyword_data = {
                    'keyword': row['keyword'],
                    'search_volume': int(row.get('search_volume', 0)),
                    'intent_type': row.get('intent_type', 'informational'),
                    'competitor_brands': [b.strip() for b in row.get('competitor_brands', '').split(',') if b.strip()]
                }
                self.keywords.append(keyword_data)
                self.keywords_by_intent[keyword_data['intent_type']].append(keyword_data)

    def get_all_keywords(self) -> List[Dict[str, Any]]:
        """
        Get all keywords.

        Returns:
            List of keyword dictionaries
        """
        return self.keywords

    def get_keywords_by_intent(self, intent_type: str) -> List[Dict[str, Any]]:
        """
        Get keywords filtered by intent type.

        Args:
            intent_type: Intent type to filter by

        Returns:
            List of keyword dictionaries
        """
        return self.keywords_by_intent.get(intent_type, [])

    def get_high_volume_keywords(self, threshold: int = 1000) -> List[Dict[str, Any]]:
        """
        Get keywords with search volume above threshold.

        Args:
            threshold: Minimum search volume

        Returns:
            List of high-volume keyword dictionaries
        """
        return [k for k in self.keywords if k['search_volume'] >= threshold]

    def get_keywords_with_competitors(self) -> List[Dict[str, Any]]:
        """
        Get keywords that have competitor brands listed.

        Returns:
            List of keyword dictionaries with competitors
        """
        return [k for k in self.keywords if k['competitor_brands']]

    def get_random_keywords(self, count: int, intent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get random keywords, optionally filtered by intent.

        Args:
            count: Number of keywords to return
            intent_type: Optional intent type to filter by

        Returns:
            List of random keyword dictionaries
        """
        import random

        if intent_type:
            pool = self.keywords_by_intent.get(intent_type, [])
        else:
            pool = self.keywords

        if not pool:
            return []

        # Sample with replacement if count > pool size
        if count <= len(pool):
            return random.sample(pool, count)
        else:
            return random.choices(pool, k=count)

    def get_intent_distribution(self) -> Dict[str, int]:
        """
        Get distribution of keywords by intent type.

        Returns:
            Dictionary mapping intent type to count
        """
        return {intent: len(keywords) for intent, keywords in self.keywords_by_intent.items()}

    def get_all_competitors(self) -> List[str]:
        """
        Get unique list of all competitor brands.

        Returns:
            List of unique competitor brand names
        """
        competitors = set()
        for keyword in self.keywords:
            competitors.update(keyword['competitor_brands'])
        return sorted(list(competitors))

    def select_keywords_for_topic(self, topic: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        Select keywords that are relevant to a given topic.

        Args:
            topic: Topic string to match against
            count: Number of keywords to return

        Returns:
            List of relevant keyword dictionaries
        """
        import random

        # Simple relevance: keywords containing any word from the topic
        topic_words = set(topic.lower().split())
        relevant = []

        for keyword in self.keywords:
            keyword_words = set(keyword['keyword'].lower().split())
            if topic_words & keyword_words:  # If there's any overlap
                relevant.append(keyword)

        if not relevant:
            # Fall back to random keywords
            return self.get_random_keywords(count)

        return random.sample(relevant, min(count, len(relevant)))

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about keywords.

        Returns:
            Dictionary with statistics
        """
        total_volume = sum(k['search_volume'] for k in self.keywords)
        avg_volume = total_volume / len(self.keywords) if self.keywords else 0

        return {
            'total_keywords': len(self.keywords),
            'total_search_volume': total_volume,
            'average_search_volume': avg_volume,
            'intent_types': list(self.keywords_by_intent.keys()),
            'keywords_with_competitors': len(self.get_keywords_with_competitors()),
            'unique_competitors': len(self.get_all_competitors())
        }

    def validate_keywords(self) -> List[str]:
        """
        Validate keyword data and return any issues.

        Returns:
            List of validation error messages
        """
        issues = []

        # Check for required fields
        required_fields = ['keyword', 'search_volume', 'intent_type']
        for i, keyword in enumerate(self.keywords):
            for field in required_fields:
                if field not in keyword or keyword[field] == '':
                    issues.append(f"Keyword at row {i+1} missing required field: {field}")

        # Check for duplicate keywords
        keyword_texts = [k['keyword'] for k in self.keywords]
        if len(keyword_texts) != len(set(keyword_texts)):
            issues.append("Duplicate keywords found")

        # Check search volumes are non-negative
        for keyword in self.keywords:
            if keyword['search_volume'] < 0:
                issues.append(f"Keyword '{keyword['keyword']}' has negative search volume")

        return issues
