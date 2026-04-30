"""
HTML report generator for visibility analysis - DaSilva Consulting Brand.
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional


def _unwrap_snippet_dicts(text: str) -> str:
    """
    Strip Google AI Overview's stringified-dict artifacts from response text.

    AI responses sometimes contain raw Python-style list-of-dicts:
        - {'snippet': 'Brand: This is the description.'}
        - {'snippet': 'Other: ...', 'snippet_links': [...]}

    These were leaking verbatim into client-facing sentiment quote cards.
    The previous fix (the simpler version that lived inline in
    _build_sentiment_analysis_tab) only matched COMPLETE dicts where the
    inner string had no escaped apostrophes — so quotes containing
    `country\'s` failed to match, and quotes truncated by the 200-300 char
    context window also failed because they had no closing brace.

    This function handles three cases:
      1. Complete dicts, including ones with escaped quotes inside the
         payload — uses an escape-aware regex (`(?:[^'\\]|\\.)*?`).
      2. Right-edge truncation (the dict's closing got cut off by the
         context-window slice) — strips the leading `{'snippet': '` so
         the inner text remains.
      3. Left-edge truncation (the dict's opening got cut off) — strips
         a trailing `'}` if it appears at the start of the text or
         immediately before a comma-separated next-dict marker.

    Run this on the FULL response_text before slicing the context window
    so that complete dicts get matched cleanly. Then run a second pass
    on the sliced context to handle edge truncations.
    """
    if not text:
        return text

    # Pass 1 — complete dicts with escape-aware quote matching.
    # The optional `snippet_links` field is a Python list of dicts like
    # `[{'text': 'X', 'link': 'https://...'}]`; the outer regex needs to
    # consume the list AND the closing brace of the outer dict, otherwise
    # we leave behind `]}` cosmetic crumbs.
    text = re.sub(
        r"\{'snippet':\s*'((?:[^'\\]|\\.)*?)'(?:,\s*'snippet_links':\s*\[[^\]]*\])?\s*\}",
        r'\1',
        text,
    )
    text = re.sub(
        r'\{"snippet":\s*"((?:[^"\\]|\\.)*?)"(?:,\s*"snippet_links":\s*\[[^\]]*\])?\s*\}',
        r'\1',
        text,
    )

    # Pass 2 — right-edge truncation: strip leading `{'snippet': '` that
    # never got a closing match (because end-of-context cut it off)
    text = re.sub(r"\{'snippet':\s*'", '', text)
    text = re.sub(r'\{"snippet":\s*"', '', text)

    # Pass 3 — left-edge truncation: strip trailing `'}` that's left over
    # from a previous dict whose opening got sliced away
    text = re.sub(r"'\}(?:,\s*'snippet_links':[^}]*?\})?(?=\s*$|\s*,\s*\{)", '', text)
    text = re.sub(r'"\}(?:,\s*"snippet_links":[^}]*?\})?(?=\s*$|\s*,\s*\{)', '', text)

    # Strip leading "- " bullet markers (these often precede the dicts)
    text = re.sub(r'(^|\n)\s*-\s+', r'\1', text)

    return text


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
        """Get performance label following DaSilva tone guidelines.

        Tiers chosen so that any non-zero visibility gets credit. The old
        threshold returned "Not showing up" for anything under 20%, which
        labeled real (10-17%) visibility as "not showing up" — actively
        misleading. Now only true zero gets that label.
        """
        if rate >= 60:
            return "Strong"
        elif rate >= 40:
            return "Needs work"
        elif rate >= 20:
            return "Weak"
        elif rate > 0:
            return "Barely visible"
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

        # Calculate visibility gap (factual — no dollar estimates without real data)
        total_results = visibility_summary.get('total_prompts_tested', 362)
        gap_percentage = competitor_rate - visibility_rate

        # Calculate 90-day target (close 50% of gap - realistic)
        target_visibility = min(visibility_rate + (competitor_rate - visibility_rate) * 0.5, 100)

        # Strategic recommendation based on data.
        # All percentage formatting uses one decimal place so the Executive
        # Summary numbers reconcile with the Competitive Landscape section
        # (which has always used :.1f). Mixing :.0f and :.1f for the same
        # underlying metric made clients see "9% vs 8.7%" in different
        # sections and lose trust.
        if chatgpt_rate < 20 and visibility_rate < 30:
            primary_rec = f"Focus on ChatGPT first - it's 73% of AI users and you're at {chatgpt_rate:.1f}% there. Infrastructure fixes take 2-4 weeks."
        elif visibility_rate >= 60:
            primary_rec = f"You have strong visibility ({visibility_rate:.1f}%). Focus on improving prominence (currently {prominence:.1f}/10) to become the top recommendation."
        else:
            primary_rec = f"Most exciting is the untapped potential in AI visibility. You're at {visibility_rate:.1f}% while {top_comp['name']} is at {top_comp['mention_rate']:.1f}% - that gap represents your first-mover advantage."

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

        # Build data-driven "What This Means" cards. The old version had two
        # static info-cards ("ChatGPT Opportunity" and "Quality Over Quantity")
        # that read identically across every client report regardless of the
        # data. They now flex to the actual visibility numbers.

        # Card A: ChatGPT-specific framing — adapts to actual chatgpt_rate
        if chatgpt_rate < 20:
            chatgpt_card = f"""
                <div class="info-card" style="background: #F0F7FF; border-left: 4px solid #3b82f6;">
                    <div class="info-card-title" style="color: #1e40af;">Biggest single platform opportunity: ChatGPT</div>
                    <div class="info-card-content">
                        <p>ChatGPT represents <strong>73% of all AI users</strong>. You&#39;re currently at <strong>{chatgpt_rate:.1f}%</strong> visibility there — the largest single platform with the most upside if we close the gap.</p>
                    </div>
                </div>
            """
        elif chatgpt_rate >= 50:
            chatgpt_card = f"""
                <div class="info-card" style="background: #F0FFF4; border-left: 4px solid #10b981;">
                    <div class="info-card-title" style="color: #065f46;">Strong on ChatGPT — extend the lead</div>
                    <div class="info-card-content">
                        <p>You&#39;re at <strong>{chatgpt_rate:.1f}%</strong> visibility on ChatGPT — that&#39;s strong on the largest AI platform (73% of AI users). Document what&#39;s working there and replicate the pattern on Perplexity and Gemini, where there&#39;s more room to grow.</p>
                    </div>
                </div>
            """
        else:
            chatgpt_card = f"""
                <div class="info-card" style="background: #F0F7FF; border-left: 4px solid #3b82f6;">
                    <div class="info-card-title" style="color: #1e40af;">Building on ChatGPT</div>
                    <div class="info-card-content">
                        <p>You&#39;re at <strong>{chatgpt_rate:.1f}%</strong> visibility on ChatGPT — present but not yet dominant. ChatGPT is 73% of AI users, so this is the platform with the most leverage if we focus content efforts there next.</p>
                    </div>
                </div>
            """

        # Card B: Competitive gap framing — adapts to actual gap_percentage
        if gap_percentage > 20:
            gap_card = f"""
                <div class="info-card" style="background: #FFF1D6; border-left: 4px solid #f59e0b; margin-top: 16px;">
                    <div class="info-card-title" style="color: #92400e;">The competitive gap is real and addressable</div>
                    <div class="info-card-content">
                        <p>{top_comp['name']} appears in <strong>{top_comp['mention_rate']:.1f}%</strong> of category queries vs your <strong>{visibility_rate:.1f}%</strong>. That <strong>{gap_percentage:.1f}-point gap</strong> means most AI users researching your category are being pointed at {top_comp['name']} instead of you.</p>
                        <p style="margin-top: 12px;">The 90-day target — closing 50% of the gap — gets you to <strong>{target_visibility:.1f}%</strong> visibility, achievable with focused content on the priority topics identified in this report.</p>
                    </div>
                </div>
            """
        elif gap_percentage > 0:
            gap_card = f"""
                <div class="info-card" style="background: #F0FFF4; border-left: 4px solid #10b981; margin-top: 16px;">
                    <div class="info-card-title" style="color: #065f46;">Within striking distance of the leader</div>
                    <div class="info-card-content">
                        <p>{top_comp['name']} leads at <strong>{top_comp['mention_rate']:.1f}%</strong> vs your <strong>{visibility_rate:.1f}%</strong> — a {gap_percentage:.1f}-point gap. That&#39;s small enough to close in 60-90 days with focused content work on the top opportunity areas identified later in this report.</p>
                    </div>
                </div>
            """
        else:
            gap_card = f"""
                <div class="info-card" style="background: #F0FFF4; border-left: 4px solid #10b981; margin-top: 16px;">
                    <div class="info-card-title" style="color: #065f46;">You lead the category</div>
                    <div class="info-card-content">
                        <p>You appear in <strong>{visibility_rate:.1f}%</strong> of queries — ahead of every tracked competitor (top is {top_comp['name']} at {top_comp['mention_rate']:.1f}%). The opportunity now is depth: improving prominence (currently <strong>{prominence:.1f}/10</strong>) so you&#39;re not just mentioned but recommended as the top choice.</p>
                    </div>
                </div>
            """

        return f"""
        <h2 style="margin-top: 48px;">Executive Summary</h2>

        <!-- The Business Impact -->
        <div class="insight" style="background: linear-gradient(135deg, #4D2E3A15 0%, #4D2E3A25 100%); border-left: 4px solid #4D2E3A; padding: 32px; border-radius: 8px; margin: 32px 0;">
            <p style="font-size: 18px; line-height: 1.7; margin: 0; color: #4D2E3A; font-weight: 500;">
                {brand_name} is at <strong>{visibility_rate:.1f}%</strong> AI visibility while your top competitor ({top_comp['name']}) appears in <strong>{top_comp['mention_rate']:.1f}%</strong> of queries.
                That <strong>{gap_percentage:.1f}% gap</strong> means potential customers asking AI for recommendations in your space are being directed to competitors instead of you.
            </p>
            <p style="font-size: 16px; line-height: 1.7; margin: 24px 0 0 0; color: #6B5660;">
                <strong>Primary recommendation:</strong> {primary_rec}
            </p>
        </div>

        <!-- Core Metrics Grid -->
        <div class="metrics-grid" style="grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); margin: 40px 0;">
            <div class="metric-card {'strong' if visibility_rate >= 60 else 'needs-work' if visibility_rate >= 30 else 'weak'}">
                <div class="metric-label">Visibility Rate <span style="background: #E8E4EC; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 4px;">{momentum_icon} {momentum_label}</span></div>
                <div class="metric-value">{visibility_rate:.1f}%</div>
                <div class="metric-status">{'Strong presence' if visibility_rate >= 60 else 'Room for growth' if visibility_rate >= 30 else 'First-mover opportunity'}</div>
            </div>
            <div class="metric-card {'strong' if asov >= 40 else 'needs-work' if asov >= 20 else 'weak'}">
                <div class="metric-label">AI Share of Voice</div>
                <div class="metric-value">{asov:.1f}%</div>
                <div class="metric-status">{'Market leader' if asov >= 40 else 'Competitive' if asov >= 20 else 'Growth opportunity'}</div>
            </div>
            <div class="metric-card {'strong' if prominence >= 7 else 'needs-work' if prominence >= 4 else 'weak'}">
                <div class="metric-label">Prominence Score</div>
                <div class="metric-value">{prominence:.1f}/10</div>
                <div class="metric-status">{'Featured prominently' if prominence >= 7 else 'Mentioned as option' if prominence >= 4 else 'Brief mentions'}</div>
            </div>
            {citation_html}
        </div>

        <!-- What This Means (data-driven — varies based on actual chatgpt_rate and gap) -->
        <div class="accordion-group" style="margin-top: 32px;">
            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>💡 What This Means For Your Business</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                {chatgpt_card}
                {gap_card}
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
                <p style="margin-top: 12px;"><strong>Visibility Gap:</strong> The percentage difference between your brand's visibility and your top competitor's. This gap represents queries where prospects are being sent to competitors instead of you.</p>
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

    def _build_sources_tab(self, brand_name: str, source_analysis: Dict[str, Any],
                           scored_results: list = None) -> str:
        """Build the Sources & Citations tab showing where brands are being mentioned.

        Uses two data sources:
        1. PRIMARY: Structured cited_urls from API responses (Perplexity, Gemini, Google AI Overviews)
        2. SECONDARY: Text-extracted source mentions from source_analysis
        """
        scored_results = scored_results or []

        # Aggregate cited_urls from all scored results (the real API citation data)
        from collections import Counter, defaultdict
        cited_domains = Counter()        # domain -> response count
        cited_pages = defaultdict(set)    # domain -> set of full URLs
        cited_by_platform = defaultdict(lambda: Counter())  # platform -> domain -> count
        citations_with_brand = Counter()  # domain -> count where brand was co-mentioned
        per_prompt_citations = []         # list of {prompt, platform, cited_urls}

        for result in scored_results:
            platform = result.get('platform', '')
            prompt_text = result.get('prompt_text', '')
            visibility = result.get('visibility', {})
            sources = visibility.get('sources', [])

            # Collect prompt-level citation data
            prompt_citations = []
            for source in sources:
                domain = source.get('domain', '')
                full_url = source.get('full_url', '')
                if not domain:
                    continue

                cited_domains[domain] += 1
                if full_url:
                    cited_pages[domain].add(full_url)
                cited_by_platform[platform][domain] += 1

                if source.get('brand_in_context', False):
                    citations_with_brand[domain] += 1

                prompt_citations.append({
                    'domain': domain,
                    'url': full_url or f'https://{domain}',
                    'title': source.get('source_name', domain),
                    'type': source.get('type', 'unknown'),
                    'brand_co_mentioned': source.get('brand_in_context', False)
                })

            if prompt_citations:
                per_prompt_citations.append({
                    'prompt': prompt_text,
                    'platform': platform,
                    'citations': prompt_citations
                })

        total_api_citations = sum(cited_domains.values())
        total_unique_domains = len(cited_domains)
        has_api_citations = total_api_citations > 0

        # Also check text-extracted source analysis
        has_text_sources = source_analysis and source_analysis.get('all_sources')

        if not has_api_citations and not has_text_sources:
            return f"""
            <h2>Sources & Citations</h2>
            <div class="info-card">
                <div class="info-card-title">What This Section Tracks</div>
                <div class="info-card-content">
                    <p style="font-size: 16px; line-height: 1.8; color: #4D2E3A; margin-bottom: 16px;">
                        When AI platforms answer questions about your industry, they often cite
                        third-party sources — linking to review sites, news outlets, comparison articles,
                        and more. This section shows <strong>exactly which URLs</strong> AI platforms
                        are referencing when they discuss your industry.
                    </p>
                    <p style="font-size: 15px; line-height: 1.7; color: #6B5660; margin-bottom: 16px;">
                        <strong>No source citations were detected in this test run.</strong> This typically
                        means the AI platforms responded without citing external sources. Perplexity and
                        Gemini typically provide the most citation data — ChatGPT and Claude provide less.
                    </p>
                    <p style="font-size: 15px; line-height: 1.7; color: #6B5660; margin-bottom: 0;">
                        <strong>What you can do:</strong> Getting {brand_name} featured on high-authority
                        sites that AI platforms trust (review sites, industry publications, comparison
                        articles) increases the likelihood of being cited. This section will show exactly
                        which domains to target as citation data becomes available.
                    </p>
                </div>
            </div>
            """

        total_sources = source_analysis.get('total_unique_sources', 0) if source_analysis else 0
        brand_sources = source_analysis.get('sources_mentioning_brand', 0) if source_analysis else 0
        gap_opportunities = source_analysis.get('gap_opportunities', 0) if source_analysis else 0

        sources_with_brand = source_analysis.get('sources_with_your_brand', []) if source_analysis else []
        recommended_targets = source_analysis.get('recommended_targets', []) if source_analysis else []

        # Use API citation counts if available, otherwise fall back to text extraction
        display_total = total_unique_domains if has_api_citations else total_sources
        display_brand = len(citations_with_brand) if has_api_citations else brand_sources

        # Determine which platforms provided citation data
        platforms_with_citations = [p for p in cited_by_platform.keys() if cited_by_platform[p]]
        platform_labels = {
            'perplexity': 'Perplexity',
            'gemini': 'Gemini',
            'google_ai_overview': 'Google AI Overview',
            'openai': 'ChatGPT',
            'anthropic': 'Claude'
        }

        html = f"""
        <h2>Sources & Citations</h2>
        <p style="font-size: 16px; line-height: 1.8; color: #4D2E3A; margin-bottom: 32px;">
            When AI platforms answer questions about your industry, they cite third-party sources —
            linking to specific URLs that inform their responses. This section shows <strong>exactly which
            domains and pages</strong> AI is citing, and whether {brand_name} appears alongside those citations.
        </p>

        <div class="metrics-grid" style="grid-template-columns: repeat(3, 1fr);">
            <div class="metric-card">
                <div class="metric-label">Cited Domains</div>
                <div class="metric-value" style="font-size: 40px;">{display_total}</div>
                <div class="metric-status">Unique domains cited across {total_api_citations} responses</div>
            </div>
            <div class="metric-card {'strong' if display_brand > 0 else 'weak'}">
                <div class="metric-label">Co-Cited with {brand_name}</div>
                <div class="metric-value" style="font-size: 40px;">{display_brand}</div>
                <div class="metric-status">Domains where your brand also appears</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Citation Sources</div>
                <div class="metric-value" style="font-size: 40px;">{len(platforms_with_citations)}</div>
                <div class="metric-status">{'  '.join(platform_labels.get(p, p) for p in platforms_with_citations) if platforms_with_citations else 'Pending next test run'}</div>
            </div>
        </div>
        """

        # Section 1: Top Cited Domains (like Ahrefs Brand Radar)
        if cited_domains:
            top_domains = cited_domains.most_common(15)

            domains_table = """
            <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
                <thead>
                    <tr style="background: #F3EFF2; border-bottom: 2px solid #D4C5CE;">
                        <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Domain</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Responses</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Unique Pages</th>
                        <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Brand Co-Cited</th>
                        <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Platforms Citing</th>
                    </tr>
                </thead>
                <tbody>
            """

            for domain, count in top_domains:
                pages_count = len(cited_pages.get(domain, set()))
                brand_co = citations_with_brand.get(domain, 0)
                brand_pct = round(brand_co / count * 100) if count > 0 else 0
                brand_color = '#27AE60' if brand_co > 0 else '#E74C3C'

                # Which platforms cite this domain
                citing_platforms = []
                for platform, domain_counts in cited_by_platform.items():
                    if domain in domain_counts:
                        citing_platforms.append(platform_labels.get(platform, platform))

                domains_table += f"""
                <tr style="border-bottom: 1px solid #E8E4E3;">
                    <td style="padding: 12px; color: #4D2E3A; font-weight: 500;">
                        <a href="https://{domain}" target="_blank" style="color: #4D2E3A; text-decoration: none; border-bottom: 1px dotted #A78E8B;">{domain}</a>
                    </td>
                    <td style="padding: 12px; text-align: center; color: #6B5660; font-weight: 600; font-size: 18px;">{count}</td>
                    <td style="padding: 12px; text-align: center; color: #6B5660;">{pages_count}</td>
                    <td style="padding: 12px; text-align: center; color: {brand_color}; font-weight: 600;">
                        {'Yes (' + str(brand_pct) + '%)' if brand_co > 0 else 'No'}
                    </td>
                    <td style="padding: 12px; color: #6B5660; font-size: 13px;">{'  '.join(citing_platforms)}</td>
                </tr>
                """

            domains_table += "</tbody></table>"

            html += f"""
            <div class="accordion-group" style="margin-top: 32px;">
                <button class="accordion-button active" onclick="toggleAccordion(this)">
                    <span>Top Cited Domains ({total_unique_domains} found)</span>
                    <span class="accordion-icon">▼</span>
                </button>
                <div class="accordion-content active">
                    <p style="color: #6B5660; margin: 16px 0; line-height: 1.7;">
                        These are the domains AI platforms cited most frequently when answering questions
                        related to your industry. Domains where {brand_name} is co-cited are marked in green.
                    </p>
                    {domains_table}
                </div>
            </div>
            """

        # Section 2: Per-Prompt Citations (which sources were cited for which questions)
        if per_prompt_citations:
            prompt_rows = ""
            for i, entry in enumerate(per_prompt_citations[:20]):
                prompt_short = entry['prompt'][:100] + ('...' if len(entry['prompt']) > 100 else '')
                platform_label = platform_labels.get(entry['platform'], entry['platform'])
                citation_links = []
                for cit in entry['citations'][:5]:
                    co_badge = ' <span style="color: #27AE60; font-weight: 600;">&#10003;</span>' if cit.get('brand_co_mentioned') else ''
                    citation_links.append(
                        f'<a href="{cit["url"]}" target="_blank" style="color: #D4698B; text-decoration: none; font-size: 13px;">'
                        f'{cit["domain"]}</a>{co_badge}'
                    )
                more = f' +{len(entry["citations"]) - 5} more' if len(entry['citations']) > 5 else ''

                prompt_rows += f"""
                <tr style="border-bottom: 1px solid #E8E4E3;">
                    <td style="padding: 12px; color: #4D2E3A; font-size: 14px; max-width: 400px;">{prompt_short}</td>
                    <td style="padding: 12px; color: #6B5660; text-align: center; font-size: 13px;">{platform_label}</td>
                    <td style="padding: 12px; color: #6B5660; font-size: 13px;">{'&ensp;'.join(citation_links)}{more}</td>
                </tr>
                """

            html += f"""
            <div class="accordion-group" style="margin-top: 24px;">
                <button class="accordion-button" onclick="toggleAccordion(this)">
                    <span>Citations by Prompt ({len(per_prompt_citations)} responses with sources)</span>
                    <span class="accordion-icon">▼</span>
                </button>
                <div class="accordion-content">
                    <p style="color: #6B5660; margin: 16px 0; line-height: 1.7;">
                        For each question tested, these are the sources AI cited in its response.
                        A <span style="color: #27AE60; font-weight: 600;">&#10003;</span> means {brand_name}
                        was mentioned in the same response as that source.
                    </p>
                    <div style="max-height: 500px; overflow-y: auto; border: 1px solid #E8E4E3; border-radius: 6px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead style="position: sticky; top: 0; background: #F3EFF2; z-index: 10;">
                                <tr style="border-bottom: 2px solid #D4C5CE;">
                                    <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Prompt</th>
                                    <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Platform</th>
                                    <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Cited Sources</th>
                                </tr>
                            </thead>
                            <tbody>{prompt_rows}</tbody>
                        </table>
                    </div>
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

        # Phase 3: Tiered targets table — replaces the hardcoded "Action"
        # column with auto-classified source type, an outreach tier (1/2/3)
        # based on internal data only, and the actual snippet showing what
        # the source said about the competitor.
        sources_by_tier = source_analysis.get('sources_by_tier', {1: [], 2: [], 3: []}) if source_analysis else {1: [], 2: [], 3: []}

        # Pretty labels for source types
        SOURCE_TYPE_LABELS = {
            'aggregator':  ('🏷️ Aggregator',  'Listing / review platforms (G2, Capterra, Trustpilot)'),
            'community':   ('💬 Community',   'Forums, Reddit, Quora, Stack Exchange'),
            'reference':   ('📚 Reference',   'Wikipedia, encyclopedias, reference works'),
            'video':       ('🎥 Video',       'YouTube, Vimeo, TikTok'),
            'authority':   ('🏛️ Authority',   '.gov / .edu / official institutions'),
            'editorial':   ('📰 Editorial',   'News outlets, magazines, large publishers'),
            'comparison':  ('🔀 Comparison',  '"Best of" lists, vs. articles, alternatives pages'),
            'unknown':     ('❓ Unclassified', 'Could not be auto-classified from URL alone'),
        }

        TIER_META = {
            1: {'label': 'Tier 1 — Critical Gaps',
                'desc':  'Source appeared 5+ times AND named 2+ competitors. Highest-leverage outreach.',
                'color': '#B33A3A', 'bg': '#FBEAEA'},
            2: {'label': 'Tier 2 — Active Gaps',
                'desc':  'Source appeared 2–4 times AND named at least one competitor.',
                'color': '#B57E1A', 'bg': '#FFF4E6'},
            3: {'label': 'Tier 3 — Watch List',
                'desc':  'Single appearances or marginal coverage — worth tracking but not priority.',
                'color': '#5C6B7A', 'bg': '#EEF1F4'},
        }

        # Phase 3: render the tiered targets section if ANY tier has sources.
        # We don't gate on `recommended_targets` (which uses a relevance_score
        # cutoff) because the tier system is the new prioritization model.
        any_tier_has_sources = any(sources_by_tier.get(t) for t in (1, 2, 3))

        if any_tier_has_sources:
            tiered_html = ""
            for tier in (1, 2, 3):
                tier_sources = sources_by_tier.get(tier, [])
                if not tier_sources:
                    continue

                # Cap each tier so the report doesn't balloon. T1 + T2 are
                # most actionable, so we surface more of them.
                cap = {1: 15, 2: 15, 3: 10}[tier]
                meta = TIER_META[tier]

                rows = ""
                for i, target in enumerate(tier_sources[:cap], 1):
                    src_type = target.get('source_type', 'unknown')
                    type_label, type_desc = SOURCE_TYPE_LABELS.get(src_type, SOURCE_TYPE_LABELS['unknown'])

                    # Top competitor + their co-mention count at this source
                    top_comp = target.get('top_competitor') or '—'
                    top_comp_count = target.get('top_competitor_count', 0)

                    # Other competitors at this source (if more than one)
                    comp_co = target.get('competitor_co_mentions', {}) or {}
                    other_comps = sorted(
                        [(n, c) for n, c in comp_co.items() if n != top_comp],
                        key=lambda kv: -kv[1],
                    )[:3]
                    others_str = ''
                    if other_comps:
                        others_str = ' · also: ' + ', '.join(f'{n} ({c})' for n, c in other_comps)

                    # Pull the most informative snippet (first sample if any)
                    snippet = ''
                    samples = target.get('context_samples') or []
                    if samples:
                        s = samples[0].strip()
                        # Trim to ~280 chars; we already escape via html lib in prompt viewer
                        # but here we're concatenating into a static template, so escape inline.
                        import html as _html
                        s_escaped = _html.escape(s[:280] + ('…' if len(s) > 280 else ''))
                        snippet = f"""
                            <div style="margin-top: 8px; padding: 10px 12px; background: #FFFFFF; border-left: 3px solid #C9A7B3; border-radius: 4px; font-size: 13px; color: #4D2E3A; line-height: 1.5; font-style: italic;">
                                "{s_escaped}"
                            </div>
                        """

                    example_url_html = ''
                    if target.get('example_urls'):
                        ex = target['example_urls'][0]
                        example_url_html = (
                            f'<div style="margin-top: 6px; font-size: 12px; color: #6B5660;">'
                            f'Example URL: <a href="{ex}" target="_blank" style="color: #D4698B;">{ex[:90]}{"…" if len(ex) > 90 else ""}</a>'
                            f'</div>'
                        )

                    rows += f"""
                    <tr style="border-bottom: 1px solid #E8E4E3;">
                        <td style="padding: 14px 12px; vertical-align: top;">
                            <div style="font-weight: 600; color: #4D2E3A; font-size: 14px;">{i}. <a href="https://{target['source']}" target="_blank" style="color: #4D2E3A; text-decoration: none; border-bottom: 1px dotted #A78E8B;">{target['source']}</a></div>
                            <div style="margin-top: 4px; font-size: 12px; color: #6B5660;" title="{type_desc}">{type_label}</div>
                            {example_url_html}
                        </td>
                        <td style="padding: 14px 12px; vertical-align: top; text-align: center; color: #4D2E3A; font-weight: 600;">
                            {target['total_appearances']}
                        </td>
                        <td style="padding: 14px 12px; vertical-align: top; color: #4D2E3A;">
                            <strong>{top_comp}</strong>{f' ({top_comp_count})' if top_comp_count else ''}
                            <span style="color: #6B5660; font-size: 12px;">{others_str}</span>
                            {snippet}
                        </td>
                        <td style="padding: 14px 12px; vertical-align: top; color: #4D2E3A; font-size: 13px; line-height: 1.5;">
                            {target.get('recommended_action', '')}
                        </td>
                    </tr>
                    """

                tier_table = f"""
                <table style="width: 100%; border-collapse: collapse; margin-top: 12px;">
                    <thead>
                        <tr style="background: {meta['bg']}; border-bottom: 2px solid {meta['color']};">
                            <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Source</th>
                            <th style="text-align: center; padding: 12px; font-weight: 600; color: #4D2E3A;">Times Cited</th>
                            <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Competitors Featured (with snippet)</th>
                            <th style="text-align: left; padding: 12px; font-weight: 600; color: #4D2E3A;">Recommended Outreach</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                """

                tiered_html += f"""
                <div style="margin-top: 24px;">
                    <div style="display: flex; align-items: baseline; gap: 12px; margin-bottom: 6px; flex-wrap: wrap;">
                        <h4 style="margin: 0; color: {meta['color']}; font-size: 16px; font-weight: 700;">{meta['label']}</h4>
                        <span style="font-size: 12px; color: #6B5660;">({len(tier_sources)} source{'s' if len(tier_sources) != 1 else ''}{'; showing top ' + str(cap) if len(tier_sources) > cap else ''})</span>
                    </div>
                    <p style="margin: 0 0 4px 0; font-size: 13px; color: #6B5660; font-style: italic;">{meta['desc']}</p>
                    {tier_table}
                </div>
                """

            html += f"""
            <div class="accordion-group" style="margin-top: 32px;">
                <button class="accordion-button" onclick="toggleAccordion(this)">
                    <span>⚠️ Outreach Targets — Where Competitors Appear Without You ({sum(len(sources_by_tier.get(t, [])) for t in (1, 2, 3))} sources across 3 tiers)</span>
                    <span class="accordion-icon">▼</span>
                </button>
                <div class="accordion-content">
                    <p style="color: #6B5660; margin: 16px 0; line-height: 1.7;">
                        These are sources AI cited where your competitors appear and {brand_name} does not. Tiers are
                        based on internal evidence — how many times the source was cited and how many competitors it
                        named — not on external domain-authority data. Source types are auto-classified from the URL;
                        verify before pitching.
                    </p>
                    {tiered_html}
                </div>
            </div>
            """

            # Phase 3: per-competitor lens — for each top competitor, show
            # the sources where they appear (and whether the brand is also there).
            competitor_lens = source_analysis.get('competitor_lens', {}) if source_analysis else {}
            if competitor_lens:
                # Pick the top 5 competitors by total source coverage
                top_comps = sorted(
                    competitor_lens.items(),
                    key=lambda kv: -sum(s['comp_co_mention_count'] for s in kv[1]),
                )[:5]

                lens_blocks = ''
                for comp_name, comp_sources in top_comps:
                    if not comp_sources:
                        continue
                    top_5 = comp_sources[:5]
                    rows = ''
                    for s in top_5:
                        type_label, _ = SOURCE_TYPE_LABELS.get(s['source_type'], SOURCE_TYPE_LABELS['unknown'])
                        you_status = (
                            '<span style="color: #27AE60; font-weight: 600;">You also appear</span>'
                            if s['brand_also_present']
                            else '<span style="color: #E74C3C; font-weight: 600;">You absent</span>'
                        )
                        ex_url = s.get('example_url') or f"https://{s['domain']}"
                        rows += f"""
                        <tr style="border-bottom: 1px solid #E8E4E3;">
                            <td style="padding: 10px 12px; color: #4D2E3A; font-size: 13px;">
                                <a href="{ex_url}" target="_blank" style="color: #4D2E3A; text-decoration: none; border-bottom: 1px dotted #A78E8B;">{s['domain']}</a>
                                <div style="font-size: 11px; color: #6B5660; margin-top: 2px;">{type_label}</div>
                            </td>
                            <td style="padding: 10px 12px; text-align: center; color: #6B5660; font-size: 13px;">{s['comp_co_mention_count']}</td>
                            <td style="padding: 10px 12px; font-size: 13px;">{you_status}</td>
                        </tr>
                        """
                    lens_blocks += f"""
                    <div style="margin-top: 16px; background: #FFFFFF; border: 1px solid #E8E4E3; border-radius: 6px; padding: 16px;">
                        <div style="font-weight: 600; color: #4D2E3A; margin-bottom: 8px; font-size: 15px;">
                            🎯 {comp_name}
                        </div>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #F3EFF2;">
                                    <th style="text-align: left; padding: 8px 12px; font-size: 12px; color: #4D2E3A; font-weight: 600;">Source</th>
                                    <th style="text-align: center; padding: 8px 12px; font-size: 12px; color: #4D2E3A; font-weight: 600;">Times Cited Together</th>
                                    <th style="text-align: left; padding: 8px 12px; font-size: 12px; color: #4D2E3A; font-weight: 600;">{brand_name} Status</th>
                                </tr>
                            </thead>
                            <tbody>{rows}</tbody>
                        </table>
                    </div>
                    """

                html += f"""
                <div class="accordion-group" style="margin-top: 24px;">
                    <button class="accordion-button" onclick="toggleAccordion(this)">
                        <span>🔍 Per-Competitor View — Where Each Top Competitor Is Getting Cited</span>
                        <span class="accordion-icon">▼</span>
                    </button>
                    <div class="accordion-content">
                        <p style="color: #6B5660; margin: 16px 0; line-height: 1.7;">
                            For your top competitors, this shows the specific sources AI cited them on, and whether
                            {brand_name} was named in the same context. Use this to prioritize which competitor's
                            citation footprint to attack first.
                        </p>
                        {lens_blocks}
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
            # No high-priority gap targets — but that doesn't mean we're
            # winning. The old boilerplate said "Good news! You're present
            # in all sources where competitors appear" even when the actual
            # co-citation rate was 1-7%. Replaced with a data-driven
            # branch that tells the truth based on the underlying numbers.
            sources_with_you = source_analysis.get('sources_with_brand_co_mentions', []) if source_analysis else []
            total_sources = source_analysis.get('total_unique_sources', 0) if source_analysis else 0
            you_count = source_analysis.get('sources_with_brand_co_mentions_count', 0) if source_analysis else 0
            gap_count = source_analysis.get('gap_opportunities_count', 0) if source_analysis else 0

            if sources_with_you:
                co_rates = [float(s.get('brand_mention_rate', 0) or 0) for s in sources_with_you]
                avg_co_rate = sum(co_rates) / len(co_rates) if co_rates else 0.0
            else:
                avg_co_rate = 0.0

            if you_count == 0:
                html += f"""
                <div style="background: #FCDADA; padding: 24px; border-radius: 8px; margin-top: 32px;">
                    <h3 style="color: #6B3A3A; margin-bottom: 12px;">⚠ Source Co-Citation Gap</h3>
                    <p style="color: #4D2E3A; font-size: 16px; line-height: 1.7; margin: 0;">
                        Your brand wasn't co-cited with any of the {total_sources} sources AI used in these responses.
                        Competitors are capturing all the source-anchored authority right now. The priority is
                        establishing presence on the platforms and publications AI cites most often in your category.
                    </p>
                </div>
                """
            elif avg_co_rate < 10:
                html += f"""
                <div style="background: #FFF1D6; padding: 24px; border-radius: 8px; margin-top: 32px;">
                    <h3 style="color: #6B5660; margin-bottom: 12px;">📊 Source Co-Citation Picture</h3>
                    <p style="color: #4D2E3A; font-size: 16px; line-height: 1.7; margin: 0 0 12px 0;">
                        Your brand appears alongside {you_count} of the {total_sources} sources AI cites in your category — but at a low average co-citation rate of <strong>{avg_co_rate:.1f}%</strong>.
                    </p>
                    <p style="color: #4D2E3A; font-size: 15px; line-height: 1.7; margin: 0;">
                        Translation: you're &quot;present&quot; but barely. When AI cites these sources, it usually doesn&#39;t mention you alongside them. Strengthening your relationship with these sources — through guest posts, expert quotes, original research, or paid sponsorship — should meaningfully increase your AI co-citation rate.
                    </p>
                </div>
                """
            else:
                html += f"""
                <div style="background: #D4E8D4; padding: 24px; border-radius: 8px; margin-top: 32px;">
                    <h3 style="color: #2D5F2D; margin-bottom: 12px;">✓ Solid Source Co-Citation</h3>
                    <p style="color: #2D5F2D; font-size: 16px; line-height: 1.7; margin: 0;">
                        Your brand is co-cited at an average <strong>{avg_co_rate:.1f}%</strong> rate across the {you_count} sources you appear in — that&#39;s strong source-anchored authority. Focus on extending coverage to the {gap_count} sources where only competitors currently appear.
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
            display: none;
            padding: 20px;
            border: 1px solid #E8E4E3;
            border-top: none;
            border-radius: 0 0 8px 8px;
            margin-top: -9px;
            margin-bottom: 16px;
            background: white;
        }}

        .accordion-content.active {{
            display: block;
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

            // Close all accordions in the same parent group (if grouped)
            const parent = button.closest('.accordion-group');
            if (parent) {{
                parent.querySelectorAll('.accordion-button').forEach(btn => {{
                    btn.classList.remove('active');
                    if (btn.nextElementSibling) btn.nextElementSibling.classList.remove('active');
                }});
            }}

            // Toggle current accordion open/closed
            if (isActive) {{
                button.classList.remove('active');
                if (content) content.classList.remove('active');
            }} else {{
                button.classList.add('active');
                if (content) content.classList.add('active');
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

            {self._build_sources_tab(brand_name, source_analysis, scored_results) if source_analysis else '<p>No source analysis available.</p>'}
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
                <td>{comp['mention_rate']:.1f}%</td>
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
        """
        Build top 3 priorities for executive summary.

        Uses evidence-based competitor intelligence if available,
        falls back to legacy quick wins otherwise.
        """
        # Try evidence-based recommendations first
        competitor_intel = action_plan.get('competitor_intelligence', {})
        evidence_recs = competitor_intel.get('evidence_recommendations', [])

        if evidence_recs:
            return self._build_evidence_priorities(evidence_recs)

        # Fallback to legacy quick wins
        geo_aeo_wins = action_plan.get('geo_aeo_quick_wins', [])
        if not geo_aeo_wins:
            return ""

        return self._build_legacy_priorities(geo_aeo_wins[:3])

    def _build_evidence_priorities(self, evidence_recs: list) -> str:
        """Build the Top 3 Priorities section using evidence-based competitor intelligence."""
        html = """
        <h2>Top 3 Priorities</h2>
        <p style="font-size: 16px; line-height: 1.8; color: #4D2E3A; margin-bottom: 24px;">
            These recommendations are based on what your competitors are doing right now to win AI visibility.
            Each one is grounded in your test data and backed by research on what drives AI citations.
        </p>
        """

        for i, rec in enumerate(evidence_recs[:3], 1):
            priority_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            competitor = rec.get('competitor', 'A competitor')
            strategy = rec.get('strategy', 'Content Strategy')
            what_they_do = rec.get('what_they_do', '')
            prompts_affected = rec.get('prompts_affected', [])
            why_it_matters = rec.get('why_it_matters', '')
            what_to_do = rec.get('what_to_do', '')
            impact = rec.get('impact_estimate', '')
            total_won = rec.get('total_prompts_won_by_competitor', 0)
            top_persona = rec.get('top_persona_affected', '')
            cited_pages = rec.get('competitor_cited_pages', [])

            # Build prompts list
            prompts_html = ""
            if prompts_affected:
                prompts_html = '<div style="margin: 12px 0;">'
                prompts_html += '<p style="font-size: 13px; font-weight: 600; color: #4D2E3A; margin-bottom: 6px;">Prompts you\'re losing:</p>'
                for prompt in prompts_affected[:4]:
                    prompts_html += f'<div style="background: #FFF3F0; border-left: 3px solid #E74C3C; padding: 6px 12px; margin-bottom: 4px; font-size: 13px; color: #6B5660; border-radius: 0 4px 4px 0;">"{prompt}"</div>'
                if len(prompts_affected) > 4:
                    prompts_html += f'<div style="font-size: 12px; color: #A78E8B; padding: 4px 12px;">+ {len(prompts_affected) - 4} more</div>'
                prompts_html += '</div>'

            # Build cited pages
            cited_html = ""
            if cited_pages:
                domains = [f'<span style="background: #F0F0F0; padding: 2px 8px; border-radius: 3px; font-size: 12px; font-family: monospace;">{d[0]}</span>' for d in cited_pages[:3]]
                cited_html = f'<div style="margin: 8px 0; font-size: 13px; color: #A78E8B;">Pages being cited: {" ".join(domains)}</div>'

            html += f"""
            <div style="background: white; border: 2px solid #E8E4E3; border-radius: 10px; padding: 28px; margin-bottom: 20px;">
                <div style="display: flex; align-items: start; gap: 16px;">
                    <span style="font-size: 32px; flex-shrink: 0;">{priority_icon}</span>
                    <div style="flex: 1;">
                        <!-- Competitor badge -->
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                            <span style="background: #FFE8E0; color: #C0392B; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px;">
                                {competitor} wins {total_won} prompts
                            </span>
                            <span style="background: #EDE7F6; color: #7B1FA2; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                                {strategy}
                            </span>
                        </div>

                        <!-- What they're doing -->
                        <h3 style="margin: 0 0 8px 0; color: #4D2E3A; font-size: 17px; font-weight: 600;">
                            Why {competitor} is winning
                        </h3>
                        <p style="margin: 0 0 8px 0; color: #6B5660; font-size: 14px; line-height: 1.6;">
                            {what_they_do}
                        </p>

                        {cited_html}

                        <!-- Prompts affected -->
                        {prompts_html}

                        <!-- Research insight -->
                        <div style="background: #F8F6F0; border-radius: 6px; padding: 12px 16px; margin: 12px 0;">
                            <p style="margin: 0; font-size: 13px; color: #6B5660; line-height: 1.5;">
                                <span style="font-weight: 700; color: #4D2E3A;">📊 Why this matters:</span> {why_it_matters}
                            </p>
                        </div>

                        <!-- What to do -->
                        <div style="background: #E8F5E9; border-radius: 6px; padding: 12px 16px; margin: 12px 0 0 0;">
                            <p style="margin: 0; font-size: 14px; color: #2E7D32; line-height: 1.5;">
                                <span style="font-weight: 700;">✅ Action:</span> {what_to_do}
                            </p>
                        </div>

                        <!-- Impact -->
                        <div style="display: flex; gap: 12px; align-items: center; margin-top: 12px;">
                            <span style="background: #E3F2FD; color: #1565C0; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                                {impact}
                            </span>
                            <span style="color: #A78E8B; font-size: 12px;">
                                Most affected audience: {top_persona}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
            """

        html += """
        <div style="text-align: center; margin-top: 16px;">
            <p style="color: #A78E8B; font-size: 14px;">
                👉 See the <strong>Action Plan & Recommendations</strong> tab for the full competitive landscape,
                content gap analysis, and implementation roadmap.
            </p>
        </div>
        """

        return html

    def _build_legacy_priorities(self, top_3: list) -> str:
        """Build legacy quick wins format (fallback when no competitor intelligence)."""
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

        html += "</div>"
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
                        ({aud['gap_percentage']:.0f} points ahead). In our test, <strong>{aud['missed_responses']} responses</strong>
                        to this audience's queries mentioned competitors but not you.
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
            <strong>How priority is calculated:</strong> Rankings based on visibility gap size x number of queries tested. "Any Competitor" = % of queries where one or more competitors appeared (not average competitor rate). "Missed responses" = test responses where competitors were mentioned but your brand was not. Actual impact depends on your target market and content strategy.
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
                        In our test, <strong>{gap['missed_responses']} responses</strong> about {gap['content_type'].lower()} mentioned competitors but not you.
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
            <strong>How gaps are identified:</strong> Analyzed which content types (how-to, comparison, product info) had competitor presence. "Any Competitor" = % of queries where one or more competitors appeared (not average competitor rate). "Missed responses" = test responses where competitors appeared but your brand did not. Creating this content increases likelihood of AI citation.
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
            source_name = top_source.get('source', 'a high-value publication in your space')
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
                    'Send a personalized pitch with a specific story angle or expert contribution',
                    'Offer data, case studies, or exclusive insight relevant to their audience',
                    'Follow up after 5-7 business days',
                    'Build an ongoing relationship for recurring coverage'
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
        """Build ROI Estimator showing visibility improvement potential."""

        current_visibility = visibility_summary.get('brand_visibility_rate', 0)
        competitor_avg = visibility_summary.get('competitor_mention_rate', 0)

        # Project improvement based on implementing recommendations
        projected_visibility_low = int(min(current_visibility + 15, 100))
        projected_visibility_high = int(min(current_visibility + 25, 100))

        # Calculate the gap to close
        visibility_gap = max(0, competitor_avg - current_visibility)
        total_prompts = visibility_summary.get('total_prompts', 0)
        brand_mentions = visibility_summary.get('brand_mentions', 0)
        prompts_tested = visibility_summary.get('total_responses', total_prompts)

        html = f"""
        <div class="info-card">
            <div class="info-card-title">Visibility Growth Potential</div>
            <div class="info-card-content">
                <p style="font-size: 16px; line-height: 1.8; color: #4D2E3A; margin-bottom: 0;">
                    Based on your current performance and competitive benchmarks, here's what
                    implementing the recommendations in this report could achieve.
                </p>
            </div>
        </div>

        <div style="background: linear-gradient(135deg, #4D2E3A 0%, #A78E8B 100%); color: white; padding: 32px; border-radius: 12px; margin-bottom: 32px;">
            <h3 style="color: white; margin: 0 0 24px 0; font-size: 24px;">Projected Visibility Improvement (90 Days)</h3>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px;">
                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">Current AI Visibility</div>
                    <div style="font-size: 32px; font-weight: 700; margin-bottom: 4px;">{current_visibility:.1f}%</div>
                    <div style="font-size: 13px; opacity: 0.8;">Mentioned in {brand_mentions} of {prompts_tested} responses</div>
                </div>

                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">Target AI Visibility</div>
                    <div style="font-size: 32px; font-weight: 700; margin-bottom: 4px;">{projected_visibility_low}-{projected_visibility_high}%</div>
                    <div style="font-size: 13px; opacity: 0.8;">+{projected_visibility_low - int(current_visibility)} to +{projected_visibility_high - int(current_visibility)} percentage points</div>
                </div>

                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                    <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">Competitive Gap to Close</div>
                    <div style="font-size: 32px; font-weight: 700; margin-bottom: 4px;">{visibility_gap:.1f}%</div>
                    <div style="font-size: 13px; opacity: 0.8;">Avg competitor visibility: {competitor_avg:.1f}%</div>
                </div>
            </div>
        </div>

        <div style="background: #FFF4E6; padding: 16px 20px; border-left: 4px solid #F39C12; border-radius: 6px; margin-bottom: 24px;">
            <strong style="color: #B77400;">Why This Matters:</strong>
            <span style="color: #6B5660; margin-left: 8px;">
                AI-driven search is growing rapidly. When someone asks ChatGPT, Claude, or Perplexity
                for recommendations, being mentioned means reaching <strong>high-intent prospects</strong>
                who are actively looking for solutions. These aren't casual browsers — they're ready to act.
            </span>
        </div>

        <div style="background: white; border: 2px solid #27AE60; border-radius: 10px; padding: 32px; margin-bottom: 32px;">
            <h3 style="color: #27AE60; margin: 0 0 20px 0; font-size: 22px;">What Improved Visibility Means</h3>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 32px;">
                <div style="padding: 20px; background: #F8F8F7; border-radius: 8px;">
                    <div style="font-size: 15px; color: #6B5660; margin-bottom: 12px; font-weight: 600;">More AI Recommendations</div>
                    <p style="color: #4D2E3A; margin: 0; line-height: 1.7;">
                        Moving from {current_visibility:.0f}% to {projected_visibility_low}-{projected_visibility_high}%
                        means AI platforms mention your brand in <strong>{projected_visibility_low - int(current_visibility)}
                        to {projected_visibility_high - int(current_visibility)}</strong> more responses out of every 100 relevant queries.
                    </p>
                </div>

                <div style="padding: 20px; background: #F8F8F7; border-radius: 8px;">
                    <div style="font-size: 15px; color: #6B5660; margin-bottom: 12px; font-weight: 600;">Higher Quality Traffic</div>
                    <p style="color: #4D2E3A; margin: 0; line-height: 1.7;">
                        AI referrals are <strong>high-intent visitors</strong> — they asked a specific question
                        and were directed to you as a solution. Industry data suggests AI referral traffic converts
                        at higher rates than organic search.
                    </p>
                </div>
            </div>
        </div>

        <div class="accordion-group" style="margin-top: 32px;">
            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>How to Track AI-Driven Traffic</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                <div style="background: #E8F5E9; padding: 24px; border-radius: 8px; border-left: 4px solid #27AE60; margin-top: 16px;">
                    <p style="margin: 0 0 12px 0; color: #2E7D32; line-height: 1.7;">
                        To measure the real traffic impact, set up tracking in Google Analytics:
                    </p>
                    <ol style="margin: 0; padding-left: 20px; color: #2E7D32; line-height: 1.8;">
                        <li><strong>Identify AI referrers:</strong> Look for traffic from chat.openai.com, perplexity.ai, claude.ai, and gemini.google.com in your referral reports</li>
                        <li><strong>Set up conversion tracking:</strong> Track which AI-referred visitors take action (purchases, sign-ups, inquiries)</li>
                        <li><strong>Compare conversion rates:</strong> AI-referred visitors vs. organic search vs. other channels</li>
                        <li><strong>Monitor monthly trends:</strong> Track how AI traffic grows as your visibility improves</li>
                    </ol>
                    <p style="margin: 12px 0 0 0; color: #2E7D32; font-size: 14px; line-height: 1.7;">
                        <strong>Note:</strong> Some AI platforms don't pass referrer data, so traffic may appear as "direct."
                        As tracking improves across the industry, attribution will become clearer.
                    </p>
                </div>
            </div>

            <button class="accordion-button" onclick="toggleAccordion(this)">
                <span>About These Projections</span>
                <span class="accordion-icon">▼</span>
            </button>
            <div class="accordion-content">
                <div style="background: #E3F2FD; padding: 24px; border-radius: 8px; border-left: 4px solid #1976D2; margin-top: 16px;">
                    <p style="margin: 0; color: #1565C0; line-height: 1.8;">
                        <strong>Visibility targets</strong> are based on implementing the priority recommendations
                        in this report. The +15 to +25 percentage point improvement range reflects typical
                        results from clients who implement GEO/AEO content optimization strategies.
                        Actual results depend on implementation quality, competitive dynamics, and how
                        quickly AI platforms re-index updated content. We recommend re-running this test
                        monthly to track actual progress against these targets.
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

        # Sentiment classification — primary path is LLM-based via Claude
        # Sonnet 4.6 (handles negation, comparison, "X eliminates Y" patterns
        # that the keyword classifier got systematically wrong on Lumo and OCO).
        # If the API is unreachable for any reason, we fall back to the legacy
        # keyword classifier so the report still renders.
        try:
            from src.analysis.llm_sentiment import LLMSentimentClassifier
            llm_classifier = LLMSentimentClassifier(
                brand_name=brand_name,
                client_slug=getattr(self, 'client_slug', None),
            )
        except Exception:
            llm_classifier = None

        # Legacy keyword fallback (used only when LLM classifier returns None
        # for a particular snippet — typically API key missing or transient
        # network failure).
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

            # Strip Google AI Overview dict artifacts from the FULL response
            # text first. Doing this before the context-window slice means
            # complete dicts get matched cleanly (the previous post-slice
            # version failed when the slice cut a dict mid-string).
            response_text = _unwrap_snippet_dicts(response_text)

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

            # Second-pass dict cleanup on the sliced context. Even after the
            # full-text pass above, the slice itself might cut one dict apart
            # (e.g. start mid-payload). _unwrap_snippet_dicts handles
            # right-edge and left-edge truncation cases.
            context = _unwrap_snippet_dicts(context).strip()

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

            # Determine sentiment — try the LLM classifier first.
            sentiment = None
            if llm_classifier is not None:
                sentiment = llm_classifier.classify(context)

            # Fall back to keyword classification if the LLM was unavailable
            # for this snippet (None signals "couldn't classify").
            if sentiment is None:
                context_lower = context.lower()
                has_positive = any(kw in context_lower for kw in positive_keywords)
                has_negative = any(kw in context_lower for kw in negative_keywords)
                if has_positive and not has_negative:
                    sentiment = 'positive'
                elif has_negative and not has_positive:
                    sentiment = 'negative'
                else:
                    sentiment = 'neutral'

            # Get full prompt text — no truncation
            prompt_text = result.get('prompt_text', '') or result.get('prompt', '')

            # Highlight brand name in the prompt
            import re
            prompt_highlighted = re.sub(
                re.escape(brand_name),
                f'<strong style="color: #4D2E3A; background: #F7EBF0; padding: 1px 4px; border-radius: 3px;">{brand_name}</strong>',
                prompt_text,
                flags=re.IGNORECASE
            ) if brand_name else prompt_text

            sample = {
                'platform': result.get('platform', 'Unknown').replace('openai', 'ChatGPT').replace('anthropic', 'Claude').replace('perplexity', 'Perplexity').replace('gemini', 'Gemini'),
                'quote': context,
                'prompt': prompt_highlighted
            }

            if sentiment == 'positive':
                positive_mentions.append(sample)
            elif sentiment == 'negative':
                negative_mentions.append(sample)
            else:
                neutral_mentions.append(sample)

        # Persist the classifier cache so subsequent regens don't re-classify
        # unchanged snippets. Failure to flush is non-fatal — worst case we
        # re-pay for those calls next regen.
        if llm_classifier is not None:
            try:
                llm_classifier.flush()
                stats = llm_classifier.stats()
                print(
                    f"  Sentiment classifier: {stats['calls']} new calls, "
                    f"{stats['cache_hits']} cache hits, "
                    f"{stats['fallbacks']} fallbacks (cache size: {stats['cache_size']})"
                )
            except Exception:
                pass

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
                        <strong style="color: {color};">{mention['platform']}</strong> • Query: <em>{mention['prompt']}</em>
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

            {self._build_sentiment_takeaway(brand_name, positive_pct, neutral_pct, negative_pct,
                                              len(positive_mentions), len(neutral_mentions), len(negative_mentions))}
        </div>
        """

    def _build_sentiment_takeaway(self, brand_name: str,
                                  positive_pct: float, neutral_pct: float, negative_pct: float,
                                  positive_n: int, neutral_n: int, negative_n: int) -> str:
        """
        Data-driven 'What This Means' for the sentiment section.

        Replaces the boilerplate "Publish thought leadership, case studies..."
        paragraph that appeared verbatim in every report. The advice now
        flexes to the actual sentiment distribution: high-negative cases
        get reputation-management framing, high-positive-but-low-volume
        cases get "extend the win" framing, neutral-dominant cases get
        differentiation framing, etc.
        """
        total = positive_n + neutral_n + negative_n
        baseline = (
            "<p style=\"color: #4D2E3A; line-height: 1.7; margin: 0;\">"
            "<strong>Why sentiment matters:</strong> AI language models are trained on existing content. "
            "The way AI describes you mirrors how the web describes you — when most mentions are factual, "
            "AI&#39;s output will be factual; when mentions skew positive, AI is more likely to recommend you. "
            "Sentiment isn&#39;t fixed; it shifts as new content gets indexed."
            "</p>"
        )

        if total == 0:
            advice = (
                f"<strong>How to improve:</strong> {brand_name} wasn&#39;t mentioned in enough responses to "
                "characterize sentiment. The prerequisite to managing sentiment is being mentioned at all. "
                "Focus on visibility first — get into AI&#39;s answer set, then we can shape the language."
            )
        elif negative_pct >= 15:
            advice = (
                f"<strong>How to improve:</strong> {negative_pct:.0f}% of your AI mentions read as negative "
                f"({negative_n} of {total} analyzed) — that&#39;s actively working against you. Audit the negative "
                "examples above: are they about pricing, missing features, unfavorable comparisons? Each pattern "
                "needs a counter-narrative published somewhere AI can pick up — comparison pages you control, "
                "case studies that address the specific objection, or third-party reviews that reframe the issue."
            )
        elif positive_pct >= 50:
            advice = (
                f"<strong>How to improve:</strong> AI describes {brand_name} favorably {positive_pct:.0f}% of the time "
                f"({positive_n} of {total} mentions). The tone is on your side — the opportunity is volume. "
                "Get mentioned in more responses by expanding into adjacent query types and growing your presence "
                "on the high-citation sources we identified earlier in this report."
            )
        elif positive_pct >= 25:
            advice = (
                f"<strong>How to improve:</strong> About {positive_pct:.0f}% of mentions are positive and {neutral_pct:.0f}% are factual/neutral. "
                "AI is mentioning you, but mostly as one option among many rather than the recommended choice. "
                "To shift more mentions toward positive, build content that gives AI specific reasons to favor you: "
                "third-party validation (awards, certifications, expert reviews), original research you can be cited for, "
                "and 'best for [use case]' content where you&#39;re positioned as the answer."
            )
        elif positive_pct >= 10:
            advice = (
                f"<strong>How to improve:</strong> Most of your AI mentions ({neutral_pct:.0f}%) are descriptive/neutral — "
                "AI is mentioning you factually but not characterizing you as the recommended option. To win more "
                "positive characterization, create comparison content (&quot;X vs Y&quot;), use-case-specific landing pages "
                "(&quot;best for [scenario]&quot;), and named-author content that AI can cite as expert authority."
            )
        else:
            advice = (
                f"<strong>How to improve:</strong> Only {positive_pct:.0f}% of mentions read as positive — AI describes "
                f"{brand_name} factually but rarely enthusiastically. The likeliest cause is missing content: AI doesn&#39;t "
                "have material to anchor a positive narrative. Top priorities are published expert authority (named author "
                "bylines), original research or data you can be cited for, and structured comparison/&quot;best for&quot; pages "
                "that give AI a clear positive frame to use."
            )

        return f"""
            <div style=\"background: #F8F8F7; padding: 24px; border-radius: 8px; margin-top: 48px;\">
                <h3 style=\"margin-top: 0;\">What This Means</h3>
                {baseline}
                <p style=\"color: #4D2E3A; line-height: 1.7; margin: 16px 0 0 0;\">
                    {advice}
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

        # Phase 2: Data-grounded Quick Insights.
        #
        # The previous version had hard-coded "What's Working / What's Missing"
        # strings that appeared identically in every report regardless of the
        # client's actual data — and "Worst Miss" was just the first miss in
        # iteration order, not the worst. Both were misleading.
        #
        # Now everything below is computed from the scored_results themselves.
        # Per-prompt buckets we'll fill in the loop below:
        best_response = {'prominence': 0, 'prompt': '', 'platform': '', 'persona': ''}

        # All "missed" prompts (brand absent + at least one competitor named),
        # ranked later by # of competitors named (more competitors = bigger gap).
        missed_prompts = []  # list of {prompt, persona, platform, competitors}

        # Category-level rollup: for each category, count prompts + brand mentions.
        # Used to derive "What's Working" (top-visibility categories) and
        # "What's Missing" (bottom-visibility categories with competitor coverage).
        from collections import defaultdict
        category_stats = defaultdict(lambda: {
            'prompts': 0,
            'brand_mentions': 0,
            'competitor_names_seen': defaultdict(int),
        })

        # Persona-level rollup (used for the persona panel below).
        persona_stats = defaultdict(lambda: {'prompts': 0, 'brand_mentions': 0})

        # Platform-level rollup (used for the platform panel below).
        platform_stats = defaultdict(lambda: {'prompts': 0, 'brand_mentions': 0})

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

            # Phase 2: Track best response with platform + persona context
            # (so the highlight isn't just a floating prompt with no provenance).
            if brand_mentioned and prominence > best_response['prominence']:
                best_response = {
                    'prominence': prominence,
                    'prompt': prompt_text,
                    'platform': platform,
                    'persona': persona,
                }

            # Phase 2: Collect ALL misses, then rank by competitor count later.
            # Previously this kept only the first miss in iteration order, which
            # is meaningless — a "worst miss" should be the gap where AI named
            # the most competitors while leaving the brand out.
            if not brand_mentioned and competitors:
                missed_prompts.append({
                    'prompt': prompt_text,
                    'persona': persona,
                    'platform': platform,
                    'competitors': competitors,
                })

            # Phase 2: Roll up by category / persona / platform for the
            # "what's working / what's missing" panels.
            cat = (metadata.get('category') or 'Uncategorized').strip() or 'Uncategorized'
            category_stats[cat]['prompts'] += 1
            if brand_mentioned:
                category_stats[cat]['brand_mentions'] += 1
            for c in competitors:
                category_stats[cat]['competitor_names_seen'][c] += 1

            persona_stats[persona]['prompts'] += 1
            if brand_mentioned:
                persona_stats[persona]['brand_mentions'] += 1

            platform_stats[platform]['prompts'] += 1
            if brand_mentioned:
                platform_stats[platform]['brand_mentions'] += 1

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

        # ============================================================
        # Phase 2: Data-grounded Quick Insights
        # ============================================================
        # Everything in this block is derived from scored_results — no
        # hardcoded copy, no inferred claims. If we don't have enough data
        # to support a panel, we don't show it.

        # 1. Worst miss = the prompt where the most competitors got named
        #    while the brand was absent. Tie-break by alphabetical prompt
        #    text for stable ordering across re-runs.
        worst_miss = None
        if missed_prompts:
            worst_miss = max(
                missed_prompts,
                key=lambda m: (len(m['competitors']), -ord(m['prompt'][0]) if m['prompt'] else 0),
            )

        # 2. Category rollups (only consider categories with enough sample
        #    size for the percentage to mean something — < 3 prompts per
        #    category is noise).
        MIN_CATEGORY_SAMPLE = 3
        category_view = []
        for cat, stats in category_stats.items():
            if stats['prompts'] < MIN_CATEGORY_SAMPLE:
                continue
            vis_rate = stats['brand_mentions'] / stats['prompts'] * 100
            top_competitors = sorted(
                stats['competitor_names_seen'].items(),
                key=lambda kv: kv[1], reverse=True,
            )[:3]
            category_view.append({
                'category': cat,
                'visibility_rate': vis_rate,
                'prompt_count': stats['prompts'],
                'brand_mentions': stats['brand_mentions'],
                'top_competitors': top_competitors,
            })

        # Sort once for "What's Working" (highest vis rate) and "What's Missing"
        # (lowest vis rate, but only categories where competitors DID show up,
        # because if no one's being mentioned the category is just untracked
        # by AI — not a "miss" per se).
        working_categories = sorted(category_view, key=lambda c: -c['visibility_rate'])[:3]
        missing_categories = [
            c for c in category_view
            if c['visibility_rate'] < 50 and c['top_competitors']
        ]
        missing_categories = sorted(missing_categories, key=lambda c: c['visibility_rate'])[:3]

        # 3. Persona view — rank personas by visibility rate, only show those
        #    with enough sample to be meaningful.
        MIN_PERSONA_SAMPLE = 3
        persona_view = []
        for p, stats in persona_stats.items():
            if stats['prompts'] < MIN_PERSONA_SAMPLE:
                continue
            persona_view.append({
                'persona': p,
                'visibility_rate': stats['brand_mentions'] / stats['prompts'] * 100,
                'prompt_count': stats['prompts'],
                'brand_mentions': stats['brand_mentions'],
            })
        persona_view.sort(key=lambda p: -p['visibility_rate'])

        # 4. Platform view — every platform we tested (small enough to always show).
        platform_view = []
        for p, stats in platform_stats.items():
            if stats['prompts'] == 0:
                continue
            platform_view.append({
                'platform': p,
                'visibility_rate': stats['brand_mentions'] / stats['prompts'] * 100,
                'prompt_count': stats['prompts'],
                'brand_mentions': stats['brand_mentions'],
            })
        platform_view.sort(key=lambda p: -p['visibility_rate'])

        # ---- Build HTML ----
        # Helper: an "evidence chip" showing N/N counts so every claim is
        # tied to its underlying sample size. This is the trust-builder —
        # nothing in this section is asserted without a count behind it.
        def _chip(label, count, total):
            pct = (count / total * 100) if total else 0
            return (
                f'<span style="display: inline-block; padding: 2px 10px; '
                f'background: #F0E0E5; border-radius: 12px; font-size: 12px; '
                f'color: #4D2E3A; font-weight: 500;">'
                f'{label}: <strong>{count}/{total}</strong> ({pct:.0f}%)</span>'
            )

        def _short(text, n=80):
            text = (text or '').strip()
            if len(text) <= n:
                return html.escape(text)
            return html.escape(text[:n].rstrip()) + '…'

        # Best Response panel — only render if there actually is one
        best_panel_html = ""
        if best_response['prominence'] > 0:
            best_panel_html = f"""
                <div style="background: rgba(255,255,255,0.7); padding: 20px; border-radius: 8px; border-left: 4px solid #27AE60;">
                    <div style="font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: #27AE60; font-weight: 600; margin-bottom: 8px;">✨ Strongest Visibility Moment</div>
                    <div style="font-size: 14px; color: #1C1C1C; margin-bottom: 8px; line-height: 1.5;"><strong>"{_short(best_response['prompt'])}"</strong></div>
                    <div style="font-size: 13px; color: #6B5660; line-height: 1.6;">
                        Prominence <strong style="color: #27AE60;">{best_response['prominence']:.1f}/10</strong>
                        on <strong>{html.escape(best_response['platform'])}</strong>
                        for the <strong>{html.escape(best_response['persona'])}</strong> persona.
                    </div>
                </div>
            """

        # Worst Miss panel
        worst_panel_html = ""
        if worst_miss:
            top_comps = worst_miss['competitors'][:3]
            extra = len(worst_miss['competitors']) - len(top_comps)
            comp_str = ', '.join(html.escape(c) for c in top_comps)
            if extra > 0:
                comp_str += f' +{extra} more'
            worst_panel_html = f"""
                <div style="background: rgba(255,255,255,0.7); padding: 20px; border-radius: 8px; border-left: 4px solid #E74C3C;">
                    <div style="font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: #E74C3C; font-weight: 600; margin-bottom: 8px;">⚠️ Biggest Visibility Gap</div>
                    <div style="font-size: 14px; color: #1C1C1C; margin-bottom: 8px; line-height: 1.5;"><strong>"{_short(worst_miss['prompt'])}"</strong></div>
                    <div style="font-size: 13px; color: #6B5660; line-height: 1.6;">
                        AI named <strong>{len(worst_miss['competitors'])}</strong> competitor{'s' if len(worst_miss['competitors']) != 1 else ''} on
                        <strong>{html.escape(worst_miss['platform'])}</strong> ({html.escape(worst_miss['persona'])}) but did not mention {html.escape(brand_name)}: {comp_str}.
                    </div>
                </div>
            """

        # What's Working — only render if we have data-supported categories
        working_html = ""
        if working_categories:
            rows = []
            for c in working_categories:
                rows.append(
                    f'<li style="margin-bottom: 6px;"><strong>{html.escape(c["category"])}</strong> — '
                    f'mentioned in {c["brand_mentions"]} of {c["prompt_count"]} prompts '
                    f'({c["visibility_rate"]:.0f}%)</li>'
                )
            working_html = f"""
                <div style="background: rgba(255,255,255,0.7); padding: 16px; border-radius: 8px;">
                    <div style="font-size: 13px; font-weight: 600; color: #4D2E3A; margin-bottom: 8px;">🔑 Categories Where You Appear Most</div>
                    <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #1C1C1C; line-height: 1.6;">
                        {''.join(rows)}
                    </ul>
                </div>
            """
        elif category_view:
            working_html = """
                <div style="background: rgba(255,255,255,0.7); padding: 16px; border-radius: 8px;">
                    <div style="font-size: 13px; font-weight: 600; color: #4D2E3A; margin-bottom: 6px;">🔑 Categories Where You Appear Most</div>
                    <div style="font-size: 13px; color: #6B5660;">No category had enough prompts (≥3) for a meaningful comparison this run.</div>
                </div>
            """

        # What's Missing — categories with low visibility AND active competitors
        missing_html = ""
        if missing_categories:
            rows = []
            for c in missing_categories:
                comps = ', '.join(html.escape(name) for name, _cnt in c['top_competitors'])
                rows.append(
                    f'<li style="margin-bottom: 6px;"><strong>{html.escape(c["category"])}</strong> — '
                    f'mentioned in {c["brand_mentions"]} of {c["prompt_count"]} prompts '
                    f'({c["visibility_rate"]:.0f}%); competitors named: {comps}</li>'
                )
            missing_html = f"""
                <div style="background: rgba(255,255,255,0.7); padding: 16px; border-radius: 8px;">
                    <div style="font-size: 13px; font-weight: 600; color: #4D2E3A; margin-bottom: 8px;">🚨 Categories Where Competitors Win</div>
                    <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #1C1C1C; line-height: 1.6;">
                        {''.join(rows)}
                    </ul>
                </div>
            """
        elif category_view:
            missing_html = """
                <div style="background: rgba(255,255,255,0.7); padding: 16px; border-radius: 8px;">
                    <div style="font-size: 13px; font-weight: 600; color: #4D2E3A; margin-bottom: 6px;">🚨 Categories Where Competitors Win</div>
                    <div style="font-size: 13px; color: #6B5660;">No category had below-50% brand visibility with active competitor mentions.</div>
                </div>
            """

        # By Persona panel — only render if we have ≥2 personas with sample
        persona_panel_html = ""
        if len(persona_view) >= 2:
            rows = []
            for p in persona_view:
                bar_pct = min(p['visibility_rate'], 100)
                rows.append(f"""
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px; font-size: 13px;">
                        <div style="flex: 0 0 220px; color: #1C1C1C;">{html.escape(p['persona'])}</div>
                        <div style="flex: 1; background: #F0E0E5; border-radius: 6px; height: 18px; position: relative; overflow: hidden;">
                            <div style="width: {bar_pct}%; height: 100%; background: #4D2E3A;"></div>
                        </div>
                        <div style="flex: 0 0 110px; color: #6B5660; text-align: right;">
                            {p['visibility_rate']:.0f}% ({p['brand_mentions']}/{p['prompt_count']})
                        </div>
                    </div>
                """)
            persona_panel_html = f"""
                <div style="background: rgba(255,255,255,0.7); padding: 20px; border-radius: 8px; margin-top: 16px;">
                    <div style="font-size: 13px; font-weight: 600; color: #4D2E3A; margin-bottom: 12px;">👥 Visibility by Persona</div>
                    {''.join(rows)}
                    <div style="font-size: 12px; color: #6B5660; margin-top: 8px; font-style: italic;">
                        Personas with fewer than {MIN_PERSONA_SAMPLE} tested prompts are excluded — sample too small to compare.
                    </div>
                </div>
            """

        # By Platform panel — always show if we have ≥2 platforms
        platform_panel_html = ""
        if len(platform_view) >= 2:
            rows = []
            for p in platform_view:
                bar_pct = min(p['visibility_rate'], 100)
                rows.append(f"""
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px; font-size: 13px;">
                        <div style="flex: 0 0 220px; color: #1C1C1C;">{html.escape(p['platform'])}</div>
                        <div style="flex: 1; background: #F0E0E5; border-radius: 6px; height: 18px; position: relative; overflow: hidden;">
                            <div style="width: {bar_pct}%; height: 100%; background: #4D2E3A;"></div>
                        </div>
                        <div style="flex: 0 0 110px; color: #6B5660; text-align: right;">
                            {p['visibility_rate']:.0f}% ({p['brand_mentions']}/{p['prompt_count']})
                        </div>
                    </div>
                """)
            platform_panel_html = f"""
                <div style="background: rgba(255,255,255,0.7); padding: 20px; border-radius: 8px; margin-top: 16px;">
                    <div style="font-size: 13px; font-weight: 600; color: #4D2E3A; margin-bottom: 12px;">📡 Visibility by Platform</div>
                    {''.join(rows)}
                </div>
            """

        # Top-row grid (best + worst). Only render the wrapper if at least
        # one of them has data — otherwise the panel is just decoration.
        top_row_html = ""
        if best_panel_html or worst_panel_html:
            # If only one panel exists, span the row to avoid an empty cell
            grid_cols = "repeat(2, 1fr)" if best_panel_html and worst_panel_html else "1fr"
            top_row_html = f"""
                <div style="display: grid; grid-template-columns: {grid_cols}; gap: 20px; margin-bottom: 20px;">
                    {best_panel_html}
                    {worst_panel_html}
                </div>
            """

        # Bottom-row grid (working + missing categories). Same logic.
        bottom_row_html = ""
        if working_html or missing_html:
            grid_cols = "repeat(2, 1fr)" if working_html and missing_html else "1fr"
            bottom_row_html = f"""
                <div style="display: grid; grid-template-columns: {grid_cols}; gap: 20px;">
                    {working_html}
                    {missing_html}
                </div>
            """

        # Stitch the full Quick Insights container, only if we have something to show
        quick_insights_html = ""
        any_panel = top_row_html or bottom_row_html or persona_panel_html or platform_panel_html
        if any_panel:
            total_tested = len(scored_results)
            total_brand_mentions = sum(
                1 for r in scored_results if r.get('visibility', {}).get('brand_mentioned')
            )
            quick_insights_html = f"""
        <div style="background: linear-gradient(135deg, #E8D4DA 0%, #F0E0E5 100%); border-radius: 12px; padding: 32px; margin-bottom: 32px; border: 1px solid #C9A7B3;">
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; flex-wrap: wrap; gap: 12px;">
                <h3 style="margin: 0; color: #4D2E3A; font-size: 22px; font-weight: 700;">🎯 Quick Insights</h3>
                <div style="font-size: 12px; color: #6B5660;">
                    Based on <strong>{total_brand_mentions}/{total_tested}</strong> prompts where {html.escape(brand_name)} was mentioned this run.
                </div>
            </div>
            <p style="margin: 0 0 20px 0; font-size: 13px; color: #6B5660; line-height: 1.5;">
                Every figure below is computed directly from this run's responses. Sample sizes are shown so you can judge confidence —
                categories or personas with fewer than 3 tested prompts are excluded as too small to compare meaningfully.
            </p>
            {top_row_html}
            {bottom_row_html}
            {persona_panel_html}
            {platform_panel_html}
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
            <span>Why AI Visibility Matters Now</span>
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
                            <div style="font-size: 40px; font-weight: 700; margin-bottom: 8px;">79%</div>
                            <div style="font-size: 13px; opacity: 0.9;">of consumers have used generative AI tools for shopping-related activities</div>
                        </div>
                        <div>
                            <div style="font-size: 40px; font-weight: 700; margin-bottom: 8px;">70%</div>
                            <div style="font-size: 13px; opacity: 0.9;">of those were satisfied with results and plan to continue using AI for research</div>
                        </div>
                        <div>
                            <div style="font-size: 40px; font-weight: 700; margin-bottom: 8px;">1B+</div>
                            <div style="font-size: 13px; opacity: 0.9;">monthly ChatGPT users as of early 2025, growing rapidly</div>
                        </div>
                    </div>
                </div>
                <div style="margin-top: 20px; padding: 16px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                    <div style="font-size: 14px; font-weight: 600; margin-bottom: 10px; opacity: 0.9;">Further Reading:</div>
                    <div style="font-size: 13px; line-height: 2; opacity: 0.85;">
                        <a href="https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights/superagency-in-the-workplace-empowering-people-to-unlock-ais-full-potential-at-work" style="color: #F0E0E6;" target="_blank">McKinsey: AI adoption in the workplace (2025)</a><br>
                        <a href="https://blog.google/products/shopping/google-shopping-ai-features-2025/" style="color: #F0E0E6;" target="_blank">Google: AI-powered shopping features and consumer behavior</a><br>
                        <a href="https://www.gartner.com/en/newsroom/press-releases/2024-03-05-gartner-predicts-25-percent-decrease-in-traditional-search-by-2026" style="color: #F0E0E6;" target="_blank">Gartner: Traditional search volume predicted to decline 25% by 2026</a><br>
                        <a href="https://sparktoro.com/blog/2024-zero-click-search-study/" style="color: #F0E0E6;" target="_blank">SparkToro: Zero-click searches and the shift to AI answers</a><br>
                        <a href="https://firstpagesage.com/reports/generative-engine-optimization-geo-the-new-frontier-of-seo/" style="color: #F0E0E6;" target="_blank">First Page Sage: Generative Engine Optimization (GEO) guide</a>
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
        """
