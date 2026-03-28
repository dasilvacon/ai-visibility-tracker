"""
Client Auto-Onboarding Engine for AI Visibility Tracker.

Automates the generation of keywords.csv, personas.json, and brand_config.json
for new clients using Ahrefs API data or manual input.

This script is designed to work in two modes:
1. "ahrefs_data" mode: accepts pre-fetched Ahrefs data (dicts) from MCP tools
2. "manual" mode: accepts raw keyword lists and competitor lists

The script DOES NOT make API calls directly — it processes data passed in from
external sources (Streamlit dashboard or Cowork).
"""

import csv
import json
import os
import re
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class ClientAutoOnboarder:
    """
    Automates client onboarding by generating configuration files from Ahrefs data
    or manual input.
    """

    # French/non-English stopwords for language detection
    FRENCH_PATTERNS = {
        "du", "de", "des", "le", "la", "les", "un", "une", "et", "en", "au",
        "aux", "deuil", "phase", "etape", "artinya", "objectifs", "smart",
        "decede", "decedee", "prealable"
    }

    # Generic single words that are too broad
    GENERIC_WORDS = {
        "oco", "read", "scale", "health", "support", "information", "resources",
        "community", "help", "care", "tips", "advice", "guide", "review",
        "about", "contact", "home", "page", "site", "web", "link"
    }

    # Navigational keyword patterns
    NAV_PATTERNS = [
        r"login", r"sign in", r"signin", r"sign-in", r"register", r"signup",
        r"www\.", r"\.com", r"\.ca", r"\.org", r"\.co\.uk", r"site:",
        r"homepage", r"home page"
    ]

    def __init__(self, brand_name: str, domain: str, countries: str = "ca"):
        """
        Initialize the client auto-onboarder.

        Args:
            brand_name: Full name of the brand (e.g., "Ontario Caregiver Organization")
            domain: Domain of the brand (e.g., "ontariocaregiver.ca")
            countries: Comma-separated country codes or "global" for worldwide
                       Examples: "ca", "us,ca", "global"
                       When pulling Ahrefs data, each country should be queried separately
                       and the results merged via ingest_ahrefs_keywords()
        """
        self.brand_name = brand_name
        self.domain = domain
        # Parse countries — "global" is a special flag, otherwise split comma-separated codes
        if countries.lower().strip() == "global":
            self.countries = ["global"]
        else:
            self.countries = [c.strip().lower() for c in countries.split(",") if c.strip()]
        # Keep a primary country for backward compatibility
        self.country = self.countries[0] if self.countries else "us"

        # Data containers
        self.raw_keywords = []
        self.raw_competitors = []
        self.questionnaire_data = {}
        self.filtered_keywords = []
        self.generated_personas = []

        # Statistics
        self.stats = {
            "raw_keywords_count": 0,
            "keywords_after_filtering": 0,
            "filtered_out_reasons": defaultdict(int),
            "personas_generated": 0,
            "competitors_identified": 0,
        }

    def ingest_ahrefs_keywords(
        self,
        organic_keywords_data: List[Dict[str, Any]],
        related_terms_data: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Ingest raw Ahrefs keyword data.

        Expected fields in organic_keywords_data:
        - keyword: str
        - volume: int (search volume)
        - sum_traffic: int (estimated traffic if ranking)
        - best_position: int (current best position)
        - keyword_difficulty: int (0-100)
        - is_informational: bool
        - is_commercial: bool
        - is_transactional: bool
        - is_navigational: bool

        Expected fields in related_terms_data:
        - keyword: str
        - volume: int
        - difficulty: int
        - traffic_potential: int
        - intents: dict with keys: informational, navigational, commercial, transactional

        Args:
            organic_keywords_data: List of organic keyword dicts from Ahrefs
            related_terms_data: Optional list of related keyword dicts from Ahrefs
        """
        self.raw_keywords = []

        # Process organic keywords
        if organic_keywords_data:
            for kw_data in organic_keywords_data:
                kw = {
                    "keyword": kw_data.get("keyword", "").strip(),
                    "volume": kw_data.get("volume", 0),
                    "traffic_potential": kw_data.get("sum_traffic", 0),
                    "position": kw_data.get("best_position"),
                    "difficulty": kw_data.get("keyword_difficulty", 0),
                    "is_informational": kw_data.get("is_informational", False),
                    "is_commercial": kw_data.get("is_commercial", False),
                    "is_transactional": kw_data.get("is_transactional", False),
                    "is_navigational": kw_data.get("is_navigational", False),
                    "intents": {},
                }
                if kw["keyword"]:
                    self.raw_keywords.append(kw)

        # Process related terms (lower priority, higher volume threshold)
        if related_terms_data:
            for kw_data in related_terms_data:
                kw = {
                    "keyword": kw_data.get("keyword", "").strip(),
                    "volume": kw_data.get("volume", 0),
                    "traffic_potential": kw_data.get("traffic_potential", 0),
                    "position": None,
                    "difficulty": kw_data.get("difficulty", 0),
                    "is_informational": False,
                    "is_commercial": False,
                    "is_transactional": False,
                    "is_navigational": False,
                    "intents": kw_data.get("intents", {}),
                }
                if kw["keyword"]:
                    self.raw_keywords.append(kw)

        self.stats["raw_keywords_count"] = len(self.raw_keywords)

    def ingest_ahrefs_competitors(
        self, competitors_data: List[Dict[str, Any]]
    ) -> None:
        """
        Ingest raw Ahrefs competitor data.

        Expected fields:
        - competitor_domain: str
        - keywords_common: int (keywords both rank for)
        - keywords_competitor: int (keywords only competitor ranks for)
        - traffic: int (estimated monthly traffic)

        Args:
            competitors_data: List of competitor dicts from Ahrefs
        """
        self.raw_competitors = []
        seen_domains = set()

        for comp_data in competitors_data:
            domain = comp_data.get("competitor_domain", "").strip()
            if domain and domain not in seen_domains:
                self.raw_competitors.append({
                    "domain": domain,
                    "keywords_common": comp_data.get("keywords_common", 0),
                    "keywords_exclusive": comp_data.get("keywords_competitor", 0),
                    "traffic": comp_data.get("traffic", 0),
                })
                seen_domains.add(domain)

        self.stats["competitors_identified"] = len(self.raw_competitors)

    def ingest_questionnaire(self, questionnaire_data: Dict[str, Any]) -> None:
        """
        Ingest structured data from a strategy questionnaire.

        Expected fields:
        - business_description: str
        - target_audiences: list[str]
        - key_features: list[str]
        - differentiators: list[str]
        - important_topics: list[str]
        - customer_questions: list[str]
        - competitors_manual: list[str]

        Args:
            questionnaire_data: Dict with questionnaire fields
        """
        self.questionnaire_data = questionnaire_data

    def _is_non_english(self, keyword: str) -> bool:
        """
        Detect if a keyword is likely non-English (French, etc.).

        Args:
            keyword: Keyword to check

        Returns:
            True if likely non-English, False otherwise
        """
        words = keyword.lower().split()
        french_matches = sum(1 for w in words if w in self.FRENCH_PATTERNS)
        return french_matches / len(words) >= 0.5 if words else False

    def _is_navigational(self, keyword: str) -> bool:
        """
        Check if a keyword is navigational (brand/domain search).

        Args:
            keyword: Keyword to check

        Returns:
            True if navigational, False otherwise
        """
        kw_lower = keyword.lower()
        for pattern in self.NAV_PATTERNS:
            if re.search(pattern, kw_lower, re.IGNORECASE):
                return True
        return False

    def _is_self_branded(self, keyword: str) -> bool:
        """
        Check if a keyword is just the client's own brand name or domain.

        Args:
            keyword: Keyword to check

        Returns:
            True if self-branded, False otherwise
        """
        kw_lower = keyword.lower()
        brand_lower = self.brand_name.lower()
        domain_lower = self.domain.lower()

        # Exact or near-exact match to brand or domain
        if kw_lower == brand_lower or kw_lower == domain_lower:
            return True

        # Check if keyword is mostly just the brand/domain
        words = kw_lower.split()
        brand_words = brand_lower.split()
        domain_words = domain_lower.split()

        for word in words:
            if word not in brand_words and word not in domain_words:
                # Has words beyond brand/domain, so not purely self-branded
                return False

        return True

    def _is_too_generic(self, keyword: str) -> bool:
        """
        Check if a keyword is too generic/broad.

        Args:
            keyword: Keyword to check

        Returns:
            True if too generic, False otherwise
        """
        words = keyword.lower().split()

        # If it's a single word and it's in the generic list, filter it
        if len(words) == 1 and words[0] in self.GENERIC_WORDS:
            return True

        # If it's very short and not compound, it's probably generic
        if len(words) <= 2:
            kw_lower = keyword.lower()
            if len(kw_lower) <= 4 and kw_lower in self.GENERIC_WORDS:
                return True

        return False

    def filter_keywords(self) -> List[Dict[str, Any]]:
        """
        Filter keywords to remove noise and keep high-quality, relevant keywords.

        For AI visibility tracking, we KEEP brand keywords (people searching
        for the brand should find it in AI responses). We only remove true
        junk: navigational (login), foreign language, zero-volume, and
        exact duplicates.

        Returns:
            List of filtered, deduplicated keywords
        """
        self.filtered_keywords = []
        filtered_out = defaultdict(int)

        seen_keywords = set()
        temp_keywords = []

        for kw_data in self.raw_keywords:
            keyword = kw_data.get("keyword", "").strip()
            volume = kw_data.get("volume", 0)

            if not keyword:
                filtered_out["empty"] += 1
                continue

            # Normalize for deduplication (remove extra spaces)
            normalized = " ".join(keyword.split()).lower()
            if normalized in seen_keywords:
                filtered_out["duplicate"] += 1
                continue

            seen_keywords.add(normalized)

            # Volume check — but keep keywords with any traffic
            traffic = kw_data.get("traffic_potential", 0) or kw_data.get("sum_traffic", 0)
            if volume == 0 and traffic == 0:
                filtered_out["no_volume"] += 1
                continue

            # Navigational check (login, sign in, etc.) — these are useless
            if kw_data.get("is_navigational") or self._is_navigational(keyword):
                filtered_out["navigational"] += 1
                continue

            # NOTE: We intentionally do NOT filter self-branded keywords.
            # For AI visibility tracking, brand keywords are essential —
            # you need to know if AI engines mention you when someone asks
            # about your brand by name.

            # Language check
            if self._is_non_english(keyword):
                filtered_out["non_english"] += 1
                continue

            # Generic check — only filter single generic words
            if self._is_too_generic(keyword):
                filtered_out["too_generic"] += 1
                continue

            temp_keywords.append(kw_data)

        # Light dedup: only remove exact singular/plural matches, keep variations
        # like "ukraine shirt" vs "ukraine shirts" since AI engines may answer differently
        self.filtered_keywords = temp_keywords

        self.stats["keywords_after_filtering"] = len(self.filtered_keywords)
        self.stats["filtered_out_reasons"] = dict(filtered_out)

        return self.filtered_keywords

    def _deduplicate_near_matches(
        self, keywords: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove near-duplicate keywords (e.g., singular/plural variants).

        Args:
            keywords: List of keyword dicts to deduplicate

        Returns:
            Deduplicated list
        """
        seen_base_forms = {}

        for kw_data in keywords:
            keyword = kw_data.get("keyword", "").lower().strip()

            # Simple normalization: remove trailing 's' for plural matching
            base = keyword.rstrip("s")
            if base.endswith("ies"):
                base = base[:-3] + "y"

            # Keep the one with higher volume
            if base not in seen_base_forms:
                seen_base_forms[base] = kw_data
            else:
                existing = seen_base_forms[base]
                if kw_data.get("volume", 0) > existing.get("volume", 0):
                    seen_base_forms[base] = kw_data

        return list(seen_base_forms.values())

    def classify_intent(
        self, keyword: str, ahrefs_intents: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Classify the search intent of a keyword.

        Args:
            keyword: The keyword to classify
            ahrefs_intents: Optional Ahrefs intent dict with boolean flags

        Returns:
            Intent type: 'informational', 'how_to', 'comparison', 'problem_solving',
                        'recommendation', 'review'
        """
        keyword_lower = keyword.lower()

        # Check for explicit patterns first
        if keyword_lower.startswith(("how to ", "how do ")):
            return "how_to"

        if any(x in keyword_lower for x in [" vs ", " versus ", " compared to ", " or "]):
            return "comparison"

        if any(x in keyword_lower for x in ["best ", "top ", "which ", "recommend"]):
            return "recommendation"

        if any(x in keyword_lower for x in ["review", "worth it", "is ", "good ", "quality"]):
            return "review"

        if any(x in keyword_lower for x in ["fix", "problem", "issue", "not working", "error"]):
            return "problem_solving"

        # Use Ahrefs intent flags if available
        if ahrefs_intents:
            if ahrefs_intents.get("transactional"):
                return "problem_solving"
            if ahrefs_intents.get("commercial"):
                return "recommendation"

        # Default to informational
        return "informational"

    def generate_personas(self) -> List[Dict[str, Any]]:
        """
        Generate personas based on keywords or questionnaire data.

        If questionnaire data exists, uses target_audiences and important_topics.
        Otherwise, clusters keywords by topic to create personas.

        Returns:
            List of persona dicts with id, name, weight, description, priority_topics
        """
        self.generated_personas = []

        # Prefer questionnaire-based personas if available
        if self.questionnaire_data and self.questionnaire_data.get("target_audiences"):
            self.generated_personas = self._personas_from_questionnaire()
        elif self.filtered_keywords:
            self.generated_personas = self._personas_from_keywords()
        else:
            # Fallback: create a single generic persona
            self.generated_personas = [
                {
                    "id": "generic_user",
                    "name": "General User",
                    "weight": 1.0,
                    "description": f"Users searching for information about {self.brand_name}",
                    "priority_topics": [],
                }
            ]

        self.stats["personas_generated"] = len(self.generated_personas)
        return self.generated_personas

    def _personas_from_questionnaire(self) -> List[Dict[str, Any]]:
        """Create personas from questionnaire data."""
        personas = []
        target_audiences = self.questionnaire_data.get("target_audiences", [])
        important_topics = self.questionnaire_data.get("important_topics", [])

        # Create one persona per target audience (up to 6)
        num_personas = min(len(target_audiences), 6)
        weight_per_persona = 1.0 / num_personas if num_personas > 0 else 1.0

        for i, audience in enumerate(target_audiences[:num_personas]):
            persona_id = f"persona_{i+1}"
            personas.append({
                "id": persona_id,
                "name": audience,
                "weight": weight_per_persona,
                "description": f"Target audience: {audience}. Interested in {self.brand_name} offerings.",
                "priority_topics": important_topics[:5] if important_topics else [],
            })

        return personas

    def _personas_from_keywords(self) -> List[Dict[str, Any]]:
        """Create personas based on intent distribution across keywords.

        Instead of clustering by keyword words (which produces garbage like
        'The Ukraine Focused User'), this creates universal intent-based
        personas weighted by the actual keyword data.
        """
        # Count keywords and volume by intent
        intent_buckets = {
            "informational": {"keywords": [], "volume": 0},
            "commercial": {"keywords": [], "volume": 0},
            "transactional": {"keywords": [], "volume": 0},
        }

        for kw_data in self.filtered_keywords:
            volume = kw_data.get("volume", 0)

            if kw_data.get("is_transactional"):
                intent_buckets["transactional"]["keywords"].append(kw_data)
                intent_buckets["transactional"]["volume"] += volume
            if kw_data.get("is_commercial"):
                intent_buckets["commercial"]["keywords"].append(kw_data)
                intent_buckets["commercial"]["volume"] += volume
            if kw_data.get("is_informational"):
                intent_buckets["informational"]["keywords"].append(kw_data)
                intent_buckets["informational"]["volume"] += volume

            # If no intent flags, classify by pattern
            if not any(kw_data.get(f"is_{t}") for t in ["informational", "commercial", "transactional", "navigational"]):
                intent = self.classify_intent(kw_data.get("keyword", ""))
                if intent in ("how_to", "informational", "problem_solving"):
                    intent_buckets["informational"]["keywords"].append(kw_data)
                    intent_buckets["informational"]["volume"] += volume
                elif intent in ("recommendation", "comparison", "review"):
                    intent_buckets["commercial"]["keywords"].append(kw_data)
                    intent_buckets["commercial"]["volume"] += volume
                else:
                    intent_buckets["commercial"]["keywords"].append(kw_data)
                    intent_buckets["commercial"]["volume"] += volume

        # Define persona templates — these work for any business
        persona_templates = [
            {
                "intent": "informational",
                "name": "Information Seeker",
                "description": f"People researching topics related to {self.brand_name}. They're looking for answers, guides, and educational content.",
            },
            {
                "intent": "commercial",
                "name": "Comparison Shopper",
                "description": f"People evaluating {self.brand_name} against alternatives. They want reviews, comparisons, and recommendations.",
            },
            {
                "intent": "transactional",
                "name": "Ready Buyer",
                "description": f"People ready to purchase from or engage with {self.brand_name}. They're searching for specific products or services.",
            },
        ]

        # Build personas from templates, weighted by actual keyword volume
        personas = []
        total_volume = sum(b["volume"] for b in intent_buckets.values())
        if total_volume == 0:
            total_volume = 1  # avoid division by zero

        for i, template in enumerate(persona_templates):
            bucket = intent_buckets.get(template["intent"], {"keywords": [], "volume": 0})
            if not bucket["keywords"]:
                continue  # skip empty intent buckets

            weight = bucket["volume"] / total_volume
            # Extract top topics from this bucket's keywords
            priority_topics = list(set(
                kw.get("keyword", "") for kw in bucket["keywords"][:5]
            ))

            personas.append({
                "id": f"persona_{i + 1}",
                "name": template["name"],
                "weight": round(weight, 2),
                "description": template["description"],
                "priority_topics": priority_topics,
            })

        # Normalize weights
        total_weight = sum(p["weight"] for p in personas)
        if total_weight > 0:
            for persona in personas:
                persona["weight"] = round(persona["weight"] / total_weight, 2)

        # If we ended up with nothing (unlikely), create a default
        if not personas:
            personas = [
                {
                    "id": "persona_1",
                    "name": "General User",
                    "weight": 1.0,
                    "description": f"Users searching for information about {self.brand_name}",
                    "priority_topics": [kw.get("keyword", "") for kw in self.filtered_keywords[:5]],
                }
            ]

        return personas

    def generate_brand_config(self) -> Dict[str, Any]:
        """
        Generate brand configuration from ingested data.

        Returns:
            Dict with brand, competitors, source_categories, known_sources
        """
        # Build brand info
        brand_config = {
            "brand": {
                "name": self.brand_name,
                "domain": self.domain,
                "description": self.questionnaire_data.get("business_description", ""),
                "countries": self.countries,
            },
            "competitors": [],
            "known_sources": [],
            "source_categories": {
                "government": [],
                "academic": [],
                "media": [],
                "industry": [],
                "other": [],
            },
            "irrelevant_sources": [],
        }

        # Add competitors from Ahrefs
        for comp in self.raw_competitors:
            domain = comp.get("domain", "")
            competitors_list = brand_config["competitors"]

            # Avoid duplicates
            if not any(c.get("website") == domain for c in competitors_list):
                competitors_list.append({
                    "name": domain.replace("www.", "").split(".")[0].title(),
                    "website": domain,
                    "category": "direct",
                    "added_date": datetime.now().strftime("%Y-%m-%d"),
                    "notes": f"Common keywords: {comp.get('keywords_common', 0)}"
                })

        # Add competitors from questionnaire
        for comp_name in self.questionnaire_data.get("competitors_manual", []):
            competitors_list = brand_config["competitors"]
            if not any(c.get("name") == comp_name for c in competitors_list):
                competitors_list.append({
                    "name": comp_name,
                    "website": "",
                    "category": "direct",
                    "added_date": datetime.now().strftime("%Y-%m-%d"),
                    "notes": "From questionnaire"
                })

        # Categorize sources (known_sources would come from various sources in practice)
        # For now, we'll add competitor domains as sources
        for comp in self.raw_competitors:
            domain = comp.get("domain", "")
            source_obj = {"domain": domain}

            # Categorize by domain pattern
            if ".gov" in domain or ".gc.ca" in domain or ".on.ca" in domain:
                brand_config["source_categories"]["government"].append(source_obj)
            elif ".edu" in domain or ".ac.uk" in domain:
                brand_config["source_categories"]["academic"].append(source_obj)
            elif any(x in domain for x in ["bbc", "cnn", "globe", "times", "nyt"]):
                brand_config["source_categories"]["media"].append(source_obj)
            else:
                brand_config["source_categories"]["industry"].append(source_obj)

            brand_config["known_sources"].append(source_obj)

        return brand_config

    def save_client_files(self, output_dir: str) -> Dict[str, Any]:
        """
        Save generated files to disk.

        Creates:
        - {client_slug}_keywords.csv
        - {client_slug}_personas.json
        - {client_slug}_brand_config.json

        Args:
            output_dir: Directory to save files to

        Returns:
            Summary dict with file paths and stats
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate client slug from brand name
        client_slug = self.brand_name.lower().replace(" ", "_")
        client_slug = re.sub(r"[^a-z0-9_]", "", client_slug)

        summary = {
            "client_name": self.brand_name,
            "client_slug": client_slug,
            "created_at": datetime.now().isoformat(),
            "files": {},
        }

        # Save keywords CSV
        keywords_file = output_path / f"{client_slug}_keywords.csv"
        with open(keywords_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["keyword", "search_volume", "intent_type", "competitor_brands"])
            writer.writeheader()

            for kw_data in self.filtered_keywords:
                intent = self.classify_intent(kw_data.get("keyword", ""))
                writer.writerow({
                    "keyword": kw_data.get("keyword", ""),
                    "search_volume": kw_data.get("volume", 0),
                    "intent_type": intent,
                    "competitor_brands": "",  # Will be populated in separate enrichment step
                })

        summary["files"]["keywords"] = str(keywords_file)
        summary["files"]["keywords_count"] = len(self.filtered_keywords)

        # Save personas JSON
        personas_file = output_path / f"{client_slug}_personas.json"
        with open(personas_file, "w", encoding="utf-8") as f:
            json.dump({"personas": self.generated_personas}, f, indent=2, ensure_ascii=False)

        summary["files"]["personas"] = str(personas_file)
        summary["files"]["personas_count"] = len(self.generated_personas)

        # Save brand config JSON
        brand_config_file = output_path / f"{client_slug}_brand_config.json"
        brand_config = self.generate_brand_config()
        with open(brand_config_file, "w", encoding="utf-8") as f:
            json.dump(brand_config, f, indent=2, ensure_ascii=False)

        summary["files"]["brand_config"] = str(brand_config_file)
        summary["files"]["competitors_count"] = len(brand_config.get("competitors", []))

        return summary

    def get_onboarding_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the onboarding process.

        Returns:
            Dict with statistics and metadata
        """
        return {
            "brand_name": self.brand_name,
            "domain": self.domain,
            "countries": self.countries,
            "statistics": {
                "raw_keywords": self.stats["raw_keywords_count"],
                "keywords_after_filtering": self.stats["keywords_after_filtering"],
                "filter_rejection_reasons": dict(self.stats["filtered_out_reasons"]),
                "personas_generated": self.stats["personas_generated"],
                "competitors_identified": self.stats["competitors_identified"],
            },
            "personas": [
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "weight": p.get("weight"),
                }
                for p in self.generated_personas
            ],
            "keywords_sample": [
                {
                    "keyword": k.get("keyword"),
                    "volume": k.get("volume"),
                    "intent": self.classify_intent(k.get("keyword", "")),
                }
                for k in self.filtered_keywords[:10]
            ],
        }


# Example usage
if __name__ == "__main__":
    # Example 1: Onboarding with Ahrefs data
    print("=" * 70)
    print("EXAMPLE: Auto-Onboarding with Ahrefs Data")
    print("=" * 70)

    # Mock Ahrefs data
    mock_organic_keywords = [
        {
            "keyword": "caregiver support",
            "volume": 200,
            "sum_traffic": 150,
            "best_position": 5,
            "keyword_difficulty": 45,
            "is_informational": True,
            "is_commercial": False,
            "is_transactional": False,
            "is_navigational": False,
        },
        {
            "keyword": "how to find a caregiver",
            "volume": 80,
            "sum_traffic": 60,
            "best_position": 12,
            "keyword_difficulty": 30,
            "is_informational": True,
            "is_commercial": False,
            "is_transactional": False,
            "is_navigational": False,
        },
        {
            "keyword": "caregiver vs family care",
            "volume": 45,
            "sum_traffic": 30,
            "best_position": 8,
            "keyword_difficulty": 35,
            "is_informational": False,
            "is_commercial": False,
            "is_transactional": False,
            "is_navigational": False,
        },
        {
            "keyword": "login",
            "volume": 5000,
            "sum_traffic": 4000,
            "best_position": 1,
            "keyword_difficulty": 0,
            "is_informational": False,
            "is_commercial": False,
            "is_transactional": False,
            "is_navigational": True,
        },
        {
            "keyword": "phase du deuil",
            "volume": 300,
            "sum_traffic": 200,
            "best_position": 3,
            "keyword_difficulty": 20,
            "is_informational": True,
            "is_commercial": False,
            "is_transactional": False,
            "is_navigational": False,
        },
    ]

    mock_competitors = [
        {
            "competitor_domain": "eldercare.com",
            "keywords_common": 45,
            "keywords_competitor": 120,
            "traffic": 5000,
        },
        {
            "competitor_domain": "caregiversupport.org",
            "keywords_common": 30,
            "keywords_competitor": 80,
            "traffic": 3000,
        },
    ]

    mock_questionnaire = {
        "business_description": "Ontario Caregiver Organization provides support programs for family caregivers.",
        "target_audiences": [
            "Adult child caregivers",
            "Spousal caregivers",
            "Young caregivers"
        ],
        "key_features": ["Support groups", "Helpline", "Coaching"],
        "differentiators": ["Government-funded", "Peer support", "Specialized programs"],
        "important_topics": [
            "caregiver burnout",
            "respite care",
            "caregiver rights",
            "support groups"
        ],
        "customer_questions": [
            "How do I find respite care?",
            "What is caregiver burnout?"
        ],
        "competitors_manual": ["Caregiver Action Network", "The Caregiver Alliance"],
    }

    onboarder = ClientAutoOnboarder(
        brand_name="Ontario Caregiver Organization",
        domain="ontariocaregiver.ca",
        countries="ca"
    )

    onboarder.ingest_ahrefs_keywords(mock_organic_keywords)
    onboarder.ingest_ahrefs_competitors(mock_competitors)
    onboarder.ingest_questionnaire(mock_questionnaire)

    # Filter and generate
    onboarder.filter_keywords()
    onboarder.generate_personas()

    # Save files
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        summary = onboarder.save_client_files(tmpdir)
        print("\nFiles saved:")
        for key, path in summary["files"].items():
            if isinstance(path, str) and path.startswith("/"):
                print(f"  {key}: {path}")

    # Print summary
    print("\nOnboarding Summary:")
    onboarding_summary = onboarder.get_onboarding_summary()
    print(json.dumps(onboarding_summary, indent=2))

    print("\n" + "=" * 70)
    print("Onboarding complete!")
    print("=" * 70)
