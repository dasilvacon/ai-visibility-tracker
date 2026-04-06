"""
Perplexity API client implementation.

Perplexity returns structured citations (URLs) in its API responses.
These are normalized into the standard cited_urls format for the
Sources & Citations report tab.
"""

from typing import Dict, Any, Optional
from urllib.parse import urlparse
from .base_client import BaseAPIClient


class PerplexityClient(BaseAPIClient):
    """Perplexity API client for testing prompts."""

    def _get_platform_name(self) -> str:
        """Return the platform name."""
        return 'perplexity'

    def send_prompt(self, prompt: str, temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a prompt to Perplexity and get response.

        Args:
            prompt: The prompt text to send
            temperature: Temperature setting for response generation
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with response data including structured citations
        """
        try:
            from openai import OpenAI

            # Perplexity uses OpenAI-compatible API
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.perplexity.ai"
            )

            temperature = temperature or self.config.get('testing', {}).get('default_temperature', 0.7)
            max_tokens = max_tokens or self.config.get('testing', {}).get('max_tokens', 1000)
            timeout = self.config.get('testing', {}).get('timeout_seconds', 30)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout
            )

            # Extract raw citations from Perplexity response
            raw_citations = []
            if hasattr(response, 'citations') and response.citations:
                raw_citations = response.citations

            # Normalize into standard cited_urls format
            cited_urls = []
            seen_domains = set()
            for citation in raw_citations:
                url = citation if isinstance(citation, str) else citation.get('url', '') if isinstance(citation, dict) else str(citation)
                if not url:
                    continue
                domain = self._extract_domain(url)
                cited_urls.append({
                    'url': url,
                    'domain': domain,
                    'title': citation.get('title', '') if isinstance(citation, dict) else '',
                    'source_type': 'api_citation'
                })
                seen_domains.add(domain)

            return {
                'response_text': response.choices[0].message.content,
                'success': True,
                'error': None,
                'metadata': {
                    'tokens_used': response.usage.total_tokens if response.usage else None,
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else None,
                    'completion_tokens': response.usage.completion_tokens if response.usage else None,
                    'finish_reason': response.choices[0].finish_reason,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'citations': raw_citations,
                    'cited_urls': cited_urls,
                    'citation_count': len(cited_urls)
                }
            }

        except ImportError as e:
            return {
                'response_text': '',
                'success': False,
                'error': f'OpenAI library not installed (required for Perplexity): {str(e)}',
                'metadata': {}
            }
        except Exception as e:
            return {
                'response_text': '',
                'success': False,
                'error': f'Perplexity API error: {str(e)}',
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
