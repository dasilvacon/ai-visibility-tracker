"""
Visibility scorer for analyzing AI responses and detecting brand mentions.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse


class VisibilityScorer:
    """Analyzes AI responses to score brand visibility."""

    def __init__(self, brand_name: str, brand_aliases: Optional[List[str]] = None,
                 competitor_names: Optional[List[str]] = None,
                 known_sources: Optional[List[str]] = None,
                 industry_keywords: Optional[List[str]] = None):
        """
        Initialize the visibility scorer.

        Args:
            brand_name: Primary brand name to track
            brand_aliases: Alternative names/acronyms for the brand
            competitor_names: List of competitor brand names
            known_sources: List of known source domains/names relevant to this client's industry
            industry_keywords: List of industry-specific keywords for relevance scoring
        """
        self.brand_name = brand_name
        self.brand_aliases = brand_aliases or []
        self.competitor_names = competitor_names or []

        # Per-client known sources (no more hardcoded beauty/retail sites)
        self.known_sources = set(s.lower() for s in (known_sources or []))
        self.industry_keywords = [k.lower() for k in (industry_keywords or [])]

        # Create pattern variations for detection
        self.brand_patterns = self._create_patterns([brand_name] + self.brand_aliases)
        self.competitor_patterns = {
            comp: self._create_patterns([comp])
            for comp in self.competitor_names
        }

    def _create_patterns(self, names: List[str]) -> List[re.Pattern]:
        """
        Create regex patterns for name matching.

        Args:
            names: List of names to create patterns for

        Returns:
            List of compiled regex patterns
        """
        patterns = []
        for name in names:
            # Exact match with word boundaries
            pattern = r'\b' + re.escape(name) + r'\b'
            patterns.append(re.compile(pattern, re.IGNORECASE))
        return patterns

    def extract_sources(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Extract actual sources (domains, known sites) from AI response.
        Focus on URLs and known source names, filter out noise.
        Includes enriched context data for each source.

        Args:
            response_text: The AI's response text

        Returns:
            List of source dictionaries containing:
            - type: 'url', 'known_source', or 'attribution'
            - domain: extracted domain (e.g., 'ontario.ca')
            - full_url: complete URL if available
            - source_name: display name (e.g., 'Ontario')
            - context_snippet: ~200 chars surrounding the source mention
            - brand_in_context: True if brand appears in the same snippet
            - competitors_in_context: List of competitor names in the snippet
            - position_in_response: Float 0.0-1.0 indicating where in response
        """
        sources = []
        seen_domains = set()
        text_length = len(response_text) if response_text else 1

        def enrich_source(source_dict: Dict, match_position: int) -> Dict:
            """Add context enrichment to a source dict."""
            # Extract context snippet (~200 chars around match)
            start = max(0, match_position - 100)
            end = min(text_length, match_position + 100)
            snippet = response_text[start:end].strip()

            # Check if brand appears in context
            brand_in_context = False
            for pattern in self.brand_patterns:
                if pattern.search(snippet):
                    brand_in_context = True
                    break

            # Check which competitors appear in context
            competitors_in_context = []
            for comp_name, patterns in self.competitor_patterns.items():
                for pattern in patterns:
                    if pattern.search(snippet):
                        competitors_in_context.append(comp_name)
                        break

            # Calculate position in response (0.0 = start, 1.0 = end)
            position_in_response = match_position / text_length if text_length > 0 else 0.0

            source_dict['context_snippet'] = snippet
            source_dict['brand_in_context'] = brand_in_context
            source_dict['competitors_in_context'] = competitors_in_context
            source_dict['position_in_response'] = round(position_in_response, 3)

            return source_dict

        # PRIORITY 1: Extract URLs (most reliable)
        url_pattern = r'https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})(?:/[^\s]*)?'
        for match in re.finditer(url_pattern, response_text):
            domain = match.group(1).lower().strip()

            # Clean domain (remove trailing chars)
            domain = re.sub(r'[^a-z0-9.-].*', '', domain)

            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                source = {
                    'type': 'url',
                    'domain': domain,
                    'source_name': domain.split('.')[0].title(),
                    'full_url': match.group(0)
                }
                sources.append(enrich_source(source, match.start()))

        # PRIORITY 1.5: Bare domain mentions (e.g., "sephora.com", "temptalia.com")
        bare_domain_pattern = r'(?<!\w)([a-zA-Z0-9-]+\.(?:com|org|net|ca|co\.uk|com\.au|io|gov|edu))(?!\w)'
        for match in re.finditer(bare_domain_pattern, response_text):
            domain = match.group(1).lower().strip()
            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                source = {
                    'type': 'url',
                    'domain': domain,
                    'source_name': domain.split('.')[0].title(),
                    'full_url': f'https://{domain}'
                }
                sources.append(enrich_source(source, match.start()))

        # PRIORITY 2: Known sources (loaded per-client from brand_config.json)
        for source_name in self.known_sources:
            pattern = r'\b' + re.escape(source_name) + r'\b'
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                # Handle sources that already look like domains
                if '.' in source_name:
                    domain = source_name.lower()
                else:
                    domain = source_name.lower() + '.com'

                if domain not in seen_domains:
                    seen_domains.add(domain)
                    source = {
                        'type': 'known_source',
                        'domain': domain,
                        'source_name': source_name.split('.')[0].title() if '.' in source_name else source_name.title(),
                        'full_url': None
                    }
                    sources.append(enrich_source(source, match.start()))

        # PRIORITY 3: Expanded attribution patterns (multiple styles)
        attribution_patterns = [
            r'(?:According to|Per|From|As (?:reported|mentioned|noted|seen|featured|reviewed) (?:by|on|in))\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[,:.]',
            r'(?:recommended|featured|reviewed|listed|mentioned|covered|profiled|highlighted|discussed) (?:by|on|in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'(?:on|via|through|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,\s*(?:users?|people|reviewers?|customers?|experts?)',
            r'(?:sites?\s+like|platforms?\s+(?:like|such as|including))\s+([A-Z][a-z]+(?:(?:\s+[A-Z][a-z]+)|(?:\.[a-z]+))?)',
            r'(?:popular|trending|discussed|reviewed|rated)\s+on\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
            r'(?:check|visit|see|try|browse|explore)\s+([A-Z][a-z]+(?:\.[a-z]+)?)',
        ]

        # Known brand/source keywords to filter
        brand_keywords = set([b.lower() for b in self.brand_aliases + self.competitor_names])
        brand_keywords.add(self.brand_name.lower())
        noise_words = {
            'you', 'your', 'the', 'this', 'that', 'they', 'their', 'here', 'there',
            'offers', 'makes', 'provides', 'features', 'includes', 'contains',
            'products', 'items', 'options', 'choices', 'selections'
        }

        for pattern in attribution_patterns:
            for match in re.finditer(pattern, response_text):
                source_name = match.group(1).strip()
                source_lower = source_name.lower()

                # Filter out brand names and noise
                if source_lower in brand_keywords or source_lower in noise_words:
                    continue

                # Filter out if it's part of a brand name
                is_brand_part = any(source_lower in brand.lower() for brand in (self.brand_aliases + self.competitor_names))
                if is_brand_part:
                    continue

                # Validate source name
                if not self._is_valid_source(source_name):
                    continue

                # Handle sources that already look like domains
                if '.' in source_name:
                    domain = source_name.lower()
                else:
                    domain = source_lower.replace(' ', '') + '.com'

                if domain not in seen_domains and len(source_name) > 2:
                    seen_domains.add(domain)
                    source = {
                        'type': 'attribution',
                        'domain': domain,
                        'source_name': source_name,
                        'full_url': None
                    }
                    sources.append(enrich_source(source, match.start()))

        # Sort by type priority (URLs first, then known sources, then attributions)
        type_priority = {'url': 0, 'known_source': 1, 'attribution': 2}
        sources.sort(key=lambda x: type_priority.get(x['type'], 3))

        return sources

    def _is_valid_source(self, source_name: str) -> bool:
        """Check if extracted source is actually valid."""

        # Must be at least 3 characters
        if len(source_name) < 3:
            return False

        # Can't be all lowercase (likely a word, not a name)
        if source_name.islower():
            return False

        # Can't be a common pronoun/word
        common_words = {'You', 'Your', 'The', 'This', 'That', 'They', 'Their', 'Here', 'There'}
        if source_name in common_words:
            return False

        # Must contain at least one letter
        if not re.search(r'[a-zA-Z]', source_name):
            return False

        return True

    def score_response(self, response_text: str, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single AI response for brand visibility.

        Args:
            response_text: The AI's response text
            prompt_data: Dictionary with prompt metadata

        Returns:
            Dictionary with visibility scoring data
        """
        # Check brand mentions
        brand_mentioned, brand_positions = self._find_mentions(response_text, self.brand_patterns)

        # Check competitor mentions and calculate their prominence
        competitor_mentions = {}
        for comp_name, patterns in self.competitor_patterns.items():
            mentioned, positions = self._find_mentions(response_text, patterns)
            if mentioned:
                # Calculate prominence score for this competitor
                comp_prominence = self._calculate_competitor_prominence(
                    response_text, positions, brand_positions
                )
                competitor_mentions[comp_name] = {
                    'mentioned': True,
                    'positions': positions,
                    'count': len(positions),
                    'prominence_score': comp_prominence
                }

        # Calculate prominence score
        prominence_score = self._calculate_prominence(
            response_text,
            brand_mentioned,
            brand_positions,
            competitor_mentions
        )

        # Determine citation position
        citation_position = brand_positions[0] if brand_positions else None

        # Analyze sentiment/context around brand mention
        context = self._extract_context(response_text, brand_positions) if brand_mentioned else None

        # Extract sources/citations from response
        sources = self.extract_sources(response_text)

        return {
            'brand_mentioned': brand_mentioned,
            'brand_mention_count': len(brand_positions),
            'brand_positions': brand_positions,
            'prominence_score': prominence_score,
            'citation_position': citation_position,
            'competitors_mentioned': list(competitor_mentions.keys()),
            'competitor_details': competitor_mentions,
            'total_competitors_mentioned': len(competitor_mentions),
            'context_snippets': context,
            'response_length': len(response_text),
            'brand_density': len(brand_positions) / max(len(response_text.split()), 1) * 100,
            'sources': sources,
            'source_count': len(sources)
        }

    def _find_mentions(self, text: str, patterns: List[re.Pattern]) -> Tuple[bool, List[int]]:
        """
        Find all mentions of patterns in text.

        Args:
            text: Text to search
            patterns: List of regex patterns

        Returns:
            Tuple of (mentioned: bool, positions: List[int])
        """
        positions = []
        for pattern in patterns:
            matches = pattern.finditer(text)
            for match in matches:
                positions.append(match.start())

        return len(positions) > 0, sorted(positions)

    def _calculate_prominence(self, text: str, brand_mentioned: bool,
                             brand_positions: List[int],
                             competitor_mentions: Dict[str, Any]) -> float:
        """
        Calculate prominence score (0-10).

        Args:
            text: Response text
            brand_mentioned: Whether brand was mentioned
            brand_positions: Positions of brand mentions
            competitor_mentions: Dictionary of competitor mention data

        Returns:
            Prominence score from 0-10
        """
        if not brand_mentioned:
            return 0.0

        score = 0.0

        # Base score for being mentioned
        score += 3.0

        # Score based on position (earlier is better)
        first_position = brand_positions[0]
        text_length = len(text)
        if text_length > 0:
            relative_position = first_position / text_length
            if relative_position < 0.2:  # First 20% of response
                score += 4.0
            elif relative_position < 0.4:  # First 40%
                score += 2.5
            elif relative_position < 0.6:  # First 60%
                score += 1.5
            else:
                score += 0.5

        # Bonus for multiple mentions
        mention_count = len(brand_positions)
        if mention_count >= 3:
            score += 2.0
        elif mention_count == 2:
            score += 1.0

        # Penalty if competitors are mentioned before brand
        for comp_data in competitor_mentions.values():
            if comp_data['positions']:
                comp_first = comp_data['positions'][0]
                if comp_first < first_position:
                    score -= 1.5

        # Penalty if many competitors are mentioned
        if len(competitor_mentions) >= 3:
            score -= 1.0
        elif len(competitor_mentions) >= 2:
            score -= 0.5

        # Clamp to 0-10 range
        return max(0.0, min(10.0, score))

    def _calculate_competitor_prominence(self, text: str,
                                         competitor_positions: List[int],
                                         brand_positions: List[int]) -> float:
        """
        Calculate prominence score for a competitor (0-10).

        Args:
            text: Response text
            competitor_positions: Positions of competitor mentions
            brand_positions: Positions of brand mentions (for comparison)

        Returns:
            Prominence score from 0-10
        """
        if not competitor_positions:
            return 0.0

        score = 0.0

        # Base score for being mentioned
        score += 3.0

        # Score based on position (earlier is better)
        first_position = competitor_positions[0]
        text_length = len(text)
        if text_length > 0:
            relative_position = first_position / text_length
            if relative_position < 0.2:  # First 20% of response
                score += 4.0
            elif relative_position < 0.4:  # First 40%
                score += 2.5
            elif relative_position < 0.6:  # First 60%
                score += 1.5
            else:
                score += 0.5

        # Bonus for multiple mentions
        mention_count = len(competitor_positions)
        if mention_count >= 3:
            score += 2.0
        elif mention_count == 2:
            score += 1.0

        # Bonus if mentioned before brand (or brand not mentioned at all)
        if not brand_positions or first_position < brand_positions[0]:
            score += 1.0

        # Clamp to 0-10 range
        return max(0.0, min(10.0, score))

    def _extract_context(self, text: str, positions: List[int],
                        context_chars: int = 100) -> List[str]:
        """
        Extract context snippets around brand mentions.

        Args:
            text: Response text
            positions: Positions of brand mentions
            context_chars: Characters to extract on each side

        Returns:
            List of context snippets
        """
        snippets = []
        for pos in positions[:3]:  # Max 3 snippets
            start = max(0, pos - context_chars)
            end = min(len(text), pos + context_chars)
            snippet = text[start:end].strip()
            snippets.append(f"...{snippet}...")
        return snippets

    def score_all_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score all test results.

        Args:
            results: List of test result dictionaries

        Returns:
            List of results with visibility scores added
        """
        scored_results = []

        for result in results:
            response_text = result.get('response_text', '')
            metadata = result.get('metadata', {})
            platform = result.get('platform', '')

            # Handle Google AI Overview special cases
            if platform == 'google_ai_overview':
                if not metadata.get('has_ai_overview', False):
                    # No AI Overview shown for this query — valid data point
                    result_with_score = result.copy()
                    result_with_score['visibility'] = {
                        'brand_mentioned': False,
                        'brand_mention_count': 0,
                        'brand_positions': [],
                        'prominence_score': 0,
                        'citation_position': None,
                        'competitors_mentioned': [],
                        'competitor_details': {},
                        'total_competitors_mentioned': 0,
                        'context_snippets': None,
                        'response_length': 0,
                        'brand_density': 0,
                        'sources': [],
                        'source_count': 0,
                        'ai_overview_absent': True
                    }
                    scored_results.append(result_with_score)
                    continue
                elif not response_text:
                    continue

            elif not response_text:
                continue

            # Score this response
            visibility_score = self.score_response(response_text, result)

            # For AI Overviews, enrich sources from SerpAPI references
            if platform == 'google_ai_overview' and metadata.get('references'):
                ai_overview_sources = self._extract_ai_overview_sources(metadata['references'])
                visibility_score['sources'].extend(ai_overview_sources)
                visibility_score['source_count'] = len(visibility_score['sources'])
                # Check if any reference directly cites a brand domain
                visibility_score['ai_overview_brand_cited'] = any(
                    s.get('brand_in_context', False) for s in ai_overview_sources
                )

            # Add visibility data to result
            result_with_score = result.copy()
            result_with_score['visibility'] = visibility_score

            scored_results.append(result_with_score)

        return scored_results

    def _extract_ai_overview_sources(self, references: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert SerpAPI AI Overview references into our source format.

        Args:
            references: List of reference dicts from SerpAPI metadata

        Returns:
            List of source dicts in our standard format
        """
        sources = []
        for ref in references:
            domain = ref.get('domain', '')
            link = ref.get('link', '')
            title = ref.get('title', '')
            snippet = ref.get('snippet', '')

            # Check if brand appears in reference title or snippet
            brand_in_context = False
            for pattern in self.brand_patterns:
                if pattern.search(title) or pattern.search(snippet):
                    brand_in_context = True
                    break

            # Check which competitors appear in reference
            competitors_in_context = []
            for comp_name, patterns in self.competitor_patterns.items():
                for pattern in patterns:
                    if pattern.search(title) or pattern.search(snippet):
                        competitors_in_context.append(comp_name)
                        break

            sources.append({
                'type': 'ai_overview_reference',
                'domain': domain,
                'full_url': link,
                'source_name': title or domain,
                'context_snippet': snippet[:200] if snippet else '',
                'brand_in_context': brand_in_context,
                'competitors_in_context': competitors_in_context,
                'position_in_response': 0.0  # References are top-level, no position
            })

        return sources

    def get_visibility_summary(self, scored_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from scored results.

        Args:
            scored_results: List of results with visibility scores

        Returns:
            Dictionary with summary statistics
        """
        total_prompts = len(scored_results)
        if total_prompts == 0:
            return {'error': 'No results to analyze'}

        # Count mentions
        brand_mentions = sum(1 for r in scored_results
                            if r.get('visibility', {}).get('brand_mentioned', False))

        # Average prominence
        prominence_scores = [r.get('visibility', {}).get('prominence_score', 0)
                           for r in scored_results]
        avg_prominence = sum(prominence_scores) / len(prominence_scores) if prominence_scores else 0

        # Competitor analysis
        all_competitors = set()
        competitor_mention_count = 0
        for r in scored_results:
            competitors = r.get('visibility', {}).get('competitors_mentioned', [])
            all_competitors.update(competitors)
            if competitors:
                competitor_mention_count += 1

        # Position analysis
        positions = []
        for r in scored_results:
            pos = r.get('visibility', {}).get('citation_position')
            if pos is not None:
                positions.append(pos)

        avg_position = sum(positions) / len(positions) if positions else None

        return {
            'total_prompts_tested': total_prompts,
            'brand_mentions': brand_mentions,
            'brand_visibility_rate': brand_mentions / total_prompts * 100,
            'average_prominence_score': round(avg_prominence, 2),
            'competitors_encountered': list(all_competitors),
            'competitor_mention_rate': competitor_mention_count / total_prompts * 100,
            'average_citation_position': round(avg_position, 0) if avg_position else None,
            'high_prominence_count': sum(1 for s in prominence_scores if s >= 7),
            'medium_prominence_count': sum(1 for s in prominence_scores if 4 <= s < 7),
            'low_prominence_count': sum(1 for s in prominence_scores if 0 < s < 4),
            'no_mention_count': sum(1 for s in prominence_scores if s == 0)
        }
