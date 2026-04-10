"""
Topic Cluster Generator — fan-out prompt generation for AI visibility.

Instead of testing one keyword → one prompt, this module generates TOPIC
CLUSTERS that simulate how AI engines actually process queries:

  1. A user types a broad question into ChatGPT / Perplexity / Gemini
  2. The AI engine internally "fans out" into 6-10 specific sub-queries
  3. It synthesizes results from ALL those sub-queries into one answer

Brand citations often come from those secondary fan-out branches, not the
original query. This generator creates prompt clusters that test visibility
across the entire fan-out tree, giving a much more realistic picture of
how a brand is discovered (or missed) by AI engines.

Usage:
    cluster_gen = TopicClusterGenerator(
        persona_manager=persona_manager,
        keyword_processor=keyword_processor,
        api_client=api_client,
        brand_config=brand_config
    )
    clusters = cluster_gen.generate_all_clusters()
    # Returns list of prompt dicts, each tagged with topic_cluster_id
    # and cluster_role ("parent" or "fanout")
"""

import json
import random
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .persona_manager import PersonaManager
from .keyword_processor import KeywordProcessor


# Fan-out sub-query categories. Each cluster should cover several of these
# angles to simulate the breadth of real AI fan-out behavior.
FANOUT_ANGLES = [
    "specific_services",      # Specific programs, services, or products
    "geographic",             # Location-specific or regional variations
    "competitor_alternative", # Competitor or alternative organizations
    "how_to_practical",       # Step-by-step, practical action queries
    "emotional_support",      # Emotional, support-seeking variations
    "eligibility_access",     # Who qualifies, how to access, requirements
]


class TopicClusterGenerator:
    """
    Generates topic-based fan-out prompt clusters for AI visibility testing.

    Each cluster consists of:
      - 1 parent prompt: the broad question a real user would type
      - 5 fan-out prompts: specific sub-queries that AI engines run internally

    All prompts in a cluster share a topic_cluster_id so they can be scored
    together for topic-level visibility metrics.
    """

    def __init__(
        self,
        persona_manager: PersonaManager,
        keyword_processor: KeywordProcessor,
        api_client: Optional[Any] = None,
        brand_config: Optional[Dict[str, Any]] = None,
        fanout_count: int = 5,
        topics_file: Optional[str] = None,
    ):
        """
        Args:
            persona_manager: Loaded PersonaManager instance
            keyword_processor: Loaded KeywordProcessor instance
            api_client: AI API client for generating natural prompts
            brand_config: Brand configuration dict (from brand_config.json)
            fanout_count: Number of fan-out sub-queries per cluster (default 5)
            topics_file: Path to topics.json (the strategic topic definitions).
                         If provided, topics drive everything — each topic maps
                         to specific personas rather than the other way around.
                         If not provided, falls back to persona priority_topics
                         or auto-generated topics.
        """
        self.persona_manager = persona_manager
        self.keyword_processor = keyword_processor
        self.api_client = api_client
        self.brand_config = brand_config or {}
        self.fanout_count = fanout_count
        self.topics_data = self._load_topics(topics_file)

        self.clusters = []  # List of cluster dicts for reporting
        self.all_prompts = []  # Flat list of all prompt dicts (for CSV export)
        self.stats = {
            'total_clusters': 0,
            'total_prompts': 0,
            'by_persona': {},
            'by_topic': {},
            'ai_generated': 0,
            'template_fallback': 0,
            'start_time': None,
            'end_time': None,
        }

    @staticmethod
    def _load_topics(topics_file: Optional[str]) -> Optional[List[Dict[str, Any]]]:
        """Load topics from topics.json if provided."""
        if not topics_file:
            return None
        import os
        if not os.path.exists(topics_file):
            print(f"  ⚠ Topics file not found: {topics_file}")
            return None
        with open(topics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        topics = data.get('topics', [])
        if topics:
            print(f"  Loaded {len(topics)} topics from {os.path.basename(topics_file)}")
        return topics

    # ── Public API ─────────────────────────────────────────────────────

    def generate_all_clusters(self) -> List[Dict[str, Any]]:
        """
        Generate fan-out topic clusters for every persona × priority topic.

        Returns:
            Flat list of prompt dicts (parent + fan-out), each containing:
              - prompt_id, persona, category, intent_type, prompt_text
              - topic_cluster_id:  shared ID linking the cluster
              - cluster_role:      "parent" or "fanout"
              - cluster_topic:     the seed topic
              - fanout_angle:      (fan-out only) which angle this covers
              - expected_visibility_score, notes
        """
        print(f"\n{'='*60}")
        print(f"Starting Topic Cluster Generation (Fan-Out Mode)")
        print(f"{'='*60}")

        self.stats['start_time'] = datetime.now()
        self.all_prompts = []
        self.clusters = []

        # ── Topics-first mode (preferred) ──────────────────────────────
        # When topics.json is loaded, topics drive the generation and each
        # topic maps to its relevant personas.
        if self.topics_data:
            print(f"  Mode: Topics-first ({len(self.topics_data)} topics)")
            for topic_def in self.topics_data:
                topic_name = topic_def['name']
                topic_desc = topic_def.get('description', '')
                persona_ids = topic_def.get('personas', [])

                # Resolve persona objects
                personas_for_topic = []
                for pid in persona_ids:
                    p = self.persona_manager.get_persona_by_id(pid)
                    if p:
                        personas_for_topic.append(p)

                if not personas_for_topic:
                    # If no personas mapped, use all personas
                    personas_for_topic = self.persona_manager.get_all_personas()

                # Generate one cluster per topic × persona combination
                for persona in personas_for_topic:
                    cluster = self._generate_cluster(
                        persona, topic_name, topic_description=topic_desc
                    )
                    if cluster:
                        self.clusters.append(cluster)
                        self.all_prompts.extend(cluster['prompts'])

                        persona_id = persona['id']
                        self.stats['total_clusters'] += 1
                        self.stats['total_prompts'] += len(cluster['prompts'])
                        self.stats['by_persona'][persona_id] = \
                            self.stats['by_persona'].get(persona_id, 0) + 1
                        self.stats['by_topic'][topic_name] = \
                            self.stats['by_topic'].get(topic_name, 0) + len(cluster['prompts'])

                persona_names = ', '.join(p['name'] for p in personas_for_topic)
                print(f"  ✓ {topic_name} → {len(personas_for_topic)} persona(s)")

        # ── Persona-first fallback ─────────────────────────────────────
        # When no topics.json, fall back to persona priority_topics or auto-generation.
        else:
            print(f"  Mode: Persona-first (no topics.json found)")
            personas = self.persona_manager.get_all_personas()

            for persona in personas:
                persona_id = persona['id']
                topics = persona.get('priority_topics', [])

                # Auto-generate topics if none defined
                if not topics:
                    topics = self._infer_topics_from_persona(persona)
                    if topics:
                        print(f"\n{persona['name']} — {len(topics)} topics (auto-generated)")
                    else:
                        print(f"  ⚠ {persona['name']}: could not generate topics, skipping")
                        continue
                else:
                    print(f"\n{persona['name']} — {len(topics)} topics")

                for topic in topics:
                    cluster = self._generate_cluster(persona, topic)
                    if cluster:
                        self.clusters.append(cluster)
                        self.all_prompts.extend(cluster['prompts'])

                        self.stats['total_clusters'] += 1
                        self.stats['total_prompts'] += len(cluster['prompts'])
                        self.stats['by_persona'][persona_id] = \
                            self.stats['by_persona'].get(persona_id, 0) + 1
                        self.stats['by_topic'][topic] = len(cluster['prompts'])

                    # Update stats
                    self.stats['total_clusters'] += 1
                    self.stats['total_prompts'] += len(cluster['prompts'])
                    self.stats['by_persona'][persona_id] = \
                        self.stats['by_persona'].get(persona_id, 0) + 1
                    self.stats['by_topic'][topic] = len(cluster['prompts'])

        self.stats['end_time'] = datetime.now()

        print(f"\n{'='*60}")
        print(f"✓ Generated {self.stats['total_clusters']} clusters, "
              f"{self.stats['total_prompts']} total prompts")
        print(f"  AI-generated: {self.stats['ai_generated']}, "
              f"Template fallback: {self.stats['template_fallback']}")
        print(f"{'='*60}\n")

        return self.all_prompts

    # ── Cluster generation ─────────────────────────────────────────────

    def _generate_cluster(
        self, persona: Dict[str, Any], topic: str,
        topic_description: str = ''
    ) -> Optional[Dict[str, Any]]:
        """
        Generate one topic cluster: 1 parent prompt + N fan-out sub-queries.

        Tries AI generation first, falls back to template-based generation.

        Args:
            persona: Persona dict
            topic: Topic name string
            topic_description: Optional richer description from topics.json
        """
        cluster_id = f"tc_{persona['id']}_{topic.replace(' ', '_')[:30]}_{int(time.time())}"

        # Try AI-powered cluster generation first
        if self.api_client:
            cluster = self._generate_cluster_with_ai(
                persona, topic, cluster_id, topic_description
            )
            if cluster:
                self.stats['ai_generated'] += len(cluster['prompts'])
                print(f"  ✓ {topic}: {len(cluster['prompts'])} prompts (AI)")
                return cluster

        # Fallback: template-based cluster generation
        cluster = self._generate_cluster_with_templates(persona, topic, cluster_id)
        if cluster:
            self.stats['template_fallback'] += len(cluster['prompts'])
            print(f"  ✓ {topic}: {len(cluster['prompts'])} prompts (template)")
        return cluster

    def _generate_cluster_with_ai(
        self, persona: Dict[str, Any], topic: str, cluster_id: str,
        topic_description: str = ''
    ) -> Optional[Dict[str, Any]]:
        """
        Use the AI API to generate a natural topic cluster.

        Sends a single prompt asking for 1 parent query + N fan-out queries,
        with full brand + persona context.
        """
        brand_context = self._build_brand_context()
        persona_context = self._build_persona_context(persona)

        # Find relevant keywords for this topic to give the AI grounding
        related_keywords = self.keyword_processor.select_keywords_for_topic(topic, 8)
        kw_list = ', '.join(kw['keyword'] for kw in related_keywords[:8])

        # Build topic context (richer when topics.json provides a description)
        topic_block = topic
        if topic_description:
            topic_block = f"{topic}\nContext: {topic_description}"

        system_prompt = f"""You are generating a TOPIC CLUSTER for AI visibility testing.

A topic cluster simulates how AI search engines (ChatGPT, Perplexity, Gemini) actually
process user questions. When a user asks a broad question, the AI internally "fans out"
into multiple specific sub-queries to gather information before composing its answer.

--- BRAND ---
{brand_context}

--- PERSONA ---
{persona_context}

--- SEED TOPIC ---
{topic_block}

--- RELATED KEYWORDS (for grounding) ---
{kw_list}

--- YOUR TASK ---
Generate a topic cluster with:

1. ONE parent prompt — the broad, natural question this persona would actually type
   into ChatGPT or Perplexity about this topic. Should be 8-20 words, conversational.

2. {self.fanout_count} fan-out sub-queries — the specific searches an AI engine would
   run internally to build its answer. Each sub-query should cover a DIFFERENT angle:

   - specific_services: Specific programs, services, or products related to the topic
   - geographic: Location-specific or regional variations (province, city, country)
   - competitor_alternative: Competing or alternative organizations/resources
   - how_to_practical: Step-by-step or practical "how do I..." action queries
   - emotional_support: Emotional, support-seeking, or coping-focused variations
   - eligibility_access: Who qualifies, how to access, requirements or criteria

   Pick the {self.fanout_count} most relevant angles for this topic. Not every angle
   applies to every topic — use your judgment.

--- RULES ---
- ALL queries should sound like real people, not marketers or SEO professionals
- Parent prompt should be broad and natural
- Fan-out queries should be SPECIFIC and narrow — these are the "side doors"
- Each fan-out query should be 6-15 words
- Do NOT use the brand name in fan-out queries (the AI engine discovers brands, it
  doesn't search for them by name in fan-out)
- DO mention the brand name naturally in the parent prompt ONLY if a real person would
- Vary sentence structure across the cluster

Return ONLY a JSON object in this exact format:
{{
  "parent": {{
    "prompt": "The broad parent question here",
    "intent": "informational"
  }},
  "fanout": [
    {{
      "prompt": "Specific sub-query here",
      "intent": "commercial",
      "angle": "specific_services"
    }},
    ...
  ]
}}

Return ONLY the JSON object. No other text."""

        try:
            result = self.api_client.send_prompt(
                system_prompt,
                temperature=0.85,
                max_tokens=2000
            )

            if not result['success']:
                return None

            raw = result['response_text'].strip()
            # Strip markdown code fences if present
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
                if raw.endswith('```'):
                    raw = raw[:-3]
                raw = raw.strip()

            parsed = json.loads(raw)
            return self._parsed_cluster_to_prompts(parsed, persona, topic, cluster_id)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"    AI cluster parse error for '{topic}': {e}")
            return None
        except Exception as e:
            print(f"    AI cluster failed for '{topic}': {e}")
            return None

    def _parsed_cluster_to_prompts(
        self,
        parsed: Dict[str, Any],
        persona: Dict[str, Any],
        topic: str,
        cluster_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Convert parsed AI JSON response into structured prompt dicts."""
        prompts = []

        # Parent prompt
        parent = parsed.get('parent', {})
        parent_text = parent.get('prompt', '').strip().strip('"\'')
        if not parent_text or len(parent_text) < 10:
            return None

        parent_intent = parent.get('intent', 'informational')
        prompts.append(self._make_prompt_dict(
            persona=persona,
            prompt_text=parent_text,
            intent_type=parent_intent,
            cluster_id=cluster_id,
            cluster_role='parent',
            cluster_topic=topic,
            fanout_angle=None,
        ))

        # Fan-out sub-queries
        fanout_items = parsed.get('fanout', [])
        for item in fanout_items:
            text = item.get('prompt', '').strip().strip('"\'')
            if not text or len(text) < 8:
                continue
            intent = item.get('intent', 'informational')
            angle = item.get('angle', 'unknown')

            prompts.append(self._make_prompt_dict(
                persona=persona,
                prompt_text=text,
                intent_type=intent,
                cluster_id=cluster_id,
                cluster_role='fanout',
                cluster_topic=topic,
                fanout_angle=angle,
            ))

        if len(prompts) < 2:
            # Need at least parent + 1 fan-out to be useful
            return None

        return {
            'cluster_id': cluster_id,
            'persona': persona['name'],
            'topic': topic,
            'parent_prompt': parent_text,
            'fanout_count': len(prompts) - 1,
            'prompts': prompts,
        }

    def _generate_cluster_with_templates(
        self, persona: Dict[str, Any], topic: str, cluster_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Template-based fallback for cluster generation.

        Uses the topic + persona context to create a parent prompt and
        fan-out variations without an AI API call.
        """
        prompts = []

        # ── Parent prompt ──────────────────────────────────────────────
        parent_templates = [
            "What are my options for {topic} as {context}",
            "I need help with {topic} — where do I start",
            "Can you help me understand {topic}",
            "What should I know about {topic} as {context}",
            "I'm looking for information about {topic}",
            "What's the best approach to {topic}",
        ]

        context = self._get_short_persona_context(persona)
        parent_text = random.choice(parent_templates).format(
            topic=topic, context=context
        )
        prompts.append(self._make_prompt_dict(
            persona=persona,
            prompt_text=parent_text,
            intent_type='informational',
            cluster_id=cluster_id,
            cluster_role='parent',
            cluster_topic=topic,
            fanout_angle=None,
        ))

        # ── Fan-out sub-queries ────────────────────────────────────────
        fanout_templates = {
            'specific_services': [
                "companies that offer {topic}",
                "best providers for {topic}",
                "{topic} services and solutions",
            ],
            'geographic': [
                "{topic} options in Canada",
                "{topic} providers near me",
                "local {topic} options by region",
            ],
            'how_to_practical': [
                "how to get started with {topic}",
                "step by step guide for {topic}",
                "checklist for {topic}",
            ],
            'emotional_support': [
                "common challenges with {topic}",
                "community forums for {topic}",
                "advice from people experienced with {topic}",
            ],
            'eligibility_access': [
                "who qualifies for {topic}",
                "how to access {topic}",
                "requirements for {topic}",
            ],
        }

        # Pick angles and generate fan-out prompts
        angles = random.sample(
            list(fanout_templates.keys()),
            min(self.fanout_count, len(fanout_templates))
        )

        for angle in angles:
            templates = fanout_templates[angle]
            text = random.choice(templates).format(topic=topic)
            prompts.append(self._make_prompt_dict(
                persona=persona,
                prompt_text=text,
                intent_type='informational' if angle != 'specific_services' else 'commercial',
                cluster_id=cluster_id,
                cluster_role='fanout',
                cluster_topic=topic,
                fanout_angle=angle,
            ))

        return {
            'cluster_id': cluster_id,
            'persona': persona['name'],
            'topic': topic,
            'parent_prompt': parent_text,
            'fanout_count': len(prompts) - 1,
            'prompts': prompts,
        }

    # ── Auto-topic inference ──────────────────────────────────────────

    def _infer_topics_from_persona(self, persona: Dict[str, Any]) -> List[str]:
        """
        Auto-generate priority topics for personas that don't have them.

        Uses two strategies:
          1. AI-powered: sends persona description + brand context to the API
             and asks for 5 topic suggestions
          2. Keyword-based fallback: extracts the most relevant keyword clusters
             from the persona description

        Returns:
            List of 3-5 topic strings
        """
        # Strategy 1: AI-powered topic inference
        if self.api_client:
            topics = self._infer_topics_with_ai(persona)
            if topics:
                return topics

        # Strategy 2: Keyword-based fallback
        return self._infer_topics_from_keywords(persona)

    def _infer_topics_with_ai(self, persona: Dict[str, Any]) -> List[str]:
        """Use AI to generate topics from persona description + brand context."""
        brand_context = self._build_brand_context()
        persona_desc = persona.get('description', '')
        persona_name = persona.get('name', 'Unknown')

        system_prompt = f"""Given this brand and persona, suggest exactly 5 topic areas
that this persona would search for in AI engines like ChatGPT or Perplexity.

--- BRAND ---
{brand_context}

--- PERSONA ---
Name: {persona_name}
Description: {persona_desc}

--- RULES ---
- Each topic should be 2-5 words, lowercase
- Topics should be specific enough to generate useful sub-queries
- Topics should match what this persona would actually search for
- Do NOT include the brand name in topics

Return ONLY a JSON array of 5 strings. Example:
["venture debt vs equity", "non-dilutive funding options", "startup growth financing", "debt covenants explained", "revenue-based lending"]
"""
        try:
            result = self.api_client.send_prompt(
                system_prompt, temperature=0.7, max_tokens=500
            )
            if not result['success']:
                return []

            raw = result['response_text'].strip()
            if raw.startswith('```'):
                raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
                if raw.endswith('```'):
                    raw = raw[:-3]
                raw = raw.strip()

            topics = json.loads(raw)
            if isinstance(topics, list) and len(topics) >= 3:
                return [t.strip().lower() for t in topics[:5] if isinstance(t, str)]
        except Exception:
            pass
        return []

    def _infer_topics_from_keywords(self, persona: Dict[str, Any]) -> List[str]:
        """
        Extract topics from persona description by finding matching keyword clusters.

        Splits the persona description into meaningful phrases, then finds
        keywords that overlap. Groups overlapping keywords into topics.
        """
        description = persona.get('description', '').lower()
        if not description:
            return []

        # Extract meaningful noun phrases from the description
        # by looking for multi-word segments that match keywords
        all_keywords = self.keyword_processor.get_all_keywords()
        if not all_keywords:
            return []

        # Score each keyword by relevance to this persona's description
        desc_words = set(description.split())
        scored = []
        for kw in all_keywords:
            kw_text = kw['keyword'].lower()
            kw_words = set(kw_text.split())
            overlap = len(desc_words & kw_words)
            if overlap > 0:
                # Weight by overlap count and search volume
                score = overlap * (1 + kw.get('search_volume', 0) / 1000)
                scored.append((kw_text, score))

        if not scored:
            # No keyword overlap — fall back to extracting key phrases
            # from the description itself
            return self._extract_phrases_from_description(description)

        # Sort by relevance score, take top keywords
        scored.sort(key=lambda x: x[1], reverse=True)

        # Deduplicate overlapping keywords into topics
        topics = []
        seen_words = set()
        for kw_text, _ in scored:
            kw_words = set(kw_text.split())
            if kw_words - seen_words:  # Has at least one new word
                topics.append(kw_text)
                seen_words.update(kw_words)
            if len(topics) >= 5:
                break

        return topics if len(topics) >= 3 else self._extract_phrases_from_description(description)

    @staticmethod
    def _extract_phrases_from_description(description: str) -> List[str]:
        """
        Last-resort topic extraction: pull key phrases from the description.

        Splits on common delimiters and filters to meaningful phrases.
        """
        import re

        # Split on commas, periods, "and", dashes, semicolons
        fragments = re.split(r'[,;.\-–—]|\band\b|\bor\b', description)
        phrases = []
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'shall',
            'of', 'in', 'to', 'for', 'with', 'on', 'at', 'from', 'by',
            'as', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'out', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'their', 'they', 'them', 'who',
            'which', 'what', 'this', 'that', 'these', 'those', 'other',
        }

        for frag in fragments:
            words = frag.strip().split()
            # Remove leading/trailing stop words
            cleaned = [w for w in words if w.lower() not in stop_words]
            if 2 <= len(cleaned) <= 5:
                phrases.append(' '.join(cleaned).strip())

        # Deduplicate and return top 5
        seen = set()
        unique = []
        for p in phrases:
            p_lower = p.lower()
            if p_lower not in seen and len(p_lower) > 5:
                seen.add(p_lower)
                unique.append(p_lower)
        return unique[:5]

    # ── Helpers ─────────────────────────────────────────────────────────

    def _make_prompt_dict(
        self,
        persona: Dict[str, Any],
        prompt_text: str,
        intent_type: str,
        cluster_id: str,
        cluster_role: str,
        cluster_topic: str,
        fanout_angle: Optional[str],
    ) -> Dict[str, Any]:
        """Build a standardized prompt dict compatible with the main generator's CSV schema."""
        prompt_id = f"tc_{int(time.time()*1000)}_{random.randint(1000, 9999)}"

        # Map intent to category (same logic as PromptBuilder.categorize_prompt)
        category_map = {
            'informational': 'educational',
            'commercial': 'business',
            'transactional': 'business',
            'review': 'business',
            'comparison': 'business',
        }
        category = category_map.get(intent_type, 'educational')

        role_label = "Parent" if cluster_role == 'parent' else f"Fan-out ({fanout_angle})"
        notes = f"Topic cluster: {cluster_topic} | {role_label}"

        return {
            'prompt_id': prompt_id,
            'persona': persona['name'],
            'category': category,
            'intent_type': intent_type,
            'prompt_text': prompt_text,
            'expected_visibility_score': 5.0,  # Neutral — fan-out is exploratory
            'notes': notes,
            # ── Topic cluster fields ──
            'topic_cluster_id': cluster_id,
            'cluster_role': cluster_role,        # "parent" or "fanout"
            'cluster_topic': cluster_topic,      # the seed topic string
            'fanout_angle': fanout_angle or '',   # e.g. "specific_services"
        }

    def _build_brand_context(self) -> str:
        """Build brand context string for AI prompts."""
        brand = self.brand_config.get('brand', {})
        parts = []
        if brand.get('name'):
            parts.append(f"Brand: {brand['name']}")
        if brand.get('description'):
            parts.append(f"Industry: {brand['description']}")
        goals = brand.get('business_goals', {})
        if goals.get('market_positioning'):
            parts.append(f"Positioning: {goals['market_positioning']}")

        competitors_section = self.brand_config.get('competitors', {})
        if isinstance(competitors_section, dict):
            names = [c.get('name', '') for c in competitors_section.get('expected', [])]
        elif isinstance(competitors_section, list):
            names = []
            for c in competitors_section:
                if isinstance(c, str):
                    names.append(c)
                elif isinstance(c, dict):
                    names.append(c.get('name', c.get('domain', str(c))))
        else:
            names = []
        if names:
            parts.append(f"Competitors: {', '.join(names[:5])}")

        return '\n'.join(parts)

    def _build_persona_context(self, persona: Dict[str, Any]) -> str:
        """Build rich persona context for AI prompts."""
        parts = [f"Persona: {persona.get('name', 'Unknown')}"]
        parts.append(f"Description: {persona.get('description', '')}")
        if persona.get('caregiving_role'):
            parts.append(f"Role: {persona['caregiving_role']}")
        if persona.get('key_trigger'):
            parts.append(f"Trigger: {persona['key_trigger']}")
        if persona.get('priority_program'):
            parts.append(f"Key program: {persona['priority_program']}")
        if persona.get('top_barrier'):
            parts.append(f"Barrier: {persona['top_barrier']}")
        if persona.get('priority_topics'):
            parts.append(f"Topics: {', '.join(persona['priority_topics'][:5])}")
        return '\n'.join(parts)

    def _get_short_persona_context(self, persona: Dict[str, Any]) -> str:
        """Short natural-language context for template generation."""
        role = persona.get('caregiving_role', '') or persona.get('role', '')
        if role:
            return role.lower()
        name = persona.get('name', '')
        if name:
            return f"a {name.lower()}"
        return "someone seeking support"

    # ── Reporting ──────────────────────────────────────────────────────

    def get_cluster_summary(self) -> str:
        """Return a human-readable summary of generated clusters."""
        if not self.clusters:
            return "No clusters generated yet."

        lines = []
        lines.append(f"Topic Clusters: {len(self.clusters)}")
        lines.append(f"Total Prompts:  {self.stats['total_prompts']}")
        lines.append("")

        for cluster in self.clusters:
            lines.append(f"  [{cluster['persona']}] {cluster['topic']}")
            lines.append(f"    Parent: {cluster['parent_prompt']}")
            lines.append(f"    Fan-out queries: {cluster['fanout_count']}")
            lines.append("")

        return '\n'.join(lines)
