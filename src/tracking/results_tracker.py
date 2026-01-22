"""
Results tracker for logging visibility test results.
"""

import csv
import os
import json
from typing import Dict, Any, List
from datetime import datetime


class ResultsTracker:
    """Tracks and logs visibility test results."""

    def __init__(self, results_dir: str):
        """
        Initialize the results tracker.

        Args:
            results_dir: Directory to store results
        """
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)

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
            'error'
        ]

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
            'error': result.get('error', '')
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
