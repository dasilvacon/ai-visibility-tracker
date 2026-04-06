"""
Google Gemini API client implementation.
"""

from typing import Dict, Any, Optional
from .base_client import BaseAPIClient


class GeminiClient(BaseAPIClient):
    """Google Gemini API client for testing prompts."""

    def _get_platform_name(self) -> str:
        """Return the platform name."""
        return 'gemini'

    def send_prompt(self, prompt: str, temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a prompt to Google Gemini and get response.

        Args:
            prompt: The prompt text to send
            temperature: Temperature setting for response generation
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with response data
        """
        try:
            from google import genai

            # Initialize client
            client = genai.Client(api_key=self.api_key)

            temperature = temperature or self.config.get('testing', {}).get('default_temperature', 0.7)
            max_tokens = max_tokens or self.config.get('testing', {}).get('max_tokens', 1000)
            timeout = self.config.get('testing', {}).get('timeout_seconds', 30)

            # Generate response with new API
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    'temperature': temperature,
                    'max_output_tokens': max_tokens,
                    'http_options': {'timeout': timeout * 1000}  # milliseconds
                }
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

            return {
                'response_text': response_text,
                'success': True,
                'error': None,
                'metadata': {
                    'tokens_used': tokens_used,
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'temperature': temperature,
                    'max_tokens': max_tokens
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
