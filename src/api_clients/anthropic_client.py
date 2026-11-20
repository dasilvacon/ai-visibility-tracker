"""
Anthropic Claude API client implementation.

Calls the Messages API with the web search tool switched on, so Claude can
search the web and the response carries the links it used.

Measurement Standard (docs/MEASUREMENT_STANDARD.md), check 1: the saved
response must include the links the AI used. This client saves them in
metadata['cited_urls'] (links cited in the answer) and
metadata['sources_consulted'] (every search result Claude was given).
"""

from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from .base_client import BaseAPIClient


class AnthropicClient(BaseAPIClient):
    """Anthropic Claude API client for testing prompts, with web search on."""

    # Web search answers take longer than plain completions.
    min_timeout_seconds = 180
    min_output_tokens = 4096

    WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}
    MAX_CONTINUATIONS = 3

    def _get_platform_name(self) -> str:
        """Return the platform name."""
        return 'anthropic'

    def send_prompt(self, prompt: str, temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a prompt to Claude with web search on and get the response.

        Temperature is left at the model default on purpose: the consumer
        product does not expose it.

        Returns:
            Dictionary with response data, cited links and search queries
        """
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=self.api_key)

            testing = self.config.get('testing', {})
            max_tokens = max(int(max_tokens or testing.get('max_tokens', 1000)), self.min_output_tokens)
            timeout = max(int(testing.get('timeout_seconds', 30)), self.min_timeout_seconds)

            messages: List[Dict[str, Any]] = [{"role": "user", "content": prompt}]
            all_blocks: List[Any] = []
            input_tokens = 0
            output_tokens = 0
            search_requests = 0
            stop_reason = None

            # A long search turn can come back as "pause_turn". Sending the
            # paused assistant message back unchanged lets it finish.
            for _ in range(self.MAX_CONTINUATIONS + 1):
                response = client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=messages,
                    tools=[self.WEB_SEARCH_TOOL],
                    timeout=timeout,
                )
                all_blocks.extend(response.content or [])
                usage = getattr(response, 'usage', None)
                if usage:
                    input_tokens += getattr(usage, 'input_tokens', 0) or 0
                    output_tokens += getattr(usage, 'output_tokens', 0) or 0
                    server_use = getattr(usage, 'server_tool_use', None)
                    if server_use:
                        search_requests += getattr(server_use, 'web_search_requests', 0) or 0
                stop_reason = response.stop_reason
                if stop_reason != 'pause_turn':
                    break
                messages = messages + [{"role": "assistant", "content": response.content}]

            text_parts: List[str] = []
            cited_urls: List[Dict[str, Any]] = []
            sources_consulted: List[Dict[str, Any]] = []
            search_queries: List[str] = []
            search_errors: List[str] = []
            seen_cited = set()
            seen_sources = set()

            for block in all_blocks:
                block_type = getattr(block, 'type', '')
                if block_type == 'text':
                    text_parts.append(getattr(block, 'text', '') or '')
                    for cit in (getattr(block, 'citations', None) or []):
                        url = getattr(cit, 'url', '') or ''
                        if not url or url in seen_cited:
                            continue
                        seen_cited.add(url)
                        cited_urls.append({
                            'url': url,
                            'domain': self._extract_domain(url),
                            'title': getattr(cit, 'title', '') or '',
                            'source_type': 'api_citation',
                        })
                elif block_type == 'server_tool_use':
                    query = (getattr(block, 'input', None) or {}).get('query')
                    if query:
                        search_queries.append(query)
                elif block_type == 'web_search_tool_result':
                    content = getattr(block, 'content', None)
                    if isinstance(content, list):
                        for res in content:
                            url = getattr(res, 'url', '') or ''
                            if url and url not in seen_sources:
                                seen_sources.add(url)
                                sources_consulted.append({
                                    'url': url,
                                    'domain': self._extract_domain(url),
                                    'title': getattr(res, 'title', '') or '',
                                })
                    elif content is not None:
                        search_errors.append(getattr(content, 'error_code', 'unknown') or 'unknown')

            response_text = ''.join(text_parts)

            return {
                'response_text': response_text,
                'success': bool(response_text),
                'error': None if response_text else 'Anthropic returned no answer text',
                'metadata': {
                    'tokens_used': input_tokens + output_tokens,
                    'prompt_tokens': input_tokens,
                    'completion_tokens': output_tokens,
                    'stop_reason': stop_reason,
                    'temperature': None,
                    'max_tokens': max_tokens,
                    'web_search_enabled': True,
                    'web_search_used': len(search_queries) > 0,
                    'web_search_calls': search_requests or len(search_queries),
                    'search_queries': search_queries,
                    'search_errors': search_errors,
                    'cited_urls': cited_urls,
                    'citation_count': len(cited_urls),
                    'sources_consulted': sources_consulted,
                }
            }

        except ImportError as e:
            return {
                'response_text': '',
                'success': False,
                'error': f'Anthropic library not installed: {str(e)}',
                'metadata': {}
            }
        except Exception as e:
            return {
                'response_text': '',
                'success': False,
                'error': f'Anthropic API error: {str(e)}',
                'metadata': {}
            }

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from a URL, stripping www. prefix."""
        try:
            return urlparse(url).netloc.replace('www.', '')
        except Exception:
            return ''
