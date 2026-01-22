"""
Anthropic Claude API client implementation.
"""

from typing import Dict, Any, Optional
from .base_client import BaseAPIClient


class AnthropicClient(BaseAPIClient):
    """Anthropic Claude API client for testing prompts."""

    def _get_platform_name(self) -> str:
        """Return the platform name."""
        return 'anthropic'

    def send_prompt(self, prompt: str, temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a prompt to Anthropic Claude and get response.

        Args:
            prompt: The prompt text to send
            temperature: Temperature setting for response generation
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with response data
        """
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=self.api_key)

            temperature = temperature or self.config.get('testing', {}).get('default_temperature', 0.7)
            max_tokens = max_tokens or self.config.get('testing', {}).get('max_tokens', 1000)
            timeout = self.config.get('testing', {}).get('timeout_seconds', 30)

            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                timeout=timeout
            )

            return {
                'response_text': response.content[0].text,
                'success': True,
                'error': None,
                'metadata': {
                    'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens,
                    'stop_reason': response.stop_reason,
                    'temperature': temperature,
                    'max_tokens': max_tokens
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
