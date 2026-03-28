"""
Ahrefs API v3 Client for dashboard integration.

Makes HTTP requests to Ahrefs API to pull organic keywords and competitors
for a given domain. Used by the Quick Setup flow.

Requires 'ahrefs' API key in Streamlit secrets under [api_keys].
"""

import requests
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class AhrefsClient:
    """Lightweight Ahrefs API v3 client for keyword and competitor data."""

    BASE_URL = "https://api.ahrefs.com/v3"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Ahrefs client.

        Args:
            api_key: Ahrefs API token. If not provided, reads from Streamlit secrets.
        """
        self.api_key = api_key
        if not self.api_key:
            try:
                self.api_key = st.secrets.get("api_keys", {}).get("ahrefs", "")
            except Exception:
                self.api_key = ""

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    @property
    def is_configured(self) -> bool:
        """Check if Ahrefs API key is available."""
        return bool(self.api_key and len(self.api_key) > 10)

    def get_organic_keywords(
        self,
        domain: str,
        country: str = "ca",
        limit: int = 100,
        min_volume: int = 10,
    ) -> Dict[str, Any]:
        """
        Pull organic keywords for a domain.

        Args:
            domain: Target domain (e.g., "ontariocaregiver.ca")
            country: Country code (e.g., "ca", "us")
            limit: Max keywords to return
            min_volume: Minimum search volume filter

        Returns:
            Dict with 'keywords' list and 'meta' info, or 'error' on failure
        """
        if not self.is_configured:
            return {"error": "Ahrefs API key not configured", "keywords": []}

        # Use today's date minus 1 day (Ahrefs data has 1-day lag)
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        params = {
            "target": domain,
            "mode": "subdomains",
            "country": country,
            "date": date,
            "select": "keyword,volume,sum_traffic,best_position,keyword_difficulty,is_informational,is_commercial,is_transactional,is_navigational",
            "where": f"volume >= {min_volume}",
            "order_by": "sum_traffic:desc",
            "limit": limit,
        }

        try:
            resp = requests.get(
                f"{self.BASE_URL}/site-explorer/organic-keywords",
                headers=self.headers,
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            keywords = data.get("keywords", [])
            return {
                "keywords": keywords,
                "meta": {
                    "domain": domain,
                    "country": country,
                    "date": date,
                    "total_returned": len(keywords),
                },
            }

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "unknown"
            if status == 403:
                return {"error": "Ahrefs API key is invalid or expired", "keywords": []}
            elif status == 429:
                return {"error": "Ahrefs API rate limit reached. Try again in a few minutes.", "keywords": []}
            return {"error": f"Ahrefs API error (HTTP {status}): {str(e)}", "keywords": []}
        except requests.exceptions.Timeout:
            return {"error": "Ahrefs API timed out. Try again.", "keywords": []}
        except Exception as e:
            return {"error": f"Failed to fetch keywords: {str(e)}", "keywords": []}

    def get_organic_competitors(
        self,
        domain: str,
        country: str = "ca",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Pull organic competitors for a domain.

        Args:
            domain: Target domain
            country: Country code
            limit: Max competitors to return (default 10 per Tiffany's request)

        Returns:
            Dict with 'competitors' list and 'meta' info, or 'error' on failure
        """
        if not self.is_configured:
            return {"error": "Ahrefs API key not configured", "competitors": []}

        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        params = {
            "target": domain,
            "mode": "subdomains",
            "country": country,
            "date": date,
            "select": "competitor_domain,keywords_common,keywords_competitor,traffic",
            "order_by": "keywords_common:desc",
            "limit": limit,
        }

        try:
            resp = requests.get(
                f"{self.BASE_URL}/site-explorer/organic-competitors",
                headers=self.headers,
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            competitors = data.get("competitors", [])
            return {
                "competitors": competitors,
                "meta": {
                    "domain": domain,
                    "country": country,
                    "date": date,
                    "total_returned": len(competitors),
                },
            }

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "unknown"
            if status == 403:
                return {"error": "Ahrefs API key is invalid or expired", "competitors": []}
            elif status == 429:
                return {"error": "Ahrefs API rate limit reached. Try again in a few minutes.", "competitors": []}
            return {"error": f"Ahrefs API error (HTTP {status}): {str(e)}", "competitors": []}
        except requests.exceptions.Timeout:
            return {"error": "Ahrefs API timed out. Try again.", "competitors": []}
        except Exception as e:
            return {"error": f"Failed to fetch competitors: {str(e)}", "competitors": []}

    def get_domain_metrics(
        self,
        domain: str,
        country: str = "ca",
    ) -> Dict[str, Any]:
        """
        Pull domain-level SEO metrics.

        Args:
            domain: Target domain
            country: Country code

        Returns:
            Dict with metrics or 'error' on failure
        """
        if not self.is_configured:
            return {"error": "Ahrefs API key not configured"}

        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        params = {
            "target": domain,
            "mode": "subdomains",
            "date": date,
        }

        try:
            resp = requests.get(
                f"{self.BASE_URL}/site-explorer/metrics",
                headers=self.headers,
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            return {"error": f"Failed to fetch metrics: {str(e)}"}
