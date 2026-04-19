"""
Results tracker for logging visibility test results.

Every result row is stamped with the prompt-set version that was active
when the test ran, so historical trends remain auditable across prompt
regenerations. See docs/prompt-versioning.md for the full schema.
"""

import csv
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class ResultsTracker:
    """Tracks and logs visibility test results."""

    def __init__(
        self,
        client_slug: str,
        base_dir: str = "data/results",
        client_data_dir: str = "data",
        prompts_version_meta: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the results tracker with per-client isolation.

        Args:
            client_slug: Client identifier (e.g., 'ontario_caregiver_organization')
            base_dir: Base directory for results (default: data/results)
            client_data_dir: Base directory holding per-client active prompts
                and their meta.json sidecar (default: data). Used to auto-load
                the active prompts version if ``prompts_version_meta`` is None.
            prompts_version_meta: Full meta dict for the active prompt set.
                If None, the tracker tries to load it from
                ``{client_data_dir}/{client_slug}/{client_slug}_prompts.meta.json``.
                If that file is also missing, the version fields are left blank
                (legacy / pre-migration behavior).
        """
        self.client_slug = client_slug
        self.results_dir = os.path.join(base_dir, client_slug)
        os.makedirs(self.results_dir, exist_ok=True)

        # Resolve active prompt-set version metadata.
        self.prompts_version_meta: Dict[str, Any] = (
            prompts_version_meta
            if prompts_version_meta is not None
            else self._load_active_meta(client_data_dir, client_slug)
        )
        self.prompts_version: str = self.prompts_version_meta.get('version', '')

        self.csv_fieldnames = [
            'test_id',
            'timestamp',
            'prompt_id',
            'platform',
            'model',
            'persona',
            'category',
            'intent_type',
            'expected_visibility_score',
            'success',
            'latency_seconds',
            'tokens_used',
            'error',
            'prompts_version',
        ]

    @staticmethod
    def _load_active_meta(client_data_dir: str, client_slug: str) -> Dict[str, Any]:
        """
        Try to load the active prompt-set meta.json for a client.

        Returns an empty dict if the sidecar does not exist or is unreadable.
        Being defensive here matters: during the migration window, some
        clients may not have a meta.json yet, and we don't want that to
        crash a test run.
        """
        meta_path = os.path.join(
            client_data_dir,
            client_slug,
            f"{client_slug}_prompts.meta.json",
        )
        if not os.path.exists(meta_path):
            return {}
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
        except (OSError, json.JSONDecodeError):
            return {}

    def log_result(self, result: Dict[str, Any]) -> str:
        """
        Log a test result.

        Args:
            result: Dictionary containing test result data

        Returns:
            Test ID for the logged result
        """
        test_id = self._generate_test_id()
        result['test_id'] = test_id

        # Stamp the result with the active prompt-set version so the
        # JSON file is fully self-contained even if the archive meta is
        # later edited or lost.
        if self.prompts_version_meta:
            result.setdefault('prompts_version', self.prompts_version)
            result.setdefault('prompts_version_meta', self.prompts_version_meta)

        # Save full result as JSON
        self._save_json_result(result)

        # Save summary to CSV
        self._save_csv_result(result)

        return test_id

    def log_batch_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Log multiple test results.

        Args:
            results: List of result dictionaries

        Returns:
            List of test IDs
        """
        test_ids = []
        for result in results:
            test_id = self.log_result(result)
            test_ids.append(test_id)
        return test_ids

    def _generate_test_id(self) -> str:
        """Generate a unique test ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return f"test_{timestamp}"

    def _save_json_result(self, result: Dict[str, Any]) -> None:
        """Save full result as JSON file."""
        test_id = result['test_id']
        json_path = os.path.join(self.results_dir, f"{test_id}.json")

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def _save_csv_result(self, result: Dict[str, Any]) -> None:
        """Save result summary to CSV."""
        csv_path = os.path.join(self.results_dir, 'results_summary.csv')
        file_exists = os.path.exists(csv_path)

        metadata = result.get('metadata', {})

        row = {
            'test_id': result['test_id'],
            'timestamp': result.get('timestamp', ''),
            'prompt_id': result.get('prompt_id', ''),
            'platform': result.get('platform', ''),
            'model': result.get('model', ''),
            'persona': metadata.get('persona', ''),
            'category': metadata.get('category', ''),
            'intent_type': metadata.get('intent_type', ''),
            'expected_visibility_score': result.get('expected_visibility_score', ''),
            'success': result.get('success', False),
            'latency_seconds': result.get('latency_seconds', ''),
            'tokens_used': metadata.get('tokens_used', ''),
            'error': result.get('error', ''),
            'prompts_version': result.get('prompts_version', self.prompts_version),
        }

        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(row)

    def load_results_summary(self) -> List[Dict[str, Any]]:
        """
        Load all results from the summary CSV.

        Returns:
            List of result dictionaries
        """
        csv_path = os.path.join(self.results_dir, 'results_summary.csv')

        if not os.path.exists(csv_path):
            return []

        results = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(dict(row))

        return results

    def load_full_result(self, test_id: str) -> Dict[str, Any]:
        """
        Load full result from JSON file.

        Args:
            test_id: The test ID to load

        Returns:
            Full result dictionary
        """
        json_path = os.path.join(self.results_dir, f"{test_id}.json")

        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Result not found: {test_id}")

        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_results_by_platform(self, platform: str) -> List[Dict[str, Any]]:
        """
        Get all results for a specific platform.

        Args:
            platform: Platform name to filter by

        Returns:
            List of result dictionaries
        """
        all_results = self.load_results_summary()
        return [r for r in all_results if r.get('platform') == platform]

    def get_results_by_prompt(self, prompt_id: str) -> List[Dict[str, Any]]:
        """
        Get all results for a specific prompt.

        Args:
            prompt_id: Prompt ID to filter by

        Returns:
            List of result dictionaries
        """
        all_results = self.load_results_summary()
        return [r for r in all_results if r.get('prompt_id') == prompt_id]
