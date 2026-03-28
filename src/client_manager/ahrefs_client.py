"""
Ahrefs API v3 Client for dashboard integration.

Makes HTTP requests to Ahrefs API to pull organic keywords and competitors
for a given domain. Used by the Quick Setup flow.

Requires 'ahrefs' API key in Streamlit secrets under [api_keys].
"""

import json
import requests
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


# Valid Ahrefs country codes (ISO 3166-1 alpha-2, uppercase)
VALID_COUNTRIES = {
    "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT",
    "AU", "AW", "AX", "AZ", "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI",
    "BJ", "BL", "BM", "BN", "BO", "BQ", "BR", "BS", "BT", "BV", "BW", "BY",
    "BZ", "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN",
    "CO", "CR", "CU", "CV", "CW", "CX", "CY", "CZ", "DE", "DJ", "DK", "DM",
    "DO", "DZ", "EC", "EE", "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK",
    "FM", "FO", "FR", "GA", "GB", "GD", "GE", "GF", "GG", "GH", "GI", "GL",
    "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY", "HK", "HM",
    "HN", "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR",
    "IS", "IT", "JE", "JM", "JO", "JP", "KE", "KG", "KH", "KI", "KM", "KN",
    "KP", "KR", "KW", "KY", "KZ", "LA", "LB", "LC", "LI", "LK", "LR", "LS",
    "LT", "LU", "LV", "LY", "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK",
    "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW",
    "MX", "MY", "MZ", "NA", "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP",
    "NR", "NU", "NZ", "OM", "PA", "PE", "PF", "PG", "PH", "PK", "PL", "PM",
    "PN", "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS", "RU", "RW",
    "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM",
    "SN", "SO", "SR", "SS", "ST", "SV", "SX", "SY", "SZ", "TC", "TD", "TF",
    "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO", "TR", "TT", "TV", "TW",
    "TZ", "UA", "UG", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI",
    "VN", "VU", "WF", "WS", "YE", "YT", "ZA", "ZM", "ZW",
}


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

    def _normalize_country(self, country: str) -> Optional[str]:
        """
        Normalize country code to uppercase ISO 3166-1 alpha-2.
        Returns None if 'global' or invalid (omit country param = all countries).
        """
        if not country or country.lower().strip() == "global":
            return None
        code = country.strip().upper()
        if code in VALID_COUNTRIES:
            return code
        return None

    def _get_date(self) -> str:
        """Get a safe date for Ahrefs queries (3 days back for data availability)."""
        return (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

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
            country: Country code (e.g., "ca", "us") or "global" for all
            limit: Max keywords to return
            min_volume: Minimum search volume filter

        Returns:
            Dict with 'keywords' list and 'meta' info, or 'error' on failure
        """
        if not self.is_configured:
            return {"error": "Ahrefs API key not configured", "keywords": []}

        date = self._get_date()
        country_code = self._normalize_country(country)

        # Build the where filter using Ahrefs JSON filter syntax
        where_filter = json.dumps({
            "and": [
                {"field": "volume", "is": ["gte", min_volume]},
                {"field": "is_navigational", "is": ["eq", False]},
            ]
        })

        params = {
            "target": domain,
            "mode": "subdomains",
            "date": date,
            "select": "keyword,volume,sum_traffic,best_position,keyword_difficulty,is_informational,is_commercial,is_transactional,is_navigational",
            "where": where_filter,
            "order_by": "sum_traffic:desc",
            "limit": limit,
        }

        # Only add country if it's a valid code (omit for global)
        if country_code:
            params["country"] = country_code

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
                    "country": country_code or "global",
                    "date": date,
                    "total_returned": len(keywords),
                },
            }

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "unknown"
            body = ""
            try:
                body = e.response.text[:300] if e.response else ""
            except Exception:
                pass
            if status == 403:
                return {"error": "Ahrefs API key is invalid or expired", "keywords": []}
            elif status == 429:
                return {"error": "Ahrefs API rate limit reached. Try again in a few minutes.", "keywords": []}
            elif status == 400:
                return {"error": f"Ahrefs API rejected the request. {body}", "keywords": []}
            return {"error": f"Ahrefs API error (HTTP {status}): {body}", "keywords": []}
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
            country: Country code or "global"
            limit: Max competitors to return (default 10 per Tiffany's request)

        Returns:
            Dict with 'competitors' list and 'meta' info, or 'error' on failure
        """
        if not self.is_configured:
            return {"error": "Ahrefs API key not configured", "competitors": []}

        date = self._get_date()
        country_code = self._normalize_country(country)

        params = {
            "target": domain,
            "mode": "subdomains",
            "date": date,
            "select": "competitor_domain,keywords_common,keywords_competitor,traffic",
            "order_by": "keywords_common:desc",
            "limit": limit,
        }

        # Country is required for organic-competitors endpoint
        # Default to US if global/invalid
        params["country"] = country_code or "US"

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
                    "country": country_code or "US",
                    "date": date,
                    "total_returned": len(competitors),
                },
            }

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "unknown"
            body = ""
            try:
                body = e.response.text[:300] if e.response else ""
            except Exception:
                pass
            if status == 403:
                return {"error": "Ahrefs API key is invalid or expired", "competitors": []}
            elif status == 429:
                return {"error": "Ahrefs API rate limit reached. Try again in a few minutes.", "competitors": []}
            elif status == 400:
                return {"error": f"Ahrefs API rejected the request. {body}", "competitors": []}
            return {"error": f"Ahrefs API error (HTTP {status}): {body}", "competitors": []}
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

        date = self._get_date()

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
