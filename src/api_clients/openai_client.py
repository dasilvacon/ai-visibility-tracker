"""
OpenAI API client implementation.
"""

from typing import Dict, Any, Optional
from .base_client import BaseAPIClient


class OpenAIClient(BaseAPIClient):
    """OpenAI API client for testing prompts."""

    def _get_platform_name(self) -> str:
        """Return the platform name."""
        return 'openai'

    def send_prompt(self, prompt: str, temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a prompt to OpenAI and get response.

        Args:
            prompt: The prompt text to send
            temperature: Temperature setting for response generation
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with response data
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

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
                    'max_tokens': max_tokens
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
