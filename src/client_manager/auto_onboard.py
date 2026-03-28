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
        """Create personas by clustering keywords into topic groups.

        Instead of generic intent labels ('Information Seeker'), this finds
        the actual TOPICS in the keyword set and names personas after them.
        Example for Saint Javelin: 'Ukrainian Apparel Shopper', 'NAFO Supporter',
        'Cultural Heritage Explorer' — real groups based on real keywords.

        Falls back to intent-based grouping if topic clustering produces
        too few groups.
        """
        if not self.filtered_keywords:
            return [{
                "id": "persona_1",
                "name": "General User",
                "weight": 1.0,
                "description": f"Users searching for information about {self.brand_name}",
                "priority_topics": [],
            }]

        # ── Step 1: Extract topic clusters from keywords ──────────────
        topic_clusters = self._cluster_keywords_by_topic()

        # ── Step 2: Build personas from clusters ──────────────────────
        if len(topic_clusters) >= 3:
            personas = self._personas_from_topic_clusters(topic_clusters)
        else:
            # Not enough topic diversity — use intent-based with real keywords
            personas = self._personas_from_intent_groups()

        # Normalize weights
        total_weight = sum(p["weight"] for p in personas)
        if total_weight > 0:
            for persona in personas:
                persona["weight"] = round(persona["weight"] / total_weight, 2)

        # Safety fallback
        if not personas:
            personas = [{
                "id": "persona_1",
                "name": "General User",
                "weight": 1.0,
                "description": f"Users searching for information about {self.brand_name}",
                "priority_topics": [kw.get("keyword", "") for kw in self.filtered_keywords[:5]],
            }]

        return personas

    def _cluster_keywords_by_topic(self) -> Dict[str, Dict[str, Any]]:
        """Cluster keywords by shared theme words.

        Extracts significant 'theme words' from keywords (ignoring stopwords
        and single-char words), then groups keywords that share theme words.
        Merges small clusters into an 'Other' bucket.

        Returns:
            Dict mapping theme_label -> {'keywords': [...], 'volume': int}
        """
        # Stopwords to ignore when finding theme words
        stopwords = {
            'the', 'a', 'an', 'of', 'for', 'to', 'in', 'on', 'at', 'by',
            'is', 'it', 'and', 'or', 'with', 'how', 'what', 'where', 'when',
            'who', 'why', 'which', 'do', 'does', 'can', 'vs', 'best', 'top',
            'buy', 'get', 'find', 'near', 'me', 'my', 'i', 'you', 'your',
            'free', 'online', 'new', 'good', 'review', 'reviews', 'price',
            'cost', 'cheap', 'shop', 'store', 'sale', 'from',
        }

        # Count how many keywords contain each significant word
        word_counts = defaultdict(int)
        word_volume = defaultdict(int)
        for kw_data in self.filtered_keywords:
            kw = kw_data.get("keyword", "").lower()
            volume = kw_data.get("volume", 0)
            words = set(kw.split())
            for word in words:
                if len(word) > 2 and word not in stopwords:
                    word_counts[word] += 1
                    word_volume[word] += volume

        # Merge similar theme words (e.g., 'ukraine' + 'ukrainian')
        # Keep the higher-volume variant and combine counts
        raw_themes = [w for w, c in word_counts.items() if c >= 3]
        merged = {}
        for word in sorted(raw_themes, key=lambda w: word_volume[w], reverse=True):
            # Check if this word is a prefix/variant of an existing theme
            found_parent = False
            for parent in list(merged.keys()):
                if (word.startswith(parent) or parent.startswith(word)) and \
                   abs(len(word) - len(parent)) <= 3:
                    # Merge into whichever has more volume
                    if word_volume[word] > word_volume[parent]:
                        merged[word] = merged.pop(parent)
                        merged[word] += word_counts[parent]
                        word_volume[word] += word_volume[parent]
                    else:
                        merged[parent] += word_counts[word]
                        word_volume[parent] += word_volume[word]
                    found_parent = True
                    break
            if not found_parent:
                merged[word] = word_counts[word]

        # Sort by total volume so the biggest themes come first
        theme_words = sorted(
            merged.keys(),
            key=lambda w: word_volume[w],
            reverse=True,
        )

        # Assign each keyword to its highest-volume theme word
        clusters = {}  # theme_word -> {'keywords': [...], 'volume': int}
        assigned = set()

        for theme in theme_words[:20]:  # cap at 20 candidate themes
            cluster_kws = []
            cluster_vol = 0
            for kw_data in self.filtered_keywords:
                kw = kw_data.get("keyword", "").lower()
                kw_id = kw_data.get("keyword", "")
                if kw_id in assigned:
                    continue
                if theme in kw.split():
                    cluster_kws.append(kw_data)
                    cluster_vol += kw_data.get("volume", 0)
                    assigned.add(kw_id)

            if len(cluster_kws) >= 3:
                clusters[theme] = {"keywords": cluster_kws, "volume": cluster_vol}

        # Collect unassigned keywords into 'other'
        other_kws = [kw for kw in self.filtered_keywords
                     if kw.get("keyword", "") not in assigned]
        if other_kws:
            other_vol = sum(kw.get("volume", 0) for kw in other_kws)
            clusters["other"] = {"keywords": other_kws, "volume": other_vol}

        return clusters

    def _personas_from_topic_clusters(self, clusters: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build personas from topic clusters. Max 6 personas."""
        # Sort clusters by volume (biggest first), keep top 5 + merge rest into 'other'
        sorted_themes = sorted(
            [(k, v) for k, v in clusters.items() if k != "other"],
            key=lambda x: x[1]["volume"],
            reverse=True,
        )

        # Take top 5 themes, merge everything else into 'other'
        top_themes = sorted_themes[:5]
        merge_themes = sorted_themes[5:]

        other_cluster = clusters.get("other", {"keywords": [], "volume": 0})
        for theme, data in merge_themes:
            other_cluster["keywords"].extend(data["keywords"])
            other_cluster["volume"] += data["volume"]

        personas = []
        for i, (theme, data) in enumerate(top_themes):
            # Build a readable persona name from the theme word
            persona_name = self._theme_to_persona_name(theme, data["keywords"])
            # Priority topics = top 5 keywords by volume in this cluster
            top_kws = sorted(data["keywords"], key=lambda k: k.get("volume", 0), reverse=True)
            priority_topics = [kw.get("keyword", "") for kw in top_kws[:5]]

            personas.append({
                "id": f"persona_{i + 1}",
                "name": persona_name,
                "weight": data["volume"],  # will be normalized later
                "description": (
                    f"People searching for {theme}-related products and information "
                    f"from {self.brand_name}. Top searches include: {', '.join(priority_topics[:3])}"
                ),
                "priority_topics": priority_topics,
            })

        # Add 'other' cluster if it has keywords
        if other_cluster["keywords"] and len(other_cluster["keywords"]) >= 2:
            top_other = sorted(other_cluster["keywords"],
                               key=lambda k: k.get("volume", 0), reverse=True)
            priority_topics = [kw.get("keyword", "") for kw in top_other[:5]]
            personas.append({
                "id": f"persona_{len(personas) + 1}",
                "name": "General Browser",
                "weight": other_cluster["volume"],
                "description": (
                    f"People exploring {self.brand_name} across various topics. "
                    f"Top searches include: {', '.join(priority_topics[:3])}"
                ),
                "priority_topics": priority_topics,
            })

        return personas

    def _theme_to_persona_name(self, theme: str, keywords: List[Dict]) -> str:
        """Convert a theme word + its keywords into a readable persona name.

        E.g., theme='vyshyvanka' + keywords about shirts → 'Vyshyvanka Shopper'
             theme='nafo' + keywords about patches → 'NAFO Supporter'
             theme='backpack' + tactical keywords → 'Tactical Backpack Buyer'
        """
        # Check if most keywords in this cluster are commercial/transactional
        commercial_count = sum(
            1 for kw in keywords
            if kw.get("is_commercial") or kw.get("is_transactional")
        )
        is_commercial = commercial_count > len(keywords) * 0.4

        # Build the name: capitalize the theme + add a role suffix
        theme_title = theme.title()

        # Pick a descriptive suffix based on the keyword intent mix
        if is_commercial:
            suffix = "Shopper"
        else:
            suffix = "Enthusiast"

        return f"{theme_title} {suffix}"

    def _personas_from_intent_groups(self) -> List[Dict[str, Any]]:
        """Fallback: group by intent but use real keyword topics for names.

        Better than the old 'Information Seeker / Comparison Shopper / Ready Buyer'
        because it pulls actual top keywords as priority_topics and builds
        descriptions from the real data.
        """
        intent_buckets = {
            "informational": {"keywords": [], "volume": 0},
            "commercial": {"keywords": [], "volume": 0},
            "transactional": {"keywords": [], "volume": 0},
        }

        for kw_data in self.filtered_keywords:
            volume = kw_data.get("volume", 0)
            classified = False

            if kw_data.get("is_transactional"):
                intent_buckets["transactional"]["keywords"].append(kw_data)
                intent_buckets["transactional"]["volume"] += volume
                classified = True
            if kw_data.get("is_commercial"):
                intent_buckets["commercial"]["keywords"].append(kw_data)
                intent_buckets["commercial"]["volume"] += volume
                classified = True
            if kw_data.get("is_informational"):
                intent_buckets["informational"]["keywords"].append(kw_data)
                intent_buckets["informational"]["volume"] += volume
                classified = True

            if not classified:
                intent = self.classify_intent(kw_data.get("keyword", ""))
                if intent in ("how_to", "informational", "problem_solving"):
                    intent_buckets["informational"]["keywords"].append(kw_data)
                    intent_buckets["informational"]["volume"] += volume
                else:
                    intent_buckets["commercial"]["keywords"].append(kw_data)
                    intent_buckets["commercial"]["volume"] += volume

        # Build persona names from top keywords in each bucket
        label_map = {
            "informational": ("Researcher", "researching and learning about"),
            "commercial": ("Comparison Shopper", "evaluating and comparing"),
            "transactional": ("Ready Buyer", "ready to purchase"),
        }

        personas = []
        for intent, data in intent_buckets.items():
            if not data["keywords"]:
                continue
            top_kws = sorted(data["keywords"], key=lambda k: k.get("volume", 0), reverse=True)
            priority_topics = [kw.get("keyword", "") for kw in top_kws[:5]]
            top_topic = priority_topics[0] if priority_topics else self.brand_name
            role, action = label_map[intent]

            # Use the top keyword to make the name more specific
            # e.g., "Ukraine Shirt Researcher" instead of just "Researcher"
            top_words = top_topic.split()[:2]
            specific_name = ' '.join(w.title() for w in top_words) + f" {role}"

            personas.append({
                "id": f"persona_{len(personas) + 1}",
                "name": specific_name,
                "weight": data["volume"],
                "description": (
                    f"People {action} {self.brand_name} products. "
                    f"Top searches: {', '.join(priority_topics[:3])}"
                ),
                "priority_topics": priority_topics,
            })

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
        # Generate client slug from brand name
        client_slug = self.brand_name.lower().replace(" ", "_")
        client_slug = re.sub(r"[^a-z0-9_]", "", client_slug)

        # Save into client-specific subdirectory: data/{slug}/
        # This matches the GCS download path so files survive container restarts
        output_path = Path(output_dir) / client_slug
        output_path.mkdir(parents=True, exist_ok=True)

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
