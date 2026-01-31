"""
Batch Manager - Handles prompt batch lifecycle and metadata
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd


class BatchManager:
    """Manages prompt batches and their metadata."""

    def __init__(self, data_dir: str = "data"):
        """Initialize batch manager."""
        self.data_dir = Path(data_dir)
        self.batches_file = self.data_dir / "prompt_batches.json"
        self.batches = self._load_batches()

    def _load_batches(self) -> Dict[str, Any]:
        """Load batch metadata from file."""
        if self.batches_file.exists():
            with open(self.batches_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_batches(self):
        """Save batch metadata to file."""
        self.data_dir.mkdir(exist_ok=True)
        with open(self.batches_file, 'w') as f:
            json.dump(self.batches, f, indent=2, default=str)

    def create_batch(self, batch_name: str, notes: str = "",
                     client_name: str = "") -> str:
        """
        Create a new batch.

        Args:
            batch_name: Human-readable batch name
            notes: Optional notes about this batch
            client_name: Client this batch belongs to

        Returns:
            batch_id: Unique batch identifier
        """
        # Generate batch ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_id = f"batch_{timestamp}"

        # Create batch metadata
        self.batches[batch_id] = {
            'batch_id': batch_id,
            'batch_name': batch_name,
            'client_name': client_name,
            'notes': notes,
            'date_added': datetime.now().isoformat(),
            'status': 'active',
            'prompt_count': 0,
            'prompts': []  # Store prompt IDs
        }

        self._save_batches()
        return batch_id

    def add_prompts_to_batch(self, batch_id: str, prompt_ids: List[str]):
        """Add prompts to a batch."""
        if batch_id in self.batches:
            self.batches[batch_id]['prompts'].extend(prompt_ids)
            self.batches[batch_id]['prompt_count'] = len(self.batches[batch_id]['prompts'])
            self._save_batches()

    def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch metadata."""
        return self.batches.get(batch_id)

    def get_batches_by_client(self, client_name: str) -> List[Dict[str, Any]]:
        """Get all batches for a client."""
        return [
            batch for batch in self.batches.values()
            if batch.get('client_name') == client_name
        ]

    def get_active_batches(self, client_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active batches, optionally filtered by client."""
        active = [
            batch for batch in self.batches.values()
            if batch.get('status') == 'active'
        ]

        if client_name:
            active = [b for b in active if b.get('client_name') == client_name]

        return sorted(active, key=lambda x: x['date_added'], reverse=True)

    def get_archived_batches(self, client_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all archived batches, optionally filtered by client."""
        archived = [
            batch for batch in self.batches.values()
            if batch.get('status') == 'archived'
        ]

        if client_name:
            archived = [b for b in archived if b.get('client_name') == client_name]

        return sorted(archived, key=lambda x: x.get('date_archived', ''), reverse=True)

    def archive_batch(self, batch_id: str, reason: str = ""):
        """Archive a batch."""
        if batch_id in self.batches:
            self.batches[batch_id]['status'] = 'archived'
            self.batches[batch_id]['date_archived'] = datetime.now().isoformat()
            self.batches[batch_id]['archive_reason'] = reason
            self._save_batches()

    def restore_batch(self, batch_id: str):
        """Restore an archived batch."""
        if batch_id in self.batches:
            self.batches[batch_id]['status'] = 'active'
            self.batches[batch_id]['date_restored'] = datetime.now().isoformat()
            self._save_batches()

    def delete_batch(self, batch_id: str):
        """Permanently delete a batch."""
        if batch_id in self.batches:
            del self.batches[batch_id]
            self._save_batches()

    def get_baseline_batch_id(self, client_name: str) -> Optional[str]:
        """Get the baseline batch ID for a client."""
        batches = self.get_batches_by_client(client_name)
        baseline = [b for b in batches if 'baseline' in b.get('batch_name', '').lower()]

        if baseline:
            return baseline[0]['batch_id']

        # Return oldest batch if no explicit baseline
        if batches:
            oldest = min(batches, key=lambda x: x['date_added'])
            return oldest['batch_id']

        return None

    def count_existing_prompts(self, client_name: str, status: str = 'active') -> int:
        """Count how many prompts exist for a client."""
        batches = self.get_batches_by_client(client_name)

        if status:
            batches = [b for b in batches if b.get('status') == status]

        return sum(b.get('prompt_count', 0) for b in batches)


def add_batch_metadata_to_prompts(prompts: List[Dict[str, Any]],
                                   batch_id: str,
                                   batch_name: str,
                                   batch_manager: BatchManager) -> List[Dict[str, Any]]:
    """
    Add batch metadata to generated prompts.

    Args:
        prompts: List of prompt dictionaries
        batch_id: Batch identifier
        batch_name: Human-readable batch name
        batch_manager: BatchManager instance

    Returns:
        Updated prompts with batch metadata
    """
    batch = batch_manager.get_batch(batch_id)
    date_added = batch.get('date_added', datetime.now().isoformat()) if batch else datetime.now().isoformat()

    prompt_ids = []

    for prompt in prompts:
        prompt['batch_id'] = batch_id
        prompt['batch_name'] = batch_name
        prompt['date_added'] = date_added
        prompt['status'] = 'active'

        if 'prompt_id' in prompt:
            prompt_ids.append(prompt['prompt_id'])

    # Update batch with prompt IDs
    if prompt_ids:
        batch_manager.add_prompts_to_batch(batch_id, prompt_ids)

    return prompts


def load_prompts_with_batches(csv_path: str) -> pd.DataFrame:
    """
    Load prompts CSV with batch metadata.

    Returns DataFrame with all batch information included.
    """
    try:
        df = pd.read_csv(csv_path)

        # Add batch columns if they don't exist
        required_columns = ['batch_id', 'batch_name', 'date_added', 'status']
        for col in required_columns:
            if col not in df.columns:
                if col == 'batch_id':
                    df[col] = 'batch_legacy'
                elif col == 'batch_name':
                    df[col] = 'Legacy Prompts'
                elif col == 'date_added':
                    df[col] = ''
                elif col == 'status':
                    df[col] = 'active'

        return df

    except FileNotFoundError:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=[
            'prompt_id', 'persona', 'category', 'intent_type', 'prompt_text',
            'expected_visibility_score', 'notes', 'batch_id', 'batch_name',
            'date_added', 'status'
        ])
