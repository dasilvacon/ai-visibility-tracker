"""
Approval workflow manager for prompt review and approval.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class ApprovalManager:
    """Manages approval state and bulk operations for prompts."""

    def __init__(self):
        """Initialize the approval manager."""
        self.approved: List[Dict[str, Any]] = []
        self.rejected: List[Dict[str, Any]] = []
        self.pending: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []  # Undo history

    def load_prompts(self, prompts: List[Dict[str, Any]], default_status: str = 'pending'):
        """
        Load prompts into the approval manager.

        Args:
            prompts: List of prompt dictionaries
            default_status: Default status for prompts ('pending', 'approved', 'rejected')
        """
        for prompt in prompts:
            # Add approval_status if not present
            if 'approval_status' not in prompt:
                prompt['approval_status'] = default_status

            # Sort into appropriate list
            if prompt['approval_status'] == 'approved':
                self.approved.append(prompt)
            elif prompt['approval_status'] == 'rejected':
                self.rejected.append(prompt)
            else:
                self.pending.append(prompt)

    def approve_prompts(self, prompt_ids: List[str]):
        """
        Approve prompts by ID.

        Args:
            prompt_ids: List of prompt IDs to approve
        """
        self._move_prompts(prompt_ids, 'approved')

    def reject_prompts(self, prompt_ids: List[str]):
        """
        Reject prompts by ID.

        Args:
            prompt_ids: List of prompt IDs to reject
        """
        self._move_prompts(prompt_ids, 'rejected')

    def reset_prompts(self, prompt_ids: List[str]):
        """
        Reset prompts to pending status.

        Args:
            prompt_ids: List of prompt IDs to reset
        """
        self._move_prompts(prompt_ids, 'pending')

    def _move_prompts(self, prompt_ids: List[str], new_status: str):
        """
        Move prompts between status categories.

        Args:
            prompt_ids: List of prompt IDs to move
            new_status: New status ('approved', 'rejected', 'pending')
        """
        # Create history entry for undo
        self.history.append({
            'action': f'move_to_{new_status}',
            'timestamp': datetime.now().isoformat(),
            'prompt_ids': prompt_ids.copy(),
            'previous_states': {}
        })

        # Find and move prompts
        for prompt_id in prompt_ids:
            prompt = self._find_prompt(prompt_id)
            if prompt:
                # Store previous state
                old_status = prompt.get('approval_status', 'pending')
                self.history[-1]['previous_states'][prompt_id] = old_status

                # Remove from current list
                self._remove_from_list(prompt, old_status)

                # Update status and add to new list
                prompt['approval_status'] = new_status
                self._add_to_list(prompt, new_status)

    def _find_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Find a prompt by ID across all lists."""
        for prompt in self.approved + self.rejected + self.pending:
            if prompt['prompt_id'] == prompt_id:
                return prompt
        return None

    def _remove_from_list(self, prompt: Dict[str, Any], status: str):
        """Remove prompt from its current status list."""
        if status == 'approved' and prompt in self.approved:
            self.approved.remove(prompt)
        elif status == 'rejected' and prompt in self.rejected:
            self.rejected.remove(prompt)
        elif status == 'pending' and prompt in self.pending:
            self.pending.remove(prompt)

    def _add_to_list(self, prompt: Dict[str, Any], status: str):
        """Add prompt to a status list."""
        if status == 'approved':
            self.approved.append(prompt)
        elif status == 'rejected':
            self.rejected.append(prompt)
        else:  # pending
            self.pending.append(prompt)

    def bulk_approve_filtered(self, prompts: List[Dict[str, Any]]):
        """
        Bulk approve a filtered set of prompts.

        Args:
            prompts: List of prompt dicts to approve
        """
        prompt_ids = [p['prompt_id'] for p in prompts]
        self.approve_prompts(prompt_ids)

    def bulk_reject_filtered(self, prompts: List[Dict[str, Any]]):
        """
        Bulk reject a filtered set of prompts.

        Args:
            prompts: List of prompt dicts to reject
        """
        prompt_ids = [p['prompt_id'] for p in prompts]
        self.reject_prompts(prompt_ids)

    def edit_prompt(self, prompt_id: str, updates: Dict[str, Any]):
        """
        Edit a prompt's content.

        Args:
            prompt_id: ID of prompt to edit
            updates: Dict of fields to update
        """
        prompt = self._find_prompt(prompt_id)
        if prompt:
            # Store in history
            self.history.append({
                'action': 'edit',
                'timestamp': datetime.now().isoformat(),
                'prompt_id': prompt_id,
                'old_values': {k: prompt.get(k) for k in updates.keys()}
            })

            # Apply updates
            prompt.update(updates)

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all prompts regardless of status."""
        return self.approved + self.rejected + self.pending

    def get_prompts_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get prompts by status."""
        if status == 'approved':
            return self.approved.copy()
        elif status == 'rejected':
            return self.rejected.copy()
        elif status == 'pending':
            return self.pending.copy()
        else:  # 'all'
            return self.get_all_prompts()

    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval statistics."""
        total = len(self.approved) + len(self.rejected) + len(self.pending)
        return {
            'total': total,
            'approved': len(self.approved),
            'rejected': len(self.rejected),
            'pending': len(self.pending),
            'approval_rate': (len(self.approved) / total * 100) if total > 0 else 0,
            'rejection_rate': (len(self.rejected) / total * 100) if total > 0 else 0
        }

    def save_session(self, filepath: str):
        """
        Save the current session to JSON.

        Args:
            filepath: Path to save the session
        """
        session_data = {
            'timestamp': datetime.now().isoformat(),
            'approved': self.approved,
            'rejected': self.rejected,
            'pending': self.pending,
            'stats': self.get_approval_stats()
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)

    def load_session(self, filepath: str):
        """
        Load a session from JSON.

        Args:
            filepath: Path to load the session from
        """
        with open(filepath, 'r') as f:
            session_data = json.load(f)

        self.approved = session_data.get('approved', [])
        self.rejected = session_data.get('rejected', [])
        self.pending = session_data.get('pending', [])
        self.history = []  # Reset history on load

    def undo_last_action(self):
        """Undo the last action (if possible)."""
        if not self.history:
            return False

        last_action = self.history.pop()

        if last_action['action'].startswith('move_to_'):
            # Undo move operation
            for prompt_id, old_status in last_action['previous_states'].items():
                prompt = self._find_prompt(prompt_id)
                if prompt:
                    current_status = prompt['approval_status']
                    self._remove_from_list(prompt, current_status)
                    prompt['approval_status'] = old_status
                    self._add_to_list(prompt, old_status)
            return True

        elif last_action['action'] == 'edit':
            # Undo edit operation
            prompt = self._find_prompt(last_action['prompt_id'])
            if prompt:
                prompt.update(last_action['old_values'])
            return True

        return False
