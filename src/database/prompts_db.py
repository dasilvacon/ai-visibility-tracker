"""
Prompts database manager for CSV-based storage.
"""

import csv
import os
from typing import List, Dict, Any, Optional


class PromptsDatabase:
    """Manager for prompts CSV database."""

    def __init__(self, csv_path: str):
        """
        Initialize the prompts database.

        Args:
            csv_path: Path to the prompts CSV file
        """
        self.csv_path = csv_path
        self.fieldnames = [
            'prompt_id',
            'persona',
            'category',
            'intent_type',
            'prompt_text',
            'expected_visibility_score',
            'notes'
        ]

    def load_prompts(self) -> List[Dict[str, Any]]:
        """
        Load all prompts from the CSV file.

        Returns:
            List of prompt dictionaries
        """
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Prompts CSV file not found: {self.csv_path}")

        prompts = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prompt = {
                    'prompt_id': row['prompt_id'],
                    'persona': row['persona'],
                    'category': row['category'],
                    'intent_type': row['intent_type'],
                    'prompt_text': row['prompt_text'],
                    'expected_visibility_score': float(row['expected_visibility_score']),
                    'notes': row['notes']
                }
                prompts.append(prompt)

        return prompts

    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific prompt by ID.

        Args:
            prompt_id: The prompt ID to search for

        Returns:
            Prompt dictionary or None if not found
        """
        prompts = self.load_prompts()
        for prompt in prompts:
            if prompt['prompt_id'] == prompt_id:
                return prompt
        return None

    def filter_prompts(self, persona: Optional[str] = None,
                      category: Optional[str] = None,
                      intent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Filter prompts by criteria.

        Args:
            persona: Filter by persona
            category: Filter by category
            intent_type: Filter by intent type

        Returns:
            List of filtered prompt dictionaries
        """
        prompts = self.load_prompts()
        filtered = prompts

        if persona:
            filtered = [p for p in filtered if p['persona'] == persona]
        if category:
            filtered = [p for p in filtered if p['category'] == category]
        if intent_type:
            filtered = [p for p in filtered if p['intent_type'] == intent_type]

        return filtered

    def add_prompt(self, prompt: Dict[str, Any]) -> bool:
        """
        Add a new prompt to the CSV file.

        Args:
            prompt: Dictionary containing prompt data

        Returns:
            True if successful, False otherwise
        """
        try:
            file_exists = os.path.exists(self.csv_path)

            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow(prompt)

            return True
        except Exception as e:
            print(f"Error adding prompt: {e}")
            return False

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about the prompts database.

        Returns:
            Dictionary with statistics
        """
        prompts = self.load_prompts()

        personas = set(p['persona'] for p in prompts)
        categories = set(p['category'] for p in prompts)
        intent_types = set(p['intent_type'] for p in prompts)

        return {
            'total_prompts': len(prompts),
            'unique_personas': len(personas),
            'unique_categories': len(categories),
            'unique_intent_types': len(intent_types),
            'personas': list(personas),
            'categories': list(categories),
            'intent_types': list(intent_types)
        }
