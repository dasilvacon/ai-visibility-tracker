"""
SerpAPI client for Google AI Overviews.

Queries Google via SerpAPI and extracts the AI Overview (the AI-generated
summary box shown at the top of some Google search results).
"""

import os
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from .base_client import BaseAPIClient


class SerpAPIClient(BaseAPIClient):
    """SerpAPI client for Google AI Overviews."""

    def _get_platform_name(self) -> str:
        return 'google_ai_overview'

    def send_prompt(self, prompt: str, temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a search query to Google via SerpAPI and extract AI Overview.

        Note: temperature and max_tokens are ignored — Google AI Overviews
        are not controllable. These params exist for BaseAPIClient compatibility.

        Args:
            prompt: The search query to send to Google
            temperature: Ignored (exists for interface compatibility)
            max_tokens: Ignored (exists for interface compatibility)

        Returns:
            Dictionary with response data including AI Overview text and references
        """
        import requests

        # SerpAPI config with sensible defaults
        serpapi_config = self.config.get('serpapi', {})
        country = serpapi_config.get('country', 'ca')
        language = serpapi_config.get('language', 'en')

        # Step 1: Search Google via SerpAPI
        params = {
            'engine': 'google',
            'q': prompt,
            'api_key': self.api_key,
            'gl': country,
            'hl': language,
            'num': 10
        }

        try:
            response = requests.get(
                'https://serpapi.com/search',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.Timeout:
            return {
                'response_text': '',
                'success': False,
                'error': 'SerpAPI request timed out after 30s',
                'metadata': {}
            }
        except requests.exceptions.RequestException as e:
            return {
                'response_text': '',
                'success': False,
                'error': f'SerpAPI request failed: {str(e)}',
                'metadata': {}
            }
        except ValueError as e:
            return {
                'response_text': '',
                'success': False,
                'error': f'SerpAPI returned invalid JSON: {str(e)}',
                'metadata': {}
            }

        # Step 2: Extract AI Overview
        ai_overview = data.get('ai_overview')
        search_id = data.get('search_metadata', {}).get('id', '')

        if not ai_overview:
            # No AI Overview for this query — valid data, not an error
            return {
                'response_text': '',
                'success': True,
                'error': None,
                'metadata': {
                    'has_ai_overview': False,
                    'organic_results_count': len(data.get('organic_results', [])),
                    'search_id': search_id,
                    'references': []
                }
            }

        # Step 3: Handle page_token if AI Overview needs a follow-up request
        page_token = ai_overview.get('page_token')
        if page_token and not ai_overview.get('text_blocks'):
            try:
                token_params = {
                    'engine': 'google_ai_overview',
                    'page_token': page_token,
                    'api_key': self.api_key
                }
                token_response = requests.get(
                    'https://serpapi.com/search',
                    params=token_params,
                    timeout=30
                )
                token_response.raise_for_status()
                token_data = token_response.json()
                ai_overview = token_data.get('ai_overview', ai_overview)
            except Exception:
                # Fall back to whatever we got in the first response
                pass

        # Step 4: Build response text from text_blocks
        text_parts = []
        for block in ai_overview.get('text_blocks', []):
            if block.get('snippet'):
                text_parts.append(block['snippet'])
            if block.get('list'):
                for item in block['list']:
                    text_parts.append(f"- {item}")

        response_text = '\n'.join(text_parts)

        # Step 5: Extract references (these become sources in our system)
        references = []
        cited_urls = []
        for ref in ai_overview.get('references', []):
            link = ref.get('link', '')
            domain = self._extract_domain(link)
            references.append({
                'title': ref.get('title', ''),
                'link': link,
                'snippet': ref.get('snippet', ''),
                'source': ref.get('source', ''),
                'domain': domain
            })
            if link:
                cited_urls.append({
                    'url': link,
                    'domain': domain,
                    'title': ref.get('title', ''),
                    'source_type': 'ai_overview_reference'
                })

        return {
            'response_text': response_text,
            'success': True,
            'error': None,
            'metadata': {
                'has_ai_overview': True,
                'references': references,
                'reference_count': len(references),
                'cited_urls': cited_urls,
                'citation_count': len(cited_urls),
                'text_block_count': len(ai_overview.get('text_blocks', [])),
                'organic_results_count': len(data.get('organic_results', [])),
                'search_id': search_id,
                'used_page_token': page_token is not None
            }
        }

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from a URL, stripping www. prefix."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except Exception:
            return ''
