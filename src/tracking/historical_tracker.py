"""
Historical Tracking Module - Saves and retrieves monthly visibility metrics.

Tracks three key metrics over time:
1. Visibility Rate - % of prompts where brand is mentioned
2. Prominence Rate - Average citation position (1st, 2nd, 3rd, etc.)
3. Share of Voice - Brand mentions vs. competitor mentions
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class HistoricalTracker:
    """Tracks visibility metrics over time for monthly comparison."""

    def __init__(self, client_slug: str, base_dir: str = "data/results"):
        """
        Initialize the historical tracker with per-client isolation.

        Args:
            client_slug: Client identifier (e.g., 'ontario_caregiver_organization')
            base_dir: Base directory for results (default: data/results)
        """
        self.client_slug = client_slug
        client_dir = Path(base_dir) / client_slug
        client_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = client_dir / "monthly_scores.json"

        # Create file if it doesn't exist
        if not self.history_file.exists():
            self._initialize_history_file()

    def _initialize_history_file(self):
        """Create empty history file."""
        with open(self.history_file, 'w') as f:
            json.dump({}, f, indent=2)

    def save_monthly_scores(self,
                           client_name: str,
                           visibility_summary: Dict[str, Any],
                           platform_results: Optional[Dict[str, Dict]] = None,
                           month: Optional[str] = None,
                           week: Optional[str] = None) -> None:
        """
        Save scores for a client at both monthly AND weekly granularity.

        We store under two key formats in the same client dict:
          - "YYYY-MM"    → monthly rollup (overwrites previous run in same month)
          - "YYYY-WNN"   → weekly snapshot (one entry per ISO week — preserved
                           across multiple runs because each week gets its own key)

        This is intentionally additive: the dashboard's monthly trends still
        work, AND we can now compute week-over-week deltas for the "what
        changed this week" panel.

        Args:
            client_name: Name of the client
            visibility_summary: Summary dict from VisibilityScorer.get_visibility_summary()
            platform_results: Optional dict of platform-specific results
            month: Optional month string (YYYY-MM), defaults to current month
            week: Optional ISO week string (YYYY-WNN), defaults to current week
        """
        now = datetime.now()
        # Get keys
        if month is None:
            month = now.strftime("%Y-%m")
        if week is None:
            year, iso_week, _ = now.isocalendar()
            week = f"{year}-W{iso_week:02d}"

        # Load existing history
        history = self._load_history()

        # Initialize client history if needed
        client_slug = client_name.lower().replace(' ', '_')
        if client_slug not in history:
            history[client_slug] = {}

        # Calculate share of voice
        brand_mentions = visibility_summary.get('brand_mentions', 0)
        competitor_mentions = visibility_summary.get('total_competitor_mentions', 0)
        total_mentions = brand_mentions + competitor_mentions
        share_of_voice = (brand_mentions / total_mentions * 100) if total_mentions > 0 else 0

        # Extract key metrics. Note: prominence_rate maps to
        # average_prominence_score (0-10) when available — the older field
        # name `average_citation_position` was a misnomer (it's a score, not
        # a position) and was always 0 if missing.
        prominence = (
            visibility_summary.get('average_prominence_score')
            or visibility_summary.get('average_citation_position', 0)
        )

        snapshot = {
            'test_date': now.isoformat(),
            'total_prompts': visibility_summary.get('total_prompts_tested', 0),
            'metrics': {
                'visibility_rate': round(visibility_summary.get('brand_visibility_rate', 0), 2),
                'prominence_rate': round(float(prominence), 2),
                'share_of_voice': round(share_of_voice, 2)
            },
            'detailed_stats': {
                'brand_mentions': brand_mentions,
                'competitor_mentions': competitor_mentions,
                'high_prominence_count': visibility_summary.get('high_prominence_count', 0),
                'competitors_encountered': visibility_summary.get('competitors_encountered', [])
            }
        }

        # Add platform-specific data if provided
        if platform_results:
            snapshot['by_platform'] = {}
            for platform, results in platform_results.items():
                platform_brand_mentions = results.get('brand_mentions', 0)
                platform_competitor_mentions = results.get('competitor_mentions', 0)
                platform_total = platform_brand_mentions + platform_competitor_mentions
                platform_sov = (platform_brand_mentions / platform_total * 100) if platform_total > 0 else 0

                snapshot['by_platform'][platform] = {
                    'visibility': round(results.get('visibility_rate', 0), 2),
                    'prominence': round(float(results.get('avg_prominence', results.get('avg_position', 0)) or 0), 2),
                    'share_of_voice': round(platform_sov, 2),
                    'total_prompts': results.get('total_prompts', 0),
                    'brand_mentions': platform_brand_mentions,
                }

        # Save to history under BOTH keys so monthly charts AND weekly deltas work.
        # Monthly key gets overwritten on each run within the same month (latest
        # snapshot for the month); weekly key is preserved per ISO week.
        history[client_slug][month] = snapshot
        history[client_slug][week] = snapshot

        # Write back to file
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def get_weekly_snapshots(self, client_name: str) -> List[Dict[str, Any]]:
        """
        Return all weekly snapshots for a client, sorted oldest-to-newest.

        Each entry has the snapshot dict + the `week` key it was stored under.
        Used by the 'what changed this week' panel and per-week trend charts.
        """
        client_slug = client_name.lower().replace(' ', '_')
        client_history = self._load_history().get(client_slug, {})

        weekly = []
        for key, value in client_history.items():
            # ISO week format: YYYY-WNN (the W is uppercase, position 5)
            if len(key) == 8 and key[4] == '-' and key[5] == 'W':
                weekly.append({'week': key, **value})

        # Sort by week key — works because YYYY-WNN sorts naturally
        weekly.sort(key=lambda e: e['week'])
        return weekly

    def get_week_over_week_delta(self, client_name: str) -> Optional[Dict[str, Any]]:
        """
        Compare the most recent week to the prior week for the 'what changed
        this week' alert panel. Returns None if we don't have at least 2
        weekly snapshots yet.

        Returned shape:
            {
                'current_week':  'YYYY-WNN',
                'previous_week': 'YYYY-WNN',
                'metrics': {
                    'visibility_rate': {'current': X, 'previous': Y, 'delta': Z, 'pct_change': P},
                    'prominence_rate': {...},
                    'share_of_voice': {...},
                },
                'new_competitors':  [...]   # in current, not in previous
                'lost_competitors': [...]   # in previous, not in current
                'platforms_changed': {platform: {'visibility_delta': X}, ...}
            }
        """
        weekly = self.get_weekly_snapshots(client_name)
        if len(weekly) < 2:
            return None

        previous, current = weekly[-2], weekly[-1]
        prev_metrics = previous.get('metrics', {})
        curr_metrics = current.get('metrics', {})

        def _delta(metric_key: str) -> Dict[str, float]:
            curr = float(curr_metrics.get(metric_key, 0) or 0)
            prev = float(prev_metrics.get(metric_key, 0) or 0)
            delta = curr - prev
            pct = (delta / prev * 100) if prev else 0.0
            return {
                'current': round(curr, 2),
                'previous': round(prev, 2),
                'delta': round(delta, 2),
                'pct_change': round(pct, 1),
            }

        # Compute new and lost competitors (set diff between weekly snapshots)
        prev_comps = set(previous.get('detailed_stats', {}).get('competitors_encountered', []) or [])
        curr_comps = set(current.get('detailed_stats', {}).get('competitors_encountered', []) or [])

        # Platform-level deltas (only for platforms present in both snapshots)
        platforms_changed = {}
        prev_platforms = previous.get('by_platform', {}) or {}
        curr_platforms = current.get('by_platform', {}) or {}
        for plat in set(prev_platforms) | set(curr_platforms):
            p = prev_platforms.get(plat, {})
            c = curr_platforms.get(plat, {})
            platforms_changed[plat] = {
                'visibility_current': round(float(c.get('visibility', 0) or 0), 2),
                'visibility_previous': round(float(p.get('visibility', 0) or 0), 2),
                'visibility_delta': round(float(c.get('visibility', 0) or 0) - float(p.get('visibility', 0) or 0), 2),
            }

        return {
            'current_week': current.get('week'),
            'previous_week': previous.get('week'),
            'metrics': {
                'visibility_rate': _delta('visibility_rate'),
                'prominence_rate': _delta('prominence_rate'),
                'share_of_voice': _delta('share_of_voice'),
            },
            'new_competitors': sorted(curr_comps - prev_comps),
            'lost_competitors': sorted(prev_comps - curr_comps),
            'platforms_changed': platforms_changed,
        }

    def _load_history(self) -> Dict:
        """Load history from file."""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def get_client_history(self, client_name: str) -> Dict[str, Dict]:
        """
        Get all historical data for a client.

        Args:
            client_name: Name of the client

        Returns:
            Dict of month -> metrics data
        """
        history = self._load_history()
        client_slug = client_name.lower().replace(' ', '_')
        return history.get(client_slug, {})

    def get_trend_data(self, client_name: str, metric: str) -> List[Dict[str, Any]]:
        """
        Get trend data for a specific metric.

        Args:
            client_name: Name of the client
            metric: One of: 'visibility_rate', 'prominence_rate', 'share_of_voice'

        Returns:
            List of {month, value} dicts sorted by month
        """
        history = self.get_client_history(client_name)

        trend_data = []
        for month, data in sorted(history.items()):
            value = data.get('metrics', {}).get(metric)
            if value is not None:
                trend_data.append({
                    'month': month,
                    'value': value,
                    'test_date': data.get('test_date')
                })

        return trend_data

    def get_latest_vs_previous(self, client_name: str) -> Optional[Dict[str, Any]]:
        """
        Compare latest month with previous month.

        Args:
            client_name: Name of the client

        Returns:
            Dict with comparison data or None if insufficient history
        """
        history = self.get_client_history(client_name)

        if len(history) < 2:
            return None

        # Get last two months
        sorted_months = sorted(history.keys(), reverse=True)
        latest_month = sorted_months[0]
        previous_month = sorted_months[1]

        latest = history[latest_month]['metrics']
        previous = history[previous_month]['metrics']

        return {
            'latest_month': latest_month,
            'previous_month': previous_month,
            'latest_metrics': latest,
            'previous_metrics': previous,
            'changes': {
                'visibility_rate': round(latest['visibility_rate'] - previous['visibility_rate'], 2),
                'prominence_rate': round(latest['prominence_rate'] - previous['prominence_rate'], 2),
                'share_of_voice': round(latest['share_of_voice'] - previous['share_of_voice'], 2)
            },
            'trend': self._determine_trend(latest, previous)
        }

    def _determine_trend(self, latest: Dict, previous: Dict) -> str:
        """Determine overall trend from metrics."""
        changes = [
            latest['visibility_rate'] - previous['visibility_rate'],
            # Note: Lower prominence position is better (1st vs 3rd)
            previous['prominence_rate'] - latest['prominence_rate'],
            latest['share_of_voice'] - previous['share_of_voice']
        ]

        positive_changes = sum(1 for c in changes if c > 0)

        if positive_changes >= 2:
            return 'improving'
        elif positive_changes == 1:
            return 'stable'
        else:
            return 'declining'

    def get_all_months(self, client_name: str) -> List[str]:
        """
        Get list of all months with data for a client.

        Args:
            client_name: Name of the client

        Returns:
            List of month strings (YYYY-MM) sorted chronologically
        """
        history = self.get_client_history(client_name)
        return sorted(history.keys())

    def delete_month(self, client_name: str, month: str) -> bool:
        """
        Delete a specific month's data.

        Args:
            client_name: Name of the client
            month: Month string (YYYY-MM) to delete

        Returns:
            True if deleted, False if not found
        """
        history = self._load_history()
        client_slug = client_name.lower().replace(' ', '_')
        if client_slug in history and month in history[client_slug]:
            del history[client_slug][month]
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
            return True
        return False
