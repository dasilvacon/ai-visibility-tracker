"""
Fan-out Query Collector — captures real sub-queries from Gemini grounding data.

When the Gemini client runs a prompt with Google Search grounding enabled,
the response includes `web_search_queries` — the actual sub-queries Google
ran behind the scenes. This module:

  1. Collects those fan-out queries from test results
  2. Groups them by the original prompt / topic cluster
  3. Stores them for analysis and future prompt generation
  4. Identifies patterns (what words does Google add? which angles recur?)

This gives ground-truth data about how Google actually decomposes questions,
replacing the need to simulate or guess at fan-out behavior.

Usage:
    collector = FanoutCollector(client_slug='ontario_caregiver_organization')
    collector.collect_from_results(scored_results)
    collector.save()

    # Later — use real fan-out queries as test prompts
    real_fanouts = collector.get_fanout_prompts_for_topic('hospital discharge planning')
"""

import json
import os
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
from datetime import datetime


class FanoutCollector:
    """
    Collects and analyzes real fan-out queries from Gemini grounding metadata.
    """

    def __init__(self, client_slug: str, base_dir: str = 'data'):
        """
        Args:
            client_slug: Client identifier (e.g., 'ontario_caregiver_organization')
            base_dir: Base data directory
        """
        self.client_slug = client_slug
        self.storage_dir = os.path.join(base_dir, client_slug)
        self.fanout_file = os.path.join(self.storage_dir, f'{client_slug}_fanout_queries.json')

        # In-memory collection
        self.collected = []  # Raw collected entries
        self.by_prompt = defaultdict(list)  # prompt_text → [fan-out queries]
        self.by_topic = defaultdict(list)  # cluster_topic → [fan-out queries]

        # Load existing data if available
        self._load_existing()

    def collect_from_results(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract fan-out queries from Gemini test results.

        Only processes results from the 'gemini' platform that have
        web_search_queries in their metadata.

        Args:
            scored_results: List of test result dicts

        Returns:
            Collection stats
        """
        new_entries = 0
        new_queries = 0

        for result in scored_results:
            platform = result.get('platform', '')
            if platform != 'gemini':
                continue

            metadata = result.get('metadata', {})
            web_queries = metadata.get('web_search_queries', [])
            if not web_queries:
                continue

            prompt_text = result.get('prompt_text', '')
            prompt_id = result.get('prompt_id', '')
            cluster_topic = metadata.get('cluster_topic', '')
            cluster_role = metadata.get('cluster_role', '')
            persona = metadata.get('persona', '')

            entry = {
                'prompt_id': prompt_id,
                'prompt_text': prompt_text,
                'platform': 'gemini',
                'cluster_topic': cluster_topic,
                'cluster_role': cluster_role,
                'persona': persona,
                'web_search_queries': web_queries,
                'query_count': len(web_queries),
                'collected_at': datetime.now().isoformat(),
            }

            self.collected.append(entry)
            self.by_prompt[prompt_text].extend(web_queries)

            if cluster_topic:
                self.by_topic[cluster_topic].extend(web_queries)

            new_entries += 1
            new_queries += len(web_queries)

        return {
            'new_entries': new_entries,
            'new_queries': new_queries,
            'total_entries': len(self.collected),
            'total_unique_queries': len(self._all_unique_queries()),
            'topics_with_fanout': len(self.by_topic),
        }

    def get_fanout_prompts_for_topic(self, topic: str) -> List[str]:
        """
        Get deduplicated real fan-out queries for a specific topic.

        These can be used as test prompts — they're the actual sub-queries
        Google ran when answering questions about this topic.

        Args:
            topic: Topic name to look up

        Returns:
            List of unique fan-out query strings
        """
        queries = self.by_topic.get(topic, [])
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for q in queries:
            q_lower = q.lower().strip()
            if q_lower not in seen:
                seen.add(q_lower)
                unique.append(q)
        return unique

    def get_all_fanout_topics(self) -> List[Dict[str, Any]]:
        """
        Get all topics that have fan-out data, with stats.

        Returns:
            List of dicts with topic, query_count, sample_queries
        """
        result = []
        for topic, queries in sorted(self.by_topic.items()):
            unique = self.get_fanout_prompts_for_topic(topic)
            result.append({
                'topic': topic,
                'total_queries': len(queries),
                'unique_queries': len(unique),
                'sample_queries': unique[:5],
            })
        return result

    def analyze_word_additions(self) -> Dict[str, Any]:
        """
        Analyze what words Google adds to queries during fan-out.

        Compares the original prompt text to the fan-out sub-queries
        to identify words Google injects (like "best", "top", "2026",
        "reviews", etc.). This reveals how Google reinterprets intent.

        Returns:
            Dict with added_words (Counter), top additions, and examples
        """
        added_words = Counter()
        examples = []

        for entry in self.collected:
            prompt_words = set(entry['prompt_text'].lower().split())
            for query in entry['web_search_queries']:
                query_words = set(query.lower().split())
                new_words = query_words - prompt_words
                # Filter out very common words
                stop_words = {
                    'the', 'a', 'an', 'is', 'are', 'was', 'in', 'on', 'at',
                    'to', 'for', 'of', 'and', 'or', 'but', 'with', 'from',
                    'by', 'as', 'it', 'this', 'that', 'be', 'has', 'have',
                    'do', 'does', 'did', 'will', 'would', 'could', 'should',
                }
                meaningful_new = new_words - stop_words
                added_words.update(meaningful_new)

                if meaningful_new and len(examples) < 10:
                    examples.append({
                        'original': entry['prompt_text'],
                        'fanout_query': query,
                        'added_words': list(meaningful_new),
                    })

        return {
            'top_additions': added_words.most_common(20),
            'total_unique_additions': len(added_words),
            'examples': examples,
        }

    def save(self) -> str:
        """
        Save collected fan-out data to disk.

        Returns:
            Path to saved file
        """
        os.makedirs(self.storage_dir, exist_ok=True)

        data = {
            'metadata': {
                'client': self.client_slug,
                'last_updated': datetime.now().isoformat(),
                'total_entries': len(self.collected),
                'total_unique_queries': len(self._all_unique_queries()),
            },
            'entries': self.collected,
        }

        with open(self.fanout_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✓ Fan-out data saved: {self.fanout_file} "
              f"({len(self.collected)} entries)")
        return self.fanout_file

    def _load_existing(self) -> None:
        """Load previously collected fan-out data if it exists."""
        if not os.path.exists(self.fanout_file):
            return

        try:
            with open(self.fanout_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            entries = data.get('entries', [])
            for entry in entries:
                self.collected.append(entry)
                prompt = entry.get('prompt_text', '')
                queries = entry.get('web_search_queries', [])
                self.by_prompt[prompt].extend(queries)

                topic = entry.get('cluster_topic', '')
                if topic:
                    self.by_topic[topic].extend(queries)

            if entries:
                print(f"  Loaded {len(entries)} existing fan-out entries")
        except (json.JSONDecodeError, KeyError):
            pass

    def _all_unique_queries(self) -> set:
        """Get all unique fan-out queries across all entries."""
        all_queries = set()
        for entry in self.collected:
            for q in entry.get('web_search_queries', []):
                all_queries.add(q.lower().strip())
        return all_queries

    def generate_fanout_test_prompts(self, max_per_topic: int = 10) -> List[Dict[str, Any]]:
        """
        Generate test prompts from collected real fan-out queries.

        These are the actual sub-queries Google used — testing them directly
        gives the most accurate picture of brand visibility across fan-out.

        Args:
            max_per_topic: Maximum fan-out prompts to include per topic

        Returns:
            List of prompt dicts compatible with the main testing pipeline
        """
        import time
        import random

        prompts = []

        for topic, queries in self.by_topic.items():
            unique = self.get_fanout_prompts_for_topic(topic)

            for query in unique[:max_per_topic]:
                prompt_id = f"fo_{int(time.time()*1000)}_{random.randint(1000, 9999)}"
                prompts.append({
                    'prompt_id': prompt_id,
                    'persona': '',  # Fan-out queries aren't persona-specific
                    'category': 'fanout_real',
                    'intent_type': 'informational',
                    'prompt_text': query,
                    'expected_visibility_score': 5.0,
                    'notes': f'Real Google fan-out query for topic: {topic}',
                    'topic_cluster_id': f'fo_real_{topic.replace(" ", "_")[:30]}',
                    'cluster_role': 'fanout_real',
                    'cluster_topic': topic,
                    'fanout_angle': 'google_real',
                })

        return prompts
