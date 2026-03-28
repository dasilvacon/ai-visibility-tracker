"""
Competitor intelligence engine for evidence-based recommendations.

Mines test result data to build competitor profiles:
- Which competitors win the most prompts (and which specific prompts)
- What URLs/pages get cited by AI platforms
- What content strategies those pages represent
- How to tie this to research-backed insights

This replaces generic "create tutorial content" recommendations with:
"Alzheimer Society wins 12 prompts with their resource hub at alzheimer.ca/support.
Their FAQ structure and downloadable toolkits make them the go-to citation.
Here are the exact prompts you're losing, and what research says works."
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import re


# ── Research-backed evidence for AI visibility strategies ────────────
# These are grounded in real patterns from how LLMs select sources.
STRATEGY_EVIDENCE = {
    'resource_hub': {
        'name': 'Resource Hub / Landing Page',
        'description': 'A dedicated resource page that aggregates tools, guides, and links on a specific topic.',
        'why_it_works': 'AI platforms cite resource hubs because they provide comprehensive, structured answers in one place. LLMs prefer pages that directly answer multiple related questions without requiring users to navigate elsewhere.',
        'research_note': 'Pages with high topical authority (covering a topic cluster comprehensively) are 3-4x more likely to be cited by AI assistants than isolated blog posts.',
        'action_template': 'Create a dedicated {topic} resource page that consolidates your guides, tools, FAQs, and links into one authoritative hub.',
    },
    'faq_structured': {
        'name': 'Structured FAQ Content',
        'description': 'Well-organized Q&A content with clear questions and direct answers.',
        'why_it_works': 'AI platforms extract Q&A pairs directly. When your FAQ matches the exact question a user asks, you become the cited source. FAQ schema markup makes this even more reliable.',
        'research_note': 'Pages with FAQPage schema are significantly more likely to appear in AI-generated answers because they provide pre-structured question-answer pairs that LLMs can directly reference.',
        'action_template': 'Build a comprehensive FAQ page covering the top questions your audience asks about {topic}. Use clear question headings and concise 2-3 sentence answers.',
    },
    'how_to_guide': {
        'name': 'Step-by-Step Guide',
        'description': 'Detailed how-to content with numbered steps, visuals, and expected outcomes.',
        'why_it_works': 'When users ask "how to..." questions, AI platforms look for structured step-by-step content. Pages with HowTo schema and clear numbered instructions get prioritized.',
        'research_note': 'How-to content with structured markup (HowTo schema) is the most commonly cited content type for instructional queries across ChatGPT, Perplexity, and Google AI Overviews.',
        'action_template': 'Create a detailed step-by-step guide for {topic} with numbered instructions, expected outcomes, and troubleshooting tips.',
    },
    'comparison_page': {
        'name': 'Comparison / Alternative Page',
        'description': 'Content that directly compares options, services, or organizations.',
        'why_it_works': 'When users ask "X vs Y" or "alternatives to X", AI platforms need comparison data. Having your own comparison content means you control how you are positioned.',
        'research_note': 'Brands that create their own comparison content are 2x more likely to be mentioned favorably in AI comparison responses than brands that leave this to third parties.',
        'action_template': 'Create a comparison page that honestly positions your {topic} against alternatives, highlighting your unique strengths.',
    },
    'downloadable_tool': {
        'name': 'Downloadable Tool / Template / Checklist',
        'description': 'Practical tools like PDFs, checklists, templates, or calculators that users can use immediately.',
        'why_it_works': 'AI platforms recommend actionable resources. When a competitor offers a downloadable checklist and you do not, AI will cite them because they provide a concrete next step.',
        'research_note': 'Pages offering downloadable resources (checklists, templates, worksheets) receive higher engagement signals which correlate with increased AI citation rates.',
        'action_template': 'Create a downloadable {topic} toolkit (checklist, template, or worksheet) that gives users an immediate actionable resource.',
    },
    'local_specific': {
        'name': 'Location-Specific Content',
        'description': 'Content tailored to a specific geographic area with local details.',
        'why_it_works': 'When users ask about services "in Ontario" or "near me", AI platforms strongly prefer locally-specific content over generic national pages. Local pages with specific program names, eligibility, and contact info get cited.',
        'research_note': 'Geo-specific content pages are cited at much higher rates than generic pages for location-based queries, especially when they include specific local program names and eligibility details.',
        'action_template': 'Create Ontario-specific (or region-specific) content about {topic} that includes local program names, eligibility criteria, and direct contact information.',
    },
    'program_page': {
        'name': 'Dedicated Program / Service Page',
        'description': 'A standalone page for a specific program or service with full details.',
        'why_it_works': 'AI platforms cite specific program pages over general "about us" pages. When a competitor has a dedicated page for each program, AI can point users directly to relevant content.',
        'research_note': 'Organizations with dedicated landing pages per program or service receive significantly more AI citations than those with a single services overview page.',
        'action_template': 'Create a dedicated page for your {topic} program with eligibility, how to access it, what to expect, and testimonials.',
    },
}


class CompetitorResearcher:
    """
    Mines test results to build competitor intelligence profiles
    and generate evidence-based recommendations.
    """

    def __init__(self, brand_name: str, brand_config: Optional[Dict[str, Any]] = None):
        """
        Args:
            brand_name: The client's brand name
            brand_config: Full brand config dict for context
        """
        self.brand_name = brand_name
        self.brand_config = brand_config or {}

        # Extract known competitor info from brand_config
        competitors_section = self.brand_config.get('competitors', {})
        if isinstance(competitors_section, dict):
            self.known_competitors = {
                c.get('name', ''): c.get('website', '')
                for c in competitors_section.get('expected', [])
            }
            self.category_overrides = competitors_section.get('category_overrides', {})
        else:
            self.known_competitors = {}
            self.category_overrides = {}

    def analyze_competitors(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Full competitor intelligence analysis.

        Returns:
            Dict with:
            - competitor_profiles: Top competitors with full intelligence
            - evidence_recommendations: Top 3 evidence-based recommendations
            - competitor_ranking: All competitors ranked
        """
        profiles = self._build_competitor_profiles(scored_results)
        ranking = self._rank_competitors(profiles)

        # Take top 3 competitors
        top_3 = ranking[:3]
        top_profiles = {name: profiles[name] for name in top_3 if name in profiles}

        # Generate evidence-based recommendations
        recommendations = self._generate_evidence_recommendations(
            top_profiles, scored_results
        )

        return {
            'competitor_profiles': top_profiles,
            'competitor_ranking': ranking,
            'evidence_recommendations': recommendations,
            'total_competitors_found': len(profiles),
        }

    def _build_competitor_profiles(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Dict]:
        """
        Build detailed profile for each competitor from test results.

        For each competitor, tracks:
        - Total prompts they appear in (and which ones)
        - Average prominence score
        - Which domains/URLs get cited alongside them
        - Which personas and topics they dominate
        """
        profiles = defaultdict(lambda: {
            'mention_count': 0,
            'total_prominence': 0,
            'prompts_won': [],        # Prompts where they appear and brand doesn't
            'prompts_shared': [],      # Prompts where both appear
            'cited_domains': Counter(),  # Domains cited when this competitor appears
            'cited_urls': [],           # Full URLs cited
            'personas_dominated': Counter(),
            'intents_dominated': Counter(),
            'categories_dominated': Counter(),
            'topics': Counter(),        # Keywords/topics they win
        })

        for result in scored_results:
            visibility = result.get('visibility', {})
            metadata = result.get('metadata', {})
            prompt_text = result.get('prompt_text', '')
            brand_mentioned = visibility.get('brand_mentioned', False)
            competitors = visibility.get('competitors_mentioned', [])
            competitor_details = visibility.get('competitor_details', {})
            sources = visibility.get('sources', [])

            for comp_name in competitors:
                profile = profiles[comp_name]
                profile['mention_count'] += 1

                # Get prominence for this competitor
                comp_detail = competitor_details.get(comp_name, {})
                prominence = comp_detail.get('prominence_score', 0)
                profile['total_prominence'] += prominence

                # Classify as "won" (brand absent) or "shared" (both present)
                prompt_entry = {
                    'prompt': prompt_text,
                    'prominence': prominence,
                    'persona': metadata.get('persona', 'Unknown'),
                    'intent': metadata.get('intent_type', 'Unknown'),
                    'category': metadata.get('category', 'Unknown'),
                }

                if not brand_mentioned:
                    profile['prompts_won'].append(prompt_entry)
                else:
                    profile['prompts_shared'].append(prompt_entry)

                # Track which domains are cited in responses where this competitor wins
                if not brand_mentioned:
                    for source in sources:
                        domain = source.get('domain', '')
                        if domain:
                            profile['cited_domains'][domain] += 1
                        full_url = source.get('full_url', '')
                        if full_url:
                            profile['cited_urls'].append(full_url)

                    # Track persona/intent/category dominance
                    profile['personas_dominated'][metadata.get('persona', 'Unknown')] += 1
                    profile['intents_dominated'][metadata.get('intent_type', 'Unknown')] += 1
                    profile['categories_dominated'][metadata.get('category', 'Unknown')] += 1

        # Finalize profiles
        for name, profile in profiles.items():
            count = profile['mention_count']
            profile['avg_prominence'] = round(
                profile['total_prominence'] / count, 1
            ) if count > 0 else 0
            profile['win_count'] = len(profile['prompts_won'])
            profile['website'] = self.known_competitors.get(name, '')
            profile['category'] = self.category_overrides.get(name, 'competitor')

            # Deduplicate cited URLs
            profile['cited_urls'] = list(dict.fromkeys(profile['cited_urls']))[:20]

            # Get top cited domains (exclude generic ones)
            generic_domains = {'google.com', 'youtube.com', 'facebook.com', 'twitter.com', 'linkedin.com', 'reddit.com'}
            profile['top_cited_domains'] = [
                (domain, count) for domain, count in profile['cited_domains'].most_common(10)
                if domain not in generic_domains
            ][:5]

        return dict(profiles)

    def _rank_competitors(self, profiles: Dict[str, Dict]) -> List[str]:
        """
        Rank competitors by threat level.

        Scoring: win_count * 3 + mention_count + avg_prominence * 2
        (Competitors who win where brand is absent are the biggest threats)
        """
        scored = []
        for name, profile in profiles.items():
            threat_score = (
                profile['win_count'] * 3 +
                profile['mention_count'] +
                profile['avg_prominence'] * 2
            )
            scored.append((name, threat_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in scored]

    def _infer_content_strategy(self, profile: Dict) -> List[Dict[str, Any]]:
        """
        Infer what content strategies a competitor is using based on
        the domains/URLs they get cited for and the types of queries they win.

        Returns list of strategy dicts with evidence.
        """
        strategies = []
        prompts_won = profile.get('prompts_won', [])
        cited_domains = profile.get('top_cited_domains', [])
        cited_urls = profile.get('cited_urls', [])
        intents = profile.get('intents_dominated', Counter())
        categories = profile.get('categories_dominated', Counter())

        # Analyze URLs for content patterns
        url_text = ' '.join(cited_urls).lower()
        prompt_text = ' '.join(p['prompt'] for p in prompts_won).lower()

        # Check for FAQ patterns
        faq_signals = sum(1 for p in prompts_won if any(
            w in p['prompt'].lower() for w in ['what is', 'how does', 'can i', 'where', 'who', 'when']
        ))
        if faq_signals >= 3 or 'faq' in url_text or 'questions' in url_text:
            strategies.append({
                'strategy_key': 'faq_structured',
                'evidence': f"Wins {faq_signals} question-based queries",
                'prompt_count': faq_signals,
            })

        # Check for how-to/guide patterns
        howto_signals = sum(1 for p in prompts_won if any(
            w in p['prompt'].lower() for w in ['how to', 'steps', 'guide', 'tutorial', 'learn']
        ))
        if howto_signals >= 2 or intents.get('how_to', 0) >= 2:
            strategies.append({
                'strategy_key': 'how_to_guide',
                'evidence': f"Wins {howto_signals} how-to queries",
                'prompt_count': howto_signals,
            })

        # Check for resource hub patterns
        resource_signals = any(w in url_text for w in ['resource', 'support', 'help', 'toolkit', 'guide'])
        if resource_signals or len(cited_domains) >= 2:
            strategies.append({
                'strategy_key': 'resource_hub',
                'evidence': f"Cited from {len(cited_domains)} different pages/domains",
                'prompt_count': profile['win_count'],
            })

        # Check for comparison patterns
        comparison_signals = sum(1 for p in prompts_won if any(
            w in p['prompt'].lower() for w in ['vs', 'compare', 'difference', 'or', 'alternative', 'better']
        ))
        if comparison_signals >= 2 or intents.get('comparison', 0) >= 2:
            strategies.append({
                'strategy_key': 'comparison_page',
                'evidence': f"Wins {comparison_signals} comparison queries",
                'prompt_count': comparison_signals,
            })

        # Check for downloadable tool patterns
        tool_signals = any(w in url_text for w in ['download', 'pdf', 'checklist', 'template', 'worksheet', 'tool'])
        tool_prompt_signals = sum(1 for p in prompts_won if any(
            w in p['prompt'].lower() for w in ['checklist', 'template', 'tool', 'pdf', 'download', 'form', 'worksheet']
        ))
        if tool_signals or tool_prompt_signals >= 2:
            strategies.append({
                'strategy_key': 'downloadable_tool',
                'evidence': f"Cited for {tool_prompt_signals} tool/resource queries",
                'prompt_count': tool_prompt_signals,
            })

        # Check for location-specific patterns
        local_signals = sum(1 for p in prompts_won if any(
            w in p['prompt'].lower() for w in ['ontario', 'near me', 'in my area', 'local', 'canada', 'toronto']
        ))
        if local_signals >= 3:
            strategies.append({
                'strategy_key': 'local_specific',
                'evidence': f"Wins {local_signals} location-specific queries",
                'prompt_count': local_signals,
            })

        # Check for program/service page patterns
        program_signals = any(w in url_text for w in ['program', 'service', 'about', 'what-we-do'])
        if program_signals or categories.get('business', 0) >= 3:
            strategies.append({
                'strategy_key': 'program_page',
                'evidence': f"Cited for specific program/service pages",
                'prompt_count': profile['win_count'],
            })

        # Sort by prompt_count (most impactful strategies first)
        strategies.sort(key=lambda s: s['prompt_count'], reverse=True)

        return strategies

    def _generate_evidence_recommendations(
        self,
        top_profiles: Dict[str, Dict],
        scored_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate the top 3 evidence-based, competitor-driven recommendations.

        Each recommendation is structured as:
        - competitor: Who is doing this well
        - what_they_do: What strategy they're using (with evidence)
        - prompts_affected: Exact prompts where the client is losing
        - why_it_matters: Research-backed insight
        - what_to_do: Specific action for the client
        - impact: How many prompts this could recover
        """
        all_candidates = []

        for comp_name, profile in top_profiles.items():
            strategies = self._infer_content_strategy(profile)

            for strategy in strategies[:2]:  # Top 2 strategies per competitor
                strategy_key = strategy['strategy_key']
                evidence_data = STRATEGY_EVIDENCE.get(strategy_key, {})

                if not evidence_data:
                    continue

                # Get the prompts this affects (deduplicated)
                prompts_won = profile.get('prompts_won', [])

                # Filter to prompts relevant to this strategy
                relevant_prompts = self._filter_prompts_for_strategy(
                    prompts_won, strategy_key
                )
                if not relevant_prompts:
                    relevant_prompts = prompts_won[:5]

                # Deduplicate prompt texts
                prompt_texts = list(dict.fromkeys(
                    p['prompt'] for p in relevant_prompts
                ))[:5]

                # Get the top persona affected
                persona_counts = Counter(p['persona'] for p in relevant_prompts)
                top_persona = persona_counts.most_common(1)[0][0] if persona_counts else 'Unknown'

                # Get cited pages for this competitor
                cited_pages = profile.get('top_cited_domains', [])
                website = profile.get('website', '')

                # Determine the topic from the most common keywords in affected prompts
                topic = self._extract_topic_from_prompts(relevant_prompts)

                all_candidates.append({
                    'competitor': comp_name,
                    'competitor_website': website,
                    'competitor_cited_pages': cited_pages,
                    'strategy': evidence_data.get('name', strategy_key),
                    'strategy_key': strategy_key,
                    'what_they_do': (
                        f"{comp_name} appears in {profile['win_count']} prompts where you don't. "
                        f"{strategy['evidence']}. "
                        f"Their content is being cited by AI platforms because: {evidence_data.get('why_it_works', '')}"
                    ),
                    'prompts_affected': prompt_texts,
                    'prompts_affected_count': len(relevant_prompts),
                    'total_prompts_won_by_competitor': profile['win_count'],
                    'top_persona_affected': top_persona,
                    'why_it_matters': evidence_data.get('research_note', ''),
                    'what_to_do': evidence_data.get('action_template', '').format(topic=topic),
                    'impact_estimate': f"Could recover up to {min(len(relevant_prompts), profile['win_count'])} prompts currently won by {comp_name}",
                    'priority': 'HIGH' if profile['win_count'] >= 5 else 'MEDIUM',
                    'sort_score': profile['win_count'] * 2 + strategy['prompt_count'],
                })

        # Sort by impact and deduplicate strategies
        all_candidates.sort(key=lambda c: c['sort_score'], reverse=True)

        # Deduplicate: don't repeat the same strategy type
        seen_strategies = set()
        final_recommendations = []
        for candidate in all_candidates:
            key = candidate['strategy_key']
            if key not in seen_strategies:
                seen_strategies.add(key)
                final_recommendations.append(candidate)
            if len(final_recommendations) >= 3:
                break

        # If we have < 3, allow duplicate strategies from different competitors
        if len(final_recommendations) < 3:
            for candidate in all_candidates:
                if candidate not in final_recommendations:
                    final_recommendations.append(candidate)
                if len(final_recommendations) >= 3:
                    break

        return final_recommendations[:3]

    def _filter_prompts_for_strategy(
        self, prompts: List[Dict], strategy_key: str
    ) -> List[Dict]:
        """Filter prompts to those most relevant to a specific strategy."""
        filters = {
            'faq_structured': ['what', 'how does', 'can i', 'where', 'who', 'when', 'is there'],
            'how_to_guide': ['how to', 'steps', 'guide', 'learn', 'start'],
            'comparison_page': ['vs', 'compare', 'difference', 'or', 'alternative', 'better'],
            'downloadable_tool': ['checklist', 'template', 'tool', 'pdf', 'download', 'form'],
            'local_specific': ['ontario', 'near me', 'local', 'canada', 'toronto', 'in my area'],
            'resource_hub': [],  # Broad — all prompts qualify
            'program_page': [],  # Broad — all prompts qualify
        }

        keywords = filters.get(strategy_key, [])
        if not keywords:
            return prompts[:5]

        filtered = [
            p for p in prompts
            if any(kw in p['prompt'].lower() for kw in keywords)
        ]
        return filtered[:5] if filtered else prompts[:5]

    def _extract_topic_from_prompts(self, prompts: List[Dict]) -> str:
        """Extract the most common topic/theme from a list of prompts."""
        if not prompts:
            return "your key topics"

        # Simple approach: find the most common meaningful 2-3 word phrases
        all_text = ' '.join(p['prompt'] for p in prompts).lower()

        # Remove common filler words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'shall',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'about', 'that', 'this', 'it', 'its', 'my',
            'me', 'i', 'we', 'you', 'they', 'he', 'she', 'what', 'how',
            'where', 'when', 'who', 'which', 'there', 'just', 'and',
            'or', 'but', 'not', 'no', 'if', 'so', 'any', 'all',
            'best', 'top', 'find', 'need', 'help', 'looking', 'get',
        }

        words = [w for w in re.findall(r'\b[a-z]+\b', all_text) if w not in stop_words and len(w) > 2]
        if not words:
            return "your key topics"

        # Get most common words and build a topic phrase
        common = Counter(words).most_common(3)
        topic = ' '.join(w for w, _ in common)
        return topic
