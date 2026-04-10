"""
Google Gemini API client implementation.

Gemini supports Google Search grounding, which returns structured
citation data (grounding_metadata) with source URLs, titles, and
text-to-source mappings. This client captures that data for the
Sources & Citations report tab.

IMPORTANT: The grounding_metadata also contains `web_search_queries` —
the actual sub-queries Google Search ran to build the response. This is
real fan-out data: when a user asks a broad question, Google decomposes
it into 8-12 specific sub-queries. Capturing these gives us ground-truth
data about how AI engines actually search for information.
"""

from typing import Dict, Any, Optional
from urllib.parse import urlparse
from .base_client import BaseAPIClient


class GeminiClient(BaseAPIClient):
    """Google Gemini API client for testing prompts."""

    def _get_platform_name(self) -> str:
        """Return the platform name."""
        return 'gemini'

    def send_prompt(self, prompt: str, temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a prompt to Google Gemini with Google Search grounding enabled.

        Grounding gives Gemini access to live web data and returns structured
        citation metadata showing which sources informed the response.

        Args:
            prompt: The prompt text to send
            temperature: Temperature setting for response generation
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with response data including grounding citations
        """
        try:
            from google import genai
            from google.genai import types

            # Initialize client
            client = genai.Client(api_key=self.api_key)

            temperature = temperature or self.config.get('testing', {}).get('default_temperature', 0.7)
            max_tokens = max_tokens or self.config.get('testing', {}).get('max_tokens', 1000)
            timeout = self.config.get('testing', {}).get('timeout_seconds', 30)

            # Enable Google Search grounding for citation data
            google_search_tool = types.Tool(
                google_search=types.GoogleSearch()
            )

            # Generate response with grounding enabled
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    tools=[google_search_tool],
                    http_options={'timeout': timeout * 1000}  # milliseconds
                )
            )

            # Extract response text
            response_text = response.text if hasattr(response, 'text') else ''

            # Get token counts if available
            tokens_used = None
            prompt_tokens = None
            completion_tokens = None

            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                prompt_tokens = getattr(usage, 'prompt_token_count', None)
                completion_tokens = getattr(usage, 'candidates_token_count', None)
                tokens_used = getattr(usage, 'total_token_count', None)

            # Extract grounding metadata (citations from Google Search)
            cited_urls = []
            grounding_chunks = []
            grounding_supports = []
            web_search_queries = []  # Fan-out: the actual sub-queries Google ran

            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                grounding_meta = getattr(candidate, 'grounding_metadata', None)

                if grounding_meta:
                    # ── Fan-out queries ─────────────────────────────────
                    # These are the REAL sub-queries Google Search executed
                    # to build the grounded response. This is ground-truth
                    # fan-out data — the exact decomposition Google used.
                    raw_queries = getattr(grounding_meta, 'web_search_queries', []) or []
                    web_search_queries = [q for q in raw_queries if q]

                    # Extract grounding chunks (the actual sources)
                    raw_chunks = getattr(grounding_meta, 'grounding_chunks', []) or []
                    seen_domains = set()

                    for chunk in raw_chunks:
                        web = getattr(chunk, 'web', None)
                        if web:
                            url = getattr(web, 'uri', '') or ''
                            title = getattr(web, 'title', '') or ''
                            domain = self._extract_domain(url)

                            if url:
                                cited_urls.append({
                                    'url': url,
                                    'domain': domain,
                                    'title': title,
                                    'source_type': 'grounding'
                                })
                                grounding_chunks.append({
                                    'url': url,
                                    'domain': domain,
                                    'title': title
                                })
                                seen_domains.add(domain)

                    # Extract grounding supports (text-to-source mapping)
                    raw_supports = getattr(grounding_meta, 'grounding_supports', []) or []
                    for support in raw_supports:
                        segment = getattr(support, 'segment', None)
                        chunk_indices = getattr(support, 'grounding_chunk_indices', []) or []
                        confidence = getattr(support, 'confidence_scores', []) or []

                        if segment:
                            grounding_supports.append({
                                'text': getattr(segment, 'text', ''),
                                'start_index': getattr(segment, 'start_index', 0),
                                'end_index': getattr(segment, 'end_index', 0),
                                'chunk_indices': list(chunk_indices),
                                'confidence': [round(c, 3) for c in confidence] if confidence else []
                            })

            return {
                'response_text': response_text,
                'success': True,
                'error': None,
                'metadata': {
                    'tokens_used': tokens_used,
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'cited_urls': cited_urls,
                    'citation_count': len(cited_urls),
                    'grounding_chunks': grounding_chunks,
                    'grounding_supports': grounding_supports,
                    'web_search_queries': web_search_queries,
                    'fanout_query_count': len(web_search_queries)
                }
            }

        except ImportError as e:
            return {
                'response_text': '',
                'success': False,
                'error': f'Google Genai library not installed: {str(e)}. Install with: pip install google-genai',
                'metadata': {}
            }
        except Exception as e:
            return {
                'response_text': '',
                'success': False,
                'error': f'Gemini API error: {str(e)}',
                'metadata': {}
            }

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from a URL, stripping www. prefix."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except Exception:
            return ''
