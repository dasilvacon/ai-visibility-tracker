"""
Persona manager for loading and managing persona definitions.
"""

import json
import os
from typing import Dict, List, Any, Optional


class PersonaManager:
    """Manages persona definitions for prompt generation."""

    def __init__(self, personas_file: str):
        """
        Initialize the persona manager.

        Args:
            personas_file: Path to personas JSON file
        """
        self.personas_file = personas_file
        self.personas = []
        self.personas_by_id = {}
        self._load_personas()

    def _load_personas(self) -> None:
        """Load personas from JSON file."""
        if not os.path.exists(self.personas_file):
            raise FileNotFoundError(f"Personas file not found: {self.personas_file}")

        with open(self.personas_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.personas = data.get('personas', [])

        # Create lookup dictionary
        self.personas_by_id = {p['id']: p for p in self.personas}

        # Validate weights sum to approximately 1.0
        total_weight = sum(p.get('weight', 0) for p in self.personas)
        if abs(total_weight - 1.0) > 0.01:
            print(f"Warning: Persona weights sum to {total_weight}, not 1.0")

    def get_all_personas(self) -> List[Dict[str, Any]]:
        """
        Get all personas.

        Returns:
            List of persona dictionaries
        """
        return self.personas

    def get_persona_by_id(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific persona by ID.

        Args:
            persona_id: The persona ID

        Returns:
            Persona dictionary or None if not found
        """
        return self.personas_by_id.get(persona_id)

    def get_persona_distribution(self, total_prompts: int) -> Dict[str, int]:
        """
        Calculate how many prompts should be generated for each persona.

        Args:
            total_prompts: Total number of prompts to generate

        Returns:
            Dictionary mapping persona_id to number of prompts
        """
        distribution = {}
        remaining = total_prompts

        # Sort personas by weight (highest first) to handle rounding
        sorted_personas = sorted(self.personas, key=lambda p: p.get('weight', 0), reverse=True)

        for i, persona in enumerate(sorted_personas):
            if i == len(sorted_personas) - 1:
                # Last persona gets remaining prompts
                distribution[persona['id']] = remaining
            else:
                count = int(total_prompts * persona.get('weight', 0))
                distribution[persona['id']] = count
                remaining -= count

        return distribution

    def get_priority_topics(self, persona_id: str) -> List[str]:
        """
        Get priority topics for a persona.

        Args:
            persona_id: The persona ID

        Returns:
            List of priority topic strings
        """
        persona = self.get_persona_by_id(persona_id)
        if persona:
            return persona.get('priority_topics', [])
        return []

    def get_persona_context(self, persona_id: str) -> str:
        """
        Get a formatted context string for a persona for use in prompts.

        Args:
            persona_id: The persona ID

        Returns:
            Formatted context string
        """
        persona = self.get_persona_by_id(persona_id)
        if not persona:
            return ""

        context = f"Persona: {persona.get('name', 'Unknown')}\n"
        context += f"Description: {persona.get('description', '')}\n"
        if persona.get('priority_topics'):
            context += f"Priority Topics: {', '.join(persona['priority_topics'])}\n"

        return context

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about personas.

        Returns:
            Dictionary with statistics
        """
        return {
            'total_personas': len(self.personas),
            'persona_names': [p.get('name') for p in self.personas],
            'total_weight': sum(p.get('weight', 0) for p in self.personas),
            'average_priority_topics': sum(len(p.get('priority_topics', [])) for p in self.personas) / len(self.personas) if self.personas else 0
        }

    def validate_personas(self) -> List[str]:
        """
        Validate persona definitions and return any issues.

        Returns:
            List of validation error messages
        """
        issues = []

        # Check for required fields
        required_fields = ['id', 'name', 'description', 'weight']
        for persona in self.personas:
            for field in required_fields:
                if field not in persona:
                    issues.append(f"Persona '{persona.get('id', 'unknown')}' missing required field: {field}")

        # Check for duplicate IDs
        ids = [p['id'] for p in self.personas]
        if len(ids) != len(set(ids)):
            issues.append("Duplicate persona IDs found")

        # Check weights are between 0 and 1
        for persona in self.personas:
            weight = persona.get('weight', 0)
            if weight < 0 or weight > 1:
                issues.append(f"Persona '{persona.get('id')}' has invalid weight: {weight}")

        return issues
