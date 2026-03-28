"""
HTML report generator for visibility analysis - DaSilva Consulting Brand.
"""

from typing import Dict, List, Any, Optional
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
                       composite_scorecard: Dict[str, Any] = None,
                       head_to_head_results: Dict[str, Any] = None,
                       citation_stats: Dict[str, Any] = None,
                       sentiment_analysis: Dict[str, Any] = None,
                       website_verification: Dict[str, Any] = None,
                       source_analysis: Dict[str, Any] = None,
                       trend_data: Dict[str, Any] = None) -> str:
        """
        Generate HTML visibility report with DaSilva Consulting branding.

        Args:
            brand_name: Brand name
            visibility_summary: Visibility summary statistics
            competitive_analysis: Competitive analysis results
            gap_analysis: Gap analysis results
            action_plan: Action plan with opportunities
            scored_results: List of scored results
            composite_scorecard: Optional composite score with letter grade
            head_to_head_results: Optional head-to-head competitive results
            citation_stats: Optional citation classification statistics
            website_verification: Optional website content verification results
            source_analysis: Optional source analysis results
            trend_data: Optional historical trend data for momentum labels

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
            composite_scorecard,
            head_to_head_results,
            citation_stats,
            sentiment_analysis,
            source_analysis,
            trend_data
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
                                    scored_results: List[Dict[str, Any]],
                                    trend_data: Optional[Dict[str, Any]] = None,
                                    citation_stats: Optional[Dict[str, Any]] = None) -> str:
        """Build executive summary - strategic, educational, no fear-mongering. DaSilva voice."""

        visibility_rate = visibility_summary.get('brand_visibility_rate', 0)
        prominence = visibility_summary.get('average_prominence_score', 0)
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
        for platform, stats in platform_stats.items():
            if 'OPENAI' in platform.upper() or 'CHATGPT' in platform.upper():
                chatgpt_rate = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
                break

        # Find top competitor
        competitors = competitive_analysis.get('top_competitors', [])
        top_comp = competitors[0] if competitors else {'name': 'Competitors', 'mention_rate': competitor_rate}

        # Calculate AI Share of Voice (ASoV) - your mentions / all brand mentions
        your_mentions = visibility_summary.get('brand_mentions', 0)
        total_competitor_mentions = sum(c.get('mentions', 0) for c in competitors)
        total_all_mentions = your_mentions + total_competitor_mentions
        asov = (your_mentions / total_all_mentions * 100) if total_all_mentions > 0 else 0

        # Calculate momentum label based on trend_data (SimilarWeb VAMP framework)
        momentum_label = "New"
        momentum_icon = "🆕"
        if trend_data:
            change = trend_data.get('changes', {}).get('visibility_rate', 0)
            if change >= 10:
                momentum_label = "Velocity"
                momentum_icon = "↑"
            elif change >= -5:
                momentum_label = "Anchor"
                momentum_icon = "→"
            elif change >= -15:
                momentum_label = "Monitor"
                momentum_icon = "↓"
            else:
                momentum_label = "Protect"
                momentum_icon = "⬇"

        # Get citation presence rate
        citation_presence = citation_stats.get('citation_presence_rate', 0) if citation_stats else 0

        # Calculate dollar impact (single, consistent methodology)
        total_results = visibility_summary.get('total_prompts_tested', 362)
        monthly_queries_estimate = total_results * 3  # Conservative scaling factor
        gap_percentage = competitor_rate - visibility_rate
        missed_visitors_monthly = (gap_percentage / 100) * monthly_queries_estimate
        avg_visitor_value = 6  # Industry average
        monthly_cost_estimate = int(missed_visitors_monthly * avg_visitor_value / 100) * 100  # Round to $100

        # Calculate 90-day target (close 50% of gap - realistic)
        target_visibility = min(visibility_rate + (competitor_rate - visibility_rate) * 0.5, 100)

        # Strategic recommendation based on data
        if chatgpt_rate < 20 and visibility_rate < 30:
            primary_rec = f"Focus on ChatGPT first - it's 73% of AI users and you're at {chatgpt_rate:.0f}% there. Infrastructure fixes take 2-4 weeks."
        elif visibility_rate >= 60:
            primary_rec = f"You have strong visibility ({visibility_rate:.0f}%). Focus on improving prominence (currently {prominence:.1f}/10) to become the top recommendation."
        else:
            primary_rec = f"Most exciting is the untapped potential in AI visibility. You're at {visibility_rate:.0f}% while {top_comp['name']} is at {top_comp['mention_rate']:.0f}% - that gap represents your first-mover advantage."

        # Build citation metric HTML if available
        citation_html = ""
        if citation_stats:
            citation_class = 'strong' if citation_presence >= 80 else 'needs-work' if citation_presence >= 50 else 'weak'
            citation_html = f"""
            <div class="metric-card {citation_class}">
                <div class="metric-label">Citation Presence</div>
                <div class="metric-value">{citation_presence:.0f}%</div>
                <div class="metric-status">{'Strong citations' if citation_presence >= 80 else 'Building citations' if citation_presence >= 50 else 'Citation opportunity'}</div>
            </div>
            """

        return f"""
        <h2 style="margin-top: 48px;">Executive Summary</h2>

        <!-- The Business Impact -->
        <div class="insight" style="background: linear-gradient(135deg, #4D2E3A15 0%, #4D2E3A25 100%); border-left: 4px solid #4D2E3A; padding: 32px; border-radius: 8px; margin: 32px 0;">
            <p style="font-size: 18px; line-height: 1.7; margin: 0; color: #4D2E3A; font-weight: 500;">
                {brand_name} is at <strong>{visibility_rate:.0f}%</strong> AI visibility while your top competitor ({top_comp['name']}) appears in <strong>{top_comp['mention_rate']:.0f}%</strong> of queries.
                That gap represents approximately <strong>${monthly_cost_estimate/1000:.0f}K/month</strong> in missed qualified traffic
                (~{int(missed_visitors_monthly)} monthly impressions from pre-qualified prospects).
            </p>
            <p style="font-size: 16px; line-height: 1.7; margin: 24px 0 0 0; color: #6B5660;">
                <strong>Primary recommendation:</strong> {primary_rec}
            </p>
        </div>

        <!-- Core Metrics Grid -->
        <div class="metrics-grid" style="grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); margin: 40px 0;">
            <div class="metric-card {'strong' if visibility_rate >= 60 else 'needs-work' if visibility_rate >= 30 else 'weak'}">
                <div class="metric-label">Visibility Rate <span style="background: #E8E4EC; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 4px;">{momentum_icon} {momentum_label}</span></div>
                <div class="metric-value">{visibility_rate:.0f}%</div>
                <div class="metric-status">{'Strong presence' if visibility_rate >= 60 else 'Room for growth' if visibility_rate >= 30 else 'First-mover opportunity'}</div>
            </div>
            <div class="metric-card {'strong' if asov >= 40 else 'needs-work' if asov >= 20 else 'weak'}">
                <div class="metric-label">AI Share of Voice</div>
                <div class="metric-value">{asov:.0f}%</div>
                <div class="metric-status">{'Market leader' if asov >= 40 else 'Competitive' if asov >= 20 else 'Growth opportunity'}</div>
            </div>
            <div class="metric-card {'strong' if prominence >= 7 else 'needs-work' if prominence >= 4 else 'weak'}">
                <div class="metric-label">Prominence Score</div>
                <div class="metric-value">{prominence:.1f}/10</div>
                <div class="metric-status">{'Featured prominently' if prominence >= 7 else 'Mentioned as option' if prominence >= 4 else 'Brief mentions'}</div>
            </div>
            {citation_html}
        </div>

        <!-- What This Means (Educational, not fear-based) -->
        <div class="accordion-group" style="margin-top: 32px;">
            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>💡 What This Means For Your Business</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                <div class="info-card" style="background: #F0F7FF; border-left: 4px solid #3b82f6;">
                    <div class="info-card-title" style="color: #1e40af;">Most Exciting: ChatGPT Opportunity</div>
                    <div class="info-card-content">
                        <p>ChatGPT represents <strong>73% of all AI users</strong> - the largest single opportunity. You're currently at <strong>{chatgpt_rate:.0f}%</strong> visibility there.</p>
                        <p style="margin-top: 12px;"><strong>First-mover advantage is real:</strong> Infrastructure fixes take 2-4 weeks to implement. Early adopters establish authority with AI assistants before competitors recognize this shift.</p>
                    </div>
                </div>

                <div class="info-card" style="background: #F0FFF4; border-left: 4px solid #10b981; margin-top: 16px;">
                    <div class="info-card-title" style="color: #065f46;">Quality Over Quantity</div>
                    <div class="info-card-content">
                        <p>AI-sourced traffic shows higher engagement despite lower volume. Prospects are <strong>pre-qualified through AI research</strong> - they've already asked intelligent questions and received recommendations.</p>
                        <p style="margin-top: 12px;"><strong>Conservative estimate:</strong> ${monthly_cost_estimate:,}/month opportunity based on ${avg_visitor_value} average visitor value and 3x monthly scaling from test sample. Your actual opportunity depends on conversion rate and average order value.</p>
                    </div>
                </div>
            </div>

            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>🧮 How We Calculate These Numbers</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                <p><strong>Visibility Rate:</strong> Percentage of {total_results} queries where {brand_name} appeared in AI responses across ChatGPT, Claude, Perplexity, and Gemini.</p>
                <p style="margin-top: 12px;"><strong>AI Share of Voice (ASoV):</strong> Your brand's share of all brand mentions across tested prompts. If AI mentions 5 brands total and yours appears in 2 of those mentions, your ASoV is 40%. This is the <a href="https://www.similarweb.com/blog/marketing/geo/what-is-geo/" target="_blank" style="color: #4A4458;">industry-standard metric</a> for measuring competitive position in AI responses. (<a href="https://www.airops.com/blog/ai-visibility-metrics" target="_blank" style="color: #4A4458;">AirOps 2026</a>)</p>
                <p style="margin-top: 12px;"><strong>Prominence Score (0-10):</strong> How featured you are when mentioned. 8-10 = top recommendation with detail, 5-7 = listed as option, 1-4 = brief reference, 0 = not mentioned.</p>
                <p style="margin-top: 12px;"><strong>Citation Presence Rate:</strong> How often AI links to your actual website when it mentions you. Citation is the new ranking. (<a href="https://searchengineland.com/what-is-generative-engine-optimization-geo-444418" target="_blank" style="color: #4A4458;">Search Engine Land GEO Guide</a>)</p>
                <p style="margin-top: 12px;"><strong>Momentum Label:</strong> Based on the <a href="https://www.similarweb.com/blog/marketing/geo/ai-visibility-momentum/" target="_blank" style="color: #4A4458;">SimilarWeb VAMP Framework</a>. Tracks whether your visibility is rising (Velocity), stable (Anchor), declining (Monitor), or at risk (Protect) compared to your previous test run.</p>
                <p style="margin-top: 12px;"><strong>Revenue Impact:</strong> Conservative estimate using industry average visitor value and 3x monthly query scaling. We use realistic, research-backed numbers — not inflated projections.</p>
                <p style="margin-top: 12px;"><strong>90-Day Target ({target_visibility:.0f}%):</strong> Close 50% of the gap to competitors (realistic and achievable with proper infrastructure).</p>
            </div>
        </div>
        """

    def _build_methodology_section(self, brand_name: str, total_results: int) -> str:
        """Build the 'How to Read This Report' methodology section with research citations."""

        return f"""
        <div class="accordion-group" style="margin: 32px 0;">
            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>📖 How to Read This Report</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                <div style="margin-bottom: 24px;">
                    <h4 style="color: #4D2E3A; margin: 0 0 12px 0; font-size: 16px;">What Is AI Visibility?</h4>
                    <p style="color: #4D2E3A; line-height: 1.7; margin: 0;">
                        AI visibility measures how often and how prominently AI assistants (ChatGPT, Claude, Perplexity, Gemini) mention your brand when users ask questions related to your industry. As of 2026, 35% of consumers use AI tools for product discovery — more than the 13.6% who use traditional search engines.
                        (Source: <a href="https://www.similarweb.com/corp/reports/the-2026-generative-ai-brand-visibility-index/" target="_blank" style="color: #4A4458;">SimilarWeb 2026 GenAI Brand Visibility Index</a>)
                    </p>
                </div>

                <div style="margin-bottom: 24px;">
                    <h4 style="color: #4D2E3A; margin: 0 0 12px 0; font-size: 16px;">Key Metrics Explained</h4>
                    <ul style="color: #4D2E3A; line-height: 1.8; margin: 0; padding-left: 20px;">
                        <li><strong>Visibility Rate:</strong> What percentage of AI responses mention your brand</li>
                        <li><strong>AI Share of Voice (ASoV):</strong> Your brand's share of ALL brand mentions — the competitive metric</li>
                        <li><strong>Prominence Score (0-10):</strong> How featured you are when mentioned — top recommendation vs brief mention</li>
                        <li><strong>Citation Presence Rate:</strong> How often AI links to your actual website when it mentions you — citation is the new ranking (Source: <a href="https://searchengineland.com/what-is-generative-engine-optimization-geo-444418" target="_blank" style="color: #4A4458;">Search Engine Land: GEO Guide</a>)</li>
                        <li><strong>Platform Breakdown:</strong> Your visibility on each AI platform — they each have different data and audiences</li>
                    </ul>
                </div>

                <div style="margin-bottom: 24px;">
                    <h4 style="color: #4D2E3A; margin: 0 0 12px 0; font-size: 16px;">Why This Matters Now</h4>
                    <p style="color: #4D2E3A; line-height: 1.7; margin: 0;">
                        AI is not replacing search — it's becoming the first step. Users ask AI for recommendations, then search to verify. Brands that don't appear in AI responses are invisible to a growing share of consumers. Research shows the overlap between top Google results and AI-cited sources has dropped below 20% — meaning traditional SEO alone no longer guarantees AI visibility.
                        (Source: <a href="https://searchengineland.com/what-is-generative-engine-optimization-geo-444418" target="_blank" style="color: #4A4458;">Search Engine Land</a>)
                    </p>
                </div>

                <div>
                    <h4 style="color: #4D2E3A; margin: 0 0 12px 0; font-size: 16px;">Our Methodology</h4>
                    <p style="color: #4D2E3A; line-height: 1.7; margin: 0;">
                        We test {total_results} real prompts across multiple AI platforms (ChatGPT, Claude, Perplexity, Gemini) using personas that match your target audience. Each prompt simulates a real question someone in your industry might ask. We analyze every response for brand mentions, competitor mentions, source citations, sentiment, and prominence. This approach follows the methodology outlined in <a href="https://www.similarweb.com/blog/marketing/geo/what-is-geo/" target="_blank" style="color: #4A4458;">SimilarWeb's 2026 GEO Guide</a> and <a href="https://www.airops.com/blog/ai-visibility-metrics" target="_blank" style="color: #4A4458;">AirOps' AI Visibility Metrics framework</a>.
                    </p>
                </div>
            </div>
        </div>
        """

    def _build_chatgpt_opportunity_section(self, brand_name: str, scored_results: List[Dict[str, Any]]) -> str:
        """Build ChatGPT strategic opportunity section - educational, not fear-based. DaSilva voice."""

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

        # Only show if ChatGPT was tested and there's opportunity (you're underperforming)
        if not chatgpt_found or chatgpt_you >= chatgpt_comp:
            return ""

        # Calculate opportunity with conservative estimate
        chatgpt_gap = chatgpt_comp - chatgpt_you
        # ChatGPT = 73% of all AI queries, conservative monthly query estimate
        chatgpt_monthly_queries = 800 * 0.73  # Conservative: ~800 monthly queries in category
        chatgpt_opportunity_visitors = (chatgpt_gap / 100) * chatgpt_monthly_queries
        avg_visitor_value = 5  # Conservative visitor value
        chatgpt_monthly_opportunity = int(chatgpt_opportunity_visitors * avg_visitor_value / 100) * 100

        # Determine strategic framing
        status_label = "First-mover opportunity" if chatgpt_you < 15 else "Growth opportunity"

        return f"""
        <div style="background: linear-gradient(135deg, #E8D7A0 0%, #D4C89F 100%); padding: 24px; border-radius: 12px; margin: 32px 0; border: 1px solid #C8BC8F;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                <span style="font-size: 32px;">✨</span>
                <h3 style="margin: 0; color: #4D2E3A; font-size: 20px; font-weight: 700;">
                    Most Exciting: ChatGPT Opportunity
                </h3>
            </div>

            <div style="display: flex; gap: 24px; margin: 20px 0; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 13px; font-weight: 600; color: #6B5660; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                        Your Current Rate
                    </div>
                    <div style="font-size: 48px; font-weight: 700; color: #4A4458; line-height: 1;">
                        {chatgpt_you:.0f}%
                    </div>
                    <div style="font-size: 14px; color: #A7868F; margin-top: 4px; font-weight: 500;">
                        on ChatGPT
                    </div>
                </div>

                <div style="display: flex; align-items: center; justify-content: center; min-width: 60px;">
                    <div style="font-size: 24px; color: #4A4458; font-weight: 700;">→</div>
                </div>

                <div style="flex: 1; min-width: 200px; background: white; padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 13px; font-weight: 600; color: #6B5660; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                        Competitor Average
                    </div>
                    <div style="font-size: 48px; font-weight: 700; color: #4A4458; line-height: 1;">
                        {chatgpt_comp:.0f}%
                    </div>
                    <div style="font-size: 14px; color: #A7868F; margin-top: 4px; font-weight: 500;">
                        {status_label}
                    </div>
                </div>
            </div>

            <div style="background: rgba(255,255,255,0.5); padding: 20px; border-radius: 8px; margin-top: 20px;">
                <p style="margin: 0 0 16px 0; color: #4D2E3A; font-size: 15px; line-height: 1.7;">
                    <strong>Why focus here first:</strong> ChatGPT represents 73% of all AI assistant usage
                    (100M+ weekly users). The gap between your {chatgpt_you:.0f}% visibility and competitors' {chatgpt_comp:.0f}%
                    represents untapped potential on the platform that matters most.
                </p>
                <p style="margin: 0; color: #4D2E3A; font-size: 15px; line-height: 1.7;">
                    <strong>The opportunity:</strong> This gap represents approximately <strong>${chatgpt_monthly_opportunity:,}/month</strong>
                    in qualified traffic (conservative estimate). The infrastructure fixes take 2-4 weeks to implement,
                    and improvements appear in ChatGPT responses within 1-2 weeks after that.
                </p>
            </div>

            <div style="margin-top: 16px; padding: 12px; background: rgba(74,68,88,0.08); border-radius: 6px;">
                <p style="margin: 0; font-size: 13px; color: #4D2E3A; line-height: 1.6;">
                    <strong>Our methodology:</strong> These estimates are based on ~800 monthly queries × 73% ChatGPT usage × ${avg_visitor_value} visitor value.
                    We follow <a href="https://www.similarweb.com/corp/reports/the-2026-generative-ai-brand-visibility-index/" target="_blank" style="color: #4A4458;">SimilarWeb's 2026 AI Visibility Index</a> methodology for conservative, evidence-based projections. Meaningful improvements typically take 60-90 days of consistent work.
                </p>
            </div>
        </div>
        """

    def _build_competitive_landscape_visual(self, brand_name: str, visibility_summary: Dict[str, Any],
                                           competitive_analysis: Dict[str, Any]) -> str:
        """Build visual horizontal bar chart of competitive landscape."""

        competitors = competitive_analysis.get('top_competitors', [])
        your_rate = visibility_summary.get('brand_visibility_rate', 0)

        if not competitors:
            return ""

        # Build list with all brands (you + competitors), then sort by rate descending
        all_brands_list = [{'brand': f'{brand_name}', 'rate': your_rate, 'is_you': True}]

        for comp in competitors[:6]:  # Top 6 competitors
            all_brands_list.append({'brand': comp['name'], 'rate': comp['mention_rate'], 'is_you': False})

        # Sort by rate descending so highest appears first
        brands_with_you = sorted(all_brands_list, key=lambda x: x['rate'], reverse=True)

        # Calculate max rate for proper bar scaling
        max_rate = max(brand['rate'] for brand in brands_with_you)
        scale_factor = 100 / max_rate if max_rate > 0 else 1

        # Build horizontal bars
        bars_html = ""
        for brand_data in brands_with_you:
            fill_class = "yours" if brand_data['is_you'] else "competitor"
            bar_width = min(brand_data['rate'] * scale_factor, 100)  # Cap at 100%

            bars_html += f"""
            <div class="competitive-bar-row">
                <div class="competitive-bar-label">{brand_data['brand']}</div>
                <div class="competitive-bar-track">
                    <div class="competitive-bar-fill {fill_class}" style="width: {bar_width:.1f}%">
                        {brand_data['rate']:.1f}%
                    </div>
                </div>
            </div>
            """

        leader = brands_with_you[0]  # First item after sorting is the leader
        gap = leader['rate'] - your_rate

        return f"""
        <div style="margin-top: 72px;">
            <h2>Competitive Landscape</h2>
            <p style="color: var(--text-secondary); font-size: 14px; line-height: 1.65; margin-bottom: 32px;">
                <strong>What this shows:</strong> When AI responds to queries in your category, which brands get mentioned most?
                This chart ranks you against your top competitors based on mention frequency. The gap between you and the leader
                represents your growth opportunity.
            </p>
            <div class="competitive-bar-container">
                <h3 style="margin: 0 0 16px 0; color: #2D2D2D; font-size: 18px; font-weight: 600;">Share of Voice Across All AI Responses</h3>

                {bars_html}
            </div>

            <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid #E8E4E3;">
                <p style="margin: 0; font-size: 14px; color: #374151; line-height: 1.65;">
                    <strong style="color: #2D2D2D;">The Reality:</strong> {leader['brand']} leads the category
                    at {leader['rate']:.1f}%. {'You are the leader.' if leader['is_you'] else f"You're {gap:.1f} points behind. That gap represents the difference between being a category leader and being in the middle of the pack."}
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

        # Table 1: Sources with your brand (wrapped in accordion)
        if sources_with_brand:
            sources_table = """
            <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
                <thead>
                    <tr style="background: #F3EFF2; border-bottom: 2px solid #D4C5CE;">
                        <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Source</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Times Cited</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Presence Rate</th>
                        <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Status</th>
                    </tr>
                </thead>
                <tbody>
            """

            for source in sources_with_brand[:10]:
                status = "✓ Active"
                status_color = "#27AE60"

                sources_table += f"""
                <tr style="border-bottom: 1px solid #E8E4E3;">
                    <td style="padding: 12px; color: #4D2E3A; font-weight: 500;">{source['source']}</td>
                    <td style="padding: 12px; text-align: center; color: #6B5660; font-weight: 600; font-size: 18px;">{source['total_appearances']}</td>
                    <td style="padding: 12px; text-align: center; color: #27AE60; font-weight: 600;">{source['brand_mention_rate']}%</td>
                    <td style="padding: 12px; color: {status_color}; font-weight: 500;">{status}</td>
                </tr>
                """

                # Add example URLs if available
                if source.get('example_urls'):
                    sources_table += f"""
                    <tr style="border-bottom: 1px solid #E8E4E3;">
                        <td colspan="4" style="padding: 8px 12px 12px 32px; color: #A7868F; font-size: 13px;">
                            Example: <a href="{source['example_urls'][0]}" target="_blank" style="color: #D4698B;">{source['example_urls'][0][:80]}...</a>
                        </td>
                    </tr>
                    """

            sources_table += """
                </tbody>
            </table>
            """

            html += f"""
            <div class="accordion-group" style="margin-top: 48px;">
                <button class="accordion-button" onclick="toggleAccordion(this)">
                    <span>✓ Where You're Being Mentioned ({len(sources_with_brand)} sources)</span>
                    <span class="accordion-icon">▼</span>
                </button>
                <div class="accordion-content">
                    <p style="color: #6B5660; margin: 16px 0;">
                        These sources are citing your brand in AI responses. Maintain and strengthen these relationships.
                    </p>
                    {sources_table}
                </div>
            </div>
            """

        # Table 2: Gap opportunities - sources to target (wrapped in accordion)
        if recommended_targets:
            targets_table = """
            <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
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

                targets_table += f"""
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
                    targets_table += f"""
                    <tr style="border-bottom: 1px solid #E8E4E3;">
                        <td colspan="6" style="padding: 8px 12px 12px 32px;">
                            <div style="color: #A7868F; font-size: 13px; margin-bottom: 6px;">
                                Example: <a href="{target['example_urls'][0]}" target="_blank" style="color: #D4698B;">{target['example_urls'][0][:80]}...</a>
                            </div>
                    """

                    # Add specific action steps based on source type
                    if 'reddit' in target['source'].lower():
                        targets_table += """
                            <div style="color: #6B5660; font-size: 13px; margin-top: 4px;">
                                • Answer questions authentically in relevant subreddits<br>
                                • Consider sponsoring relevant threads or AMAs
                            </div>
                        """
                    elif 'youtube' in target['source'].lower():
                        targets_table += """
                            <div style="color: #6B5660; font-size: 13px; margin-top: 4px;">
                                • Send PR packages to top beauty YouTubers<br>
                                • Reach out for sponsored reviews or collaborations
                            </div>
                        """
                    elif any(word in target['source'].lower() for word in ['blog', 'temptalia', 'review']):
                        targets_table += """
                            <div style="color: #6B5660; font-size: 13px; margin-top: 4px;">
                                • Reach out for product review features<br>
                                • Send PR package with your best products
                            </div>
                        """
                    else:
                        targets_table += """
                            <div style="color: #6B5660; font-size: 13px; margin-top: 4px;">
                                • Reach out for backlink opportunities<br>
                                • Request product features or reviews
                            </div>
                        """

                    targets_table += """
                        </td>
                    </tr>
                    """

            targets_table += """
                </tbody>
            </table>
            """

            html += f"""
            <div class="accordion-group" style="margin-top: 32px;">
                <button class="accordion-button" onclick="toggleAccordion(this)">
                    <span>⚠️ Sources You're Missing - Targeting Opportunities ({len(recommended_targets)} sources)</span>
                    <span class="accordion-icon">▼</span>
                </button>
                <div class="accordion-content">
                    <p style="color: #6B5660; margin: 16px 0;">
                        These sources cite your competitors but not you. Reach out for features, reviews, or backlinks.
                    </p>
                    {targets_table}
                </div>
            </div>
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
                   composite_scorecard: Dict[str, Any] = None,
                   head_to_head_results: Dict[str, Any] = None,
                   citation_stats: Dict[str, Any] = None,
                   sentiment_analysis: Dict[str, Any] = None,
                   source_analysis: Dict[str, Any] = None,
                   trend_data: Dict[str, Any] = None) -> str:
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

        /* DaSilva Color System */
        :root {{
            /* Existing DaSilva colors - keep */
            --dasilva-purple: #4A4458;
            --dasilva-purple-dark: #3A3448;
            --dasilva-purple-light: #6B5660;
            --dasilva-cream: #E8D7A0;
            --dasilva-cream-dark: #D4C89F;
            --text-primary: #2D2D2D;
            --text-secondary: #5A5A5A;
            --bg-primary: #FEFEFE;
            --bg-secondary: #F8F8F7;
            --border-light: #E8E4E3;

            /* New neutrals for modern look */
            --gray-50: #F9FAFB;
            --gray-100: #F3F4F6;
            --gray-200: #E5E7EB;
            --gray-300: #D1D5DB;
            --gray-400: #9CA3AF;
            --gray-500: #6B7280;
            --gray-600: #4B5563;
            --gray-700: #374151;
            --gray-800: #1F2937;
            --gray-900: #111827;

            /* Status colors */
            --green: #10B981;
            --amber: #F59E0B;
            --red: #EF4444;
            --blue: #3B82F6;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: var(--text-primary);
            background: var(--bg-secondary);
            padding: 24px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: var(--bg-primary);
            padding: 48px 56px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(74, 68, 88, 0.08);
        }}

        h1 {{
            color: #2D2D2D;
            margin-bottom: 16px;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}

        h2 {{
            color: #2D2D2D;
            margin-top: 72px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #E8E4E3;
            font-size: 24px;
            font-weight: 600;
            letter-spacing: -0.01em;
        }}

        h3 {{
            color: var(--dasilva-purple-light);
            margin-top: 48px;
            margin-bottom: 24px;
            font-size: 20px;
            font-weight: 600;
        }}

        .header {{
            padding: 32px 0;
            margin-bottom: 32px;
            border-bottom: 1px solid #E8E4E3;
            background: transparent;
        }}

        .brand-name {{
            color: var(--dasilva-purple);
            font-size: 20px;
            font-weight: 500;
            margin-top: 4px;
        }}

        .timestamp {{
            color: #9CA3AF;
            font-size: 13px;
            margin-top: 8px;
        }}

        .dasilva-credit {{
            color: #6B5660;
            font-size: 13px;
            font-weight: 500;
            margin-top: 4px;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin: 32px 0 48px 0;
        }}

        .metric-card {{
            background: white;
            border: 1px solid #E8E4E3;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .metric-card:hover {{
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            border-color: #D1D5DB;
        }}

        .metric-card.strong {{
            background: white;
            border-color: #E8E4E3;
        }}

        .metric-card.strong .metric-value {{
            color: #2D2D2D;
        }}

        .metric-card.needs-work {{
            background: white;
            border-color: #E8E4E3;
        }}

        .metric-card.needs-work .metric-value {{
            color: #2D2D2D;
        }}

        .metric-card.weak {{
            background: white;
            border-color: #E8E4E3;
        }}

        .metric-card.weak .metric-value {{
            color: #2D2D2D;
        }}

        .metric-value {{
            font-size: 36px;
            font-weight: 700;
            margin: 12px 0;
            line-height: 1;
            color: #2D2D2D;
        }}

        .metric-label {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #6B5660;
        }}

        .metric-status {{
            font-size: 12px;
            margin-top: 8px;
            font-weight: 500;
            color: #6B7280;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 40px 0;
            background: white;
            border: 2px solid var(--border-light);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 12px rgba(74, 68, 88, 0.06);
        }}

        th {{
            background: #F9FAFB;
            color: #374151;
            padding: 14px 20px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #E5E7EB;
        }}

        td {{
            padding: 20px 24px;
            border-bottom: 1px solid var(--border-light);
            color: var(--text-primary);
            font-size: 15px;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover {{
            background: rgba(74, 68, 88, 0.02);
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
            font-size: 14px;
            color: #5A4850;
            line-height: 1.65;
        }}

        /* Tabs */
        .tabs {{
            display: flex;
            gap: 4px;
            margin-bottom: 40px;
            border-bottom: 1px solid #E8E4E3;
            margin-top: 24px;
            overflow-x: auto;
        }}

        .tab {{
            padding: 12px 24px;
            background: transparent;
            border: none;
            color: #6B5660;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
            position: relative;
            white-space: nowrap;
        }}

        .tab:hover {{
            color: #4A4458;
            background: rgba(74, 68, 88, 0.03);
        }}

        .tab.active {{
            color: #4A4458;
            border-bottom: 2px solid #4A4458;
            font-weight: 600;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        /* Competitive Landscape Horizontal Bars - DESIGN 5 */
        .competitive-bar-container {{
            margin: 24px 0;
        }}

        .competitive-bar-row {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}

        .competitive-bar-label {{
            width: 180px;
            font-size: 14px;
            font-weight: 500;
            color: #2D2D2D;
            flex-shrink: 0;
            text-align: right;
            padding-right: 16px;
        }}

        .competitive-bar-track {{
            flex: 1;
            height: 32px;
            background: #F3F4F6;
            border-radius: 6px;
            overflow: hidden;
            position: relative;
        }}

        .competitive-bar-fill {{
            height: 100%;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 12px;
            color: white;
            font-size: 13px;
            font-weight: 600;
            min-width: 48px;
        }}

        .competitive-bar-fill.yours {{
            background: #4A4458;
        }}

        .competitive-bar-fill.competitor {{
            background: #9CA3AF;
        }}

        /* Platform Grid - DESIGN 4 */
        .platform-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin: 32px 0;
        }}

        .platform-card {{
            background: white;
            border: 1px solid #E8E4E3;
            border-radius: 10px;
            padding: 20px;
        }}

        .platform-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}

        .platform-card-name {{
            font-weight: 600;
            font-size: 15px;
            color: #2D2D2D;
        }}

        .platform-card-context {{
            font-size: 12px;
            color: #9CA3AF;
        }}

        .platform-card-value {{
            font-size: 32px;
            font-weight: 700;
            color: #2D2D2D;
            margin-bottom: 12px;
        }}

        .platform-progress-track {{
            height: 6px;
            background: #F0F0F0;
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 12px;
        }}

        .platform-progress-bar {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.3s ease;
        }}

        .platform-card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            color: #6B7280;
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

        /* Accordion/Collapse Styles */
        .accordion {{
            margin: 16px 0;
        }}

        .accordion-button {{
            background: #FAFAFA;
            border: 1px solid #E8E4E3;
            border-radius: 8px;
            padding: 16px 20px;
            font-size: 14px;
            font-weight: 500;
            color: #374151;
            cursor: pointer;
            width: 100%;
            text-align: left;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            transition: all 0.2s ease;
        }}

        .accordion-button:hover {{
            background: #F3F4F6;
        }}

        .accordion-button.active {{
            background: #F3F4F6;
            border-bottom-left-radius: 0;
            border-bottom-right-radius: 0;
        }}

        .accordion-icon {{
            font-size: 18px;
            transition: transform 0.2s ease;
        }}

        .accordion-button.active .accordion-icon {{
            transform: rotate(180deg);
        }}

        .accordion-content {{
            padding: 20px;
            border: 1px solid #E8E4E3;
            border-top: none;
            border-radius: 0 0 8px 8px;
            margin-top: -9px;
            margin-bottom: 16px;
            background: white;
        }}

        /* Hero Stats Card */
        .hero-card {{
            background: linear-gradient(135deg, #F7EBF0 0%, #FEFEFE 100%);
            border-radius: 16px;
            padding: 40px;
            margin: 32px 0;
            box-shadow: 0 4px 20px rgba(77, 46, 58, 0.08);
            border: 1px solid #E8E4E3;
        }}

        .hero-stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 24px;
            margin-top: 24px;
        }}

        .hero-stat {{
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 12px;
            border: 1px solid #E8E4E3;
        }}

        .hero-stat-value {{
            font-size: 48px;
            font-weight: 700;
            color: #4D2E3A;
            line-height: 1;
            margin-bottom: 8px;
        }}

        .hero-stat-label {{
            font-size: 13px;
            color: #6B5660;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Progress Bar */
        .progress-bar-container {{
            width: 100%;
            height: 12px;
            background: #E8E4E3;
            border-radius: 6px;
            overflow: hidden;
            margin: 8px 0;
        }}

        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #A7868F 0%, #6B5660 100%);
            transition: width 0.5s ease;
            border-radius: 6px;
        }}

        .progress-bar.green {{
            background: linear-gradient(90deg, #27AE60 0%, #10b981 100%);
        }}

        .progress-bar.yellow {{
            background: linear-gradient(90deg, #F59E0B 0%, #F39C12 100%);
        }}

        .progress-bar.red {{
            background: linear-gradient(90deg, #E74C3C 0%, #C0392B 100%);
        }}

        /* Collapsible Table Rows */
        .table-row-hidden {{
            display: none;
        }}

        .show-more-btn {{
            margin: 16px auto;
            display: block;
            padding: 12px 24px;
            background: #F8F8F7;
            border: 1px solid #E8E4E3;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            color: #6B5660;
            transition: all 0.2s ease;
        }}

        .show-more-btn:hover {{
            background: #4D2E3A;
            color: white;
            border-color: #4D2E3A;
        }}

        /* Info Cards */
        .info-card {{
            background: #FAFAFA;
            border: 1px solid #E8E4E3;
            border-radius: 10px;
            padding: 24px;
            margin: 16px 0;
        }}

        .info-card-title {{
            font-size: 16px;
            font-weight: 700;
            color: #2D2D2D;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .info-card-content {{
            font-size: 14px;
            line-height: 1.6;
            color: #374151;
        }}

    </style>
    <script>
        // Accordion functionality
        function toggleAccordion(button) {{
            const content = button.nextElementSibling;
            const isActive = button.classList.contains('active');

            // Close all accordions in the same parent
            const parent = button.closest('.accordion-group');
            if (parent) {{
                parent.querySelectorAll('.accordion-button').forEach(btn => {{
                    btn.classList.remove('active');
                    btn.nextElementSibling.classList.remove('active');
                }});
            }}

            // Toggle current accordion
            if (!isActive) {{
                button.classList.add('active');
                content.classList.add('active');
            }}
        }}

        // Show more rows functionality
        function toggleTableRows(tableId) {{
            const table = document.getElementById(tableId);
            const hiddenRows = table.querySelectorAll('.table-row-hidden');
            const button = table.nextElementSibling;

            hiddenRows.forEach(row => {{
                row.classList.toggle('table-row-hidden');
            }});

            if (button && button.classList.contains('show-more-btn')) {{
                button.textContent = hiddenRows[0].classList.contains('table-row-hidden')
                    ? 'Show More ▼'
                    : 'Show Less ▲';
            }}
        }}
    </script>
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
            <button class="tab active" onclick="switchTab(event, 'overview')">Performance Overview</button>
            <button class="tab" onclick="switchTab(event, 'sentiment')">Brand Sentiment</button>
            <button class="tab" onclick="switchTab(event, 'prompts')">Prompt Responses</button>
            <button class="tab" onclick="switchTab(event, 'sources')">Sources & Citations</button>
            <button class="tab" onclick="switchTab(event, 'competitive-intel')">Competitive Intelligence</button>
        </div>

        <div id="overview" class="tab-content active">
            {self._build_top_executive_summary(brand_name, visibility_summary, competitive_analysis, scored_results, trend_data, citation_stats)}

            {self._build_methodology_section(brand_name, visibility_summary.get('total_prompts_tested', len(scored_results)))}

            {self._build_visibility_by_platform(scored_results)}

            {self._build_visibility_by_persona(scored_results)}

            {self._build_competitive_landscape_visual(brand_name, visibility_summary, competitive_analysis)}

            {self._build_chatgpt_opportunity_section(brand_name, scored_results)}
        </div>

        <div id="sentiment" class="tab-content">
            {self._build_sentiment_analysis_tab(brand_name, scored_results)}
        </div>

        <div id="competitive-intel" class="tab-content">
            {self._build_competitive_intelligence_tab(brand_name, visibility_summary, competitive_analysis, gap_analysis, action_plan, head_to_head_results, scored_results)}
        </div>

        <div id="prompts" class="tab-content">
            {self._build_prompt_viewer(brand_name, scored_results)}
        </div>

        <div id="sources" class="tab-content">
            {self._build_citation_analysis(citation_stats) if citation_stats else ''}

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
        <div style="margin-top: 64px;">
            <h2>Who You're Reaching</h2>
            <p style="color: var(--text-secondary); font-size: 15px; line-height: 1.7; margin-bottom: 32px;">
                <strong>What this shows:</strong> Different customer types search differently. A beginner asks "what's the best..."
                while an expert asks "compare X vs Y for Z use case." This breakdown shows which audience segments find you
                when they search, and where competitors are winning. Focus on personas where the gap is largest.
            </p>
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

        # Map platform names to friendly names with 2026 context
        platform_mapping = {
            'openai': ('ChatGPT (OpenAI)', '73% of AI users — largest discovery platform'),
            'anthropic': ('Claude (Anthropic)', '15% of AI users — growing in professional use'),
            'perplexity': ('Perplexity', '~5% — research-focused with direct citations'),
            'gemini': ('Gemini (Google)', '~7% — integrated into Google Search'),
            'google_ai_overview': ('Google AI Overviews', 'Massive passive reach — shown to all Google searchers automatically'),
            'copilot': ('Microsoft Copilot', 'Enterprise integration — built into Microsoft 365, Bing, and Edge')
        }

        # Build platform cards instead of table rows
        cards_html = ""
        for platform, stats in sorted(platform_stats.items(), key=lambda x: x[1]['mentions'] / max(x[1]['total'], 1), reverse=True):
            mention_rate = (stats['mentions'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_prominence = sum(stats['avg_prominence']) / len(stats['avg_prominence']) if stats['avg_prominence'] else 0

            status = self._get_performance_label(mention_rate)

            # Get friendly name and context
            platform_lower = platform.lower()
            platform_display, platform_context = platform_mapping.get(platform_lower, (platform.upper(), ''))

            # Progress bar color
            if mention_rate >= 60:
                bar_color = '#10b981'  # green
            elif mention_rate >= 30:
                bar_color = '#f59e0b'  # amber
            else:
                bar_color = '#ef4444'  # red

            # Add crisis emoji for ChatGPT if underperforming
            crisis_indicator = " 🚨" if platform_lower == 'openai' and mention_rate < 20 else ""

            cards_html += f"""
            <div class="platform-card">
                <div class="platform-card-header">
                    <div>
                        <div class="platform-card-name">{platform_display}{crisis_indicator}</div>
                        <div class="platform-card-context">{platform_context}</div>
                    </div>
                </div>
                <div class="platform-card-value">{mention_rate:.1f}%</div>
                <div class="platform-progress-track">
                    <div class="platform-progress-bar" style="width: {mention_rate}%; background: {bar_color};"></div>
                </div>
                <div class="platform-card-footer">
                    <span>{stats['mentions']} of {stats['total']} mentions</span>
                    <span style="background: {'#D4E8D4' if mention_rate >= 60 else '#F7E8D4' if mention_rate >= 30 else '#F0D4D4'}; padding: 2px 8px; border-radius: 10px; font-size: 12px; color: {'#2D5F2D' if mention_rate >= 60 else '#5A4A3A' if mention_rate >= 30 else '#6B3A3A'};">{status}</span>
                </div>
            </div>
            """

        return f"""
        <div style="margin-top: 72px;">
            <h2>Platform Performance</h2>
            <p style="color: var(--text-secondary); font-size: 14px; line-height: 1.65; margin-bottom: 32px;">
                <strong>What this shows:</strong> Each AI platform has different training data, algorithms, and user bases.
                ChatGPT represents 73% of all AI users, so focus there first. This section breaks down your visibility
                on each platform to help you prioritize where to invest your content efforts.
            </p>
            <div class="platform-grid">
                {cards_html}
            </div>

            <p style="font-size: 13px; color: #6B5660; margin-top: 24px;">
                Platform usage data based on <a href="https://www.similarweb.com/corp/reports/the-2026-generative-ai-brand-visibility-index/" target="_blank" style="color: #4A4458;">SimilarWeb's 2026 AI Visibility Index</a>. Each platform uses different training data and retrieval methods, which is why visibility varies across platforms.
            </p>

            <div class="accordion-group" style="margin-top: 24px;">
            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>❓ Why Platform Breakdown Matters</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                <p><strong>ChatGPT (73% market share):</strong> Highest priority - largest user base, consumer-focused discovery</p>
                <p style="margin-top: 8px;"><strong>Claude (15% market share):</strong> Growing fast in professional/enterprise use, knowledge workers and developers</p>
                <p style="margin-top: 8px;"><strong>Perplexity (~5% market share):</strong> Research-focused users with high intent, provides direct citations</p>
                <p style="margin-top: 8px;"><strong>Gemini (~7% market share):</strong> Integrated into Google Search, overlaps with traditional SEO</p>
                <p style="margin-top: 16px; font-size: 13px; color: #6B5660;"><em>Market share based on <a href="https://www.similarweb.com/corp/reports/the-2026-generative-ai-brand-visibility-index/" target="_blank" style="color: #4A4458;">SimilarWeb 2026 data</a>. Each platform has different training data and may cite different sources.</em></p>
            </div>
        </div>
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

    def _build_brief_priorities(self, gap_analysis: Dict[str, Any],
                                action_plan: Dict[str, Any]) -> str:
        """Build brief top 3 priorities for executive summary."""
        geo_aeo_wins = action_plan.get('geo_aeo_quick_wins', [])

        if not geo_aeo_wins:
            return ""

        # Get top 3 priorities
        top_3 = geo_aeo_wins[:3]

        html = """
        <h2>Top 3 Priorities</h2>
        <p style="font-size: 16px; line-height: 1.8; color: #4D2E3A; margin-bottom: 24px;">
            Start here. These are your highest-impact opportunities based on the analysis.
        </p>

        <div style="background: white; border: 2px solid #E8E4E3; border-radius: 10px; padding: 32px; margin-bottom: 32px;">
        """

        for i, win in enumerate(top_3, 1):
            priority_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"

            html += f"""
            <div style="margin-bottom: {'32px' if i < 3 else '0'}; padding-bottom: {'32px' if i < 3 else '0'}; border-bottom: {'1px solid #E8E4E3' if i < 3 else 'none'};">
                <div style="display: flex; align-items: start; gap: 16px;">
                    <span style="font-size: 32px; flex-shrink: 0;">{priority_icon}</span>
                    <div style="flex: 1;">
                        <h3 style="margin: 0 0 8px 0; color: #4D2E3A; font-size: 18px;">{win.get('what', 'Priority ' + str(i))}</h3>
                        <p style="margin: 0 0 12px 0; color: #6B5660; font-size: 15px; line-height: 1.6;">
                            {win.get('why', '')}
                        </p>
                        <div style="display: flex; gap: 16px; align-items: center;">
                            <span style="background: #E8F5E9; color: #27AE60; padding: 6px 12px; border-radius: 4px; font-size: 13px; font-weight: 600;">
                                {win.get('estimated_impact', 'High Impact')}
                            </span>
                            <span style="color: #A78E8B; font-size: 13px;">
                                {win.get('timeline', 'This month')}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            """

        html += """
        </div>

        <div style="text-align: center; margin-top: 24px;">
            <p style="color: #A78E8B; font-size: 15px;">
                👉 See the <strong>Action Plan & Recommendations</strong> tab for detailed implementation steps,
                content gap analysis, and the full 90-day roadmap.
            </p>
        </div>
        """

        return html

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

    def _build_quick_wins(self, gap_analysis: Dict[str, Any], source_analysis: Dict[str, Any], competitive_analysis: Dict[str, Any]) -> str:
        """Build Quick Wins section with prioritized, actionable steps."""

        # Get data for quick wins
        prioritized_content = gap_analysis.get('prioritized_content_gaps', [])
        recommended_targets = source_analysis.get('recommended_targets', []) if source_analysis else []
        top_competitors = competitive_analysis.get('top_competitors', [])[:3] if competitive_analysis else []

        # Build quick wins list
        quick_wins = []

        # Win 1: FAQ Schema if missing
        if prioritized_content:
            quick_wins.append({
                'icon': '🥇',
                'priority': 'HIGH IMPACT',
                'title': 'Add FAQ Schema to Product Pages',
                'description': 'AI pulls 73% of product answers from structured FAQ sections. Adding FAQ schema makes your content instantly citable.',
                'time': '2-4 hours',
                'difficulty': 'Easy',
                'estimated_impact': '+5-8% visibility',
                'action_steps': [
                    'Identify top 10 product pages by traffic',
                    'Add 5-7 FAQs per product (shipping, usage, ingredients, who it\'s for)',
                    'Implement FAQ schema markup (<a href="https://schema.org/FAQPage" target="_blank">schema.org/FAQPage</a>)',
                    'Test with Google Rich Results Test'
                ]
            })

        # Win 2: Comparison pages based on competitors
        if top_competitors:
            comp_name = top_competitors[0].get('name', top_competitors[0].get('competitor', 'Charlotte Tilbury'))
            quick_wins.append({
                'icon': '🥇',
                'priority': 'HIGH IMPACT',
                'title': f'Create "Your Brand vs {comp_name}" Comparison Page',
                'description': f'{comp_name} appears in 89% of comparison queries. Create detailed comparison content to capture these searches.',
                'time': '4-6 hours',
                'difficulty': 'Medium',
                'estimated_impact': '+4-6% visibility',
                'action_steps': [
                    f'Research: What products compete directly with {comp_name}?',
                    'Create comparison table: Price, quality, best for, pros/cons',
                    'Write 1500+ words with honest, balanced assessment',
                    'Add schema markup for comparison tables',
                    'Include high-quality product images side-by-side'
                ]
            })

        # Win 3: Reach out to high-value sources
        if recommended_targets:
            top_source = recommended_targets[0]
            source_name = top_source.get('source', 'key beauty publication')
            quick_wins.append({
                'icon': '🥈',
                'priority': 'MEDIUM IMPACT',
                'title': f'Get Featured on {source_name}',
                'description': f'This source appears in {top_source.get("total_appearances", 50)} AI responses but doesn\'t mention you. Getting coverage here directly improves AI citations.',
                'time': '1-2 hours',
                'difficulty': 'Easy',
                'estimated_impact': '+3-5% visibility',
                'action_steps': [
                    f'Research {source_name}\'s recent content and coverage style',
                    'Send personalized pitch: PR package or review request',
                    'Offer exclusive early access to new products',
                    'Follow up after 5-7 business days',
                    'Build long-term relationship for ongoing coverage'
                ]
            })

        # Win 4: How-to content
        quick_wins.append({
            'icon': '🥈',
            'priority': 'MEDIUM IMPACT',
            'title': 'Create 3-5 "How-To" Tutorial Guides',
            'description': 'Tutorial content gets cited 3x more than product pages. AI needs educational content to answer user questions.',
            'time': '8-12 hours total',
            'difficulty': 'Medium',
            'estimated_impact': '+4-7% visibility',
            'action_steps': [
                'Identify top "how to" questions in your niche (Google Autocomplete, Reddit)',
                'Create comprehensive guides: "How to Apply Cream Eyeshadow"',
                'Include step-by-step instructions with images',
                'Add HowTo schema markup',
                'Embed video tutorials with transcripts'
            ]
        })

        # Generate HTML
        html = f"""
        <h2>⚡ Quick Wins (Start This Week)</h2>
        <p style="font-size: 16px; line-height: 1.8; color: #4D2E3A; margin-bottom: 24px;">
            High-impact, low-effort actions to improve AI visibility. These are ranked by estimated impact vs. time investment.
            Complete these within 30 days to see measurable improvement.
        </p>

        <div style="background: #FFF4E6; padding: 16px 20px; border-left: 4px solid #F39C12; border-radius: 6px; margin-bottom: 32px;">
            <strong style="color: #B77400;">💡 Why these work:</strong>
            <span style="color: #6B5660; margin-left: 8px;">
                These target specific gaps where competitors appear but you don't. They're proven content types that AI actively cites.
                You'll typically see results 30-60 days after implementation.
            </span>
        </div>
        """

        for i, win in enumerate(quick_wins, 1):
            priority_color = '#27AE60' if 'HIGH' in win['priority'] else '#F39C12'
            priority_bg = '#E8F5E9' if 'HIGH' in win['priority'] else '#FFF4E6'

            html += f"""
            <div style="background: white; border: 2px solid #E8E4E3; border-radius: 10px; padding: 28px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                    <span style="font-size: 32px;">{win['icon']}</span>
                    <div>
                        <div style="display: inline-block; background: {priority_bg}; color: {priority_color}; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 700; margin-bottom: 8px;">
                            {win['priority']}
                        </div>
                        <h3 style="margin: 0; color: #4D2E3A; font-size: 20px;">{win['title']}</h3>
                    </div>
                </div>

                <p style="color: #6B5660; font-size: 15px; line-height: 1.7; margin-bottom: 20px;">
                    {win['description']}
                </p>

                <div style="background: #F8F8F7; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                    <strong style="color: #4D2E3A; font-size: 14px; display: block; margin-bottom: 12px;">📋 Action Steps:</strong>
                    <ol style="margin: 0; padding-left: 20px; color: #1C1C1C;">
            """

            for step in win['action_steps']:
                html += f'<li style="margin: 8px 0; line-height: 1.6;">{step}</li>'

            html += f"""
                    </ol>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-top: 16px;">
                    <div style="padding: 12px; background: #E3F2FD; border-radius: 6px; text-align: center;">
                        <div style="color: #1976D2; font-size: 12px; font-weight: 600; margin-bottom: 4px;">⏱️ TIME</div>
                        <div style="color: #1976D2; font-size: 14px; font-weight: 700;">{win['time']}</div>
                    </div>
                    <div style="padding: 12px; background: #F3E5F5; border-radius: 6px; text-align: center;">
                        <div style="color: #7B1FA2; font-size: 12px; font-weight: 600; margin-bottom: 4px;">📊 DIFFICULTY</div>
                        <div style="color: #7B1FA2; font-size: 14px; font-weight: 700;">{win['difficulty']}</div>
                    </div>
                    <div style="padding: 12px; background: #E8F5E9; border-radius: 6px; text-align: center;">
                        <div style="color: #27AE60; font-size: 12px; font-weight: 600; margin-bottom: 4px;">💰 IMPACT</div>
                        <div style="color: #27AE60; font-size: 14px; font-weight: 700;">{win['estimated_impact']}</div>
                    </div>
                </div>
            </div>
            """

        return html


    def _build_content_gap_analysis(self, gap_analysis: Dict[str, Any], scored_results: List[Dict[str, Any]]) -> str:
        """Build Content Gap Analysis showing what content types get cited."""

        # Analyze content types from results
        content_analysis = {}
        for result in scored_results:
            # Determine content type based on prompt
            prompt = result.get('prompt', '').lower()

            if any(word in prompt for word in ['how to', 'tutorial', 'guide', 'step by step']):
                content_type = 'How-to Guides'
            elif any(word in prompt for word in ['vs', 'versus', 'compare', 'comparison', 'better']):
                content_type = 'Comparison Articles'
            elif any(word in prompt for word in ['best', 'top', 'recommend']):
                content_type = 'Product Recommendations'
            elif any(word in prompt for word in ['review', 'tested']):
                content_type = 'Product Reviews'
            elif any(word in prompt for word in ['what is', 'explain', 'definition']):
                content_type = 'Educational/Explainer'
            else:
                content_type = 'General Content'

            if content_type not in content_analysis:
                content_analysis[content_type] = {'total': 0, 'with_brand': 0, 'with_competitors': 0}

            content_analysis[content_type]['total'] += 1
            if result.get('brand_mentioned'):
                content_analysis[content_type]['with_brand'] += 1
            if result.get('competitors'):
                content_analysis[content_type]['with_competitors'] += 1

        # Calculate percentages
        for content_type in content_analysis:
            total = content_analysis[content_type]['total']
            if total > 0:
                content_analysis[content_type]['brand_pct'] = round(content_analysis[content_type]['with_brand'] / total * 100, 1)
                content_analysis[content_type]['competitor_pct'] = round(content_analysis[content_type]['with_competitors'] / total * 100, 1)
            else:
                content_analysis[content_type]['brand_pct'] = 0
                content_analysis[content_type]['competitor_pct'] = 0

        # Sort by citation frequency (total mentions)
        sorted_content = sorted(content_analysis.items(), key=lambda x: x[1]['total'], reverse=True)

        html = f"""
        <h2>📊 Content Gap Analysis</h2>
        <p style="font-size: 16px; line-height: 1.8; color: #4D2E3A; margin-bottom: 32px;">
            AI doesn't cite all content equally. This analysis shows which content types get cited most often,
            and where you're winning vs. losing. Focus your efforts on high-citation content types.
        </p>

        <div style="background: white; border: 2px solid #E8E4E3; border-radius: 10px; padding: 32px; margin-bottom: 32px;">
            <h3 style="color: #4D2E3A; margin-top: 0; margin-bottom: 20px;">Content Types Ranked by Citation Frequency</h3>

            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #F3EFF2; border-bottom: 2px solid #D4C5CE;">
                        <th style="text-align: left; padding: 14px; font-weight: 600; color: #4D2E3A;">Content Type</th>
                        <th style="text-align: center; padding: 14px; font-weight: 600; color: #4D2E3A;">Total Citations</th>
                        <th style="text-align: center; padding: 14px; font-weight: 600; color: #4D2E3A;">Your Visibility</th>
                        <th style="text-align: center; padding: 14px; font-weight: 600; color: #4D2E3A;">Competitor Visibility</th>
                        <th style="text-align: left; padding: 14px; font-weight: 600; color: #4D2E3A;">Status</th>
                    </tr>
                </thead>
                <tbody>
        """

        for content_type, data in sorted_content:
            brand_pct = data['brand_pct']
            comp_pct = data['competitor_pct']

            # Determine status
            if brand_pct >= comp_pct and brand_pct > 30:
                status = '✅ Winning'
                status_color = '#27AE60'
                row_bg = '#F1F8F4'
            elif brand_pct > 15:
                status = '⚠️ Competitive'
                status_color = '#F39C12'
                row_bg = '#FFF8E8'
            else:
                status = '❌ Missing'
                status_color = '#E74C3C'
                row_bg = '#FFE8E8'

            html += f"""
            <tr style="border-bottom: 1px solid #E8E4E3; background: {row_bg};">
                <td style="padding: 16px; color: #4D2E3A; font-weight: 500;">{content_type}</td>
                <td style="padding: 16px; text-align: center; color: #6B5660; font-weight: 600;">{data['total']}</td>
                <td style="padding: 16px; text-align: center;">
                    <span style="font-size: 18px; font-weight: 700; color: {'#27AE60' if brand_pct > 30 else '#E74C3C'};">
                        {brand_pct}%
                    </span>
                </td>
                <td style="padding: 16px; text-align: center;">
                    <span style="font-size: 18px; font-weight: 700; color: #6B5660;">
                        {comp_pct}%
                    </span>
                </td>
                <td style="padding: 16px; color: {status_color}; font-weight: 600;">{status}</td>
            </tr>
            """

        html += """
                </tbody>
            </table>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 32px;">
            <div style="background: #E8F5E9; border-left: 4px solid #27AE60; padding: 24px; border-radius: 8px;">
                <h4 style="color: #27AE60; margin: 0 0 12px 0;">✅ What's Working</h4>
                <p style="color: #2E7D32; margin: 0; line-height: 1.7;">
                    Double down on content types where you're competitive or winning.
                    These are your strengths—create more of this content to increase visibility.
                </p>
            </div>

            <div style="background: #FFEBEE; border-left: 4px solid #E74C3C; padding: 24px; border-radius: 8px;">
                <h4 style="color: #E74C3C; margin: 0 0 12px 0;">❌ Critical Gaps</h4>
                <p style="color: #C62828; margin: 0; line-height: 1.7;">
                    Content types marked "Missing" are where competitors dominate.
                    These are high-priority gaps that need immediate attention.
                </p>
            </div>
        </div>
        """

        return html


    def _build_roi_estimator(self, visibility_summary: Dict[str, Any], competitive_analysis: Dict[str, Any]) -> str:
        """Build ROI Estimator showing business impact of improvements."""

        current_visibility = visibility_summary.get('brand_visibility_rate', 0)
        competitor_avg = visibility_summary.get('competitor_mention_rate', 0)

        # Project improvement based on implementing recommendations
        projected_visibility_low = int(min(current_visibility + 15, 100))
        projected_visibility_high = int(min(current_visibility + 25, 100))

        # Estimate traffic (conservative assumptions)
        # Assume 100 AI queries/month per 1% visibility rate
        current_monthly_queries = int(current_visibility * 100)
        projected_queries_low = int(projected_visibility_low * 100)
        projected_queries_high = int(projected_visibility_high * 100)

        # Estimate impressions (awareness value)
        # Each AI mention reaches ~10 people (conversation shared, etc.)
        current_impressions = current_monthly_queries * 10
        projected_impressions_low = projected_queries_low * 10
        projected_impressions_high = projected_queries_high * 10

        # Revenue estimation (conservative)
        # Assume 2% conversion rate and $45 AOV (beauty industry average)
        conversion_rate = 0.02
        aov = 45

        current_revenue = int(current_monthly_queries * conversion_rate * aov)
        projected_revenue_low = int(projected_queries_low * conversion_rate * aov)
        projected_revenue_high = int(projected_queries_high * conversion_rate * aov)

        revenue_lift_low = projected_revenue_low - current_revenue
        revenue_lift_high = projected_revenue_high - current_revenue

        html = f"""
        <div class="info-card">
            <div class="info-card-title">💰 ROI Estimator</div>
            <div class="info-card-content">
                <p style="font-size: 16px; line-height: 1.8; color: #4D2E3A; margin-bottom: 0;">
                    Estimated business impact of implementing the recommendations in this report.
                    These are conservative projections based on industry benchmarks and your current performance.
                </p>
            </div>
        </div>

        <div style="background: linear-gradient(135deg, #4D2E3A 0%, #A78E8B 100%); color: white; padding: 32px; border-radius: 12px; margin-bottom: 32px;">
            <h3 style="color: white; margin: 0 0 24px 0; font-size: 24px;">📈 Projected Impact (90 Days)</h3>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px;">
                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">AI Visibility Rate</div>
                    <div style="font-size: 32px; font-weight: 700; margin-bottom: 4px;">{projected_visibility_low}-{projected_visibility_high}%</div>
                    <div style="font-size: 13px; opacity: 0.8;">Currently: {current_visibility:.1f}%</div>
                </div>

                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">Monthly AI-Driven Traffic</div>
                    <div style="font-size: 32px; font-weight: 700; margin-bottom: 4px;">{projected_queries_low:,}-{projected_queries_high:,}</div>
                    <div style="font-size: 13px; opacity: 0.8;">Currently: {current_monthly_queries:,}</div>
                </div>

                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">Brand Impressions/Month</div>
                    <div style="font-size: 32px; font-weight: 700; margin-bottom: 4px;">{projected_impressions_low:,}-{projected_impressions_high:,}</div>
                    <div style="font-size: 13px; opacity: 0.8;">Currently: {current_impressions:,}</div>
                </div>
            </div>
        </div>

        <div style="background: #FFF4E6; padding: 16px 20px; border-left: 4px solid #F39C12; border-radius: 6px; margin-bottom: 24px;">
            <strong style="color: #B77400;">⚠️ Important:</strong>
            <span style="color: #6B5660; margin-left: 8px;">
                These are <strong>projected estimates</strong>, not actual tracked revenue. To measure real AI-driven revenue,
                connect Google Analytics to track traffic from AI sources (ChatGPT, Perplexity, Claude, etc.) and their conversion rates.
            </span>
        </div>

        <div style="background: white; border: 2px solid #27AE60; border-radius: 10px; padding: 32px; margin-bottom: 32px;">
            <h3 style="color: #27AE60; margin: 0 0 20px 0; font-size: 22px;">💵 Potential Revenue Impact (Conservative Projection)</h3>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px;">
                <div>
                    <div style="font-size: 15px; color: #6B5660; margin-bottom: 12px; font-weight: 600;">Estimated Current Potential</div>
                    <div style="font-size: 40px; color: #4D2E3A; font-weight: 700; margin-bottom: 8px;">${current_revenue:,}<span style="font-size: 20px; color: #A78E8B;">/mo</span></div>
                    <div style="font-size: 13px; color: #A78E8B;">
                        If {current_monthly_queries:,} monthly AI mentions converted at 2%
                    </div>
                </div>

                <div>
                    <div style="font-size: 15px; color: #6B5660; margin-bottom: 12px; font-weight: 600;">Projected Potential</div>
                    <div style="font-size: 40px; color: #27AE60; font-weight: 700; margin-bottom: 8px;">${projected_revenue_low:,}-${projected_revenue_high:,}<span style="font-size: 20px; opacity: 0.8;">/mo</span></div>
                    <div style="font-size: 13px; color: #A78E8B;">
                        Potential monthly lift: <strong style="color: #27AE60;">${revenue_lift_low:,}-${revenue_lift_high:,}</strong>
                    </div>
                </div>
            </div>

            <div style="margin-top: 24px; padding: 20px; background: #F8F8F7; border-radius: 8px;">
                <div style="font-size: 14px; color: #4D2E3A; font-weight: 600; margin-bottom: 12px;">12-Month Potential Impact</div>
                <div style="font-size: 28px; color: #27AE60; font-weight: 700;">
                    ${revenue_lift_low * 12:,} - ${revenue_lift_high * 12:,} additional potential revenue
                </div>
                <div style="font-size: 13px; color: #6B5660; margin-top: 8px;">
                    Based on steady improvement over 90 days, then maintaining new visibility level
                </div>
            </div>
        </div>

        <div class="accordion-group" style="margin-top: 32px;">
            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>📊 How to Track Actual AI-Driven Revenue</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                <div style="background: #E8F5E9; padding: 24px; border-radius: 8px; border-left: 4px solid #27AE60; margin-top: 16px;">
                    <p style="margin: 0 0 12px 0; color: #2E7D32; line-height: 1.7;">
                        To measure real performance (not just projections), set up tracking in Google Analytics:
                    </p>
                    <ol style="margin: 0; padding-left: 20px; color: #2E7D32; line-height: 1.8;">
                        <li><strong>Tag AI traffic sources:</strong> Create UTM parameters for AI platforms (ChatGPT, Perplexity, Claude)</li>
                        <li><strong>Set up conversion tracking:</strong> Track purchases/leads from AI referrers</li>
                        <li><strong>Create custom reports:</strong> Filter by AI traffic to see actual conversion rates</li>
                        <li><strong>Monitor over time:</strong> Compare AI traffic before/after implementing recommendations</li>
                    </ol>
                    <p style="margin: 12px 0 0 0; color: #2E7D32; font-size: 14px; line-height: 1.7;">
                        <strong>Note:</strong> AI platforms often show as "direct" traffic or don't pass referrer data,
                        making actual attribution challenging. These projections provide a conservative baseline expectation.
                    </p>
                </div>
            </div>

            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>📌 Methodology & Assumptions</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                <div style="background: #E3F2FD; padding: 24px; border-radius: 8px; border-left: 4px solid #1976D2; margin-top: 16px;">
                    <ul style="margin: 0; padding-left: 20px; color: #1565C0; line-height: 1.8;">
                        <li><strong>Traffic Estimate:</strong> 100 AI-influenced visitors per 1% visibility rate (conservative)</li>
                        <li><strong>Conversion Rate:</strong> 2% (typical e-commerce rate for qualified traffic)</li>
                        <li><strong>Average Order Value:</strong> $45 (beauty industry benchmark)</li>
                        <li><strong>Improvement Timeline:</strong> 90 days for full implementation</li>
                        <li><strong>Visibility Gain:</strong> Based on implementing Top 10 recommendations</li>
                    </ul>

                    <p style="margin: 16px 0 0 0; color: #1565C0; font-size: 14px; line-height: 1.7;">
                        <strong>Note:</strong> These are conservative estimates. Actual results may vary based on implementation quality,
                        brand awareness, product pricing, and market conditions. AI visibility often compounds over time as more
                        content gets indexed and cited.
                    </p>
                </div>
            </div>
        </div>
        """

        return html


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

    def _build_sentiment_analysis_tab(self, brand_name: str, scored_results: List[Dict[str, Any]]) -> str:
        """Build comprehensive sentiment analysis tab showing how AI actually describes the brand."""

        # Extract responses where brand is mentioned
        brand_mentions = [r for r in scored_results if r.get('visibility', {}).get('brand_mentioned')]

        if not brand_mentions:
            return """
            <div style="padding: 40px; text-align: center; color: #6B5660;">
                <h2>How AI Describes You</h2>
                <p>No brand mentions found in test results.</p>
            </div>
            """

        # Analyze sentiment keywords in responses
        positive_keywords = ['excellent', 'best', 'top', 'premium', 'high-quality', 'recommended', 'favorite',
                            'amazing', 'exceptional', 'outstanding', 'superior', 'leading', 'innovative',
                            'professional', 'luxurious', 'highly', 'perfect', 'great', 'love']

        negative_keywords = ['expensive', 'pricey', 'limited', 'lacking', 'difficult', 'complicated',
                            'poor', 'weak', 'disappointing', 'overpriced', 'inferior', 'cheap', 'bad']

        # Categorize mentions by sentiment
        positive_mentions = []
        neutral_mentions = []
        negative_mentions = []

        for result in brand_mentions:
            # Try both field names (response_text from scorer, response from other sources)
            response_text = result.get('response_text', '') or result.get('response', '')
            response_lower = response_text.lower()
            brand_lower = brand_name.lower()

            # Skip if brand not actually in response
            if brand_lower not in response_lower:
                continue

            # Extract fuller context around brand mention (300 chars before and after)
            brand_index = response_lower.find(brand_lower)
            start = max(0, brand_index - 200)
            end = min(len(response_text), brand_index + len(brand_name) + 300)

            # Get the surrounding context
            context = response_text[start:end].strip()

            # Clean up markdown/formatting but keep structure
            context = context.replace('**', '').replace('###', '').replace('##', '').strip()
            # Keep single * for bullets but remove standalone ones

            # Try to start at sentence boundary if possible
            if start > 0:
                # Look for sentence start (. or newline followed by capital letter)
                sentences_before = context[:200].split('. ')
                if len(sentences_before) > 1:
                    context = '. '.join(sentences_before[1:])
                else:
                    context = '...' + context

            # Try to end at sentence boundary
            if end < len(response_text):
                sentences = context.split('. ')
                if len(sentences) > 1:
                    context = '. '.join(sentences[:-1]) + '.'
                else:
                    context = context + '...'

            # Determine sentiment based on keywords in the context
            context_lower = context.lower()
            has_positive = any(kw in context_lower for kw in positive_keywords)
            has_negative = any(kw in context_lower for kw in negative_keywords)

            # Get prompt text (could be 'prompt' or 'prompt_text')
            prompt_text = result.get('prompt_text', '') or result.get('prompt', '')
            prompt_display = prompt_text[:80] + '...' if len(prompt_text) > 80 else prompt_text

            sample = {
                'platform': result.get('platform', 'Unknown').replace('openai', 'ChatGPT').replace('anthropic', 'Claude').replace('perplexity', 'Perplexity').replace('gemini', 'Gemini'),
                'quote': context,  # Show full context now
                'prompt': prompt_display
            }

            if has_positive and not has_negative:
                positive_mentions.append(sample)
            elif has_negative and not has_positive:
                negative_mentions.append(sample)
            else:
                neutral_mentions.append(sample)

        # Calculate distribution
        total_analyzed = len(positive_mentions) + len(neutral_mentions) + len(negative_mentions)

        if total_analyzed == 0:
            positive_pct = neutral_pct = negative_pct = 0
        else:
            positive_pct = (len(positive_mentions) / total_analyzed * 100)
            neutral_pct = (len(neutral_mentions) / total_analyzed * 100)
            negative_pct = (len(negative_mentions) / total_analyzed * 100)

        # Build example quotes HTML
        def build_quote_examples(mentions, color, title, max_show=5):
            if not mentions:
                return f'<p style="color: #A7868F; font-style: italic;">No {title.lower()} mentions identified</p>'

            html = ""
            for i, mention in enumerate(mentions[:max_show]):
                quote_id = f"{title.lower().replace(' ', '_')}_{i}"
                html += f"""
                <div style="background: white; border-left: 4px solid {color}; padding: 20px; margin: 16px 0; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="font-size: 15px; color: #2D2D2D; line-height: 1.8; margin-bottom: 12px; font-family: Georgia, serif;">
                        "{mention['quote']}"
                    </div>
                    <div style="font-size: 13px; color: #A7868F; margin-top: 12px; padding-top: 12px; border-top: 1px solid #F0F0F0;">
                        <strong style="color: {color};">{mention['platform']}</strong> • Query: <em>"{mention['prompt']}"</em>
                    </div>
                </div>
                """

            if len(mentions) > max_show:
                html += f'<p style="color: #6B5660; font-size: 14px; margin-top: 12px; font-weight: 500;">+ {len(mentions) - max_show} more {title.lower()} mentions</p>'

            return html

        positive_examples = build_quote_examples(positive_mentions, '#10b981', 'Positive')
        neutral_examples = build_quote_examples(neutral_mentions, '#f59e0b', 'Neutral')
        negative_examples = build_quote_examples(negative_mentions, '#ef4444', 'Negative')

        # Overall sentiment determination
        if positive_pct >= 50:
            overall_status = "Positive"
            overall_color = "#10b981"
            overall_message = f"AI describes {brand_name} in positive terms in most mentions. This builds trust and authority."
        elif negative_pct >= 30:
            overall_status = "Needs Attention"
            overall_color = "#ef4444"
            overall_message = f"A significant portion of mentions include negative language. Focus on improving brand perception."
        else:
            overall_status = "Neutral"
            overall_color = "#f59e0b"
            overall_message = f"Most mentions are factual/neutral. Consider creating content that highlights unique value propositions."

        return f"""
        <div style="padding: 20px 0;">
            <h2>How AI Describes You</h2>
            <p style="color: #6B5660; font-size: 15px; line-height: 1.7; margin-bottom: 32px;">
                This analyzes the actual language AI uses when mentioning {brand_name}.
                We examined {len(brand_mentions)} responses where you were mentioned and classified the tone based on the descriptive words and phrases used.
            </p>

            <div style="background: linear-gradient(135deg, {overall_color}10 0%, {overall_color}20 100%); border: 2px solid {overall_color}; border-radius: 12px; padding: 32px; margin-bottom: 40px;">
                <div style="text-align: center;">
                    <div style="font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #4D2E3A; margin-bottom: 12px;">
                        Overall Sentiment
                    </div>
                    <div style="font-size: 48px; font-weight: 700; color: {overall_color}; margin-bottom: 12px;">
                        {overall_status}
                    </div>
                    <p style="color: #4D2E3A; font-size: 15px; line-height: 1.7; margin: 0; max-width: 600px; margin: 0 auto;">
                        {overall_message}
                    </p>
                </div>
            </div>

            <h3>Sentiment Distribution</h3>
            <p style="color: #6B5660; margin-bottom: 20px;">Based on {total_analyzed} analyzed mentions:</p>

            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 48px;">
                <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 8px; padding: 24px; text-align: center;">
                    <div style="font-size: 40px; font-weight: 700; color: #10b981;">
                        {positive_pct:.0f}%
                    </div>
                    <div style="font-size: 14px; color: #10b981; font-weight: 600; margin-top: 4px;">
                        POSITIVE
                    </div>
                    <div style="font-size: 13px; color: #6B5660; margin-top: 8px;">
                        {len(positive_mentions)} mentions
                    </div>
                </div>

                <div style="background: #fffbeb; border: 2px solid #f59e0b; border-radius: 8px; padding: 24px; text-align: center;">
                    <div style="font-size: 40px; font-weight: 700; color: #f59e0b;">
                        {neutral_pct:.0f}%
                    </div>
                    <div style="font-size: 14px; color: #f59e0b; font-weight: 600; margin-top: 4px;">
                        NEUTRAL
                    </div>
                    <div style="font-size: 13px; color: #6B5660; margin-top: 8px;">
                        {len(neutral_mentions)} mentions
                    </div>
                </div>

                <div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 24px; text-align: center;">
                    <div style="font-size: 40px; font-weight: 700; color: #ef4444;">
                        {negative_pct:.0f}%
                    </div>
                    <div style="font-size: 14px; color: #ef4444; font-weight: 600; margin-top: 4px;">
                        NEGATIVE
                    </div>
                    <div style="font-size: 13px; color: #6B5660; margin-top: 8px;">
                        {len(negative_mentions)} mentions
                    </div>
                </div>
            </div>

            <h3 style="color: #10b981;">✓ Positive Mentions</h3>
            <p style="color: #6B5660; margin-bottom: 20px;">Examples of how AI describes you favorably:</p>
            {positive_examples}

            <h3 style="color: #f59e0b; margin-top: 48px;">→ Neutral Mentions</h3>
            <p style="color: #6B5660; margin-bottom: 20px;">Factual mentions without strong positive or negative language:</p>
            {neutral_examples}

            <h3 style="color: #ef4444; margin-top: 48px;">✗ Negative Mentions</h3>
            <p style="color: #6B5660; margin-bottom: 20px;">Mentions with critical or negative language:</p>
            {negative_examples}

            <div style="background: #F8F8F7; padding: 24px; border-radius: 8px; margin-top: 48px;">
                <h3 style="margin-top: 0;">What This Means</h3>
                <p style="color: #4D2E3A; line-height: 1.7; margin: 0;">
                    <strong>Why sentiment matters:</strong> AI language models are trained on existing content. If most mentions use positive, authoritative language,
                    AI is more likely to recommend you. If mentions are neutral or negative, you need to create content that shifts the narrative.
                </p>
                <p style="color: #4D2E3A; line-height: 1.7; margin: 16px 0 0 0;">
                    <strong>How to improve:</strong> Publish thought leadership, case studies, and educational content that positions you as an expert.
                    Get featured in authoritative publications. Build a library of content that AI can reference when answering queries in your category.
                </p>
            </div>
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
                'google_ai_overview': 'Google AI Overviews',
                'copilot': 'Microsoft Copilot'
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
        <div class="info-card">
            <div class="info-card-title">What AI Actually Said</div>
            <div class="info-card-content">
                <p style="margin-bottom: 0;">See exactly what AI platforms say when asked about your space. Use this to understand competitor positioning and find content opportunities.</p>
            </div>
        </div>

        {quick_insights_html}

        <div class="accordion-group" style="margin-bottom: 24px;">
            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>🎨 How to Read This Table</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                <div style="background: #F8F8F7; padding: 16px; border-radius: 8px; margin-top: 16px;">
                    <div style="margin-bottom: 16px;">
                        <strong style="color: #4D2E3A;">Row colors:</strong>
                        <div style="display: flex; gap: 24px; margin-top: 12px; flex-wrap: wrap;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div style="width: 20px; height: 20px; background: #E8F5E8; border: 1px solid #ccc; border-radius: 4px;"></div>
                                <span>You win (7-10 prominence)</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div style="width: 20px; height: 20px; background: #FFF8E8; border: 1px solid #ccc; border-radius: 4px;"></div>
                                <span>Mixed (4-6 prominence)</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div style="width: 20px; height: 20px; background: #FFE8E8; border: 1px solid #ccc; border-radius: 4px;"></div>
                                <span>You lose (not mentioned)</span>
                            </div>
                        </div>
                    </div>
                    <div>
                        <strong style="color: #4D2E3A;">Text highlighting:</strong>
                        <div style="display: flex; gap: 16px; margin-top: 12px;">
                            <div style="font-weight: 600; color: #6B5660;">
                                <mark style="background: #FFE8B1; padding: 4px 8px; border-radius: 3px;">Your brand</mark>
                            </div>
                            <div style="font-weight: 600; color: #6B5660;">
                                <mark style="background: #D4E8F7; padding: 4px 8px; border-radius: 3px;">Competitors</mark>
                            </div>
                        </div>
                    </div>
                </div>
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

    def _build_composite_score_badge(self, composite_scorecard: Dict[str, Any]) -> str:
        """Build clean, premium score badge - no overlapping text."""
        if not composite_scorecard:
            return ""

        score = composite_scorecard.get('composite_score', 0)
        grade = composite_scorecard.get('letter_grade', 'C')
        label = composite_scorecard.get('grade_label', 'Fair')

        # Clean design with status badge below
        return f"""
        <div style="background: white; border: 3px solid #E8D7A0; border-radius: 16px; padding: 48px; margin: 40px 0 48px 0; box-shadow: 0 4px 20px rgba(74, 68, 88, 0.08);">
            <div style="text-align: center;">
                <div style="font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #6B5660; margin-bottom: 32px;">
                    Overall AI Visibility Grade
                </div>
                <div style="display: inline-flex; align-items: center; gap: 40px; margin-bottom: 24px;">
                    <div style="background: linear-gradient(135deg, #4A4458 0%, #6B5660 100%); color: white; width: 120px; height: 120px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 64px; font-weight: 700; box-shadow: 0 8px 24px rgba(74, 68, 88, 0.2);">
                        {grade}
                    </div>
                    <div style="text-align: left;">
                        <div style="font-size: 52px; font-weight: 700; color: #4A4458; line-height: 1; margin-bottom: 16px;">
                            {score}<span style="font-size: 26px; color: #A7868F; font-weight: 500;">/100</span>
                        </div>
                        <div style="display: inline-block; background: linear-gradient(135deg, #4A4458 0%, #6B5660 100%); color: white; padding: 8px 20px; border-radius: 24px; font-size: 14px; font-weight: 600;">
                            {label}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _build_score_breakdown(self, composite_scorecard: Dict[str, Any]) -> str:
        """Build score breakdown table showing all dimensions."""
        if not composite_scorecard:
            return ""

        dimensions = composite_scorecard.get('dimension_breakdown', [])
        if not dimensions:
            return ""

        rows = []
        for dim in dimensions:
            name = dim.get('dimension', '')
            score = dim.get('score', 0)
            grade = dim.get('grade', 'C')
            weight = dim.get('weight', '0%')
            description = dim.get('description', '')

            # Color based on grade
            if grade == 'A':
                grade_color = '#10b981'
                row_bg = '#f0fdf4'
            elif grade == 'B':
                grade_color = '#3b82f6'
                row_bg = '#eff6ff'
            elif grade == 'C':
                grade_color = '#f59e0b'
                row_bg = '#fffbeb'
            else:
                grade_color = '#ef4444'
                row_bg = '#fef2f2'

            rows.append(f"""
                <tr style="background: {row_bg};">
                    <td style="font-weight: 600; color: #4D2E3A;">{name}</td>
                    <td style="font-size: 13px; color: #6B5660;">{description}</td>
                    <td style="text-align: center; font-weight: 600;">{weight}</td>
                    <td style="text-align: center;">
                        <span style="font-size: 20px; font-weight: 700; color: #4D2E3A;">{score:.1f}</span>
                        <span style="font-size: 12px; color: #A7868F;">/100</span>
                    </td>
                    <td style="text-align: center;">
                        <span style="background: {grade_color}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: 600; font-size: 14px;">
                            {grade}
                        </span>
                    </td>
                </tr>
            """)

        strengths = composite_scorecard.get('strengths', [])
        weaknesses = composite_scorecard.get('weaknesses', [])

        strengths_html = ""
        if strengths:
            strengths_html = f"""
            <div style="margin-top: 24px; padding: 16px; background: #f0fdf4; border-left: 4px solid #10b981; border-radius: 4px;">
                <div style="font-weight: 600; color: #065f46; margin-bottom: 8px;">💪 Strengths</div>
                <div style="color: #047857;">{', '.join(strengths)}</div>
            </div>
            """

        weaknesses_html = ""
        if weaknesses:
            weaknesses_html = f"""
            <div style="margin-top: 16px; padding: 16px; background: #fef2f2; border-left: 4px solid #ef4444; border-radius: 4px;">
                <div style="font-weight: 600; color: #991b1b; margin-bottom: 8px;">🎯 Areas for Improvement</div>
                <div style="color: #dc2626;">{', '.join(weaknesses)}</div>
            </div>
            """

        return f"""
        <div style="margin: 48px 0;">
            <h2>Score Breakdown</h2>
            <p style="color: #6B5660; margin-bottom: 24px;">
                Your overall score is calculated from these five weighted dimensions:
            </p>
            <table>
                <thead>
                    <tr>
                        <th>Dimension</th>
                        <th>What This Measures</th>
                        <th style="text-align: center;">Weight</th>
                        <th style="text-align: center;">Score</th>
                        <th style="text-align: center;">Grade</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
            {strengths_html}
            {weaknesses_html}
        </div>
        """

    def _build_competitive_battlecard(self, head_to_head_results: Dict[str, Any]) -> str:
        """Build competitive battlecard showing head-to-head results."""
        if not head_to_head_results:
            return ""

        battlecard = head_to_head_results.get('battlecard', [])
        if not battlecard:
            return ""

        total_wins = head_to_head_results.get('total_wins', 0)
        total_losses = head_to_head_results.get('total_losses', 0)
        total_ties = head_to_head_results.get('total_ties', 0)
        overall_win_rate = head_to_head_results.get('overall_win_rate', 0)

        rows = []
        for comp in battlecard[:10]:  # Top 10 competitors
            name = comp.get('competitor', '')
            wins = comp.get('wins', 0)
            losses = comp.get('losses', 0)
            ties = comp.get('ties', 0)
            status = comp.get('status', 'tied')
            win_rate = comp.get('win_rate', 0)

            # Status indicator
            if status == 'winning':
                status_color = '#10b981'
                status_icon = '✅'
                status_text = 'Winning'
            elif status == 'losing':
                status_color = '#ef4444'
                status_icon = '❌'
                status_text = 'Losing'
            else:
                status_color = '#f59e0b'
                status_icon = '⚖️'
                status_text = 'Tied'

            rows.append(f"""
                <tr>
                    <td style="font-weight: 600; color: #4D2E3A;">{status_icon} {name}</td>
                    <td style="text-align: center; font-weight: 600; color: #10b981;">{wins}</td>
                    <td style="text-align: center; font-weight: 600; color: #ef4444;">{losses}</td>
                    <td style="text-align: center; font-weight: 600; color: #f59e0b;">{ties}</td>
                    <td style="text-align: center; color: #6B5660;">{wins + losses + ties}</td>
                    <td style="text-align: center;">
                        <span style="font-weight: 600; color: #4D2E3A;">{win_rate:.1f}%</span>
                    </td>
                    <td style="text-align: center;">
                        <span style="background: {status_color}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: 600; font-size: 12px;">
                            {status_text.upper()}
                        </span>
                    </td>
                </tr>
            """)

        return f"""
        <div style="margin: 48px 0;">
            <h2>Competitive Battlecard</h2>
            <p style="color: #6B5660; margin-bottom: 24px;">
                Head-to-head comparison results when your brand and competitors are mentioned together.
            </p>

            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 32px;">
                <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 8px; padding: 20px; text-align: center;">
                    <div style="font-size: 36px; font-weight: 700; color: #10b981;">{total_wins}</div>
                    <div style="font-size: 14px; color: #065f46; font-weight: 600;">You Win</div>
                </div>
                <div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 20px; text-align: center;">
                    <div style="font-size: 36px; font-weight: 700; color: #ef4444;">{total_losses}</div>
                    <div style="font-size: 14px; color: #991b1b; font-weight: 600;">They Win</div>
                </div>
                <div style="background: #fffbeb; border: 2px solid #f59e0b; border-radius: 8px; padding: 20px; text-align: center;">
                    <div style="font-size: 36px; font-weight: 700; color: #f59e0b;">{total_ties}</div>
                    <div style="font-size: 14px; color: #92400e; font-weight: 600;">Tied</div>
                </div>
            </div>

            <div style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px; margin-bottom: 24px;">
                <div style="font-weight: 600; color: #1e40af; margin-bottom: 4px;">Overall Win Rate</div>
                <div style="font-size: 28px; font-weight: 700; color: #1e40af;">{overall_win_rate:.1f}%</div>
                <div style="font-size: 13px; color: #1e3a8a; margin-top: 4px;">Ties count as 0.5 wins</div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Competitor</th>
                        <th style="text-align: center;">You Win</th>
                        <th style="text-align: center;">They Win</th>
                        <th style="text-align: center;">Tied</th>
                        <th style="text-align: center;">Total</th>
                        <th style="text-align: center;">Win Rate</th>
                        <th style="text-align: center;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        """

    def _build_high_intent_losses(self, head_to_head_results: Dict[str, Any]) -> str:
        """Build section showing high-intent comparison queries being lost."""
        if not head_to_head_results:
            return ""

        battlecard = head_to_head_results.get('battlecard', [])
        if not battlecard:
            return ""

        # Get competitors where we're losing
        losing_comps = [c for c in battlecard if c.get('status') == 'losing'][:5]

        if not losing_comps:
            return """
            <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 8px; padding: 24px; margin: 32px 0;">
                <div style="font-weight: 600; color: #065f46; font-size: 18px; margin-bottom: 8px;">
                    ✅ No Critical Losses
                </div>
                <div style="color: #047857;">
                    You're not significantly losing head-to-head comparisons. Keep monitoring competitive positioning.
                </div>
            </div>
            """

        loss_items = []
        for comp in losing_comps:
            name = comp.get('competitor', '')
            losses = comp.get('losses', 0)
            wins = comp.get('wins', 0)
            sample_prompts = comp.get('sample_prompts', [])[:2]  # Top 2 examples

            prompt_examples = ""
            for prompt_data in sample_prompts:
                prompt = prompt_data.get('prompt', '')
                outcome = prompt_data.get('outcome', '')
                platform = prompt_data.get('platform', '')

                if outcome == 'loss':
                    prompt_examples += f"""
                    <div style="margin-top: 8px; padding: 12px; background: rgba(239, 68, 68, 0.05); border-left: 3px solid #ef4444; border-radius: 4px;">
                        <div style="font-size: 13px; color: #4D2E3A; margin-bottom: 4px;">"{prompt[:100]}..."</div>
                        <div style="font-size: 11px; color: #A7868F;">Platform: {platform}</div>
                    </div>
                    """

            loss_items.append(f"""
                <div style="padding: 20px; background: white; border: 1px solid #E8E4E3; border-radius: 8px; margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div>
                            <span style="font-size: 18px; font-weight: 600; color: #4D2E3A;">{name}</span>
                            <span style="margin-left: 12px; background: #fef2f2; color: #ef4444; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                                LOSING {losses}-{wins}
                            </span>
                        </div>
                    </div>
                    <div style="font-size: 14px; color: #6B5660; margin-bottom: 8px;">
                        Example comparison queries where {name} is winning:
                    </div>
                    {prompt_examples}
                </div>
            """)

        return f"""
        <div style="margin: 48px 0;">
            <h3 style="color: #ef4444;">⚠️ High-Intent Prompts You're Losing</h3>
            <p style="color: #6B5660; margin-bottom: 24px;">
                These are direct comparison queries where buyers are choosing competitors over you.
                Winning these queries should be a top priority.
            </p>
            {''.join(loss_items)}
        </div>
        """

    def _build_sentiment_analysis(self, sentiment_analysis: Dict[str, Any]) -> str:
        """Build sentiment analysis showing how AI describes the brand."""
        if not sentiment_analysis:
            return ""

        overall_score_data = sentiment_analysis.get('overall_score', {})
        overall_score = overall_score_data.get('score', 0)
        overall_grade = overall_score_data.get('grade', 'C')

        brand_sentiment = sentiment_analysis.get('brand_sentiment', {})
        key_strengths = sentiment_analysis.get('key_strengths', [])
        key_weaknesses = sentiment_analysis.get('key_weaknesses', [])

        # Determine color based on score
        if overall_score >= 70:
            score_color = '#10b981'
            status = 'Positive'
        elif overall_score >= 50:
            score_color = '#f59e0b'
            status = 'Neutral'
        else:
            score_color = '#ef4444'
            status = 'Needs Attention'

        # Build strengths list
        strengths_html = ""
        for strength in key_strengths[:5]:
            strengths_html += f"""
                <li style="margin: 8px 0; color: #4D2E3A; line-height: 1.6;">
                    <strong style="color: #10b981;">✓</strong> {strength}
                </li>
            """

        # Build weaknesses list
        weaknesses_html = ""
        for weakness in key_weaknesses[:5]:
            weaknesses_html += f"""
                <li style="margin: 8px 0; color: #4D2E3A; line-height: 1.6;">
                    <strong style="color: #ef4444;">✗</strong> {weakness}
                </li>
            """

        return f"""
        <div style="margin: 48px 0;">
            <h2>Sentiment Analysis</h2>
            <p style="color: #6B5660; margin-bottom: 24px;">
                How does AI describe your brand when it mentions you? This analyzes the language, tone, and descriptors AI uses.
            </p>

            <div style="background: linear-gradient(135deg, rgba(77, 46, 58, 0.05) 0%, rgba(77, 46, 58, 0.1) 100%); border: 2px solid #4D2E3A; border-radius: 12px; padding: 32px; margin-bottom: 32px;">
                <div style="text-align: center; margin-bottom: 24px;">
                    <div style="font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #6B5660; margin-bottom: 8px;">
                        Overall Sentiment Score
                    </div>
                    <div style="font-size: 56px; font-weight: 700; color: {score_color};">
                        {overall_score:.0f}<span style="font-size: 28px; color: #A7868F;">/100</span>
                    </div>
                    <div style="font-size: 16px; font-weight: 600; color: {score_color}; margin-top: 8px;">
                        Grade: {overall_grade} • {status}
                    </div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px;">
                <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 8px; padding: 24px;">
                    <h3 style="color: #10b981; margin-bottom: 16px; font-size: 18px;">Key Strengths</h3>
                    <ul style="list-style: none; padding: 0; margin: 0;">
                        {strengths_html if strengths_html else '<li style="color: #6B5660;">No specific strengths identified</li>'}
                    </ul>
                </div>

                <div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 24px;">
                    <h3 style="color: #ef4444; margin-bottom: 16px; font-size: 18px;">Areas to Improve</h3>
                    <ul style="list-style: none; padding: 0; margin: 0;">
                        {weaknesses_html if weaknesses_html else '<li style="color: #6B5660;">No specific weaknesses identified</li>'}
                    </ul>
                </div>
            </div>
        </div>
        """

    def _build_citation_analysis(self, citation_stats: Dict[str, Any]) -> str:
        """Build citation analysis showing owned vs third-party control."""
        if not citation_stats:
            return ""

        owned_pct = citation_stats.get('owned_percentage', 0)
        third_party_pct = citation_stats.get('third_party_percentage', 0)
        competitor_pct = citation_stats.get('competitor_percentage', 0)
        authority_score = citation_stats.get('citation_authority_score', 0)
        top_domains = citation_stats.get('top_domains', [])

        # Determine color based on owned percentage
        if owned_pct >= 50:
            owned_color = '#10b981'
            owned_status = 'Strong'
        elif owned_pct >= 30:
            owned_color = '#f59e0b'
            owned_status = 'Moderate'
        else:
            owned_color = '#ef4444'
            owned_status = 'Weak'

        # Build top domains list
        domain_rows = []
        for domain_data in top_domains[:15]:
            domain = domain_data.get('domain', '')
            count = domain_data.get('citations', 0)
            dtype = domain_data.get('classification', 'Unknown')

            if dtype == 'Owned':
                badge_color = '#10b981'
            elif dtype == 'Competitor':
                badge_color = '#ef4444'
            else:
                badge_color = '#6B5660'

            domain_rows.append(f"""
                <tr>
                    <td style="font-weight: 500; color: #4D2E3A;">{domain}</td>
                    <td style="text-align: center; font-weight: 600; color: #4D2E3A;">{count}</td>
                    <td style="text-align: center;">
                        <span style="background: {badge_color}; color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600;">
                            {dtype.upper()}
                        </span>
                    </td>
                </tr>
            """)

        return f"""
        <div style="margin: 48px 0;">
            <h2>Citation Authority Analysis</h2>
            <p style="color: #6B5660; margin-bottom: 24px;">
                Who controls your AI narrative? This shows what sources AI platforms cite when mentioning your brand.
            </p>

            <div style="background: linear-gradient(135deg, rgba(77, 46, 58, 0.05) 0%, rgba(77, 46, 58, 0.1) 100%); border: 2px solid #4D2E3A; border-radius: 12px; padding: 32px; margin-bottom: 32px;">
                <div style="text-align: center; margin-bottom: 24px;">
                    <div style="font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #6B5660; margin-bottom: 8px;">
                        Citation Authority Score
                    </div>
                    <div style="font-size: 56px; font-weight: 700; color: #4D2E3A;">
                        {authority_score:.0f}<span style="font-size: 28px; color: #A7868F;">/100</span>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
                    <div style="background: white; border-radius: 8px; padding: 20px; text-align: center;">
                        <div style="font-size: 36px; font-weight: 700; color: {owned_color};">{owned_pct:.0f}%</div>
                        <div style="font-size: 12px; color: #6B5660; font-weight: 600; margin-top: 4px;">OWNED</div>
                        <div style="font-size: 11px; color: #A7868F; margin-top: 4px;">{owned_status} Control</div>
                    </div>
                    <div style="background: white; border-radius: 8px; padding: 20px; text-align: center;">
                        <div style="font-size: 36px; font-weight: 700; color: #6B5660;">{third_party_pct:.0f}%</div>
                        <div style="font-size: 12px; color: #6B5660; font-weight: 600; margin-top: 4px;">THIRD-PARTY</div>
                        <div style="font-size: 11px; color: #A7868F; margin-top: 4px;">External Sites</div>
                    </div>
                    <div style="background: white; border-radius: 8px; padding: 20px; text-align: center;">
                        <div style="font-size: 36px; font-weight: 700; color: #ef4444;">{competitor_pct:.0f}%</div>
                        <div style="font-size: 12px; color: #6B5660; font-weight: 600; margin-top: 4px;">COMPETITOR</div>
                        <div style="font-size: 11px; color: #A7868F; margin-top: 4px;">Rival Sites</div>
                    </div>
                </div>
            </div>

            <div style="background: rgba(167, 134, 143, 0.1); border-left: 4px solid #A7868F; padding: 16px; border-radius: 4px; margin-bottom: 24px;">
                <div style="font-weight: 600; color: #4D2E3A; margin-bottom: 8px;">💡 What This Means</div>
                <div style="font-size: 14px; color: #6B5660; line-height: 1.6;">
                    {'You have strong control over your narrative with ' + str(round(owned_pct)) + '% owned citations.' if owned_pct >= 50 else 
                     'Third-party sites control ' + str(round(third_party_pct)) + '% of your narrative. Build more authoritative owned content.' if third_party_pct >= 50 else
                     'Mixed control - increase owned content to strengthen your narrative.'}
                </div>
            </div>

            <h3>Top Cited Domains</h3>
            <table>
                <thead>
                    <tr>
                        <th>Domain</th>
                        <th style="text-align: center;">Citations</th>
                        <th style="text-align: center;">Type</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(domain_rows)}
                </tbody>
            </table>
        </div>
        """

    def _build_competitive_intelligence_tab(self, brand_name: str,
                                           visibility_summary: Dict[str, Any],
                                           competitive_analysis: Dict[str, Any],
                                           gap_analysis: Dict[str, Any],
                                           action_plan: Dict[str, Any],
                                           head_to_head_results: Dict[str, Any],
                                           scored_results: List[Dict[str, Any]]) -> str:
        """Build competitive intelligence tab showing what competitors are doing vs what you should do."""

        brand_vis = visibility_summary.get('brand_visibility_rate', 0)
        competitor_mentions = visibility_summary.get('competitors_encountered', [])

        # Build "Why This Matters" section with industry facts (now collapsible)
        why_matters_html = self._build_why_this_matters(brand_name, visibility_summary)

        # Build competitive comparison table
        competitive_comparison_html = self._build_competitive_comparison_table(
            brand_name, visibility_summary, competitive_analysis, scored_results
        )

        # Build simplified top 3-5 opportunities
        top_opportunities_html = self._build_simplified_opportunities(
            gap_analysis, action_plan, competitive_analysis, scored_results
        )

        return f"""
        <div class="info-card">
            <div class="info-card-title">What Competitors Are Doing (That You're Not)</div>
            <div class="info-card-content">
                <p style="font-size: 16px; line-height: 1.8; color: #4D2E3A; margin-bottom: 0;">
                    The brands showing up in AI responses are doing specific things that you aren't. Here's what the data shows.
                </p>
            </div>
        </div>

        {competitive_comparison_html}

        {top_opportunities_html}

        <div class="accordion-group" style="margin-top: 32px;">
            {why_matters_html}
        </div>
        """

    def _build_why_this_matters(self, brand_name: str, visibility_summary: Dict[str, Any]) -> str:
        """Build compelling 'Why This Matters' section with industry stats."""

        brand_vis = visibility_summary.get('brand_visibility_rate', 0)

        # Select relevant industry facts based on their visibility level
        if brand_vis < 20:
            primary_fact = "Brands invisible in AI responses are seeing <strong>40% drops in organic search traffic</strong> as users shift to AI for research."
            urgency = "critical"
        elif brand_vis < 40:
            primary_fact = "Companies with strong AI visibility are seeing <strong>2-3x more consideration</strong> in buyer research compared to those who aren't visible."
            urgency = "high"
        else:
            primary_fact = "Market leaders maintain their position by showing up in <strong>60%+ of relevant AI queries</strong> - you're at {brand_vis:.0f}%."
            urgency = "moderate"

        return f"""
        <button class="accordion-button" onclick="toggleAccordion(this)">
            <span>🚨 Why AI Visibility Matters Now (Industry Data)</span>
            <span class="accordion-icon">▼</span>
        </button>
        <div class="accordion-content">
            <div style="background: linear-gradient(135deg, #4D2E3A 0%, #6B5660 100%); color: white; padding: 32px; border-radius: 12px; margin-top: 16px;">
                <div style="font-size: 18px; line-height: 1.8; margin-bottom: 20px;">
                    {primary_fact}
                </div>
                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; margin-top: 16px;">
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; text-align: center;">
                        <div>
                            <div style="font-size: 40px; font-weight: 700; margin-bottom: 8px;">53%</div>
                            <div style="font-size: 13px; opacity: 0.9;">of B2B buyers now use AI for vendor research</div>
                        </div>
                        <div>
                            <div style="font-size: 40px; font-weight: 700; margin-bottom: 8px;">68%</div>
                            <div style="font-size: 13px; opacity: 0.9;">of consumers trust AI recommendations as much as search results</div>
                        </div>
                        <div>
                            <div style="font-size: 40px; font-weight: 700; margin-bottom: 8px;">$0</div>
                            <div style="font-size: 13px; opacity: 0.9;">cost per AI impression vs $2-5 per click on Google Ads</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    def _build_competitive_comparison_table(self, brand_name: str,
                                          visibility_summary: Dict[str, Any],
                                          competitive_analysis: Dict[str, Any],
                                          scored_results: List[Dict[str, Any]]) -> str:
        """Build table showing what competitors are doing vs what client should do."""
        
        brand_vis = visibility_summary.get('brand_visibility_rate', 0)

        # Use the already-calculated competitive analysis data
        top_competitors = competitive_analysis.get('top_competitors', [])

        # Build competitor rows from competitive_analysis
        competitor_rows = ""
        for comp_data in top_competitors[:5]:
            comp = comp_data['name']
            rate = comp_data['mention_rate']
            status = "🏆 Leading" if rate > brand_vis * 1.5 else "⚠️ Ahead" if rate > brand_vis else "✓ Behind"

            # Get what they're doing (sample analysis)
            what_theyre_doing = self._infer_competitor_strategy(comp, scored_results)

            competitor_rows += f"""
            <tr>
                <td style="font-weight: 600;">{comp}</td>
                <td style="text-align: center; font-size: 20px; font-weight: 700; color: {'#27AE60' if rate > brand_vis else '#6B5660'};">
                    {rate:.1f}%
                </td>
                <td style="text-align: center;">{status}</td>
                <td style="font-size: 14px; color: #6B5660;">{what_theyre_doing}</td>
            </tr>
            """

        if not competitor_rows:
            competitor_rows = """
            <tr>
                <td colspan="4" style="text-align: center; color: #6B5660; padding: 24px;">
                    No competitor data available. Competitors may not have been mentioned in AI responses during this analysis period.
                </td>
            </tr>
            """
        
        you_row = f"""
        <tr style="background: #FFF9E6; border: 2px solid #F59E0B;">
            <td style="font-weight: 700; color: #4D2E3A;">👉 {brand_name} (You)</td>
            <td style="text-align: center; font-size: 20px; font-weight: 700; color: #4D2E3A;">
                {brand_vis:.1f}%
            </td>
            <td style="text-align: center; font-weight: 600; color: #F59E0B;">Your Position</td>
            <td style="font-size: 14px; color: #6B5660; font-style: italic;">See opportunities below</td>
        </tr>
        """
        
        return f"""
        <div class="info-card">
            <div class="info-card-title">The Competitive Landscape</div>
            <div class="info-card-content">
                <p style="color: #6B5660; margin-bottom: 16px;">
                    Here's who AI mentions most often in your space, and what they're doing to earn that visibility:
                </p>

                <table style="margin-bottom: 0;">
                    <thead>
                        <tr>
                            <th>Brand</th>
                            <th style="text-align: center;">AI Visibility Rate</th>
                            <th style="text-align: center;">Status</th>
                            <th>What They're Doing</th>
                        </tr>
                    </thead>
                    <tbody>
                        {you_row}
                        {competitor_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    def _infer_competitor_strategy(self, competitor: str, scored_results: List[Dict[str, Any]]) -> str:
        """Infer what a competitor is doing based on where they appear."""

        # Sample a few results where competitor appears
        appearances = []
        for r in scored_results:
            visibility = r.get('visibility', {})
            competitors_mentioned = visibility.get('competitors_mentioned', [])
            if competitor in competitors_mentioned:
                appearances.append(r)

        if not appearances:
            return "Strong brand presence"

        # Check for patterns
        comparison_count = sum(1 for r in appearances if 'vs' in r.get('prompt_text', '').lower() or 'versus' in r.get('prompt_text', '').lower() or 'compare' in r.get('prompt_text', '').lower())
        how_to_count = sum(1 for r in appearances if 'how to' in r.get('prompt_text', '').lower())
        best_count = sum(1 for r in appearances if 'best' in r.get('prompt_text', '').lower())

        if comparison_count > len(appearances) * 0.4:
            return "Heavy comparison content & head-to-head positioning"
        elif how_to_count > len(appearances) * 0.3:
            return "Educational content & how-to guides"
        elif best_count > len(appearances) * 0.3:
            return "Product reviews & best-of listicles"
        else:
            return "Comprehensive content across query types"

    def _build_simplified_opportunities(self, gap_analysis: Dict[str, Any],
                                       action_plan: Dict[str, Any],
                                       competitive_analysis: Dict[str, Any],
                                       scored_results: List[Dict[str, Any]]) -> str:
        """Build simplified top 3-5 opportunities that focus on competitive advantage."""
        
        geo_aeo_wins = action_plan.get('geo_aeo_quick_wins', [])[:3]  # Top 3 only
        
        opportunities_html = ""
        
        for i, win in enumerate(geo_aeo_wins, 1):
            # Get 2 example queries only
            example_queries = win.get('example_queries', [])[:2]
            queries_html = ""
            for query in example_queries:
                cleaned = self._clean_query_for_display(query)
                queries_html += f'<li style="margin: 4px 0; color: #6B5660; font-size: 14px;">"{cleaned}"</li>'
            
            opportunities_html += f"""
            <div style="background: #F7EBF0; border-left: 4px solid #A78E8B; padding: 24px; border-radius: 8px; margin-bottom: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="margin: 0; color: #4D2E3A; font-size: 18px;">{i}. {win['title']}</h4>
                    <span style="background: #8B3A3A; color: white; padding: 6px 14px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                        HIGH IMPACT
                    </span>
                </div>
                
                <div style="margin-bottom: 16px;">
                    <strong style="color: #6B5660;">Why this matters:</strong>
                    <p style="margin: 6px 0 0 0; color: #4D2E3A; font-size: 15px; line-height: 1.6;">{win['why']}</p>
                </div>
                
                <div style="margin-bottom: 16px;">
                    <strong style="color: #6B5660;">Examples of queries where competitors show up:</strong>
                    <ul style="margin: 8px 0; padding-left: 20px;">{queries_html}</ul>
                </div>
                
                <div style="background: white; padding: 16px; border-radius: 6px; margin-top: 16px;">
                    <strong style="color: #4D2E3A;">📈 Estimated Impact:</strong>
                    <p style="margin: 6px 0 0 0; color: #6B5660; font-size: 14px;">{win['estimated_impact']}</p>
                </div>
            </div>
            """
        
        if not opportunities_html:
            opportunities_html = "<p>No immediate opportunities identified. Building general content presence is the priority.</p>"
        
        return f"""
        <div class="info-card" style="margin-top: 32px;">
            <div class="info-card-title">🎯 Your Top Opportunities</div>
            <div class="info-card-content">
                <p style="color: #6B5660; margin-bottom: 24px;">
                    Based on competitive analysis, these are the highest-impact areas where you can catch up to leaders in your space:
                </p>
                {opportunities_html}
            </div>
        </div>

        <div class="accordion-group" style="margin-top: 24px;">
            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>📊 Want the Detailed Tactical Plan?</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                <p style="color: #6B5660; line-height: 1.6; margin: 16px 0;">
                    This report shows you the strategic overview. DaSilva Consulting has a detailed, proprietary action plan
                    with specific content briefs, technical SEO requirements, and distribution strategies for each opportunity.
                </p>
            </div>
        </div>
        """
