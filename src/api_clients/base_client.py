"""
Base API client class for AI platform integrations.
All platform-specific clients should inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time


class BaseAPIClient(ABC):
    """Abstract base class for AI platform API clients."""

    def __init__(self, api_key: str, model: str, config: Dict[str, Any]):
        """
        Initialize the API client.

        Args:
            api_key: API key for authentication
            model: Model identifier to use
            config: Configuration dictionary with settings
        """
        self.api_key = api_key
        self.model = model
        self.config = config
        self.platform_name = self._get_platform_name()

    @abstractmethod
    def _get_platform_name(self) -> str:
        """Return the platform name (e.g., 'openai', 'anthropic')."""
        pass

    @abstractmethod
    def send_prompt(self, prompt: str, temperature: Optional[float] = None,
                   max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        Send a prompt to the AI platform and get response.

        Args:
            prompt: The prompt text to send
            temperature: Temperature setting for response generation
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary containing:
                - response_text: The AI's response
                - success: Boolean indicating if request was successful
                - error: Error message if any
                - metadata: Additional metadata (tokens used, latency, etc.)
        """
        pass

    def test_prompt(self, prompt_id: str, prompt_text: str,
                   expected_score: float, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a prompt and return structured results.

        Args:
            prompt_id: Unique identifier for the prompt
            prompt_text: The prompt to test
            expected_score: Expected visibility score
            metadata: Additional metadata about the prompt

        Returns:
            Dictionary with test results including response and metrics
        """
        start_time = time.time()

        temperature = self.config.get('testing', {}).get('default_temperature', 0.7)
        max_tokens = self.config.get('testing', {}).get('max_tokens', 1000)

        result = self.send_prompt(prompt_text, temperature, max_tokens)

        end_time = time.time()
        latency = end_time - start_time

        return {
            'prompt_id': prompt_id,
            'platform': self.platform_name,
            'model': self.model,
            'prompt_text': prompt_text,
            'response_text': result.get('response_text', ''),
            'success': result.get('success', False),
            'error': result.get('error', None),
            'expected_visibility_score': expected_score,
            'latency_seconds': round(latency, 2),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'metadata': {**metadata, **result.get('metadata', {})}
        }

    def validate_config(self) -> bool:
        """
        Validate that the client is properly configured.

        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.api_key or self.api_key.startswith('YOUR_'):
            return False
        if not self.model:
            return False
        return True
