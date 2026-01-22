"""
CSV export utilities for visibility analysis.
Creates export formats for different stakeholders.
"""

import csv
import os
from typing import Dict, List, Any
from collections import defaultdict


class CSVExporter:
    """Handles all CSV export formats."""

    def __init__(self, reports_dir: str):
        """
        Initialize CSV exporter.

        Args:
            reports_dir: Directory to save CSV exports
        """
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def export_sources(self, source_analysis: Dict[str, Any], brand_name: str) -> str:
        """
        Export source list CSV for PR/outreach team.

        Args:
            source_analysis: Source analysis data
            brand_name: Brand name

        Returns:
            Path to exported CSV
        """
        csv_path = os.path.join(self.reports_dir, f'sources_{brand_name.replace(" ", "_")}.csv')

        all_sources = source_analysis.get('all_sources', [])

        if not all_sources:
            return csv_path

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'Source',
                'Domain',
                'Total Appearances',
                'Your Brand Mentions',
                'Your Brand %',
                'Top Competitor',
                'Competitor Mentions',
                'Competitor %',
                'Should Target',
                'Priority',
                'Opportunity Score',
                'Recommended Action',
                'Example URLs'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for source in all_sources:
                # Determine priority based on opportunity score
                opp_score = source['opportunity_score']
                if opp_score >= 60:
                    priority = 'HIGH'
                elif opp_score >= 40:
                    priority = 'MEDIUM'
                else:
                    priority = 'LOW'

                # Determine recommended action
                source_name_lower = source['source'].lower()
                if 'reddit' in source_name_lower:
                    action = 'Increase Reddit presence - answer questions, engage authentically'
                elif 'youtube' in source_name_lower or 'channel' in source_name_lower:
                    action = 'Send PR packages to top beauty YouTubers for reviews'
                elif any(word in source_name_lower for word in ['blog', 'temptalia', 'review', 'beauty']):
                    action = 'Reach out for product review features'
                elif any(word in source_name_lower for word in ['sephora', 'ulta', 'nordstrom']):
                    action = 'Optimize product pages and request featured placement'
                else:
                    action = 'Reach out for backlink opportunities and product features'

                writer.writerow({
                    'Source': source['source'],
                    'Domain': source.get('domain', ''),
                    'Total Appearances': source['total_appearances'],
                    'Your Brand Mentions': source['mentions_your_brand'],
                    'Your Brand %': f"{source['brand_mention_rate']}%",
                    'Top Competitor': source.get('top_competitor', ''),
                    'Competitor Mentions': source['competitor_count'],
                    'Competitor %': f"{source['competitor_rate']}%",
                    'Should Target': 'YES' if source['should_target'] else 'No',
                    'Priority': priority if source['should_target'] else 'N/A',
                    'Opportunity Score': f"{opp_score:.0f}",
                    'Recommended Action': action if source['should_target'] else 'Maintain current relationship',
                    'Example URLs': '; '.join(source.get('example_urls', []))
                })

        return csv_path

    def export_raw_data(self, scored_results: List[Dict[str, Any]], brand_name: str) -> str:
        """
        Export raw data CSV for analysts.

        Args:
            scored_results: List of scored test results
            brand_name: Brand name

        Returns:
            Path to exported CSV
        """
        csv_path = os.path.join(self.reports_dir, f'raw_data_{brand_name.replace(" ", "_")}.csv')

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'Prompt Text',
                'Persona',
                'Category',
                'Intent Type',
                'Platform',
                'Brand Mentioned',
                'Prominence Score',
                'Competitors Mentioned',
                'Response Text',
                'Sources Found',
                'Timestamp'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for result in scored_results:
                visibility = result.get('visibility', {})
                metadata = result.get('metadata', {})

                # Get sources as semicolon-separated domains
                sources = visibility.get('sources', [])
                source_domains = '; '.join([s.get('domain', s.get('source_name', '')) for s in sources])

                writer.writerow({
                    'Prompt Text': result.get('prompt_text', ''),
                    'Persona': metadata.get('persona', ''),
                    'Category': metadata.get('category', ''),
                    'Intent Type': metadata.get('intent_type', ''),
                    'Platform': result.get('platform', ''),
                    'Brand Mentioned': 'TRUE' if visibility.get('brand_mentioned', False) else 'FALSE',
                    'Prominence Score': f"{visibility.get('prominence_score', 0):.1f}",
                    'Competitors Mentioned': ', '.join(visibility.get('competitors_mentioned', [])),
                    'Response Text': result.get('response_text', ''),
                    'Sources Found': source_domains,
                    'Timestamp': result.get('timestamp', '')
                })

        return csv_path

    def export_action_plan(self, gap_analysis: Dict[str, Any], brand_name: str) -> str:
        """
        Export action plan CSV for content team.

        Args:
            gap_analysis: Gap analysis data
            brand_name: Brand name

        Returns:
            Path to exported CSV
        """
        csv_path = os.path.join(self.reports_dir, f'action_plan_{brand_name.replace(" ", "_")}.csv')

        opportunities = gap_analysis.get('priority_opportunities', [])

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'Priority',
                'Category',
                'Opportunity Name',
                'Current Visibility %',
                'Competitor Avg %',
                'Gap',
                'Estimated Monthly Impact',
                'Specific Actions',
                'Where to Implement',
                'Target Keywords',
                'Example Questions',
                'Status',
                'Assigned To',
                'Due Date'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for opp in opportunities:
                # Format specific actions as numbered list
                actions = opp.get('specific_actions', [])
                actions_text = ' | '.join([f"{i+1}. {action}" for i, action in enumerate(actions)])

                # Get example questions
                example_prompts = opp.get('example_prompts', [])
                questions = ' | '.join([p.get('prompt', '')[:100] for p in example_prompts[:3]])

                writer.writerow({
                    'Priority': opp.get('priority', 'MEDIUM'),
                    'Category': opp.get('group', 'content').title(),
                    'Opportunity Name': opp.get('target', ''),
                    'Current Visibility %': f"{opp.get('current_visibility', 0):.1f}%",
                    'Competitor Avg %': f"{opp.get('competitor_avg', 0):.1f}%",
                    'Gap': f"{opp.get('gap', 0):.1f}%",
                    'Estimated Monthly Impact': f"~{opp.get('missed_monthly', 0)} mentions",
                    'Specific Actions': actions_text,
                    'Where to Implement': opp.get('where_to_implement', ''),
                    'Target Keywords': ', '.join(opp.get('target_keywords', [])),
                    'Example Questions': questions,
                    'Status': 'TODO',
                    'Assigned To': '',
                    'Due Date': ''
                })

        return csv_path

    def export_competitors(self, competitive_analysis: Dict[str, Any],
                          visibility_summary: Dict[str, Any],
                          brand_name: str) -> str:
        """
        Export competitor comparison CSV.

        Args:
            competitive_analysis: Competitive analysis data
            visibility_summary: Visibility summary with brand data
            brand_name: Brand name

        Returns:
            Path to exported CSV
        """
        csv_path = os.path.join(self.reports_dir, f'competitors_{brand_name.replace(" ", "_")}.csv')

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'Brand Name',
                'Mention Rate %',
                'Total Mentions',
                'Appears Without You',
                'Gap vs Your Brand',
                'Status'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Add your brand first
            your_rate = visibility_summary.get('brand_visibility_rate', 0)
            writer.writerow({
                'Brand Name': brand_name,
                'Mention Rate %': f"{your_rate:.1f}%",
                'Total Mentions': visibility_summary.get('brand_mentions', 0),
                'Appears Without You': 'N/A',
                'Gap vs Your Brand': '0.0%',
                'Status': 'Your Brand'
            })

            # Add competitors
            competitors = competitive_analysis.get('top_competitors', [])
            for i, comp in enumerate(competitors):
                gap = comp['mention_rate'] - your_rate

                # Determine status
                if i == 0:
                    status = 'Top Competitor'
                elif comp['mention_rate'] >= 10:
                    status = 'Rising Threat'
                else:
                    status = 'Competitor'

                writer.writerow({
                    'Brand Name': comp['name'],
                    'Mention Rate %': f"{comp['mention_rate']:.1f}%",
                    'Total Mentions': comp['mentions'],
                    'Appears Without You': comp.get('appears_without_you', 'N/A'),
                    'Gap vs Your Brand': f"{gap:+.1f}%",
                    'Status': status
                })

        return csv_path

    def export_personas(self, scored_results: List[Dict[str, Any]],
                       gap_analysis: Dict[str, Any],
                       brand_name: str) -> str:
        """
        Export persona performance CSV.

        Args:
            scored_results: List of scored results
            gap_analysis: Gap analysis with prioritized audiences
            brand_name: Brand name

        Returns:
            Path to exported CSV
        """
        csv_path = os.path.join(self.reports_dir, f'personas_{brand_name.replace(" ", "_")}.csv')

        # Calculate persona statistics
        persona_stats = defaultdict(lambda: {'mentions': 0, 'total': 0, 'missed_prompts': []})

        for result in scored_results:
            persona = result.get('metadata', {}).get('persona', 'Unknown')
            persona_stats[persona]['total'] += 1

            visibility = result.get('visibility', {})
            if visibility.get('brand_mentioned', False):
                persona_stats[persona]['mentions'] += 1
            else:
                # Track missed prompts for examples
                if len(persona_stats[persona]['missed_prompts']) < 3:
                    prompt = result.get('prompt_text', '')
                    if prompt:
                        persona_stats[persona]['missed_prompts'].append(prompt[:100])

        # Get prioritized audiences from gap analysis
        prioritized = gap_analysis.get('prioritized_audiences', [])
        audience_lookup = {a['target']: a for a in prioritized}

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'Persona Name',
                'Queries Tested',
                'Your Visibility %',
                'Competitor Avg %',
                'Gap',
                'Estimated Monthly Impact',
                'Why They Matter',
                'Recommended Actions',
                'Example Questions Missed'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for persona, stats in sorted(persona_stats.items(),
                                        key=lambda x: x[1]['mentions']/max(x[1]['total'], 1),
                                        reverse=True):
                visibility_rate = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0

                # Look up additional data from gap analysis
                audience_data = audience_lookup.get(persona, {})
                comp_avg = audience_data.get('competitor_avg', 0)
                gap = comp_avg - visibility_rate

                actions = audience_data.get('specific_actions', [])
                actions_text = ' | '.join([f"{i+1}. {action}" for i, action in enumerate(actions)])

                writer.writerow({
                    'Persona Name': persona,
                    'Queries Tested': stats['total'],
                    'Your Visibility %': f"{visibility_rate:.1f}%",
                    'Competitor Avg %': f"{comp_avg:.1f}%",
                    'Gap': f"{gap:.1f}%",
                    'Estimated Monthly Impact': audience_data.get('missed_monthly', 'N/A'),
                    'Why They Matter': audience_data.get('value_prop', 'Key audience segment'),
                    'Recommended Actions': actions_text if actions_text else 'Create targeted content for this persona',
                    'Example Questions Missed': ' | '.join(stats['missed_prompts'])
                })

        return csv_path
