"""
Microsoft Copilot API client via Azure OpenAI.

Copilot uses Azure OpenAI under the hood, so this client is similar to the
OpenAI client but points to Azure endpoints.
"""

import os
from typing import Dict, Any, Optional
from .base_client import BaseAPIClient


class CopilotClient(BaseAPIClient):
    """Microsoft Copilot API client via Azure OpenAI."""

    def _get_platform_name(self) -> str:
        return 'copilot'

    def send_prompt(self, prompt: str, temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a prompt to Microsoft Copilot via Azure OpenAI endpoint.

        Args:
            prompt: The prompt text to send
            temperature: Temperature setting for response generation
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with response data
        """
        try:
            from openai import AzureOpenAI

            # Azure OpenAI requires endpoint and deployment name.
            # Prefer canonical 'azure_openai' config key (matches config.template.json);
            # fall back to legacy 'azure' key and to env vars for all three fields.
            azure_cfg = self.config.get('azure_openai') or self.config.get('azure') or {}

            azure_endpoint = azure_cfg.get('endpoint') or os.getenv('AZURE_OPENAI_ENDPOINT', '')
            api_version = azure_cfg.get('api_version') or os.getenv('AZURE_OPENAI_API_VERSION', '2024-10-01-preview')

            # Deployment name: explicit azure_openai.deployment > env var > self.model fallback
            deployment = (
                azure_cfg.get('deployment')
                or os.getenv('AZURE_OPENAI_DEPLOYMENT', '')
                or self.model
            )

            if not azure_endpoint:
                return {
                    'response_text': '',
                    'success': False,
                    'error': 'Azure OpenAI endpoint not configured. Set AZURE_OPENAI_ENDPOINT or config azure_openai.endpoint.',
                    'metadata': {}
                }

            client = AzureOpenAI(
                api_key=self.api_key,
                api_version=api_version,
                azure_endpoint=azure_endpoint
            )

            temperature = temperature or self.config.get('testing', {}).get('default_temperature', 0.7)
            max_tokens = max_tokens or self.config.get('testing', {}).get('max_tokens', 1000)
            timeout = self.config.get('testing', {}).get('timeout_seconds', 30)

            # Newer Azure-deployed models (gpt-5*, o1*, o3*, gpt-4.1*) require
            # `max_completion_tokens` instead of legacy `max_tokens`, and some
            # reject non-default `temperature`. Detect by deployment/model name
            # and fall back on API errors for robustness.
            model_lower = (deployment or self.model or '').lower()
            uses_new_params = any(
                key in model_lower
                for key in ('gpt-5', 'o1', 'o3', 'o4', 'gpt-4.1')
            )

            def _call(use_new: bool):
                kwargs = {
                    'model': deployment,  # Azure deployment name
                    'messages': [{"role": "user", "content": prompt}],
                    'timeout': timeout,
                }
                if use_new:
                    kwargs['max_completion_tokens'] = max_tokens
                else:
                    kwargs['max_tokens'] = max_tokens
                    kwargs['temperature'] = temperature
                return client.chat.completions.create(**kwargs)

            try:
                response = _call(uses_new_params)
            except Exception as e:
                err_str = str(e)
                if 'max_completion_tokens' in err_str and not uses_new_params:
                    response = _call(True)
                elif "'max_tokens'" in err_str and uses_new_params:
                    response = _call(False)
                elif 'temperature' in err_str and uses_new_params:
                    response = client.chat.completions.create(
                        model=deployment,
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

        except ImportError:
            return {
                'response_text': '',
                'success': False,
                'error': 'openai package not installed. Run: pip install openai',
                'metadata': {}
            }
        except Exception as e:
            return {
                'response_text': '',
                'success': False,
                'error': str(e),
                'metadata': {}
            }
