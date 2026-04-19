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

            # Newer OpenAI models (gpt-5*, o1*, o3*, gpt-4.1*) require
            # `max_completion_tokens` instead of the legacy `max_tokens` param.
            # Some also reject non-default `temperature`. Detect by model name
            # and pick the right signature; fall back to legacy on older models.
            model_lower = (self.model or '').lower()
            uses_new_params = any(
                model_lower.startswith(prefix)
                for prefix in ('gpt-5', 'o1', 'o3', 'o4', 'gpt-4.1')
            )

            def _call(use_new: bool):
                kwargs = {
                    'model': self.model,
                    'messages': [{"role": "user", "content": prompt}],
                    'timeout': timeout,
                }
                if use_new:
                    kwargs['max_completion_tokens'] = max_tokens
                    # Newer reasoning models only accept default temperature (1.0)
                else:
                    kwargs['max_tokens'] = max_tokens
                    kwargs['temperature'] = temperature
                return client.chat.completions.create(**kwargs)

            try:
                response = _call(uses_new_params)
            except Exception as e:
                err_str = str(e)
                # Retry with the other parameter name if the API tells us to
                if 'max_completion_tokens' in err_str and not uses_new_params:
                    response = _call(True)
                elif "'max_tokens'" in err_str and uses_new_params:
                    response = _call(False)
                elif 'temperature' in err_str and uses_new_params:
                    # Strip temperature entirely — some reasoning models reject it
                    response = client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_completion_tokens=max_tokens,
                        timeout=timeout,
                    )
                else:
                    raise

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
