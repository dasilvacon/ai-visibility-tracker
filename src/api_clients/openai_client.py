"""
OpenAI API client implementation.

Uses the Responses API with the web_search tool switched on, so the answer
is built the way ChatGPT builds it: the model can search the web and the
response carries the links it used.

Measurement Standard (docs/MEASUREMENT_STANDARD.md), check 1: the saved
response must include the links the AI used. This client saves them in
metadata['cited_urls'] (links cited in the answer) and
metadata['sources_consulted'] (every page the search read).
"""

from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from .base_client import BaseAPIClient


class OpenAIClient(BaseAPIClient):
    """OpenAI API client for testing prompts, with web search on."""

    # Web search answers take longer than plain completions.
    min_timeout_seconds = 180
    min_output_tokens = 8192

    def _get_platform_name(self) -> str:
        """Return the platform name."""
        return 'openai'

    def send_prompt(self, prompt: str, temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a prompt to OpenAI with web search on and get the response.

        Temperature is left at the model default on purpose: the consumer
        product does not expose it, and newer models reject other values.

        Returns:
            Dictionary with response data, cited links and search queries
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            testing = self.config.get('testing', {})
            max_tokens = max(int(max_tokens or testing.get('max_tokens', 1000)), self.min_output_tokens)
            timeout = max(int(testing.get('timeout_seconds', 30)), self.min_timeout_seconds)

            response = client.responses.create(
                model=self.model,
                input=prompt,
                tools=[{"type": "web_search"}],
                include=["web_search_call.action.sources"],
                max_output_tokens=max_tokens,
                timeout=timeout,
            )

            text_parts: List[str] = []
            cited_urls: List[Dict[str, Any]] = []
            sources_consulted: List[Dict[str, Any]] = []
            search_queries: List[str] = []
            seen_cited = set()
            seen_sources = set()
            search_calls = 0

            for item in (getattr(response, 'output', None) or []):
                item_type = getattr(item, 'type', '')
                if item_type == 'web_search_call':
                    search_calls += 1
                    action = getattr(item, 'action', None)
                    if action is not None:
                        query = getattr(action, 'query', None)
                        if query:
                            search_queries.append(query)
                        for q in (getattr(action, 'queries', None) or []):
                            if q and q not in search_queries:
                                search_queries.append(q)
                        for src in (getattr(action, 'sources', None) or []):
                            url = getattr(src, 'url', None) or (src.get('url') if isinstance(src, dict) else None)
                            if url and url not in seen_sources:
                                seen_sources.add(url)
                                sources_consulted.append({
                                    'url': url,
                                    'domain': self._extract_domain(url),
                                })
                elif item_type == 'message':
                    for part in (getattr(item, 'content', None) or []):
                        if getattr(part, 'type', '') != 'output_text':
                            continue
                        text_parts.append(getattr(part, 'text', '') or '')
                        for ann in (getattr(part, 'annotations', None) or []):
                            if getattr(ann, 'type', '') != 'url_citation':
                                continue
                            url = getattr(ann, 'url', '') or ''
                            if not url or url in seen_cited:
                                continue
                            seen_cited.add(url)
                            cited_urls.append({
                                'url': url,
                                'domain': self._extract_domain(url),
                                'title': getattr(ann, 'title', '') or '',
                                'source_type': 'api_citation',
                            })

            response_text = ''.join(text_parts) or (getattr(response, 'output_text', '') or '')
            usage = getattr(response, 'usage', None)

            return {
                'response_text': response_text,
                'success': bool(response_text),
                'error': None if response_text else 'OpenAI returned no answer text',
                'metadata': {
                    'tokens_used': getattr(usage, 'total_tokens', None) if usage else None,
                    'prompt_tokens': getattr(usage, 'input_tokens', None) if usage else None,
                    'completion_tokens': getattr(usage, 'output_tokens', None) if usage else None,
                    'finish_reason': getattr(response, 'status', None),
                    'temperature': None,
                    'max_tokens': max_tokens,
                    'web_search_enabled': True,
                    'web_search_used': search_calls > 0,
                    'web_search_calls': search_calls,
                    'search_queries': search_queries,
                    'cited_urls': cited_urls,
                    'citation_count': len(cited_urls),
                    'sources_consulted': sources_consulted,
                }
            }

        except ImportError as e:
            return {
                'response_text': '',
                'success': False,
                'error': f'OpenAI library not installed: {str(e)}',
                'metadata': {}
            }
        except Exception as e:
            return {
                'response_text': '',
                'success': False,
                'error': f'OpenAI API error: {str(e)}',
                'metadata': {}
            }

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from a URL, stripping www. prefix."""
        try:
            return urlparse(url).netloc.replace('www.', '')
        except Exception:
            return ''
