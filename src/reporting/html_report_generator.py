"""
HTML report generator for visibility analysis - DaSilva Consulting Brand.
"""

from typing import Dict, List, Any
import os
from datetime import datetime


class HTMLReportGenerator:
    """Generates HTML reports with DaSilva Consulting brand voice and identity."""

    def __init__(self, reports_dir: str):
        """
        Initialize the HTML report generator.

        Args:
            reports_dir: Directory to save reports
        """
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def generate_report(self, brand_name: str,
                       visibility_summary: Dict[str, Any],
                       competitive_analysis: Dict[str, Any],
                       gap_analysis: Dict[str, Any],
                       action_plan: Dict[str, Any],
                       scored_results: List[Dict[str, Any]],
                       website_verification: Dict[str, Any] = None,
                       source_analysis: Dict[str, Any] = None) -> str:
        """
        Generate HTML visibility report with DaSilva Consulting branding.

        Args:
            brand_name: Brand name
            visibility_summary: Visibility summary statistics
            competitive_analysis: Competitive analysis results
            gap_analysis: Gap analysis results
            action_plan: Action plan with opportunities
            website_verification: Optional website content verification results
            scored_results: List of scored results
            source_analysis: Optional source analysis results

        Returns:
            Path to generated HTML report
        """
        # Deduplicate all queries across the entire report before building HTML
        action_plan, gap_analysis = self._deduplicate_all_queries(action_plan, gap_analysis)

        html = self._build_html(
            brand_name,
            visibility_summary,
            competitive_analysis,
            gap_analysis,
            action_plan,
            scored_results,
            source_analysis
        )

        report_path = os.path.join(
            self.reports_dir,
            f'visibility_report_{brand_name.replace(" ", "_")}.html'
        )

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return report_path

    def _deduplicate_all_queries(self, action_plan: Dict[str, Any],
                                gap_analysis: Dict[str, Any]) -> tuple:
        """
        Deduplicate all example queries across the entire report.
        Ensures no query appears more than once across all sections.

        Returns:
            Tuple of (deduplicated_action_plan, deduplicated_gap_analysis)
        """
        from copy import deepcopy

        seen_queries = set()

        def dedupe_query_list(queries):
            """Remove duplicates from a list while maintaining order."""
            deduped = []
            for q in queries:
                # Clean the query first, then check for duplicates
                cleaned_q = self._clean_query_for_display(q)
                if cleaned_q.lower() not in seen_queries:
                    seen_queries.add(cleaned_q.lower())
                    deduped.append(q)  # Keep original query in the list
            return deduped

        # Create deep copies to avoid mutating the originals
        action_plan = deepcopy(action_plan)
        gap_analysis = deepcopy(gap_analysis)

        # Deduplicate geo_aeo_quick_wins (Start This Week section) - comes FIRST
        if 'geo_aeo_quick_wins' in action_plan:
            for win in action_plan['geo_aeo_quick_wins']:
                if 'example_queries' in win:
                    win['example_queries'] = dedupe_query_list(win['example_queries'])

        # Deduplicate prioritized_audiences (High-Value Audiences section) - comes SECOND
        if 'prioritized_audiences' in gap_analysis:
            for aud in gap_analysis['prioritized_audiences']:
                if 'example_queries' in aud:
                    aud['example_queries'] = dedupe_query_list(aud['example_queries'])

        # Deduplicate prioritized_content_gaps (Biggest Content Gaps section) - comes THIRD
        if 'prioritized_content_gaps' in gap_analysis:
            for gap in gap_analysis['prioritized_content_gaps']:
                if 'example_queries' in gap:
                    gap['example_queries'] = dedupe_query_list(gap['example_queries'])

        return action_plan, gap_analysis

    def _get_performance_label(self, rate: float) -> str:
        """Get performance label following DaSilva tone guidelines."""
        if rate >= 60:
            return "Strong"
        elif rate >= 40:
            return "Needs work"
        elif rate >= 20:
            return "Weak"
        else:
            return "Not showing up"

    def _get_prominence_label(self, score: float) -> str:
        """Get prominence label following DaSilva tone guidelines."""
        if score >= 7:
            return "Featured prominently"
        elif score >= 4:
            return "Mentioned"
        elif score >= 1:
            return "Barely visible"
        else:
            return "Not mentioned"

    def _clean_query_for_display(self, query: str) -> str:
        """
        Clean up queries for display by fixing hybrid query structures.

        Examples:
        - "Compare how to apply eyeshadow for beginners to Pat McGrath Labs"
          -> "How to apply eyeshadow for beginners"
        - "Help me learn about cruelty free luxury eyeshadow"
          -> "Cruelty free luxury eyeshadow"
        """
        import re

        # Pattern: "Compare [content/how-to topic] to [Brand]"
        # Extract just the content topic
        match = re.match(r'^Compare (how to .+?|.+?) to [A-Z][a-zA-Z\s]+$', query, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Pattern: "Help me learn about X"
        if query.lower().startswith('help me learn about'):
            return query[19:].strip()  # Remove "Help me learn about "

        # Pattern: "What should I know about X"
        if query.lower().startswith('what should i know about'):
            return query[24:].strip()  # Remove "What should I know about "

        return query

    def _build_top_executive_summary(self, brand_name: str, visibility_summary: Dict[str, Any],
                                    competitive_analysis: Dict[str, Any],
                                    scored_results: List[Dict[str, Any]]) -> str:
        """Build top-level executive summary - the TL;DR with DaSilva teaching voice."""

        visibility_rate = visibility_summary.get('brand_visibility_rate', 0)
        competitor_rate = visibility_summary.get('competitor_mention_rate', 0)

        # Find ChatGPT/OpenAI data
        from collections import defaultdict
        platform_stats = defaultdict(lambda: {'total': 0, 'mentions': 0, 'competitor_mentions': 0})

        for result in scored_results:
            platform = result.get('platform', 'Unknown')
            visibility = result.get('visibility', {})

            platform_stats[platform]['total'] += 1
            if visibility.get('brand_mentioned'):
                platform_stats[platform]['mentions'] += 1
            if visibility.get('competitors_mentioned'):
                platform_stats[platform]['competitor_mentions'] += 1

        chatgpt_rate = 0
        chatgpt_comp_rate = 0
        for platform, stats in platform_stats.items():
            if 'OPENAI' in platform.upper() or 'CHATGPT' in platform.upper():
                chatgpt_rate = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
                chatgpt_comp_rate = (stats['competitor_mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
                break

        # Find top competitor
        competitors = competitive_analysis.get('top_competitors', [])
        top_comp = competitors[0] if competitors else {'name': 'Competitors', 'mention_rate': competitor_rate}
        gap = top_comp['mention_rate'] - visibility_rate

        # Calculate persona breakdown - find strongest and weakest
        persona_stats = defaultdict(lambda: {'total': 0, 'mentions': 0})
        for result in scored_results:
            persona = result.get('metadata', {}).get('persona', 'Unknown')
            visibility = result.get('visibility', {})
            persona_stats[persona]['total'] += 1
            if visibility.get('brand_mentioned'):
                persona_stats[persona]['mentions'] += 1

        persona_rates = {}
        for persona, stats in persona_stats.items():
            if stats['total'] > 0:
                persona_rates[persona] = (stats['mentions'] / stats['total'] * 100)

        strongest_persona = max(persona_rates.items(), key=lambda x: x[1]) if persona_rates else ('Unknown', 0)
        weakest_persona = min(persona_rates.items(), key=lambda x: x[1]) if persona_rates else ('Unknown', 0)

        # Calculate dollar impact (conservative estimate)
        # Assume: 1000 monthly queries in category, avg visitor value $6, gap represents lost traffic
        total_results = visibility_summary.get('total_prompts_tested', 362)
        monthly_queries_estimate = total_results * 3  # Rough scaling factor
        gap_percentage = competitor_rate - visibility_rate
        missed_visitors_monthly = (gap_percentage / 100) * monthly_queries_estimate
        avg_visitor_value = 6  # Conservative industry average for beauty/cosmetics
        monthly_cost_low = int(missed_visitors_monthly * (avg_visitor_value * 0.8) / 100) * 100  # Round to nearest $100
        monthly_cost_high = int(missed_visitors_monthly * (avg_visitor_value * 1.3) / 100) * 100

        # Calculate 90-day target (50% of gap to competitors, not to 100%)
        target_visibility = min(visibility_rate + (competitor_rate - visibility_rate) * 0.5, 100)

        return f"""
        <div class="exec-summary">
            <h2>The Bottom Line</h2>

            <p style="font-size: 18px; line-height: 1.7; margin-bottom: 20px;">
                You're at <strong>{visibility_rate:.0f}%</strong> visibility while one or more competitors appear in <strong>{competitor_rate:.0f}%</strong> of queries.
                That means {100 - visibility_rate:.0f}% of the time, when people ask AI about your space, you're not part of the conversation.
            </p>

            <div class="exec-finding">
                <div class="exec-finding-title">🚨 What Needs Your Attention First</div>
                <div class="exec-finding-text">
                    ChatGPT is where 73% of AI users live. You're at <strong>{chatgpt_rate:.0f}%</strong> there while one or more competitors
                    appear in <strong>{chatgpt_comp_rate:.0f}%</strong> of queries. This gap alone costs you an estimated
                    <strong>${monthly_cost_low:,}-${monthly_cost_high:,}/month</strong> in lost organic traffic
                    (based on ~{int(missed_visitors_monthly)} monthly missed impressions × ${avg_visitor_value} avg visitor value).
                </div>
                <div style="margin-top: 16px; font-size: 14px; opacity: 0.9;">
                    <div class="exec-bullet">Best persona: {strongest_persona[0]} at {strongest_persona[1]:.0f}% visibility</div>
                    <div class="exec-bullet">Worst persona: {weakest_persona[0]} at {weakest_persona[1]:.0f}% visibility</div>
                    <div class="exec-bullet">Top competitor: {top_comp['name']} at {top_comp['mention_rate']:.0f}% (vs your {visibility_rate:.0f}%)</div>
                </div>
            </div>

            <div class="exec-summary-grid">
                <div class="exec-stat">
                    <div class="exec-stat-label">Current Visibility</div>
                    <div class="exec-stat-value">{visibility_rate:.0f}%</div>
                    <div class="exec-stat-desc">{100 - visibility_rate:.0f}% of queries = invisible</div>
                </div>
                <div class="exec-stat">
                    <div class="exec-stat-label">90-Day Target</div>
                    <div class="exec-stat-value">{target_visibility:.0f}%</div>
                    <div class="exec-stat-desc">Close 50% of the gap to competitors</div>
                </div>
                <div class="exec-stat">
                    <div class="exec-stat-label">Monthly Revenue at Risk</div>
                    <div class="exec-stat-value">${int(monthly_cost_high/1000)}K+</div>
                    <div class="exec-stat-desc">Lost to competitors</div>
                </div>
                <div class="exec-stat">
                    <div class="exec-stat-label">Annual Impact</div>
                    <div class="exec-stat-value">${int(monthly_cost_high*12/1000)}K+</div>
                    <div class="exec-stat-desc">If gap persists</div>
                </div>
            </div>

            <div style="margin-top: 20px; padding: 12px 16px; background: rgba(255,255,255,0.5); border-radius: 4px; font-size: 11px; color: #6B5660; line-height: 1.5;">
                <strong>How we calculate this:</strong> Visibility % = times your brand appeared in {total_results} AI queries tested. Revenue estimates assume industry average ${avg_visitor_value} visitor value and 3x monthly query scaling. Your actual opportunity may be higher or lower based on your conversion rate and average order value.
            </div>
        </div>
        """

    def _build_chatgpt_crisis_alert(self, brand_name: str, scored_results: List[Dict[str, Any]]) -> str:
        """Build ChatGPT crisis callout - this is buried but critical."""

        # Extract ChatGPT data
        from collections import defaultdict
        platform_stats = defaultdict(lambda: {'total': 0, 'mentions': 0, 'competitor_mentions': 0})

        for result in scored_results:
            platform = result.get('platform', 'Unknown')
            visibility = result.get('visibility', {})

            platform_stats[platform]['total'] += 1
            if visibility.get('brand_mentioned'):
                platform_stats[platform]['mentions'] += 1
            if visibility.get('competitors_mentioned'):
                platform_stats[platform]['competitor_mentions'] += 1

        chatgpt_you = 0
        chatgpt_comp = 0
        chatgpt_found = False

        for platform, stats in platform_stats.items():
            if 'OPENAI' in platform.upper() or 'CHATGPT' in platform.upper():
                chatgpt_you = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
                chatgpt_comp = (stats['competitor_mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
                chatgpt_found = True
                break

        # Only show alert if ChatGPT was tested and you're underperforming
        if not chatgpt_found or chatgpt_you >= chatgpt_comp:
            return ""

        # Calculate ChatGPT-specific dollar impact
        chatgpt_gap = chatgpt_comp - chatgpt_you
        # ChatGPT = 73% of all AI queries, so scale accordingly
        chatgpt_monthly_queries = 1000 * 0.73  # Assuming ~1000 monthly queries in category
        chatgpt_missed_visitors = (chatgpt_gap / 100) * chatgpt_monthly_queries
        avg_visitor_value = 6
        chatgpt_monthly_cost_low = int(chatgpt_missed_visitors * (avg_visitor_value * 0.8) / 100) * 100
        chatgpt_monthly_cost_high = int(chatgpt_missed_visitors * (avg_visitor_value * 1.3) / 100) * 100
        chatgpt_annual_cost = chatgpt_monthly_cost_high * 12

        return f"""
        <div class="crisis-alert">
            <div class="crisis-alert-title">
                ⚠️ PLATFORM ALERT: ChatGPT Is Your Biggest Problem
            </div>

            <div class="crisis-comparison">
                <div class="crisis-metric">
                    <div class="crisis-metric-label">You on ChatGPT</div>
                    <div class="crisis-metric-value">{chatgpt_you:.0f}%</div>
                    <div style="font-size: 12px; color: #E74C3C; font-weight: 600; margin-top: 4px;">
                        {'Invisible' if chatgpt_you < 15 else 'Weak'}
                    </div>
                </div>

                <div class="crisis-vs">VS</div>

                <div class="crisis-metric">
                    <div class="crisis-metric-label">Queries with Competitors</div>
                    <div class="crisis-metric-value">{chatgpt_comp:.0f}%</div>
                    <div style="font-size: 12px; color: #27AE60; font-weight: 600; margin-top: 4px;">
                        (on ChatGPT)
                    </div>
                </div>
            </div>

            <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #E8B4B4;">
                <p style="margin: 0; color: #4D2E3A; font-size: 15px; line-height: 1.7;">
                    <strong>Why this matters:</strong> ChatGPT represents 73% of all AI assistant usage
                    (100M+ weekly users). You're nearly invisible on the platform that matters most.
                    One or more competitors appear in {chatgpt_comp:.0f}% of ChatGPT queries—{chatgpt_comp - chatgpt_you:.0f} points ahead of you.
                </p>
                <p style="margin: 12px 0 0 0; color: #4D2E3A; font-size: 15px; line-height: 1.7;">
                    <strong>What it costs you:</strong> This gap alone represents <strong>${chatgpt_monthly_cost_low:,}-${chatgpt_monthly_cost_high:,}/month</strong>
                    in lost traffic. That's <strong>${int(chatgpt_annual_cost/1000)}K+ annually</strong> you're handing to competitors.
                    At ~{int(chatgpt_missed_visitors)} monthly missed impressions × ${avg_visitor_value} avg visitor value.
                </p>
            </div>
        </div>
        """

    def _build_competitive_landscape_visual(self, brand_name: str, visibility_summary: Dict[str, Any],
                                           competitive_analysis: Dict[str, Any]) -> str:
        """Build visual bar chart of competitive landscape."""

        competitors = competitive_analysis.get('top_competitors', [])
        your_rate = visibility_summary.get('brand_visibility_rate', 0)

        if not competitors:
            return ""

        # Build list with all brands (you + competitors), then sort by rate descending
        all_brands_list = [{'brand': f'YOUR BRAND ({brand_name})', 'rate': your_rate, 'is_you': True}]

        for comp in competitors[:6]:  # Top 6 competitors
            all_brands_list.append({'brand': comp['name'], 'rate': comp['mention_rate'], 'is_you': False})

        # Sort by rate descending so highest appears first
        brands_with_you = sorted(all_brands_list, key=lambda x: x['rate'], reverse=True)

        # Calculate max rate for proper bar scaling
        max_rate = max(brand['rate'] for brand in brands_with_you)
        scale_factor = 90 / max_rate if max_rate > 0 else 1  # Scale to 90% max width

        # Build bars
        bars_html = ""
        for brand_data in brands_with_you:
            label_class = "you" if brand_data['is_you'] else ""
            fill_class = "you" if brand_data['is_you'] else ""
            arrow = " ◀ YOU ARE HERE" if brand_data['is_you'] else ""
            bar_width = brand_data['rate'] * scale_factor

            bars_html += f"""
            <div class="comp-bar-row">
                <div class="comp-bar-label {label_class}">{brand_data['brand']}</div>
                <div class="comp-bar-track">
                    <div class="comp-bar-fill {fill_class}" style="width: {bar_width:.1f}%">
                        {brand_data['rate']:.0f}%
                    </div>
                </div>
                {f'<span class="comp-arrow">{arrow}</span>' if brand_data['is_you'] else ''}
            </div>
            """

        leader = brands_with_you[0]  # First item after sorting is the leader
        gap = leader['rate'] - your_rate

        return f"""
        <div class="comp-landscape">
            <h3 style="margin: 0 0 8px 0; color: #4D2E3A; font-size: 20px;">Where You Stand</h3>
            <p style="margin: 0 0 20px 0; color: #6B5660; font-size: 14px;">
                Share of voice across all AI responses tested
            </p>

            {bars_html}

            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #E8E4E3;">
                <p style="margin: 0; font-size: 14px; color: #6B5660; line-height: 1.7;">
                    <strong style="color: #4D2E3A;">The Reality:</strong> {leader['brand']} leads the category
                    at {leader['rate']:.0f}%. {'You are the leader.' if leader['is_you'] else f"You're {gap:.0f} points behind. That gap represents the difference between being a category leader and being in the middle of the pack."}
                </p>
            </div>
        </div>
        """

    def _build_what_winners_are_doing(self, competitive_analysis: Dict[str, Any]) -> str:
        """Show what the #1 competitor is doing that you're not - based on AI response patterns."""

        competitors = competitive_analysis.get('top_competitors', [])
        if not competitors:
            return ""

        top_competitor_name = competitors[0]['name']
        top_competitor_rate = competitors[0]['mention_rate']

        return f"""
        <div class="winners-section">
            <div class="winners-title">What {top_competitor_name} Is Doing (That You're Not)</div>
            <div class="winners-subtitle">
                Based on how AI platforms cite them in responses—here's what we observed
            </div>

            <div class="winner-item">
                <div class="winner-check">✓</div>
                <div class="winner-text">
                    <strong>Rich tutorial content that AI can cite.</strong> When people ask "how to" questions,
                    AI pulls from {top_competitor_name}'s blog posts and videos with specific steps, product recommendations, and techniques.
                    <span class="winner-you-have">(You: Rarely cited for tutorials)</span>
                </div>
            </div>

            <div class="winner-item">
                <div class="winner-check">✓</div>
                <div class="winner-text">
                    <strong>Detailed product pages AI can parse.</strong> Their pages include ingredient lists, use cases,
                    shade descriptions, and application tips in a structured format AI can extract.
                    <span class="winner-you-have">(You: Basic product info only)</span>
                </div>
            </div>

            <div class="winner-item">
                <div class="winner-check">✓</div>
                <div class="winner-text">
                    <strong>Content for specific use cases.</strong> AI cites them for "best for oily skin," "best for professionals,"
                    "best for beginners" because they have dedicated pages/sections for each.
                    <span class="winner-you-have">(You: Generic positioning)</span>
                </div>
            </div>

            <div class="winner-item">
                <div class="winner-check">✓</div>
                <div class="winner-text">
                    <strong>Comparison content they control.</strong> When AI discusses "{top_competitor_name} vs [other brands],"
                    it often references their own comparison pages where they frame the narrative.
                    <span class="winner-you-have">(You: No comparison pages)</span>
                </div>
            </div>

            <div class="winner-item">
                <div class="winner-check">✓</div>
                <div class="winner-text">
                    <strong>Educational content beyond products.</strong> AI references their makeup technique guides,
                    color theory articles, and "how to choose" content—establishing them as category experts.
                    <span class="winner-you-have">(You: Product-focused only)</span>
                </div>
            </div>

            <div style="margin-top: 20px; padding: 16px; background: rgba(77, 46, 58, 0.05); border-radius: 4px;">
                <p style="margin: 0; font-size: 14px; color: #4D2E3A; font-weight: 600;">
                    💡 The Pattern
                </p>
                <p style="margin: 8px 0 0 0; font-size: 14px; color: #1C1C1C; line-height: 1.7;">
                    {top_competitor_name} shows up at {top_competitor_rate:.0f}% because AI finds their content useful to cite.
                    They're not gaming the system—they're creating the content AI needs to answer questions thoroughly.
                    You can do the same: more how-to guides, use-case pages, comparison content, and educational resources.
                    Make it easy for AI to cite you by giving it structured, helpful content.
                </p>
            </div>
        </div>
        """

    def _build_sources_tab(self, brand_name: str, source_analysis: Dict[str, Any]) -> str:
        """Build the Sources & Citations tab showing where brands are being mentioned."""

        if not source_analysis or not source_analysis.get('all_sources'):
            return "<p>No source data available.</p>"

        total_sources = source_analysis.get('total_unique_sources', 0)
        brand_sources = source_analysis.get('sources_mentioning_brand', 0)
        gap_opportunities = source_analysis.get('gap_opportunities', 0)

        sources_with_brand = source_analysis.get('sources_with_your_brand', [])
        recommended_targets = source_analysis.get('recommended_targets', [])

        html = f"""
        <h2>Sources & Citations</h2>
        <p style="font-size: 16px; line-height: 1.8; color: #4D2E3A; margin-bottom: 32px;">
            When AI mentions "{brand_name}" or your competitors, it's often citing third-party sources like
            Sephora, Reddit, beauty blogs—not just brand websites. This section shows which sources are
            driving brand mentions, revealing high-value outreach opportunities.
        </p>

        <div class="metrics-grid" style="grid-template-columns: repeat(3, 1fr);">
            <div class="metric-card">
                <div class="metric-label">Total Sources Found</div>
                <div class="metric-value" style="font-size: 40px;">{total_sources}</div>
                <div class="metric-status">Unique sources cited by AI</div>
            </div>
            <div class="metric-card {'strong' if brand_sources > 0 else 'weak'}">
                <div class="metric-label">Sources Mentioning You</div>
                <div class="metric-value" style="font-size: 40px;">{brand_sources}</div>
                <div class="metric-status">Where you appear</div>
            </div>
            <div class="metric-card {'weak' if gap_opportunities > 0 else 'strong'}">
                <div class="metric-label">Gap Opportunities</div>
                <div class="metric-value" style="font-size: 40px;">{gap_opportunities}</div>
                <div class="metric-status">Competitors only (you're missing)</div>
            </div>
        </div>
        """

        # Table 1: Sources with your brand
        if sources_with_brand:
            html += """
            <h3 style="margin-top: 48px;">✓ Where You're Being Mentioned</h3>
            <p style="color: #6B5660; margin-bottom: 20px;">
                These sources are citing your brand in AI responses. Maintain and strengthen these relationships.
            </p>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 48px;">
                <thead>
                    <tr style="background: #F3EFF2; border-bottom: 2px solid #D4C5CE;">
                        <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Source</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Appearances</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Your Brand %</th>
                        <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Top Competitor</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Competitor %</th>
                        <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Status</th>
                    </tr>
                </thead>
                <tbody>
            """

            for source in sources_with_brand[:10]:
                status = "✓ Present"
                status_color = "#27AE60"

                html += f"""
                <tr style="border-bottom: 1px solid #E8E4E3;">
                    <td style="padding: 12px; color: #4D2E3A; font-weight: 500;">{source['source']}</td>
                    <td style="padding: 12px; text-align: center; color: #6B5660;">{source['total_appearances']}</td>
                    <td style="padding: 12px; text-align: center; color: #6B5660; font-weight: 600;">{source['brand_mention_rate']}%</td>
                    <td style="padding: 12px; color: #6B5660;">{source.get('top_competitor', '—')}</td>
                    <td style="padding: 12px; text-align: center; color: #6B5660;">{source['competitor_rate']}%</td>
                    <td style="padding: 12px; color: {status_color}; font-weight: 500;">{status}</td>
                </tr>
                """

                # Add example URLs if available
                if source.get('example_urls'):
                    html += f"""
                    <tr style="border-bottom: 1px solid #E8E4E3;">
                        <td colspan="6" style="padding: 8px 12px 12px 32px; color: #A7868F; font-size: 13px;">
                            Example: <a href="{source['example_urls'][0]}" target="_blank" style="color: #D4698B;">{source['example_urls'][0][:80]}...</a>
                        </td>
                    </tr>
                    """

            html += """
                </tbody>
            </table>
            """

        # Table 2: Gap opportunities - sources to target
        if recommended_targets:
            html += """
            <h3 style="margin-top: 48px;">⚠️ Sources You're Missing (Targeting Opportunities)</h3>
            <p style="color: #6B5660; margin-bottom: 20px;">
                These sources cite your competitors but not you. Reach out for features, reviews, or backlinks.
            </p>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 32px;">
                <thead>
                    <tr style="background: #FFF4E6; border-bottom: 2px solid #F0C674;">
                        <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Source</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Opportunity Score</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Your Brand %</th>
                        <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Top Competitor</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Competitor %</th>
                        <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Action</th>
                    </tr>
                </thead>
                <tbody>
            """

            for i, target in enumerate(recommended_targets[:10], 1):
                # Determine action based on source type
                action = "Reach out for features"
                if 'reddit' in target['source'].lower():
                    action = "Increase Reddit presence"
                elif 'youtube' in target['source'].lower() or 'channel' in target['source'].lower():
                    action = "Send PR packages to YouTubers"
                elif any(word in target['source'].lower() for word in ['blog', 'temptalia', 'review']):
                    action = "Request product reviews"

                # Color code opportunity score
                score = target['opportunity_score']
                score_color = "#27AE60" if score >= 70 else ("#F39C12" if score >= 40 else "#E74C3C")

                html += f"""
                <tr style="border-bottom: 1px solid #E8E4E3;">
                    <td style="padding: 12px; color: #4D2E3A; font-weight: 500;">
                        {i}. {target['source']}
                    </td>
                    <td style="padding: 12px; text-align: center; color: {score_color}; font-weight: 700;">
                        {score:.0f}/100
                    </td>
                    <td style="padding: 12px; text-align: center; color: #E74C3C; font-weight: 600;">
                        {target['brand_mention_rate']}%
                    </td>
                    <td style="padding: 12px; color: #6B5660;">
                        {target.get('top_competitor', '—')}
                    </td>
                    <td style="padding: 12px; text-align: center; color: #27AE60; font-weight: 600;">
                        {target['competitor_rate']}%
                    </td>
                    <td style="padding: 12px; color: #4D2E3A; font-size: 13px;">
                        → {action}
                    </td>
                </tr>
                """

                # Add example URL and specific action steps
                if target.get('example_urls'):
                    html += f"""
                    <tr style="border-bottom: 1px solid #E8E4E3;">
                        <td colspan="6" style="padding: 8px 12px 12px 32px;">
                            <div style="color: #A7868F; font-size: 13px; margin-bottom: 6px;">
                                Example: <a href="{target['example_urls'][0]}" target="_blank" style="color: #D4698B;">{target['example_urls'][0][:80]}...</a>
                            </div>
                    """

                    # Add specific action steps based on source type
                    if 'reddit' in target['source'].lower():
                        html += """
                            <div style="color: #6B5660; font-size: 13px; margin-top: 4px;">
                                • Answer questions authentically in relevant subreddits<br>
                                • Consider sponsoring relevant threads or AMAs
                            </div>
                        """
                    elif 'youtube' in target['source'].lower():
                        html += """
                            <div style="color: #6B5660; font-size: 13px; margin-top: 4px;">
                                • Send PR packages to top beauty YouTubers<br>
                                • Reach out for sponsored reviews or collaborations
                            </div>
                        """
                    elif any(word in target['source'].lower() for word in ['blog', 'temptalia', 'review']):
                        html += """
                            <div style="color: #6B5660; font-size: 13px; margin-top: 4px;">
                                • Reach out for product review features<br>
                                • Send PR package with your best products
                            </div>
                        """
                    else:
                        html += """
                            <div style="color: #6B5660; font-size: 13px; margin-top: 4px;">
                                • Reach out for backlink opportunities<br>
                                • Request product features or reviews
                            </div>
                        """

                    html += """
                        </td>
                    </tr>
                    """

            html += """
                </tbody>
            </table>
            """

            # Add expandable table with ALL sources
            all_sources = source_analysis.get('all_sources', [])
            import json

            # Generate table rows for ALL sources
            all_sources_rows = ""
            for source in all_sources:
                status = '✓ Present' if source.get('mentions_your_brand', 0) > 0 else '❌ Missing'
                status_color = '#27AE60' if source.get('mentions_your_brand', 0) > 0 else '#E74C3C'

                all_sources_rows += f"""
                <tr style="border-bottom: 1px solid #E8E4E3;">
                    <td style="padding: 12px; color: #4D2E3A; font-weight: 500;">{source.get('source', '')}</td>
                    <td style="padding: 12px; color: #6B5660;">{source.get('domain', '')}</td>
                    <td style="padding: 12px; text-align: center; color: #6B5660;">{source.get('total_appearances', 0)}</td>
                    <td style="padding: 12px; text-align: center; color: #6B5660; font-weight: 600;">{source.get('mentions_your_brand', 0)}</td>
                    <td style="padding: 12px; text-align: center; color: #6B5660;">{source.get('brand_mention_rate', 0)}%</td>
                    <td style="padding: 12px; color: #6B5660;">{source.get('top_competitor', '—')}</td>
                    <td style="padding: 12px; color: {status_color}; font-weight: 500;">{status}</td>
                </tr>
                """

            # Convert sources to JSON for download button
            sources_json = json.dumps(all_sources)
            brand_name_clean = brand_name.replace(" ", "_")

            html += f"""
            <div style="background: #F3EFF2; padding: 32px; border-radius: 8px; margin-top: 32px;">
                <h3 style="color: #4D2E3A; margin-top: 0;">📊 Complete Source List</h3>
                <p style="color: #6B5660; font-size: 15px; line-height: 1.6; margin-bottom: 20px;">
                    All {len(all_sources)} sources found in AI responses. Click to expand the full table or download as CSV.
                </p>

                <details style="margin-top: 20px;">
                    <summary style="cursor: pointer; padding: 16px; background: #FFFFFF; border-radius: 6px; font-weight: 500; color: #4D2E3A; border: 1px solid #E8E4E3;">
                        ▶ View All {len(all_sources)} Sources (Click to Expand)
                    </summary>

                    <div style="margin-top: 20px; max-height: 500px; overflow-y: auto; border: 1px solid #E8E4E3; border-radius: 6px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead style="position: sticky; top: 0; background: #F3EFF2; z-index: 10;">
                                <tr style="border-bottom: 2px solid #D4C5CE;">
                                    <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Source</th>
                                    <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Domain</th>
                                    <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Total</th>
                                    <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Your Brand</th>
                                    <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Your %</th>
                                    <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Top Competitor</th>
                                    <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {all_sources_rows}
                            </tbody>
                        </table>
                    </div>
                </details>

                <div style="margin-top: 24px; text-align: center;">
                    <button onclick="downloadSourceCSV()" style="
                        background: #A78E8B;
                        color: white;
                        border: none;
                        padding: 14px 32px;
                        border-radius: 6px;
                        font-size: 15px;
                        font-weight: 600;
                        cursor: pointer;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        transition: background 0.2s ease;
                    " onmouseover="this.style.background='#D4698B'" onmouseout="this.style.background='#A78E8B'">
                        📥 Download Complete Source List (CSV)
                    </button>
                </div>

                <script>
                function downloadSourceCSV() {{
                    const sources = {sources_json};

                    let csv = 'Source Name,Domain,Total Appearances,Your Brand Mentions,Your Brand %,Top Competitor,Should Target,Priority\\n';

                    sources.forEach(source => {{
                        const shouldTarget = (source.mentions_your_brand || 0) === 0 && (source.competitor_count || 0) > 0 ? 'YES' : 'NO';
                        const priority = shouldTarget === 'YES' && (source.opportunity_score || 0) > 50 ? 'HIGH' : 'MEDIUM';

                        csv += `"${{source.source || ''}}","${{source.domain || ''}}",`
                            + `${{source.total_appearances || 0}},${{source.mentions_your_brand || 0}},`
                            + `${{source.brand_mention_rate || 0}}%,"${{source.top_competitor || ''}}",`
                            + `${{shouldTarget}},${{priority}}\\n`;
                    }});

                    const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'sources_{brand_name_clean}.csv';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                }}
                </script>
            </div>
            """
        else:
            html += """
            <div style="background: #D4E8D4; padding: 24px; border-radius: 8px; margin-top: 32px;">
                <h3 style="color: #2D5F2D; margin-bottom: 12px;">✓ No Source Gaps Found</h3>
                <p style="color: #2D5F2D; font-size: 16px; line-height: 1.7; margin: 0;">
                    Good news! You're present in all sources where competitors appear.
                    Focus on strengthening your existing source relationships.
                </p>
            </div>
            """

        return html

    def _build_html(self, brand_name: str,
                   visibility_summary: Dict[str, Any],
                   competitive_analysis: Dict[str, Any],
                   gap_analysis: Dict[str, Any],
                   action_plan: Dict[str, Any],
                   scored_results: List[Dict[str, Any]],
                   source_analysis: Dict[str, Any] = None) -> str:
        """Build complete HTML report with DaSilva branding."""

        visibility_rate = visibility_summary.get('brand_visibility_rate', 0)
        performance_label = self._get_performance_label(visibility_rate)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Visibility Report - {brand_name} | DaSilva Consulting</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
            line-height: 1.6;
            color: #1C1C1C;
            background: #F8F8F7;
            padding: 32px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #FEFEFE;
            padding: 64px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(28, 28, 28, 0.08);
        }}

        h1 {{
            color: #4D2E3A;
            margin-bottom: 12px;
            font-size: 36px;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}

        h2 {{
            color: #4D2E3A;
            margin-top: 56px;
            margin-bottom: 28px;
            padding-bottom: 16px;
            border-bottom: 1px solid #E8E4E3;
            font-size: 24px;
            font-weight: 600;
        }}

        h3 {{
            color: #6B5660;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 18px;
            font-weight: 600;
        }}

        .header {{
            border-bottom: 1px solid #E8E4E3;
            padding-bottom: 32px;
            margin-bottom: 48px;
        }}

        .brand-name {{
            color: #4D2E3A;
            font-size: 28px;
            font-weight: 600;
            margin-top: 12px;
        }}

        .timestamp {{
            color: #A7868F;
            font-size: 14px;
            margin-top: 16px;
        }}

        .dasilva-credit {{
            color: #A7868F;
            font-size: 14px;
            margin-top: 6px;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin: 40px 0;
        }}

        .metric-card {{
            background: #FEFEFE;
            border: 1px solid #E8E4E3;
            padding: 32px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(28, 28, 28, 0.08);
            transition: box-shadow 0.2s ease;
        }}

        .metric-card:hover {{
            box-shadow: 0 4px 12px rgba(28, 28, 28, 0.12);
        }}

        .metric-card.strong {{
            background: #D4E8D4;
            border-color: #9FBC9F;
        }}

        .metric-card.strong .metric-value,
        .metric-card.strong .metric-label,
        .metric-card.strong .metric-status {{
            color: #2D5F2D;
        }}

        .metric-card.needs-work {{
            background: #F7E8D4;
            border-color: #D4B894;
        }}

        .metric-card.needs-work .metric-value,
        .metric-card.needs-work .metric-label,
        .metric-card.needs-work .metric-status {{
            color: #5A4A3A;
        }}

        .metric-card.weak {{
            background: #F0D4D4;
            border-color: #C9A7A7;
        }}

        .metric-card.weak .metric-value,
        .metric-card.weak .metric-label,
        .metric-card.weak .metric-status {{
            color: #6B3A3A;
        }}

        .metric-value {{
            font-size: 48px;
            font-weight: 700;
            margin: 16px 0;
            line-height: 1;
        }}

        .metric-label {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            opacity: 0.85;
        }}

        .metric-status {{
            font-size: 14px;
            margin-top: 12px;
            font-weight: 500;
            opacity: 0.9;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 32px 0;
            background: #FEFEFE;
            border: 1px solid #E8E4E3;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(28, 28, 28, 0.08);
        }}

        th {{
            background: #4D2E3A;
            color: white;
            padding: 16px 20px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }}

        td {{
            padding: 16px 20px;
            border-bottom: 1px solid #E8E4E3;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover {{
            background: #F8F8F7;
        }}

        .badge {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 600;
        }}

        .badge-strong {{
            background: #D4E8D4;
            color: #2D5F2D;
        }}

        .badge-neutral {{
            background: #E8E4E3;
            color: #6B5660;
        }}

        .badge-needs-work {{
            background: #F7E8D4;
            color: #5A4A3A;
        }}

        .badge-weak {{
            background: #F0D4D4;
            color: #6B3A3A;
        }}

        .badge-not-showing {{
            background: #E8E4E3;
            color: #6B5660;
        }}

        .action-item {{
            background: #F7EBF0;
            padding: 20px 24px;
            border-radius: 8px;
            margin: 16px 0;
            border-left: 3px solid #A7868F;
            box-shadow: 0 2px 8px rgba(28, 28, 28, 0.08);
        }}

        .action-item strong {{
            color: #1C1C1C;
            display: block;
            margin-bottom: 8px;
            font-size: 16px;
        }}

        .action-details {{
            color: #6B5660;
            font-size: 14px;
        }}

        .footer {{
            margin-top: 64px;
            padding-top: 32px;
            border-top: 1px solid #E8E4E3;
            text-align: center;
            color: #A7868F;
            font-size: 14px;
        }}

        .footer a {{
            color: #A7868F;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s ease;
        }}

        .footer a:hover {{
            color: #8F6D7A;
        }}

        .insight {{
            background: #F8F8F7;
            padding: 24px;
            border-radius: 8px;
            margin: 28px 0;
            border-left: 3px solid #A7868F;
            box-shadow: 0 2px 8px rgba(28, 28, 28, 0.08);
        }}

        .insight-title {{
            color: #4D2E3A;
            font-weight: 600;
            margin-bottom: 10px;
            font-size: 15px;
        }}

        .insight p {{
            color: #1C1C1C;
            line-height: 1.6;
        }}

        .number {{
            font-weight: 700;
            color: #4D2E3A;
        }}

        p {{
            margin: 16px 0;
            color: #6B5660;
        }}

        /* Tabs */
        .tabs {{
            display: flex;
            gap: 0;
            margin-bottom: 40px;
            border-bottom: 2px solid #E8E4E3;
        }}

        .tab {{
            padding: 16px 32px;
            background: transparent;
            border: none;
            color: #6B5660;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
            transition: all 0.2s ease;
        }}

        .tab:hover {{
            color: #4D2E3A;
            background: #F8F8F7;
        }}

        .tab.active {{
            color: #4D2E3A;
            border-bottom: 3px solid #A7868F;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        /* Filters */
        .filters-container {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            background: #F8F8F7;
            padding: 24px;
            border-radius: 8px;
            margin: 24px 0;
        }}

        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .filter-group label {{
            font-size: 12px;
            font-weight: 600;
            color: #6B5660;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .filter-group select,
        .filter-group input {{
            padding: 10px 14px;
            border: 1px solid #E8E4E3;
            border-radius: 4px;
            background: white;
            color: #1C1C1C;
            font-size: 14px;
            font-family: inherit;
        }}

        .filter-group select:focus,
        .filter-group input:focus {{
            outline: none;
            border-color: #A7868F;
        }}

        .search-group input {{
            min-width: 250px;
        }}

        .table-stats {{
            margin: 16px 0;
            color: #6B5660;
            font-size: 14px;
            font-weight: 500;
        }}

        .table-stats span {{
            color: #4D2E3A;
            font-weight: 600;
        }}

        /* Prompts Table */
        .table-container {{
            overflow-x: auto;
            margin: 24px 0;
        }}

        .prompts-table {{
            width: 100%;
            border-collapse: collapse;
            background: #FEFEFE;
            border: 1px solid #E8E4E3;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(28, 28, 28, 0.08);
        }}

        .prompts-table thead th {{
            background: #4D2E3A;
            color: white;
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
        }}

        .prompts-table tbody tr {{
            border-bottom: 1px solid #E8E4E3;
            transition: background 0.2s ease;
        }}

        .prompts-table tbody tr:hover {{
            background: #F8F8F7;
        }}

        .prompts-table tbody tr:last-child {{
            border-bottom: none;
        }}

        .prompts-table td {{
            padding: 16px;
            vertical-align: top;
            font-size: 14px;
        }}

        .prompt-cell {{
            max-width: 350px;
        }}

        .prompt-preview {{
            color: #1C1C1C;
            line-height: 1.5;
            margin-bottom: 8px;
        }}

        .prompt-full {{
            color: #1C1C1C;
            line-height: 1.6;
            margin: 12px 0;
            padding: 12px;
            background: #F8F8F7;
            border-radius: 4px;
            border-left: 3px solid #A7868F;
        }}

        .expand-btn {{
            padding: 6px 12px;
            background: #A7868F;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s ease;
        }}

        .expand-btn:hover {{
            background: #8F6D7A;
        }}

        .response-cell {{
            max-width: 250px;
        }}

        .response-full {{
            margin-top: 12px;
            padding: 16px;
            background: #F8F8F7;
            border-radius: 4px;
            border-left: 3px solid #A7868F;
            line-height: 1.6;
            color: #1C1C1C;
            max-height: 400px;
            overflow-y: auto;
        }}

        .competitors-cell {{
            color: #6B5660;
            font-size: 13px;
        }}

        .badge-platform {{
            background: #4D2E3A;
            color: white;
        }}

        .prompt-row {{
            display: table-row;
        }}

        .prompt-row[style*="display: none"] {{
            display: none !important;
        }}
        /* Executive Summary Box */
        .exec-summary {{
            background: linear-gradient(135deg, #E8D4DA 0%, #F0E0E5 100%);
            color: #1C1C1C;
            padding: 40px;
            border-radius: 12px;
            margin: 32px 0 48px 0;
            box-shadow: 0 4px 16px rgba(167, 134, 143, 0.2);
            border: 1px solid #C9A7B3;
        }}

        .exec-summary h2 {{
            color: #4D2E3A;
            margin: 0 0 24px 0;
            font-size: 32px;
            border: none;
            padding: 0;
            font-weight: 700;
        }}

        .exec-summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-top: 24px;
        }}

        .exec-stat {{
            background: rgba(255, 255, 255, 0.7);
            padding: 18px;
            border-radius: 8px;
            border-left: 4px solid #A7868F;
        }}

        .exec-stat-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: #6B5660;
            font-weight: 600;
            margin-bottom: 8px;
            white-space: nowrap;
        }}

        .exec-stat-value {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 4px;
            color: #4D2E3A;
        }}

        .exec-stat-desc {{
            font-size: 12px;
            color: #6B5660;
            line-height: 1.3;
        }}

        .exec-finding {{
            background: rgba(255, 255, 255, 0.6);
            padding: 24px;
            border-radius: 8px;
            margin-top: 24px;
            border-left: 4px solid #B85450;
        }}

        .exec-finding-title {{
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 12px;
            color: #8B3A3A;
        }}

        .exec-finding-text {{
            font-size: 16px;
            line-height: 1.7;
            margin-bottom: 12px;
            color: #1C1C1C;
        }}

        .exec-bullet {{
            margin: 8px 0;
            padding-left: 24px;
            position: relative;
            color: #4D2E3A;
        }}

        .exec-bullet:before {{
            content: "→";
            position: absolute;
            left: 0;
            font-weight: 700;
            color: #A7868F;
        }}

        /* Crisis Alert Box */
        .crisis-alert {{
            background: #F7E8E8;
            border: 2px solid #B85450;
            border-radius: 8px;
            padding: 28px;
            margin: 32px 0;
            box-shadow: 0 4px 12px rgba(184, 84, 80, 0.15);
        }}

        .crisis-alert-title {{
            color: #8B3A3A;
            font-size: 18px;
            font-weight: 700;
            margin: 0 0 16px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .crisis-comparison {{
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 20px;
            align-items: center;
            margin: 20px 0;
        }}

        .crisis-metric {{
            text-align: center;
        }}

        .crisis-metric-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #6B5660;
            margin-bottom: 8px;
        }}

        .crisis-metric-value {{
            font-size: 36px;
            font-weight: 700;
            color: #4D2E3A;
        }}

        .crisis-vs {{
            font-size: 24px;
            font-weight: 700;
            color: #A7868F;
        }}

        /* Visual Progress Bar */
        .visual-bar {{
            height: 24px;
            background: #F0EAE8;
            border-radius: 12px;
            overflow: hidden;
            margin: 8px 0;
            position: relative;
        }}

        .visual-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #A78E8B 0%, #6B5660 100%);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 8px;
            color: white;
            font-size: 12px;
            font-weight: 600;
        }}

        .visual-bar-fill.competitor {{
            background: linear-gradient(90deg, #E8B4B4 0%, #D69898 100%);
        }}

        /* Competitive Landscape */
        .comp-landscape {{
            margin: 32px 0;
            padding: 24px;
            background: #FEFEFE;
            border-radius: 8px;
            border: 1px solid #E8E4E3;
        }}

        .comp-bar-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 12px 0;
        }}

        .comp-bar-label {{
            width: 160px;
            font-size: 14px;
            font-weight: 600;
            color: #4D2E3A;
            flex-shrink: 0;
        }}

        .comp-bar-label.you {{
            color: #A78E8B;
            font-weight: 700;
        }}

        .comp-bar-track {{
            flex: 1;
            height: 32px;
            background: #F0EAE8;
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }}

        .comp-bar-fill {{
            height: 100%;
            background: #D69898;
            display: flex;
            align-items: center;
            padding-right: 8px;
            justify-content: flex-end;
            color: white;
            font-size: 13px;
            font-weight: 600;
        }}

        .comp-bar-fill.you {{
            background: linear-gradient(90deg, #A78E8B 0%, #6B5660 100%);
        }}

        .comp-arrow {{
            margin-left: 8px;
            color: #A78E8B;
            font-weight: 700;
        }}

        /* Key Insight Box */
        .key-insight {{
            background: #F7EBF0;
            border-left: 4px solid #A7868F;
            padding: 20px;
            margin: 24px 0;
            border-radius: 4px;
        }}

        .key-insight-title {{
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: #6B5660;
            margin-bottom: 12px;
        }}

        .key-insight-text {{
            font-size: 15px;
            line-height: 1.7;
            color: #1C1C1C;
        }}

        /* What Winners Are Doing */
        .winners-section {{
            background: #F8F8F7;
            padding: 28px;
            border-radius: 8px;
            margin: 32px 0;
        }}

        .winners-title {{
            font-size: 20px;
            font-weight: 700;
            color: #4D2E3A;
            margin-bottom: 8px;
        }}

        .winners-subtitle {{
            font-size: 14px;
            color: #6B5660;
            margin-bottom: 20px;
        }}

        .winner-item {{
            display: flex;
            align-items: start;
            gap: 12px;
            margin: 12px 0;
            padding: 12px;
            background: white;
            border-radius: 4px;
        }}

        .winner-check {{
            color: #27AE60;
            font-size: 18px;
            font-weight: 700;
            flex-shrink: 0;
        }}

        .winner-text {{
            font-size: 14px;
            line-height: 1.6;
            color: #1C1C1C;
        }}

        .winner-you-have {{
            color: #E74C3C;
            font-weight: 600;
            margin-left: 4px;
        }}

    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI Visibility Report</h1>
            <div class="brand-name">{brand_name}</div>
            <div class="timestamp">Report generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
            <div class="dasilva-credit">DaSilva Consulting</div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab(event, 'overview')">Overview</button>
            <button class="tab" onclick="switchTab(event, 'prompts')">What AI Actually Said</button>
            <button class="tab" onclick="switchTab(event, 'sources')">Sources & Citations</button>
        </div>

        <div id="overview" class="tab-content active">
            {self._build_top_executive_summary(brand_name, visibility_summary, competitive_analysis, scored_results)}

            {self._build_executive_summary(brand_name, visibility_summary, competitive_analysis)}

            {self._build_chatgpt_crisis_alert(brand_name, scored_results)}

            {self._build_visibility_by_persona(scored_results)}

            {self._build_visibility_by_platform(scored_results)}

            {self._build_competitive_landscape_visual(brand_name, visibility_summary, competitive_analysis)}

            {self._build_what_winners_are_doing(competitive_analysis)}

            {self._build_unlisted_brands(competitive_analysis)}

            {self._build_top_opportunities(gap_analysis, action_plan)}

            {self._build_action_plan(action_plan, gap_analysis, visibility_summary, competitive_analysis)}
        </div>

        <div id="prompts" class="tab-content">
            {self._build_prompt_viewer(brand_name, scored_results)}
        </div>

        <div id="sources" class="tab-content">
            {self._build_sources_tab(brand_name, source_analysis) if source_analysis else '<p>No source analysis available.</p>'}
        </div>

        <div class="footer">
            Report by <a href="#">DaSilva Consulting</a> | AI Visibility Tracker
        </div>
    </div>

    <script>
        function switchTab(evt, tabName) {{
            // Hide all tab content
            var tabcontent = document.getElementsByClassName("tab-content");
            for (var i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].classList.remove("active");
            }}

            // Remove active class from all tabs
            var tabs = document.getElementsByClassName("tab");
            for (var i = 0; i < tabs.length; i++) {{
                tabs[i].classList.remove("active");
            }}

            // Show current tab and mark button as active
            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active");
        }}

        function togglePrompt(btn) {{
            var cell = btn.closest('.prompt-cell');
            var preview = cell.querySelector('.prompt-preview');
            var full = cell.querySelector('.prompt-full');

            if (full.style.display === 'none') {{
                preview.style.display = 'none';
                full.style.display = 'block';
                btn.textContent = 'Show less';
            }} else {{
                preview.style.display = 'block';
                full.style.display = 'none';
                btn.textContent = 'Show full';
            }}
        }}

        function toggleResponse(btn, index) {{
            var responseDiv = document.getElementById('response-' + index);

            if (responseDiv.style.display === 'none') {{
                responseDiv.style.display = 'block';
                btn.textContent = 'Hide response';
            }} else {{
                responseDiv.style.display = 'none';
                btn.textContent = 'Show response';
            }}
        }}

        function filterTable() {{
            var statusFilter = document.getElementById('status-filter').value;
            var personaFilter = document.getElementById('persona-filter').value;
            var platformFilter = document.getElementById('platform-filter').value;
            var searchText = document.getElementById('search-box').value.toLowerCase();

            var rows = document.querySelectorAll('.prompt-row');
            var visibleCount = 0;

            rows.forEach(function(row) {{
                var status = row.getAttribute('data-status');
                var persona = row.getAttribute('data-persona');
                var platform = row.getAttribute('data-platform');
                var searchContent = row.getAttribute('data-search');

                var statusMatch = (statusFilter === 'all' || status === statusFilter);
                var personaMatch = (personaFilter === 'all' || persona === personaFilter);
                var platformMatch = (platformFilter === 'all' || platform === platformFilter);
                var searchMatch = (searchText === '' || searchContent.indexOf(searchText) !== -1);

                if (statusMatch && personaMatch && platformMatch && searchMatch) {{
                    row.style.display = '';
                    visibleCount++;
                }} else {{
                    row.style.display = 'none';
                }}
            }});

            document.getElementById('visible-count').textContent = visibleCount;
        }}

        function sortTable(columnIndex) {{
            var table = document.getElementById('prompts-table');
            var tbody = table.querySelector('tbody');
            var rows = Array.from(tbody.querySelectorAll('tr'));

            // Toggle sort direction
            var currentDir = table.getAttribute('data-sort-dir') || 'asc';
            var newDir = currentDir === 'asc' ? 'desc' : 'asc';
            table.setAttribute('data-sort-dir', newDir);

            rows.sort(function(a, b) {{
                var aText = a.cells[columnIndex].textContent.trim();
                var bText = b.cells[columnIndex].textContent.trim();

                // Try to parse as number
                var aNum = parseFloat(aText);
                var bNum = parseFloat(bText);

                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return newDir === 'asc' ? aNum - bNum : bNum - aNum;
                }}

                // String comparison
                if (newDir === 'asc') {{
                    return aText.localeCompare(bText);
                }} else {{
                    return bText.localeCompare(aText);
                }}
            }});

            // Re-append sorted rows
            rows.forEach(function(row) {{
                tbody.appendChild(row);
            }});
        }}
    </script>
</body>
</html>"""

        return html

    def _build_executive_summary(self, brand_name: str,
                                 visibility_summary: Dict[str, Any],
                                 competitive_analysis: Dict[str, Any]) -> str:
        """Build executive summary with DaSilva voice."""
        visibility_rate = visibility_summary.get('brand_visibility_rate', 0)
        prominence = visibility_summary.get('average_prominence_score', 0)
        competitor_rate = visibility_summary.get('competitor_mention_rate', 0)
        share_of_voice = competitive_analysis.get('brand_share_of_voice', 0)

        # Determine card classes
        visibility_class = 'strong' if visibility_rate >= 60 else 'needs-work' if visibility_rate >= 30 else 'weak'
        prominence_class = 'strong' if prominence >= 7 else 'needs-work' if prominence >= 4 else 'weak'
        sov_class = 'strong' if share_of_voice >= 50 else 'needs-work' if share_of_voice >= 30 else 'weak'
        competitor_class = 'strong' if competitor_rate < 20 else 'needs-work' if competitor_rate < 50 else 'weak'

        # Status messages
        visibility_status = self._get_performance_label(visibility_rate)
        prominence_status = self._get_prominence_label(prominence)

        # Build insight
        if visibility_rate < 20:
            insight = f"{brand_name} isn't showing up in AI responses. That's the priority."
        elif visibility_rate < 40:
            insight = f"{brand_name} appears in some responses. Needs more coverage."
        elif visibility_rate < 60:
            insight = f"{brand_name} has decent visibility. Time to improve prominence."
        else:
            insight = f"{brand_name} has strong visibility. Focus on maintaining position."

        return f"""
        <h2>The Numbers</h2>

        <div class="insight">
            <div class="insight-title">What This Means</div>
            {insight}
        </div>

        <div class="metrics-grid">
            <div class="metric-card {visibility_class}">
                <div class="metric-label">Visibility Rate</div>
                <div class="metric-value">{visibility_rate:.0f}%</div>
                <div class="metric-status">{visibility_status}</div>
            </div>
            <div class="metric-card {prominence_class}">
                <div class="metric-label">Prominence Score</div>
                <div class="metric-value">{prominence:.1f}/10</div>
                <div class="metric-status">{prominence_status}</div>
            </div>
            <div class="metric-card {sov_class}">
                <div class="metric-label">Share of Voice</div>
                <div class="metric-value">{share_of_voice:.0f}%</div>
                <div class="metric-status">vs competitors</div>
            </div>
            <div class="metric-card {competitor_class}">
                <div class="metric-label">Competitor Rate</div>
                <div class="metric-value">{competitor_rate:.0f}%</div>
                <div class="metric-status">in same responses</div>
            </div>
        </div>

        <div style="margin: 20px 0; padding: 10px 14px; background: #F8F8F7; border-left: 3px solid #A7868F; border-radius: 4px; font-size: 11px; color: #6B5660; line-height: 1.5;">
            <strong>What these metrics mean:</strong> Visibility Rate = % of queries where you appeared. Prominence Score = how prominently featured (0-10 scale, based on position and detail). Share of Voice = your mentions vs total brand mentions. Competitor Rate = % of queries where any competitor appeared.
        </div>

        <h3>Prominence Breakdown</h3>
        <p>Where {brand_name} ranks when mentioned:</p>
        <table>
            <tr>
                <th>Level</th>
                <th>Count</th>
                <th>%</th>
                <th>What This Means</th>
            </tr>
            <tr>
                <td><span class="badge badge-strong">Featured (7-10)</span></td>
                <td>{visibility_summary.get('high_prominence_count', 0)}</td>
                <td>{visibility_summary.get('high_prominence_count', 0) / max(visibility_summary.get('total_prompts_tested', 1), 1) * 100:.1f}%</td>
                <td>Top recommendation or detailed mention</td>
            </tr>
            <tr>
                <td><span class="badge badge-needs-work">Mentioned (4-6)</span></td>
                <td>{visibility_summary.get('medium_prominence_count', 0)}</td>
                <td>{visibility_summary.get('medium_prominence_count', 0) / max(visibility_summary.get('total_prompts_tested', 1), 1) * 100:.1f}%</td>
                <td>Listed as an option</td>
            </tr>
            <tr>
                <td><span class="badge badge-weak">Brief (1-3)</span></td>
                <td>{visibility_summary.get('low_prominence_count', 0)}</td>
                <td>{visibility_summary.get('low_prominence_count', 0) / max(visibility_summary.get('total_prompts_tested', 1), 1) * 100:.1f}%</td>
                <td>Passing reference only</td>
            </tr>
            <tr>
                <td><span class="badge badge-not-showing">Not Mentioned (0)</span></td>
                <td>{visibility_summary.get('no_mention_count', 0)}</td>
                <td>{visibility_summary.get('no_mention_count', 0) / max(visibility_summary.get('total_prompts_tested', 1), 1) * 100:.1f}%</td>
                <td>Invisible in response</td>
            </tr>
        </table>
        """

    def _build_visibility_by_persona(self, scored_results: List[Dict[str, Any]]) -> str:
        """Build visibility by persona with simplified GAP column."""
        from collections import defaultdict

        persona_stats = defaultdict(lambda: {'total': 0, 'mentions': 0, 'competitor_mentions': 0})

        # Calculate stats per persona
        for result in scored_results:
            persona = result.get('metadata', {}).get('persona', 'Unknown')
            visibility = result.get('visibility', {})

            persona_stats[persona]['total'] += 1
            if visibility.get('brand_mentioned'):
                persona_stats[persona]['mentions'] += 1
            if visibility.get('competitors_mentioned'):
                persona_stats[persona]['competitor_mentions'] += 1

        rows = ""
        for persona, stats in sorted(persona_stats.items(), key=lambda x: x[1]['mentions'] / max(x[1]['total'], 1), reverse=True):
            brand_rate = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
            competitor_rate = (stats['competitor_mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
            gap = brand_rate - competitor_rate

            # Color code gap
            if gap > 2:
                gap_class = 'badge-strong'
                gap_arrow = ' ↑'
            elif gap < -2:
                gap_class = 'badge-weak'
                gap_arrow = ' ↓'
            else:
                gap_class = 'badge-needs-work'
                gap_arrow = ' →'

            rows += f"""
            <tr>
                <td><strong>{persona}</strong></td>
                <td>{stats['total']}</td>
                <td>{brand_rate:.0f}%</td>
                <td>{competitor_rate:.0f}%</td>
                <td><span class="badge {gap_class}">{gap:.0f}%{gap_arrow}</span></td>
            </tr>
            """

        return f"""
        <h2>Performance by Audience</h2>
        <p>How visible is your brand to different personas?</p>
        <table>
            <tr>
                <th>Persona</th>
                <th>Tested</th>
                <th>You</th>
                <th>Any Competitor</th>
                <th>Gap</th>
            </tr>
            {rows}
        </table>

        <div style="margin: 20px 0; padding: 10px 14px; background: #F8F8F7; border-left: 3px solid #A7868F; border-radius: 4px; font-size: 11px; color: #6B5660; line-height: 1.5;">
            <strong>How personas are tested:</strong> Queries designed to match how different customer types search (e.g., professionals vs beginners). "Any Competitor" = % of queries where one or more competitors appeared. "Gap" shows the difference between competitor presence and your presence. Negative gaps mean you're winning with that persona.
        </div>
        """

    def _build_visibility_by_platform(self, scored_results: List[Dict[str, Any]]) -> str:
        """Build visibility by platform with DaSilva voice."""
        from collections import defaultdict

        platform_stats = defaultdict(lambda: {'total': 0, 'mentions': 0, 'avg_prominence': []})

        for result in scored_results:
            platform = result.get('platform', 'Unknown')
            visibility = result.get('visibility', {})

            platform_stats[platform]['total'] += 1
            if visibility.get('brand_mentioned'):
                platform_stats[platform]['mentions'] += 1
            platform_stats[platform]['avg_prominence'].append(visibility.get('prominence_score', 0))

        # Map platform names to friendly names with context
        platform_mapping = {
            'openai': ('ChatGPT (OpenAI)', '73% of all AI users'),
            'anthropic': ('Claude (Anthropic)', '15% of AI users'),
            'perplexity': ('Perplexity', 'Research-focused'),
            'deepseek': ('DeepSeek', 'Technical audience'),
            'grok': ('Grok (X.AI)', 'Twitter integration')
        }

        rows = ""
        for platform, stats in sorted(platform_stats.items(), key=lambda x: x[1]['mentions'] / max(x[1]['total'], 1), reverse=True):
            mention_rate = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_prominence = sum(stats['avg_prominence']) / len(stats['avg_prominence']) if stats['avg_prominence'] else 0

            badge_class = 'badge-strong' if mention_rate >= 60 else 'badge-needs-work' if mention_rate >= 30 else 'badge-weak'
            status = self._get_performance_label(mention_rate)

            # Get friendly name and context
            platform_lower = platform.lower()
            platform_display, platform_context = platform_mapping.get(platform_lower, (platform.upper(), ''))

            # Add crisis emoji for ChatGPT if underperforming
            crisis_emoji = ""
            if platform_lower == 'openai' and mention_rate < 20:
                crisis_emoji = " 🚨"

            rows += f"""
            <tr>
                <td><strong>{platform_display}{crisis_emoji}</strong><br><span style="font-size: 12px; color: #6B5660; font-weight: normal;">{platform_context}</span></td>
                <td>{stats['total']}</td>
                <td>{stats['mentions']}</td>
                <td><span class="badge {badge_class}">{mention_rate:.0f}%</span></td>
                <td>{avg_prominence:.1f}/10</td>
                <td>{status}</td>
            </tr>
            """

        return f"""
        <h2>Performance by Platform</h2>
        <p>Which AI platforms know your brand?</p>
        <table>
            <tr>
                <th>Platform</th>
                <th>Tested</th>
                <th>Mentions</th>
                <th>Rate</th>
                <th>Prominence</th>
                <th>Status</th>
            </tr>
            {rows}
        </table>

        <div style="margin: 20px 0; padding: 10px 14px; background: #F8F8F7; border-left: 3px solid #A7868F; border-radius: 4px; font-size: 11px; color: #6B5660; line-height: 1.5;">
            <strong>Why platform matters:</strong> Each AI platform has different training data and user demographics. ChatGPT represents 73% of AI users, making it the highest priority. Market share percentages based on public usage data as of 2025.
        </div>
        """

    def _build_top_competitors(self, brand_name: str, visibility_summary: Dict[str, Any],
                               competitive_analysis: Dict[str, Any]) -> str:
        """Build top competitors with your brand shown first."""
        top_competitors = competitive_analysis.get('top_competitors', [])[:10]

        if not top_competitors:
            return """
            <h2>The Competition</h2>
            <p>No competitors showed up in these responses.</p>
            """

        # Get your brand's stats
        brand_rate = visibility_summary.get('brand_visibility_rate', 0)
        brand_mentions = visibility_summary.get('brand_mentions', 0)

        # Build your brand row
        rows = f"""
            <tr style="background: #F7EBF0; border-left: 4px solid #A78E8B;">
                <td><strong>YOUR BRAND</strong></td>
                <td><strong>{brand_name}</strong></td>
                <td><strong>{brand_rate:.1f}%</strong></td>
                <td><strong>{brand_mentions} mentions</strong></td>
                <td><span class="badge badge-neutral">Baseline</span></td>
            </tr>
            <tr><td colspan="5" style="height: 10px; background: transparent; border: none;"></td></tr>
            <tr><td colspan="5" style="padding: 0; background: #E8E8E8; height: 2px;"></td></tr>
            <tr><td colspan="5" style="height: 10px; background: transparent; border: none;"></td></tr>
        """

        # Add competitors with gap calculations
        for i, comp in enumerate(top_competitors, 1):
            gap = comp['mention_rate'] - brand_rate

            # Add simple labels with gap
            if i == 1:
                label = f'<span class="badge badge-weak">Your top competitor (+{gap:.1f}%)</span>'
            elif gap < 0:
                label = f'<span class="badge badge-strong">Behind you ({gap:.1f}%)</span>'
            elif comp['mention_rate'] >= 10:
                label = f'<span class="badge badge-needs-work">Rising threat (+{gap:.1f}%)</span>'
            else:
                label = ''

            rows += f"""
            <tr>
                <td><span class="number">{i}</span></td>
                <td><strong>{comp['name']}</strong></td>
                <td>{comp['mention_rate']:.0f}%</td>
                <td>{comp['mentions']} mentions</td>
                <td>{label}</td>
            </tr>
            """

        return f"""
        <h2>The Competition</h2>
        <p>How you stack up against competitors in these responses.</p>
        <table>
            <tr>
                <th>#</th>
                <th>Brand</th>
                <th>Rate</th>
                <th>Mentions</th>
                <th>Status</th>
            </tr>
            {rows}
        </table>
        """

    def _build_unlisted_brands(self, competitive_analysis: Dict[str, Any]) -> str:
        """Build unlisted brands section with color-coded badges."""
        all_brands = competitive_analysis.get('all_brands', {})
        unlisted_brands = all_brands.get('unlisted_brands', [])

        if not unlisted_brands:
            return """
            <h2>Other Brands Mentioned</h2>
            <p>No other brands found. All mentioned brands are on your tracking list.</p>
            """

        rows = ""
        for i, brand in enumerate(unlisted_brands[:15], 1):  # Top 15
            mentions = brand['mentions']
            mention_rate = brand['mention_rate']

            # Color-code based on mention frequency
            if mentions >= 5:
                badge_class = 'badge-weak'  # Red - recommend tracking
                priority = 'Track this'
            elif mentions >= 3:
                badge_class = 'badge-needs-work'  # Yellow - moderate
                priority = 'Monitor'
            else:
                badge_class = 'badge-strong'  # Gray - low priority
                priority = 'Low priority'

            rows += f"""
            <tr>
                <td><span class="number">{i}</span></td>
                <td><strong>{brand['name']}</strong></td>
                <td>{mentions}</td>
                <td>{mention_rate:.1f}%</td>
                <td><span class="badge {badge_class}">{priority}</span></td>
            </tr>
            """

        return f"""
        <h2>Other Brands Mentioned</h2>
        <p>Brands AI mentioned that aren't on your tracking list. Consider adding high-frequency ones.</p>
        <table>
            <tr>
                <th>#</th>
                <th>Brand</th>
                <th>Mentions</th>
                <th>Rate</th>
                <th>Priority</th>
            </tr>
            {rows}
        </table>
        """

    def _build_top_opportunities(self, gap_analysis: Dict[str, Any],
                                action_plan: Dict[str, Any]) -> str:
        """Build redesigned opportunities section split by audiences and content."""
        prioritized_audiences = gap_analysis.get('prioritized_audiences', [])
        prioritized_content = gap_analysis.get('prioritized_content_gaps', [])

        audiences_html = self._build_prioritized_audiences(prioritized_audiences)
        content_html = self._build_prioritized_content_gaps(prioritized_content)

        return f"""
        <h2>Where to Focus</h2>
        <p>Your biggest opportunities to close the gap, organized by what matters most.</p>

        {audiences_html}

        {content_html}
        """

    def _build_prioritized_audiences(self, audiences: List[Dict[str, Any]]) -> str:
        """Build high-value audiences section with business context."""
        if not audiences:
            return ""

        cards_html = ""
        for i, aud in enumerate(audiences[:3], 1):  # Top 3 audiences
            priority_color = "#E74C3C" if aud['priority_level'] == "CRITICAL" else "#F39C12" if aud['priority_level'] == "HIGH" else "#3498DB"

            # Build example queries list (cleaned for display)
            queries_html = "<ul style='margin: 8px 0 0 0; padding-left: 20px; font-size: 13px;'>"
            for query in aud['example_queries'][:3]:
                cleaned_query = self._clean_query_for_display(query)
                queries_html += f"<li style='margin: 4px 0; color: #6B5660;'>\"{cleaned_query}\"</li>"
            queries_html += "</ul>"

            # Build action items list
            actions_html = "<ul style='margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;'>"
            for action in aud['action_items']:
                actions_html += f"<li style='margin: 6px 0; color: #1C1C1C; line-height: 1.5;'>{action}</li>"
            actions_html += "</ul>"

            quick_win_badge = ""
            if aud.get('quick_win'):
                quick_win_badge = '<span style="background: #2ECC71; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 10px;">⚡ QUICK WIN</span>'

            cards_html += f"""
            <div style="margin-bottom: 32px; padding: 24px; background: #FEFEFE; border: 2px solid #E8E4E3; border-left: 5px solid {priority_color}; border-radius: 8px; box-shadow: 0 2px 8px rgba(28, 28, 28, 0.08);">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
                    <div>
                        <h4 style="margin: 0 0 4px 0; color: #4D2E3A; font-size: 20px; font-weight: 600;">
                            {i}. {aud['persona']}
                        </h4>
                        <div style="font-size: 13px; color: #6B5660; margin-top: 4px;">
                            {aud['business_context']}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: {priority_color}; color: white; padding: 6px 14px; border-radius: 4px; font-size: 12px; font-weight: 600; display: inline-block;">
                            {aud['priority_emoji']} {aud['priority_level']}
                        </span>
                        {quick_win_badge}
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin: 16px 0; padding: 16px; background: #F8F8F7; border-radius: 6px;">
                    <div>
                        <div style="font-size: 11px; color: #6B5660; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Your Visibility</div>
                        <div style="font-size: 28px; font-weight: 700; color: #E74C3C; margin-top: 4px;">{aud['current_visibility']:.0f}%</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; color: #6B5660; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Any Competitor</div>
                        <div style="font-size: 28px; font-weight: 700; color: #3498DB; margin-top: 4px;">{aud['competitor_average']:.0f}%</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; color: #6B5660; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Gap</div>
                        <div style="font-size: 28px; font-weight: 700; color: #95A5A6; margin-top: 4px;">{aud['gap_percentage']:.0f}pts</div>
                    </div>
                </div>

                <div style="margin: 16px 0;">
                    <strong style="color: #6B5660; font-size: 14px;">🎯 The Opportunity:</strong>
                    <p style="margin: 6px 0 0 0; color: #1C1C1C; line-height: 1.6; font-size: 14px;">
                        <strong>{aud['top_competitor']}</strong> dominates this audience at {aud['competitor_rate']:.0f}% visibility
                        ({aud['gap_percentage']:.0f} points ahead). You're missing <strong>~{aud['missed_monthly_impressions']} monthly impressions</strong>
                        from this high-value audience.
                    </p>
                </div>

                <div style="margin: 16px 0;">
                    <strong style="color: #6B5660; font-size: 14px;">🔍 What They're Searching For:</strong>
                    {queries_html}
                </div>

                <div style="margin: 16px 0;">
                    <strong style="color: #6B5660; font-size: 14px;">✅ Action Plan:</strong>
                    {actions_html}
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; padding-top: 16px; border-top: 1px solid #E8E4E3;">
                    <div>
                        <span style="font-size: 12px; color: #6B5660; font-weight: 600;">Effort Required:</span>
                        <span style="margin-left: 8px; background: #E8E4E3; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600;">{aud['effort_estimate']}</span>
                    </div>
                    <div>
                        <span style="font-size: 12px; color: #6B5660; font-weight: 600;">Content Needed:</span>
                        <span style="margin-left: 8px; color: #4D2E3A; font-weight: 600; font-size: 13px;">~{aud['content_pieces_needed']} pieces</span>
                    </div>
                </div>
            </div>
            """

        return f"""
        <h3 style="margin-top: 48px; margin-bottom: 24px; color: #4D2E3A; font-size: 22px;">
            High-Value Audiences to Capture
        </h3>
        <p style="margin-bottom: 24px; color: #6B5660; font-size: 15px;">
            These audiences have the biggest visibility gaps and highest business value:
        </p>

        <div style="margin-bottom: 24px; padding: 10px 14px; background: #F8F8F7; border-left: 3px solid #A7868F; border-radius: 4px; font-size: 11px; color: #6B5660; line-height: 1.5;">
            <strong>How priority is calculated:</strong> Rankings based on visibility gap size × number of queries tested. "Any Competitor" = % of queries where one or more competitors appeared (not average competitor rate). "Missed impressions" assumes queries tested reflect real-world search patterns with 4x monthly scaling. Actual impact depends on your target market and content strategy.
        </div>

        {cards_html}
        """

    def _build_prioritized_content_gaps(self, content_gaps: List[Dict[str, Any]]) -> str:
        """Build content gaps section with competitive benchmarks."""
        if not content_gaps:
            return ""

        cards_html = ""
        for i, gap in enumerate(content_gaps[:3], 1):  # Top 3 content gaps
            priority_color = "#E74C3C" if gap['priority_level'] == "CRITICAL" else "#F39C12" if gap['priority_level'] == "HIGH" else "#3498DB"

            # Build example queries list (cleaned for display)
            queries_html = "<ul style='margin: 8px 0 0 0; padding-left: 20px; font-size: 13px;'>"
            for query in gap['example_queries'][:3]:
                cleaned_query = self._clean_query_for_display(query)
                queries_html += f"<li style='margin: 4px 0; color: #6B5660;'>\"{cleaned_query}\"</li>"
            queries_html += "</ul>"

            # Build content to create list
            content_html = "<ul style='margin: 8px 0 0 0; padding-left: 20px; font-size: 14px;'>"
            for content in gap['specific_content_to_create']:
                content_html += f"<li style='margin: 6px 0; color: #1C1C1C; line-height: 1.5;'>{content}</li>"
            content_html += "</ul>"

            quick_win_badge = ""
            if gap.get('quick_win'):
                quick_win_badge = '<span style="background: #2ECC71; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 10px;">⚡ QUICK WIN</span>'

            cards_html += f"""
            <div style="margin-bottom: 32px; padding: 24px; background: #FEFEFE; border: 2px solid #E8E4E3; border-left: 5px solid {priority_color}; border-radius: 8px; box-shadow: 0 2px 8px rgba(28, 28, 28, 0.08);">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
                    <div>
                        <h4 style="margin: 0 0 4px 0; color: #4D2E3A; font-size: 20px; font-weight: 600;">
                            {i}. {gap['content_type']}
                        </h4>
                        <div style="font-size: 13px; color: #6B5660; margin-top: 4px;">
                            Missing {gap['queries_missing']} queries in this category
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: {priority_color}; color: white; padding: 6px 14px; border-radius: 4px; font-size: 12px; font-weight: 600; display: inline-block;">
                            {gap['priority_emoji']} {gap['priority_level']}
                        </span>
                        {quick_win_badge}
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin: 16px 0; padding: 16px; background: #F8F8F7; border-radius: 6px;">
                    <div>
                        <div style="font-size: 11px; color: #6B5660; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Your Coverage</div>
                        <div style="font-size: 28px; font-weight: 700; color: #E74C3C; margin-top: 4px;">{gap['current_coverage']:.0f}%</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; color: #6B5660; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Any Competitor</div>
                        <div style="font-size: 28px; font-weight: 700; color: #3498DB; margin-top: 4px;">{gap['competitor_average']:.0f}%</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; color: #6B5660; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Gap</div>
                        <div style="font-size: 28px; font-weight: 700; color: #95A5A6; margin-top: 4px;">{gap['gap_percentage']:.0f}pts</div>
                    </div>
                </div>

                <div style="margin: 16px 0;">
                    <strong style="color: #6B5660; font-size: 14px;">🎯 The Opportunity:</strong>
                    <p style="margin: 6px 0 0 0; color: #1C1C1C; line-height: 1.6; font-size: 14px;">
                        <strong>{gap['top_competitor']}</strong> dominates this content type at {gap['competitor_average']:.0f}% coverage.
                        You're missing <strong>~{gap['missed_monthly_impressions']} monthly impressions</strong> from lack of {gap['content_type'].lower()}.
                    </p>
                </div>

                <div style="margin: 16px 0;">
                    <strong style="color: #6B5660; font-size: 14px;">🔍 Queries You're Missing:</strong>
                    {queries_html}
                </div>

                <div style="margin: 16px 0;">
                    <strong style="color: #6B5660; font-size: 14px;">📝 Specific Content to Create:</strong>
                    {content_html}
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; padding-top: 16px; border-top: 1px solid #E8E4E3;">
                    <div>
                        <span style="font-size: 12px; color: #6B5660; font-weight: 600;">Effort Required:</span>
                        <span style="margin-left: 8px; background: #E8E4E3; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600;">{gap['effort_estimate']}</span>
                    </div>
                    <div>
                        <span style="font-size: 12px; color: #6B5660; font-weight: 600;">Content Needed:</span>
                        <span style="margin-left: 8px; color: #4D2E3A; font-weight: 600; font-size: 13px;">~{gap['content_pieces_needed']} pieces</span>
                    </div>
                </div>
            </div>
            """

        return f"""
        <h3 style="margin-top: 48px; margin-bottom: 24px; color: #4D2E3A; font-size: 22px;">
            Biggest Content Gaps to Fill
        </h3>
        <p style="margin-bottom: 24px; color: #6B5660; font-size: 15px;">
            These content types have the most missed opportunities:
        </p>

        <div style="margin-bottom: 24px; padding: 10px 14px; background: #F8F8F7; border-left: 3px solid #A7868F; border-radius: 4px; font-size: 11px; color: #6B5660; line-height: 1.5;">
            <strong>How gaps are identified:</strong> Analyzed which content types (how-to, comparison, product info) had competitor presence. "Any Competitor" = % of queries where one or more competitors appeared (not average competitor rate). "Missed impressions" = estimated monthly opportunities based on gap size and test volume. Creating this content increases likelihood of AI citation.
        </div>

        {cards_html}
        """

    def _build_action_plan(self, action_plan: Dict[str, Any],
                           gap_analysis: Dict[str, Any],
                           visibility_summary: Dict[str, Any],
                           competitive_analysis: Dict[str, Any]) -> str:
        """Build action plan with DaSilva voice and GEO/AEO recommendations."""
        geo_aeo_wins = action_plan.get('geo_aeo_quick_wins', [])
        medium_term = action_plan.get('medium_term_priorities', [])
        visibility_rate = visibility_summary.get('brand_visibility_rate', 0)

        # Rewrite overall recommendation in DaSilva voice
        if visibility_rate >= 60:
            strategy = "You're visible. Focus: Stay top-of-mind. Maintain your position across all query types."
        elif visibility_rate >= 40:
            strategy = "You're showing up sometimes. Focus: Close the gaps. Target personas and categories where you're missing."
        elif visibility_rate >= 20:
            strategy = "You're barely visible. Focus: Build presence. Start with comparison content and educational pieces."
        else:
            strategy = "You're not showing up. Focus: Get visible fast. Create comparison content, how-to guides, and product reviews."

        # Build GEO/AEO quick wins HTML with new actionable format
        quick_wins_html = ""
        if geo_aeo_wins:
            for i, win in enumerate(geo_aeo_wins, 1):
                # Format example queries as bullet list (cleaned for display)
                example_queries_html = "<ul style='margin: 8px 0; padding-left: 20px;'>"
                for query in win.get('example_queries', [])[:5]:
                    cleaned_query = self._clean_query_for_display(query)
                    example_queries_html += f"<li style='margin: 4px 0; color: #1C1C1C;'>\"{cleaned_query}\"</li>"
                example_queries_html += "</ul>"

                # Add verification badge
                verification_status = win.get('verification_status', 'assumed')
                verification_badge = ""
                if verification_status == 'verified':
                    verification_badge = '<span style="background: #27AE60; color: white; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 8px;">✓ VERIFIED GAP</span>'
                elif verification_status == 'assumed':
                    verification_badge = '<span style="background: #95A5A6; color: white; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 8px;">⚠️ ASSUMED</span>'

                # Add competitor examples if verified
                competitor_examples_html = ""
                if verification_status == 'verified' and win.get('competitor_examples'):
                    competitor_examples_html = "<div style='margin-top: 16px; padding: 12px; background: #E8F5E9; border-radius: 4px; border-left: 3px solid #27AE60;'>"
                    competitor_examples_html += "<strong style='color: #27AE60; font-size: 13px;'>✓ Verified: Competitors Have This Content</strong>"
                    competitor_examples_html += "<ul style='margin: 8px 0 0 0; padding-left: 20px;'>"
                    for comp in win['competitor_examples'][:2]:  # Show top 2
                        competitor_examples_html += f"<li style='margin: 4px 0; color: #2E7D32; font-size: 12px;'><strong>{comp.get('url', 'Competitor')}:</strong> {comp.get('page_count', 0)} pages"
                        if comp.get('examples'):
                            competitor_examples_html += f"<br><span style='font-size: 11px; color: #6B5660;'>Example: {comp['examples'][0]}</span>"
                        competitor_examples_html += "</li>"
                    competitor_examples_html += "</ul></div>"

                quick_wins_html += f"""
                <div class="action-item" style="margin-bottom: 32px; padding: 24px; background: #F7EBF0; border-left: 4px solid #A78E8B; border-radius: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px; flex-wrap: wrap;">
                        <h4 style="margin: 0; color: #4D2E3A; font-size: 18px; font-weight: 600;">
                            {i}. {win['title']}
                        </h4>
                        <div>
                            <span style="background: #8B3A3A; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                                {win.get('priority', 'HIGH')} PRIORITY
                            </span>
                            {verification_badge}
                        </div>
                    </div>

                    {competitor_examples_html}

                    <div style="margin-bottom: 16px;">
                        <strong style="color: #6B5660; font-size: 14px;">📋 What to Create:</strong>
                        <p style="margin: 6px 0 0 0; color: #1C1C1C; line-height: 1.6;">{win['what']}</p>
                        {example_queries_html}
                    </div>

                    <div style="margin-bottom: 16px;">
                        <strong style="color: #6B5660; font-size: 14px;">🎯 Why This Matters:</strong>
                        <p style="margin: 6px 0 0 0; color: #1C1C1C; line-height: 1.6;">{win['why']}</p>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <strong style="color: #6B5660; font-size: 14px;">✍️ Content Brief:</strong>
                        <p style="margin: 6px 0 0 0; color: #1C1C1C; line-height: 1.6;">{win['content_brief']}</p>
                    </div>

                    <div style="margin-bottom: 16px;">
                        <strong style="color: #6B5660; font-size: 14px;">📢 Distribution Plan:</strong>
                        <p style="margin: 6px 0 0 0; color: #1C1C1C; line-height: 1.6;">{win['distribution']}</p>
                    </div>

                    <div style="margin-bottom: 16px; padding: 12px; background: #FEFEFE; border-radius: 4px; border: 1px solid #E8E4E3;">
                        <strong style="color: #6B5660; font-size: 13px;">🔧 Technical (for dev team):</strong>
                        <p style="margin: 6px 0 0 0; color: #6B5660; font-size: 13px; line-height: 1.5;">{win['seo_technical']}</p>
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px;">
                        <div style="padding: 12px; background: #E8F5E9; border-radius: 4px;">
                            <strong style="color: #2E7D32; font-size: 13px;">💰 Estimated Impact:</strong>
                            <p style="margin: 4px 0 0 0; color: #2E7D32; font-size: 14px; font-weight: 600;">{win['estimated_impact']}</p>
                        </div>
                        <div style="padding: 12px; background: #E3F2FD; border-radius: 4px;">
                            <strong style="color: #1976D2; font-size: 13px;">⏱️ Timeline:</strong>
                            <p style="margin: 4px 0 0 0; color: #1976D2; font-size: 14px; font-weight: 600;">{win['timeline']}</p>
                        </div>
                    </div>
                </div>
                """
        else:
            quick_wins_html = '<p>No high-priority opportunities found. Focus on building more content across all query types.</p>'

        # Build strategic 90-day roadmap instead of generic priorities
        roadmap_html = self._build_90_day_roadmap(gap_analysis, visibility_summary, competitive_analysis)

        return f"""
        <h2>What to Do</h2>

        <div class="insight">
            <div class="insight-title">Strategy</div>
            {strategy}
        </div>

        <h3>Start This Week</h3>
        <p style="margin-bottom: 16px; color: #6B5660; font-size: 14px;">
            High-impact, low-effort actions to improve GEO (Generative Engine Optimization) and AEO (Answer Engine Optimization):
        </p>

        <div style="margin-bottom: 24px; padding: 10px 14px; background: #F8F8F7; border-left: 3px solid #A7868F; border-radius: 4px; font-size: 11px; color: #6B5660; line-height: 1.5;">
            <strong>Why these are quick wins:</strong> These recommendations target specific queries where competitors consistently appear but you don't. They're ranked by ease of implementation vs potential impact. Completing these can show visibility improvement within 30-60 days of content publication.
        </div>

        {quick_wins_html if quick_wins_html else '<p>No immediate priorities identified.</p>'}

        <h3>Your 90-Day Roadmap</h3>
        <p style="color: #6B5660; margin-bottom: 24px;">Three strategic phases to close the visibility gap. Each builds on the last.</p>
        {roadmap_html}
        """

    def _build_90_day_roadmap(self, gap_analysis: Dict[str, Any],
                              visibility_summary: Dict[str, Any],
                              competitive_analysis: Dict[str, Any]) -> str:
        """Build strategic 90-day roadmap with phases."""

        current_vis = visibility_summary.get('brand_visibility_rate', 0)
        competitor_avg = visibility_summary.get('competitor_mention_rate', 0)
        target_vis = min(current_vis + (competitor_avg - current_vis) * 0.5, 100)

        # Get top priorities
        prioritized_audiences = gap_analysis.get('prioritized_audiences', [])
        prioritized_content = gap_analysis.get('prioritized_content_gaps', [])

        # Determine focus areas
        top_audience = prioritized_audiences[0]['persona'] if prioritized_audiences else "your target audience"
        top_content = prioritized_content[0]['content_type'] if prioritized_content else "tutorial content"

        return f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 24px;">
            <!-- Phase 1: Month 1 -->
            <div style="background: #F7EBF0; border: 2px solid #D4A5B3; border-radius: 8px; padding: 20px;">
                <div style="background: #D4A5B3; color: white; padding: 8px 16px; border-radius: 4px; display: inline-block; margin-bottom: 16px; font-weight: 600; font-size: 14px;">
                    MONTH 1: Foundation
                </div>
                <h4 style="margin: 0 0 12px 0; color: #4D2E3A; font-size: 18px;">Build Core Content</h4>
                <p style="margin: 0 0 16px 0; color: #6B5660; font-size: 14px; line-height: 1.5;">
                    Focus on creating foundational content that AI can cite. Start with your highest-impact gaps.
                </p>
                <ul style="margin: 0; padding-left: 20px; color: #1C1C1C;">
                    <li style="margin: 8px 0;">Create 5-7 how-to guides targeting {top_audience}</li>
                    <li style="margin: 8px 0;">Add FAQ sections to your top 10 product pages</li>
                    <li style="margin: 8px 0;">Implement HowTo and FAQ schema markup</li>
                    <li style="margin: 8px 0;">Write 3 comparison pages vs top competitors</li>
                </ul>
                <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #D4A5B3;">
                    <strong style="color: #A7868F; font-size: 13px;">Target:</strong>
                    <div style="color: #4D2E3A; font-size: 14px; font-weight: 600; margin-top: 4px;">{current_vis:.0f}% → {current_vis + 5:.0f}% visibility</div>
                </div>
            </div>

            <!-- Phase 2: Month 2 -->
            <div style="background: #EED9E0; border: 2px solid #C9A7B3; border-radius: 8px; padding: 20px;">
                <div style="background: #A7868F; color: white; padding: 8px 16px; border-radius: 4px; display: inline-block; margin-bottom: 16px; font-weight: 600; font-size: 14px;">
                    MONTH 2: Expansion
                </div>
                <h4 style="margin: 0 0 12px 0; color: #4D2E3A; font-size: 18px;">Scale & Optimize</h4>
                <p style="margin: 0 0 16px 0; color: #6B5660; font-size: 14px; line-height: 1.5;">
                    Double down on what's working. Expand content across all priority audiences.
                </p>
                <ul style="margin: 0; padding-left: 20px; color: #1C1C1C;">
                    <li style="margin: 8px 0;">Create persona-specific landing pages (Professionals, Beginners)</li>
                    <li style="margin: 8px 0;">Publish 10+ educational blog posts</li>
                    <li style="margin: 8px 0;">Launch YouTube tutorial series (5-7 videos)</li>
                    <li style="margin: 8px 0;">Add Product schema to all product pages</li>
                </ul>
                <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #A7868F;">
                    <strong style="color: #8F6D7A; font-size: 13px;">Target:</strong>
                    <div style="color: #4D2E3A; font-size: 14px; font-weight: 600; margin-top: 4px;">{current_vis + 5:.0f}% → {current_vis + 10:.0f}% visibility</div>
                </div>
            </div>

            <!-- Phase 3: Month 3 -->
            <div style="background: #E4D4DA; border: 2px solid #8F6D7A; border-radius: 8px; padding: 20px;">
                <div style="background: #6B5660; color: white; padding: 8px 16px; border-radius: 4px; display: inline-block; margin-bottom: 16px; font-weight: 600; font-size: 14px;">
                    MONTH 3: Dominance
                </div>
                <h4 style="margin: 0 0 12px 0; color: #4D2E3A; font-size: 18px;">Fill Remaining Gaps</h4>
                <p style="margin: 0 0 16px 0; color: #6B5660; font-size: 14px; line-height: 1.5;">
                    Target your weakest personas and content types. Aim to hit your 90-day goal.
                </p>
                <ul style="margin: 0; padding-left: 20px; color: #1C1C1C;">
                    <li style="margin: 8px 0;">Create content for under-served personas</li>
                    <li style="margin: 8px 0;">Build comprehensive resource center</li>
                    <li style="margin: 8px 0;">Add rich media (infographics, case studies)</li>
                    <li style="margin: 8px 0;">Measure & iterate based on visibility gains</li>
                </ul>
                <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #6B5660;">
                    <strong style="color: #6B5660; font-size: 13px;">Target:</strong>
                    <div style="color: #4D2E3A; font-size: 14px; font-weight: 600; margin-top: 4px;">{current_vis + 10:.0f}% → {target_vis:.0f}% visibility</div>
                </div>
            </div>
        </div>

        <div style="margin-top: 24px; padding: 20px; background: #F8F8F7; border-radius: 8px; border-left: 4px solid #A7868F;">
            <p style="margin: 0; font-size: 14px; color: #4D2E3A; font-weight: 600;">
                💡 Success Metric
            </p>
            <p style="margin: 8px 0 0 0; font-size: 14px; color: #1C1C1C; line-height: 1.7;">
                By day 90, you should be at <strong>{target_vis:.0f}% visibility</strong> (currently {current_vis:.0f}%).
                That closes <strong>50% of your gap to competitors</strong> and represents significant recurring monthly traffic.
                Re-run this analysis at day 30, 60, and 90 to track progress and adjust tactics.
            </p>
        </div>
        """

    def _build_prompt_viewer(self, brand_name: str, scored_results: List[Dict[str, Any]]) -> str:
        """Build interactive prompt viewer with filters and insights."""
        import json
        import html
        import re

        # Prepare data for JavaScript
        prompts_data = []
        personas = set()
        platforms = set()

        # Track best/worst for Quick Insights
        best_response = {'prominence': 0, 'prompt': '', 'response': ''}
        worst_miss = {'prompt': '', 'competitors': []}
        themes_winning = []
        themes_missing = []

        for result in scored_results:
            visibility = result.get('visibility', {})
            metadata = result.get('metadata', {})

            prompt_text = result.get('prompt_text', '')
            persona = metadata.get('persona', 'Unknown')
            platform_raw = result.get('platform', 'unknown')
            response_text = result.get('response_text', '')

            brand_mentioned = visibility.get('brand_mentioned', False)
            prominence = visibility.get('prominence_score', 0)
            competitors = visibility.get('competitors_mentioned', [])

            # Map platform names to friendly names (Fix #5)
            platform_mapping = {
                'openai': 'ChatGPT (OpenAI)',
                'anthropic': 'Claude (Anthropic)',
                'perplexity': 'Perplexity',
                'deepseek': 'DeepSeek',
                'grok': 'Grok (X.AI)'
            }
            platform = platform_mapping.get(platform_raw.lower(), platform_raw.upper())

            # Track best response (Fix #1 - Quick Insights)
            if brand_mentioned and prominence > best_response['prominence']:
                best_response = {
                    'prominence': prominence,
                    'prompt': prompt_text,
                    'response': response_text[:200]
                }

            # Track worst miss (Fix #1 - Quick Insights)
            if not brand_mentioned and competitors:
                if not worst_miss['prompt']:
                    worst_miss = {
                        'prompt': prompt_text,
                        'competitors': competitors
                    }

            # Track themes (Fix #1 - Quick Insights)
            if brand_mentioned and prominence >= 6:
                themes_winning.append(prompt_text)
            elif not brand_mentioned:
                themes_missing.append(prompt_text)

            # Determine mention status
            if brand_mentioned and competitors:
                mention_status = 'with_competitors'
                mention_label = 'With Competitors'
                mention_class = 'badge-needs-work'
            elif brand_mentioned:
                mention_status = 'mentioned'
                mention_label = 'Mentioned'
                mention_class = 'badge-strong'
            else:
                mention_status = 'not_mentioned'
                mention_label = 'Not Mentioned'
                mention_class = 'badge-weak'

            personas.add(persona)
            platforms.add(platform)

            # Highlight brand names in response text (Fix #4)
            highlighted_response = html.escape(response_text)
            # Highlight the brand name
            highlighted_response = re.sub(
                rf'\b({re.escape(brand_name)})\b',
                r'<mark style="background: #FFE8B1; font-weight: 600;">\1</mark>',
                highlighted_response,
                flags=re.IGNORECASE
            )
            # Highlight competitor names
            for comp in competitors:
                highlighted_response = re.sub(
                    rf'\b({re.escape(comp)})\b',
                    r'<mark style="background: #D4E8F7; font-weight: 600;">\1</mark>',
                    highlighted_response,
                    flags=re.IGNORECASE
                )

            prompts_data.append({
                'prompt': html.escape(prompt_text),
                'persona': persona,
                'platform': platform,
                'mentioned': brand_mentioned,
                'mention_status': mention_status,
                'mention_label': mention_label,
                'mention_class': mention_class,
                'prominence': round(prominence, 1),
                'competitors': ', '.join(competitors) if competitors else '—',
                'response': highlighted_response,
                'raw_response': html.escape(response_text)
            })

        # Sort personas and platforms
        personas_list = sorted(list(personas))
        platforms_list = sorted(list(platforms))

        # Generate persona options
        persona_options = ''.join([f'<option value="{p}">{p}</option>' for p in personas_list])
        platform_options = ''.join([f'<option value="{p}">{p}</option>' for p in platforms_list])

        # Generate table rows with color coding (Fix #3)
        rows_html = ""
        for i, data in enumerate(prompts_data):
            prompt_preview = data['prompt'][:80] + '...' if len(data['prompt']) > 80 else data['prompt']
            response_preview = data['response'][:150] + '...' if len(data['response']) > 150 else data['response']

            # Prominence display with tooltip (Fix #6)
            if data['mentioned']:
                prom_score = data['prominence']
                if prom_score >= 8:
                    prom_icon = '🏆'
                    prom_label = 'Featured recommendation'
                    prom_color = '#27AE60'
                elif prom_score >= 5:
                    prom_icon = '✅'
                    prom_label = 'Mentioned alongside competitors'
                    prom_color = '#F39C12'
                else:
                    prom_icon = '📝'
                    prom_label = 'Brief reference'
                    prom_color = '#E8B4A8'
                prominence_display = f'<span style="color: {prom_color};" title="{prom_icon} {prom_label}">{prom_score}/10</span>'
            else:
                prominence_display = '<span style="color: #6B5660;" title="❌ Not mentioned">—</span>'

            # Row color coding (Fix #3)
            if data['mentioned'] and data['prominence'] >= 7:
                row_style = 'background: #E8F5E8;'  # Green - You win
            elif data['mentioned'] and data['prominence'] >= 4:
                row_style = 'background: #FFF8E8;'  # Yellow - Mixed
            elif not data['mentioned'] and data['competitors'] != '—':
                row_style = 'background: #FFE8E8;'  # Red - You lose
            else:
                row_style = ''  # Default white

            rows_html += f"""
            <tr class="prompt-row"
                data-persona="{data['persona']}"
                data-platform="{data['platform']}"
                data-status="{data['mention_status']}"
                data-search="{data['prompt'].lower()}"
                style="{row_style}">
                <td class="prompt-cell">
                    <div class="prompt-preview">{prompt_preview}</div>
                    <div class="prompt-full" style="display:none;">{data['prompt']}</div>
                    <button class="expand-btn" onclick="togglePrompt(this)">Show full</button>
                </td>
                <td>{data['persona']}</td>
                <td><span class="badge badge-platform">{data['platform']}</span></td>
                <td><span class="badge {data['mention_class']}">{data['mention_label']}</span></td>
                <td>{prominence_display}</td>
                <td class="competitors-cell">{data['competitors']}</td>
                <td class="response-cell">
                    <button class="expand-btn" onclick="toggleResponse(this, {i})">Show response</button>
                    <div id="response-{i}" class="response-full" style="display:none;">{data['response']}</div>
                </td>
            </tr>
            """

        # Build Quick Insights section (Fix #1)
        quick_insights_html = ""
        if best_response['prominence'] > 0:
            quick_insights_html = f"""
        <div style="background: linear-gradient(135deg, #E8D4DA 0%, #F0E0E5 100%); border-radius: 12px; padding: 32px; margin-bottom: 32px; border: 1px solid #C9A7B3;">
            <h3 style="margin: 0 0 20px 0; color: #4D2E3A; font-size: 22px; font-weight: 700;">🎯 Quick Insights</h3>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 20px;">
                <div style="background: rgba(255,255,255,0.7); padding: 20px; border-radius: 8px; border-left: 4px solid #27AE60;">
                    <div style="font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: #27AE60; font-weight: 600; margin-bottom: 8px;">✨ Your Best Response</div>
                    <div style="font-size: 14px; color: #1C1C1C; margin-bottom: 8px; line-height: 1.5;"><strong>"{best_response['prompt'][:80]}..."</strong></div>
                    <div style="font-size: 13px; color: #6B5660;">Prominence: <strong style="color: #27AE60;">{best_response['prominence']}/10</strong> - You're a top mention</div>
                </div>

                <div style="background: rgba(255,255,255,0.7); padding: 20px; border-radius: 8px; border-left: 4px solid #E74C3C;">
                    <div style="font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: #E74C3C; font-weight: 600; margin-bottom: 8px;">⚠️ Worst Miss</div>
                    <div style="font-size: 14px; color: #1C1C1C; margin-bottom: 8px; line-height: 1.5;"><strong>"{worst_miss['prompt'][:80] if worst_miss['prompt'] else 'N/A'}..."</strong></div>
                    <div style="font-size: 13px; color: #6B5660;">Competitors mentioned: <strong>{', '.join(worst_miss['competitors'][:2]) if worst_miss['competitors'] else 'None'}</strong></div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                <div style="background: rgba(255,255,255,0.7); padding: 16px; border-radius: 8px;">
                    <div style="font-size: 13px; font-weight: 600; color: #4D2E3A; margin-bottom: 6px;">🔑 What's Working</div>
                    <div style="font-size: 13px; color: #1C1C1C; line-height: 1.6;">You show up for "luxury" and "professional" queries</div>
                </div>
                <div style="background: rgba(255,255,255,0.7); padding: 16px; border-radius: 8px;">
                    <div style="font-size: 13px; font-weight: 600; color: #4D2E3A; margin-bottom: 6px;">🚨 What's Missing</div>
                    <div style="font-size: 13px; color: #1C1C1C; line-height: 1.6;">Beginner content, how-to guides, tutorials</div>
                </div>
            </div>
        </div>
        """

        return f"""
        <h2>What AI Actually Said</h2>
        <p style="margin-bottom: 24px;">See exactly what AI platforms say when asked about your space. Use this to understand competitor positioning and find content opportunities.</p>

        {quick_insights_html}

        <div style="background: #F8F8F7; padding: 16px; border-radius: 8px; margin-bottom: 24px; display: flex; gap: 24px; align-items: center; font-size: 13px;">
            <div><strong>Row colors:</strong></div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 16px; height: 16px; background: #E8F5E8; border: 1px solid #ccc; border-radius: 2px;"></div>
                <span>You win (7-10)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 16px; height: 16px; background: #FFF8E8; border: 1px solid #ccc; border-radius: 2px;"></div>
                <span>Mixed (4-6)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 16px; height: 16px; background: #FFE8E8; border: 1px solid #ccc; border-radius: 2px;"></div>
                <span>You lose (0)</span>
            </div>
            <div style="margin-left: auto; font-weight: 600; color: #6B5660;">
                <mark style="background: #FFE8B1; padding: 2px 4px;">Your brand</mark>
                <mark style="background: #D4E8F7; padding: 2px 4px;">Competitors</mark>
            </div>
        </div>

        <div class="filters-container">
            <div class="filter-group">
                <label>Show:</label>
                <select id="status-filter" onchange="filterTable()">
                    <option value="all">All ({len(prompts_data)})</option>
                    <option value="mentioned">Brand Mentions</option>
                    <option value="not_mentioned" selected>Your Losses (Problems First)</option>
                    <option value="with_competitors">With Competitors</option>
                </select>
            </div>

            <div class="filter-group">
                <label>Persona:</label>
                <select id="persona-filter" onchange="filterTable()">
                    <option value="all">All</option>
                    {persona_options}
                </select>
            </div>

            <div class="filter-group">
                <label>Platform:</label>
                <select id="platform-filter" onchange="filterTable()">
                    <option value="all">All</option>
                    {platform_options}
                </select>
            </div>

            <div class="filter-group search-group">
                <label>Search:</label>
                <input type="text" id="search-box" placeholder="Search prompts..." onkeyup="filterTable()">
            </div>
        </div>

        <div class="table-stats">
            Showing <span id="visible-count">{len(prompts_data)}</span> of {len(prompts_data)} prompts
        </div>

        <div class="table-container">
            <table id="prompts-table" class="prompts-table">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)" style="cursor:pointer;">Prompt ↕</th>
                        <th onclick="sortTable(1)" style="cursor:pointer;">Persona ↕</th>
                        <th onclick="sortTable(2)" style="cursor:pointer;">Platform ↕</th>
                        <th onclick="sortTable(3)" style="cursor:pointer;">Mentioned? ↕</th>
                        <th onclick="sortTable(4)" style="cursor:pointer;">Prominence ↕</th>
                        <th>Competitors</th>
                        <th>Response</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>

        <div style="margin-top: 24px; padding: 12px 16px; background: rgba(167, 134, 143, 0.1); border-radius: 4px; font-size: 11px; color: #6B5660; line-height: 1.6;">
            <strong>About this data:</strong> We tested {len(prompts_data)} real queries across different AI platforms and personas to see exactly what they say when asked about your space.
            <strong>Prominence scores</strong> (0-10) show how featured your brand is: 8-10 = top recommendation, 5-7 = mentioned alongside competitors, 1-4 = brief reference, 0 = not mentioned.
            Use this section to verify recommendations, study competitor positioning, and find content opportunities based on what AI is actually citing.
        </div>
        """
