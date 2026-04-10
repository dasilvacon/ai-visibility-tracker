"""
Topic Cluster Analyzer — turns fan-out test results into actionable content gaps.

After the TopicClusterGenerator creates prompt clusters and those prompts are
tested against AI platforms, this module analyzes the results at the TOPIC
level (not individual prompt level) to answer:

  1. Which topics is the brand strong/weak on overall?
  2. For weak topics, WHICH fan-out angles are failing?
     (e.g., visible for broad questions but invisible for eligibility queries)
  3. What specific content should be created to close those gaps?

The output is a prioritized list of content recommendations tied directly
to the fan-out angles where the brand is invisible — the "side doors"
that AI engines use to discover (or miss) brands.

Usage:
    analyzer = TopicClusterAnalyzer(brand_name="Ontario Caregiver Organization")
    analysis = analyzer.analyze(scored_results)
    # Returns topic scorecards, angle heatmap, and content recommendations
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict


# Human-readable descriptions for each fan-out angle.
# Used in reports and recommendations so clients understand WHY they're
# invisible, not just that they are.
ANGLE_DESCRIPTIONS = {
    'specific_services': {
        'label': 'Specific Products & Services',
        'description': 'Queries about specific products, services, or solutions',
        'content_fix': 'Create dedicated pages for each product/service with clear descriptions, features, pricing, and how to get started',
        'page_type': 'Product/service landing pages',
    },
    'geographic': {
        'label': 'Location-Specific',
        'description': 'Queries filtered by city, region, or country',
        'content_fix': 'Add location-specific content, service area pages, and geo-targeted landing pages',
        'page_type': 'Location/service area pages',
    },
    'competitor_alternative': {
        'label': 'Alternatives & Competitors',
        'description': 'Queries comparing brands or looking for alternatives',
        'content_fix': 'Create comparison content, "alternatives to" pages, and differentiation messaging',
        'page_type': 'Comparison/alternative pages',
    },
    'how_to_practical': {
        'label': 'How-To & Practical Steps',
        'description': 'Step-by-step, practical action queries',
        'content_fix': 'Create how-to guides, checklists, and step-by-step walkthroughs with HowTo schema markup',
        'page_type': 'Tutorial/guide pages',
    },
    'emotional_support': {
        'label': 'Community & Social Proof',
        'description': 'Experience-seeking, review, and community-focused queries',
        'content_fix': 'Add customer stories, community content, testimonials, and real-world experience pages that build trust',
        'page_type': 'Community/testimonial pages',
    },
    'eligibility_access': {
        'label': 'Eligibility & Access',
        'description': 'Who qualifies, how to access, pricing, requirements',
        'content_fix': 'Create clear eligibility/pricing pages with criteria, getting-started steps, and FAQ content',
        'page_type': 'Eligibility/pricing/access pages',
    },
}


class TopicClusterAnalyzer:
    """
    Analyzes fan-out test results at the topic cluster level.

    Takes scored_results (the same format GapAnalyzer uses) and filters
    to cluster-tagged prompts, then produces:
      - Topic scorecards (overall visibility per topic)
      - Angle heatmaps (which fan-out angles are weak across all topics)
      - Prioritized content recommendations with specific actions
    """

    def __init__(self, brand_name: str):
        self.brand_name = brand_name

    def analyze(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Full topic cluster analysis.

        Args:
            scored_results: List of test results. Each result should have:
                - metadata.topic_cluster_id (if it's a cluster prompt)
                - metadata.cluster_role ("parent" or "fanout")
                - metadata.cluster_topic (the seed topic)
                - metadata.fanout_angle (e.g. "specific_services")
                - metadata.persona
                - visibility.brand_mentioned (bool)
                - visibility.competitors_mentioned (list)
                - visibility.prominence_score (float, 0-10)
                - prompt_text (the actual prompt)
                - platform (which AI engine)

        Returns:
            Dictionary with:
                - topic_scorecards: per-topic visibility breakdown
                - angle_heatmap: cross-topic angle performance
                - content_recommendations: prioritized actions
                - summary: executive summary stats
        """
        # Filter to only cluster-tagged results
        cluster_results = self._filter_cluster_results(scored_results)

        if not cluster_results:
            return {
                'topic_scorecards': [],
                'angle_heatmap': {},
                'content_recommendations': [],
                'summary': {'message': 'No topic cluster results found in test data.'}
            }

        scorecards = self._build_topic_scorecards(cluster_results)
        heatmap = self._build_angle_heatmap(cluster_results)
        recommendations = self._generate_recommendations(scorecards, heatmap, cluster_results)
        summary = self._build_summary(scorecards, heatmap)

        return {
            'topic_scorecards': scorecards,
            'angle_heatmap': heatmap,
            'content_recommendations': recommendations,
            'summary': summary,
        }

    # ── Filtering ──────────────────────────────────────────────────────

    def _filter_cluster_results(
        self, scored_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract only results that belong to a topic cluster."""
        cluster_results = []
        for r in scored_results:
            meta = r.get('metadata', {})
            # Check both top-level and nested metadata for cluster fields
            cluster_id = meta.get('topic_cluster_id') or r.get('topic_cluster_id')
            if cluster_id:
                # Normalize: ensure cluster fields are accessible at top-level metadata
                if not meta.get('topic_cluster_id'):
                    meta['topic_cluster_id'] = cluster_id
                    meta['cluster_role'] = r.get('cluster_role', '')
                    meta['cluster_topic'] = r.get('cluster_topic', '')
                    meta['fanout_angle'] = r.get('fanout_angle', '')
                cluster_results.append(r)
        return cluster_results

    # ── Topic Scorecards ───────────────────────────────────────────────

    def _build_topic_scorecards(
        self, cluster_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build a scorecard for each topic showing overall and per-angle visibility.

        Returns list sorted by topic visibility (worst first = biggest opportunity).
        """
        # Group results by topic
        by_topic = defaultdict(list)
        for r in cluster_results:
            meta = r.get('metadata', {})
            topic = meta.get('cluster_topic', 'Unknown')
            by_topic[topic].append(r)

        scorecards = []
        for topic, results in by_topic.items():
            # Overall topic visibility
            total = len(results)
            mentions = sum(
                1 for r in results
                if r.get('visibility', {}).get('brand_mentioned')
            )
            visibility_rate = (mentions / total * 100) if total else 0

            # Parent vs fan-out split
            parent_results = [r for r in results if r.get('metadata', {}).get('cluster_role') == 'parent']
            fanout_results = [r for r in results if r.get('metadata', {}).get('cluster_role') == 'fanout']

            parent_vis = self._calc_visibility_rate(parent_results)
            fanout_vis = self._calc_visibility_rate(fanout_results)

            # Per-angle breakdown
            angle_scores = {}
            by_angle = defaultdict(list)
            for r in fanout_results:
                angle = r.get('metadata', {}).get('fanout_angle', 'unknown')
                by_angle[angle].append(r)

            for angle, angle_results in by_angle.items():
                angle_vis = self._calc_visibility_rate(angle_results)
                angle_info = ANGLE_DESCRIPTIONS.get(angle, {})
                angle_scores[angle] = {
                    'visibility_rate': angle_vis,
                    'sample_size': len(angle_results),
                    'label': angle_info.get('label', angle),
                    'status': self._rate_status(angle_vis),
                }

            # Get persona (topics map to personas)
            persona = results[0].get('metadata', {}).get('persona', 'Unknown')

            # Competitor presence
            comp_mentions = sum(
                1 for r in results
                if r.get('visibility', {}).get('competitors_mentioned')
            )
            competitor_rate = (comp_mentions / total * 100) if total else 0

            # Example prompts where brand was missed
            missed_prompts = [
                r.get('prompt_text', '')
                for r in results
                if not r.get('visibility', {}).get('brand_mentioned')
                and r.get('prompt_text')
            ][:3]

            scorecards.append({
                'topic': topic,
                'persona': persona,
                'overall_visibility': round(visibility_rate, 1),
                'parent_visibility': round(parent_vis, 1),
                'fanout_visibility': round(fanout_vis, 1),
                'competitor_rate': round(competitor_rate, 1),
                'sample_size': total,
                'angle_scores': angle_scores,
                'weak_angles': [
                    a for a, s in angle_scores.items()
                    if s['visibility_rate'] < 40
                ],
                'strong_angles': [
                    a for a, s in angle_scores.items()
                    if s['visibility_rate'] >= 60
                ],
                'missed_prompts': missed_prompts,
                'status': self._rate_status(visibility_rate),
                # The "front door / side door" gap: visible on broad question
                # but invisible on the specific sub-queries
                'fanout_gap': round(parent_vis - fanout_vis, 1),
            })

        # Sort: worst overall visibility first (biggest opportunities)
        scorecards.sort(key=lambda x: x['overall_visibility'])
        return scorecards

    # ── Angle Heatmap ──────────────────────────────────────────────────

    def _build_angle_heatmap(
        self, cluster_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build a cross-topic heatmap showing which fan-out angles are
        systematically weak across ALL topics.

        This reveals structural content gaps — e.g., if "eligibility_access"
        is weak for 7 out of 8 topics, the brand needs eligibility pages
        across the board, not just for one topic.
        """
        fanout_results = [
            r for r in cluster_results
            if r.get('metadata', {}).get('cluster_role') == 'fanout'
        ]

        by_angle = defaultdict(list)
        for r in fanout_results:
            angle = r.get('metadata', {}).get('fanout_angle', 'unknown')
            by_angle[angle].append(r)

        heatmap = {}
        for angle, results in by_angle.items():
            vis_rate = self._calc_visibility_rate(results)
            angle_info = ANGLE_DESCRIPTIONS.get(angle, {})

            # How many topics is this angle weak for?
            by_topic = defaultdict(list)
            for r in results:
                topic = r.get('metadata', {}).get('cluster_topic', 'Unknown')
                by_topic[topic].append(r)

            weak_topic_count = sum(
                1 for topic_results in by_topic.values()
                if self._calc_visibility_rate(topic_results) < 40
            )

            heatmap[angle] = {
                'label': angle_info.get('label', angle),
                'description': angle_info.get('description', ''),
                'overall_visibility': round(vis_rate, 1),
                'total_prompts': len(results),
                'topics_tested': len(by_topic),
                'topics_weak': weak_topic_count,
                'status': self._rate_status(vis_rate),
                'is_systematic_gap': weak_topic_count >= len(by_topic) * 0.6,
            }

        return heatmap

    # ── Content Recommendations ────────────────────────────────────────

    def _generate_recommendations(
        self,
        scorecards: List[Dict[str, Any]],
        heatmap: Dict[str, Any],
        cluster_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized content recommendations from topic + angle analysis.

        Two types of recommendations:
          1. Systematic angle gaps (same angle weak across many topics)
             → "You need [angle] content across the board"
          2. Topic-specific gaps (one topic is weak overall)
             → "You need content specifically for [topic]"
        """
        recommendations = []

        # ── Type 1: Systematic angle gaps ──────────────────────────────
        for angle, data in heatmap.items():
            if not data.get('is_systematic_gap'):
                continue

            angle_info = ANGLE_DESCRIPTIONS.get(angle, {})
            vis = data['overall_visibility']

            # Collect example prompts for this angle where brand was missed
            missed = [
                r.get('prompt_text', '')
                for r in cluster_results
                if r.get('metadata', {}).get('fanout_angle') == angle
                and not r.get('visibility', {}).get('brand_mentioned')
                and r.get('prompt_text')
            ]

            # Collect which competitors are winning these
            winning_competitors = []
            for r in cluster_results:
                if (r.get('metadata', {}).get('fanout_angle') == angle
                        and not r.get('visibility', {}).get('brand_mentioned')):
                    comps = r.get('visibility', {}).get('competitors_mentioned', [])
                    winning_competitors.extend(comps)

            top_competitor = self._most_common(winning_competitors) or 'competitors'

            recommendations.append({
                'type': 'systematic_angle_gap',
                'priority': 'HIGH' if vis < 20 else 'MEDIUM',
                'angle': angle,
                'title': f"Create {angle_info.get('label', angle)} Content Across All Topics",
                'problem': (
                    f"Your brand is invisible on {angle_info.get('label', angle).lower()} "
                    f"queries across {data['topics_weak']}/{data['topics_tested']} topics "
                    f"({vis}% visibility). These are the 'side door' queries that AI engines "
                    f"run behind the scenes — and {top_competitor} is showing up instead."
                ),
                'what_to_create': angle_info.get('content_fix', f'Create content targeting {angle} queries'),
                'page_type': angle_info.get('page_type', 'Content pages'),
                'example_queries': list(dict.fromkeys(missed))[:5],
                'competitor_winning': top_competitor,
                'visibility_rate': vis,
                'topics_affected': data['topics_weak'],
                'impact_score': (100 - vis) * data['topics_weak'],
            })

        # ── Type 2: Topic-specific gaps ────────────────────────────────
        for card in scorecards:
            if card['overall_visibility'] >= 50:
                continue  # Only recommend for weak topics

            # Which angles are dragging this topic down?
            weak_angle_details = []
            for angle in card['weak_angles']:
                angle_info = ANGLE_DESCRIPTIONS.get(angle, {})
                score = card['angle_scores'].get(angle, {})
                weak_angle_details.append({
                    'angle': angle,
                    'label': angle_info.get('label', angle),
                    'visibility': score.get('visibility_rate', 0),
                    'fix': angle_info.get('content_fix', ''),
                })

            if not weak_angle_details:
                continue

            recommendations.append({
                'type': 'topic_specific_gap',
                'priority': 'HIGH' if card['overall_visibility'] < 20 else 'MEDIUM',
                'topic': card['topic'],
                'persona': card['persona'],
                'title': f"Improve Visibility for \"{card['topic']}\"",
                'problem': (
                    f"For the topic \"{card['topic']}\" ({card['persona']}), "
                    f"your overall visibility is {card['overall_visibility']}%. "
                    f"{'You show up for the broad question (' + str(card['parent_visibility']) + '%) but disappear on the specific sub-queries (' + str(card['fanout_visibility']) + '%).' if card['fanout_gap'] > 20 else 'You are weak across both broad and specific queries.'}"
                ),
                'weak_angles': weak_angle_details,
                'what_to_create': '; '.join(d['fix'] for d in weak_angle_details[:3] if d['fix']),
                'example_queries': card['missed_prompts'],
                'visibility_rate': card['overall_visibility'],
                'fanout_gap': card['fanout_gap'],
                'impact_score': (100 - card['overall_visibility']) * len(card['weak_angles']),
            })

        # Sort by impact score (highest first)
        recommendations.sort(key=lambda x: x.get('impact_score', 0), reverse=True)

        # Add ranking
        for i, rec in enumerate(recommendations):
            rec['rank'] = i + 1

        return recommendations

    # ── Summary ────────────────────────────────────────────────────────

    def _build_summary(
        self,
        scorecards: List[Dict[str, Any]],
        heatmap: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build executive summary stats."""
        if not scorecards:
            return {'message': 'No topic data to summarize.'}

        total_topics = len(scorecards)
        avg_visibility = sum(c['overall_visibility'] for c in scorecards) / total_topics
        weak_topics = sum(1 for c in scorecards if c['overall_visibility'] < 40)
        strong_topics = sum(1 for c in scorecards if c['overall_visibility'] >= 60)

        # Average fanout gap (how much worse are side-door queries vs front-door)
        avg_fanout_gap = sum(c['fanout_gap'] for c in scorecards) / total_topics

        # Systematic gaps
        systematic_gaps = [
            angle for angle, data in heatmap.items()
            if data.get('is_systematic_gap')
        ]

        # Worst topic
        worst = scorecards[0] if scorecards else None
        # Best topic
        best = scorecards[-1] if scorecards else None

        return {
            'total_topics': total_topics,
            'average_topic_visibility': round(avg_visibility, 1),
            'weak_topics': weak_topics,
            'strong_topics': strong_topics,
            'average_fanout_gap': round(avg_fanout_gap, 1),
            'systematic_angle_gaps': [
                heatmap[a]['label'] for a in systematic_gaps
            ],
            'worst_topic': worst['topic'] if worst else None,
            'worst_topic_visibility': worst['overall_visibility'] if worst else None,
            'best_topic': best['topic'] if best else None,
            'best_topic_visibility': best['overall_visibility'] if best else None,
            'headline': self._generate_headline(avg_visibility, avg_fanout_gap, systematic_gaps),
        }

    def _generate_headline(
        self, avg_vis: float, avg_gap: float, systematic_gaps: List[str]
    ) -> str:
        """Generate a one-sentence executive headline."""
        if avg_vis >= 60:
            if avg_gap > 20:
                return (
                    f"Your brand shows up for broad questions ({avg_vis:.0f}% avg) but "
                    f"disappears on the specific sub-queries AI engines actually use to "
                    f"build answers. Focus on closing the fan-out gap."
                )
            return f"Strong topic visibility at {avg_vis:.0f}%. Focus on maintaining coverage and expanding weak angles."

        if systematic_gaps:
            gap_labels = ', '.join(
                ANGLE_DESCRIPTIONS.get(g, {}).get('label', g)
                for g in systematic_gaps[:2]
            )
            return (
                f"Topic visibility is {avg_vis:.0f}% with systematic gaps in "
                f"{gap_labels}. These are the sub-queries AI engines use behind "
                f"the scenes — fixing them will improve visibility across all topics."
            )

        return f"Topic visibility is low at {avg_vis:.0f}%. Content gaps exist across multiple topics and query types."

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _calc_visibility_rate(results: List[Dict[str, Any]]) -> float:
        """Calculate brand mention rate for a list of results."""
        if not results:
            return 0.0
        mentions = sum(
            1 for r in results
            if r.get('visibility', {}).get('brand_mentioned')
        )
        return (mentions / len(results)) * 100

    @staticmethod
    def _rate_status(visibility_rate: float) -> str:
        """Convert visibility rate to a status label."""
        if visibility_rate >= 60:
            return 'strong'
        elif visibility_rate >= 40:
            return 'moderate'
        elif visibility_rate >= 20:
            return 'weak'
        return 'invisible'

    @staticmethod
    def _most_common(items: list) -> Optional[str]:
        """Return the most common item in a list, or None."""
        if not items:
            return None
        from collections import Counter
        return Counter(items).most_common(1)[0][0]
