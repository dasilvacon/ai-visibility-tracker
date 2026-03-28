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

            # Azure OpenAI requires endpoint and deployment name
            azure_endpoint = self.config.get('azure', {}).get(
                'endpoint', os.getenv('AZURE_OPENAI_ENDPOINT', '')
            )
            api_version = self.config.get('azure', {}).get(
                'api_version', '2024-06-01'
            )

            if not azure_endpoint:
                return {
                    'response_text': '',
                    'success': False,
                    'error': 'Azure OpenAI endpoint not configured. Set AZURE_OPENAI_ENDPOINT or config azure.endpoint.',
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

            response = client.chat.completions.create(
                model=self.model,  # This is the Azure deployment name
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
