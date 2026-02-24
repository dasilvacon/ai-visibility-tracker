"""
Citation classifier for categorizing sources as Owned, Third-party, or Competitor.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
from urllib.parse import urlparse
import re


class CitationClassifier:
    """Classifies citations/sources from AI responses."""

    def __init__(self, brand_domains: List[str], competitor_domains: Optional[Dict[str, List[str]]] = None):
        """
        Initialize the citation classifier.

        Args:
            brand_domains: List of owned domains (e.g., ['growclass.co', 'learning.growclass.co'])
            competitor_domains: Dictionary mapping competitor names to their domains
        """
        self.brand_domains = [d.lower() for d in brand_domains]
        self.competitor_domains = competitor_domains or {}

        # Normalize competitor domains to lowercase
        self.competitor_domains = {
            comp: [d.lower() for d in domains]
            for comp, domains in self.competitor_domains.items()
        }

    def classify_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a single source as Owned, Third-party, or Competitor.

        Args:
            source: Source dictionary with domain/url information

        Returns:
            Dictionary with classification
        """
        domain = source.get('domain', '').lower()

        # Check if owned domain
        if self._is_owned_domain(domain):
            return {
                **source,
                'citation_type': 'owned',
                'classification': 'Owned'
            }

        # Check if competitor domain
        competitor_name = self._find_competitor(domain)
        if competitor_name:
            return {
                **source,
                'citation_type': 'competitor',
                'classification': 'Competitor',
                'competitor_name': competitor_name
            }

        # Default to third-party
        return {
            **source,
            'citation_type': 'third_party',
            'classification': 'Third-party'
        }

    def _is_owned_domain(self, domain: str) -> bool:
        """Check if domain is an owned domain."""
        domain = domain.lower()

        for owned_domain in self.brand_domains:
            if domain == owned_domain or domain.endswith(f'.{owned_domain}'):
                return True

        return False

    def _find_competitor(self, domain: str) -> Optional[str]:
        """Find which competitor owns this domain."""
        domain = domain.lower()

        for competitor, domains in self.competitor_domains.items():
            for comp_domain in domains:
                if domain == comp_domain or domain.endswith(f'.{comp_domain}'):
                    return competitor

        return None

    def classify_all_sources(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classify all sources across all results.

        Args:
            scored_results: List of results with visibility scores

        Returns:
            Dictionary with citation analysis
        """
        all_sources = []
        domain_counts = defaultdict(lambda: {
            'count': 0,
            'type': None,
            'competitor_name': None,
            'sample_urls': []
        })

        total_results_with_brand = 0
        results_with_owned_citation = 0

        for result in scored_results:
            visibility = result.get('visibility', {})
            brand_mentioned = visibility.get('brand_mentioned', False)

            if brand_mentioned:
                total_results_with_brand += 1

            sources = visibility.get('sources', [])
            if not sources:
                continue

            has_owned_citation = False

            for source in sources:
                # Classify this source
                classified = self.classify_source(source)
                all_sources.append(classified)

                domain = classified.get('domain', '')
                if not domain:
                    continue

                # Track domain statistics
                domain_counts[domain]['count'] += 1
                domain_counts[domain]['type'] = classified['citation_type']
                domain_counts[domain]['competitor_name'] = classified.get('competitor_name')

                if len(domain_counts[domain]['sample_urls']) < 3:
                    domain_counts[domain]['sample_urls'].append(
                        classified.get('full_url', f'https://{domain}')
                    )

                # Check if owned citation
                if classified['citation_type'] == 'owned' and brand_mentioned:
                    has_owned_citation = True

            if has_owned_citation:
                results_with_owned_citation += 1

        # Calculate citation type statistics
        total_citations = len(all_sources)
        owned_count = sum(1 for s in all_sources if s['citation_type'] == 'owned')
        competitor_count = sum(1 for s in all_sources if s['citation_type'] == 'competitor')
        third_party_count = sum(1 for s in all_sources if s['citation_type'] == 'third_party')

        # Calculate percentages
        owned_pct = (owned_count / total_citations * 100) if total_citations > 0 else 0
        competitor_pct = (competitor_count / total_citations * 100) if total_citations > 0 else 0
        third_party_pct = (third_party_count / total_citations * 100) if total_citations > 0 else 0

        # Calculate citation presence rate (% of brand mentions that cite owned domain)
        citation_presence_rate = (
            (results_with_owned_citation / total_results_with_brand * 100)
            if total_results_with_brand > 0 else 0
        )

        # Sort domains by count
        top_domains = sorted(
            domain_counts.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )

        # Format top domains
        top_domains_formatted = []
        for domain, data in top_domains[:20]:  # Top 20
            top_domains_formatted.append({
                'domain': domain,
                'citations': data['count'],
                'type': data['type'],
                'classification': self._type_to_label(data['type']),
                'competitor_name': data['competitor_name'],
                'sample_urls': data['sample_urls']
            })

        return {
            'total_citations': total_citations,
            'owned_citations': owned_count,
            'competitor_citations': competitor_count,
            'third_party_citations': third_party_count,
            'owned_percentage': round(owned_pct, 1),
            'competitor_percentage': round(competitor_pct, 1),
            'third_party_percentage': round(third_party_pct, 1),
            'citation_presence_rate': round(citation_presence_rate, 1),
            'results_with_owned_citation': results_with_owned_citation,
            'total_results_with_brand': total_results_with_brand,
            'top_domains': top_domains_formatted,
            'citation_authority_score': self._calculate_citation_authority(
                owned_pct, citation_presence_rate
            )
        }

    def _type_to_label(self, citation_type: str) -> str:
        """Convert citation type to display label."""
        labels = {
            'owned': 'Owned',
            'competitor': 'Competitor',
            'third_party': 'Third-party'
        }
        return labels.get(citation_type, 'Unknown')

    def _calculate_citation_authority(self, owned_pct: float,
                                     citation_presence_rate: float) -> float:
        """
        Calculate citation authority score (0-100).

        Args:
            owned_pct: Percentage of citations that are owned
            citation_presence_rate: Percentage of brand mentions with owned citation

        Returns:
            Score from 0-100
        """
        # Weight both metrics
        # 60% weight on citation presence (consistency)
        # 40% weight on owned percentage (share of voice in citations)
        score = (citation_presence_rate * 0.6) + (owned_pct * 0.4)
        return round(score, 1)

    def get_citation_gap_analysis(self, scored_results: List[Dict[str, Any]],
                                 citation_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze citation gaps - where third-party sites are dominating the narrative.

        Args:
            scored_results: List of results with visibility scores
            citation_stats: Citation statistics from classify_all_sources

        Returns:
            Dictionary with gap analysis
        """
        top_third_party = [
            d for d in citation_stats['top_domains']
            if d['type'] == 'third_party'
        ][:10]

        # Calculate impact
        total_citations = citation_stats['total_citations']
        third_party_citations = citation_stats['third_party_citations']

        impact = (third_party_citations / total_citations * 100) if total_citations > 0 else 0

        recommendations = []

        # Recommend action if third-party dominance is high
        if impact > 50:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Increase owned content production',
                'reason': f'{impact:.0f}% of citations are third-party sources',
                'goal': 'Increase owned citation share to 50%+'
            })

        if citation_stats['citation_presence_rate'] < 80:
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Ensure brand domain is cited consistently',
                'reason': f'Only {citation_stats["citation_presence_rate"]:.0f}% of brand mentions cite your website',
                'goal': 'Target 90%+ citation presence rate'
            })

        # Identify high-value third-party domains for outreach
        high_value_domains = [
            d for d in top_third_party
            if d['citations'] >= 5
        ]

        if high_value_domains:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Third-party citation building',
                'reason': f'{len(high_value_domains)} high-authority domains frequently cited',
                'domains': [d['domain'] for d in high_value_domains[:5]],
                'goal': 'Get featured/mentioned on these authoritative sites'
            })

        return {
            'third_party_dominance': round(impact, 1),
            'top_third_party_domains': top_third_party,
            'recommendations': recommendations,
            'opportunity_score': self._calculate_opportunity_score(impact, citation_stats)
        }

    def _calculate_opportunity_score(self, third_party_pct: float,
                                    citation_stats: Dict[str, Any]) -> float:
        """Calculate opportunity score for improving citation authority."""
        # Higher third-party % = more opportunity
        # Lower citation presence rate = more opportunity

        citation_presence = citation_stats['citation_presence_rate']
        owned_pct = citation_stats['owned_percentage']

        # Inverted scores (lower current = higher opportunity)
        opportunity = ((100 - citation_presence) * 0.4) + ((100 - owned_pct) * 0.6)

        return round(min(opportunity, 100), 1)
