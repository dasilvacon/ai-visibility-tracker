"""
Regenerate prompts for one or more clients using Claude Sonnet 4.6.

Writes the v2 "tight Intent+Context" format:
  - Short 15-25 word prompts with one clear intent
  - Explicit `intent` + `context` columns in the CSV
  - Dual text columns (prompt_text for chat-style LLMs, search_query for
    Google AI Overviews / SerpAPI keyword input)

Integrates with `PromptVersionManager` so every regeneration:
  1. Archives the previous active CSV under
     data/prompt-archive/{slug}/{version}/ (immutable)
  2. Writes new active CSV + meta.json sidecar
  3. Optionally mirrors both to GCS

Usage:
  python scripts/regenerate_prompts.py --client ontario_caregiver_organization
  python scripts/regenerate_prompts.py --all
  python scripts/regenerate_prompts.py --all --count 500
  python scripts/regenerate_prompts.py --all --dry-run
  python scripts/regenerate_prompts.py --all --version v2.1-extra-personas

See docs/prompt-versioning.md for version id conventions.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Project root on sys.path so `from src...` works when run from anywhere
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
sys.path.insert(0, str(PROJECT_ROOT))

from src.prompt_generator.version_manager import PromptVersionManager  # noqa: E402

# Anthropic model — matches config/config.json ("claude-sonnet-4-6")
ANTHROPIC_MODEL = "claude-sonnet-4-6"

# Default version id written for a fresh rewrite. Bump the MINOR (e.g.
# v2.1-expanded) when adding prompts to an existing v2 set; bump the
# MAJOR (v3.0-...) when the generation method changes meaningfully.
DEFAULT_VERSION = "v2.0-intent-context"
GENERATOR_VERSION = "2.0"
FORMAT_TAG = "intent_context_v2"

# Tone variations to ensure natural spread across prompts
TONES = [
    "frustrated and overwhelmed",
    "curious and exploratory",
    "time-pressed and direct",
    "skeptical and comparing options",
    "newly aware and confused",
    "detail-oriented and planning ahead",
    "emotional and looking for support",
    "practical and ready to act",
]

INTENT_TYPES = ["informational", "commercial", "navigational", "transactional"]


# ==============================================================================
# CONFIG / API KEY LOADING
# ==============================================================================

def load_anthropic_key() -> str:
    """Load Anthropic API key from env, config.json, or streamlit secrets."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key

    config_path = PROJECT_ROOT / "config" / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)
        key = cfg.get("api_keys", {}).get("anthropic", "")
        if key and not key.startswith("YOUR_"):
            return key

    secrets_path = PROJECT_ROOT / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        key = secrets.get("api_keys", {}).get("anthropic", "")
        if key:
            return key

    print("ERROR: Could not find Anthropic API key in env, config.json, or secrets.toml")
    sys.exit(1)


# ==============================================================================
# CLIENT DATA LOADING
# ==============================================================================

def load_client_data(slug: str) -> Dict:
    """Load brand_config, personas, topics for a client."""
    client_dir = DATA_DIR / slug
    if not client_dir.exists():
        raise FileNotFoundError(f"Client folder not found: {client_dir}")

    brand_config_path = client_dir / f"{slug}_brand_config.json"
    personas_path = client_dir / f"{slug}_personas.json"
    topics_path = client_dir / f"{slug}_topics.json"

    with open(brand_config_path) as f:
        brand_config = json.load(f)
    with open(personas_path) as f:
        personas_data = json.load(f)
    with open(topics_path) as f:
        topics_data = json.load(f)

    personas = personas_data.get("personas", [])
    topics = topics_data.get("topics", [])

    return {
        "slug": slug,
        "brand_config": brand_config,
        "personas": personas,
        "topics": topics,
        "personas_by_id": {p["id"]: p for p in personas},
    }


# ==============================================================================
# PROMPT GENERATION (CLAUDE SONNET 4.6 — TIGHT INTENT+CONTEXT v2)
# ==============================================================================

SYSTEM_PROMPT = """You are writing tight, focused prompts that real people would type into ChatGPT, Claude, Perplexity, or Gemini. Think SMS length, not email length.

OUTPUT FORMAT (for every prompt):
{
  "intent": "<3-6 words naming what the user wants to accomplish>",
  "context": "<3-10 words describing their situation — role, constraint, stage>",
  "prompt_text": "<the actual question the user would type, 15-25 words, 1-2 sentences>",
  "search_query": "<same intent as 3-7 keyword-style words for Google>",
  "tone": "<one of the tones listed in the user message>",
  "intent_type": "<one of: informational | commercial | navigational | transactional>",
  "category": "<one of the categories listed in the user message>"
}

HARD RULES:
1. prompt_text must be 15-25 words. Count them. Reject your own draft if it runs long.
2. ONE intent per prompt. No stacked questions, no "also", no "and another thing".
3. Context belongs in the `context` field AND should be implicit in prompt_text — don't re-state it word-for-word.
4. Natural speech is fine: contractions, fragments, first person. But no rambling scene-setting.
5. The brand being tracked must NEVER appear in prompt_text or search_query. We are testing whether AI mentions the brand unprompted.
6. Competitor names must also not appear in prompt_text or search_query.
7. BANNED template phrasings (rewrite if you catch yourself using them): "What's the best approach to X", "common challenges with X", "step by step guide for X", "requirements for X", "who qualifies for X", "companies that offer X", "local X options by region".
8. Vary openings across a batch: questions, direct statements, "I'm trying to…", "Looking for…", mid-thought fragments.
9. search_query is keyword-style — no "I", no punctuation except spaces, no conversational padding.

EXAMPLES (tight Intent+Context format):

{
  "intent": "hospital discharge home prep",
  "context": "adult child caregiver, parent can't do stairs",
  "prompt_text": "Mom's being discharged tomorrow and can't do stairs at home. What do I set up first?",
  "search_query": "hospital discharge home prep stairs elderly",
  "tone": "time-pressed and direct",
  "intent_type": "informational",
  "category": "support"
}

{
  "intent": "compare venture debt to inside round",
  "context": "Series A SaaS, 14mo runway, $4M ARR",
  "prompt_text": "Series A SaaS, $4M ARR, 14 months runway. Venture debt or flat inside round — which is smarter?",
  "search_query": "venture debt vs inside round series a saas",
  "tone": "skeptical and comparing options",
  "intent_type": "commercial",
  "category": "research"
}

{
  "intent": "compare last-mile carriers Canada",
  "context": "Shopify merchant shipping to Toronto + Vancouver",
  "prompt_text": "Small Shopify store shipping daily to Toronto and Vancouver. Which last-mile carrier actually shows up on time?",
  "search_query": "best last mile carrier canada toronto vancouver",
  "tone": "practical and ready to act",
  "intent_type": "commercial",
  "category": "research"
}

Output ONLY a valid JSON array of objects. No preamble, no commentary, no markdown fences. Just the JSON array."""


def build_user_prompt(
    brand_config: Dict,
    persona: Dict,
    topic: Dict,
    count: int,
    existing_prompts_sample: List[str],
) -> str:
    """Build the user prompt for generating a batch."""
    brand_name = brand_config["brand"]["name"]
    brand_aliases = brand_config["brand"].get("aliases", [])
    brand_desc = brand_config["brand"]["description"]
    competitors = [
        c["name"] for c in brand_config.get("competitors", {}).get("expected", [])
    ]

    # Pick 3 random tones for variety in this batch
    tones_for_batch = random.sample(TONES, min(3, len(TONES)))

    # Categories are derived from client brand config if present, else fall
    # back to a reasonable default set.
    categories = brand_config.get("prompt_categories") or [
        "educational",
        "commercial",
        "navigational",
        "support",
        "research",
    ]

    existing_excerpt = ""
    if existing_prompts_sample:
        existing_excerpt = (
            "\n\nAVOID producing prompts similar to these already-generated ones:\n"
            + "\n".join(f"- {p}" for p in existing_prompts_sample[:10])
        )

    return f"""Generate {count} tight prompts about the topic "{topic['name']}" from the perspective of the following persona.

BRAND BEING TRACKED (do NOT mention in prompt_text or search_query): {brand_name}
Brand aliases (also do not mention): {', '.join(brand_aliases) if brand_aliases else 'none'}
Brand context (for your understanding only): {brand_desc}
Competitors (also do not mention): {', '.join(competitors) if competitors else 'none'}

TOPIC: {topic['name']}
Topic description: {topic.get('description', '')}

PERSONA: {persona['name']}
Persona description: {persona.get('description', '')}
Their key situation: {persona.get('key_trigger', '')}
Their top barrier: {persona.get('top_barrier', '')}
Their priority topics: {', '.join(persona.get('priority_topics', []))}

TONE VARIETY: Mix these tones across the {count} prompts: {', '.join(tones_for_batch)}.
INTENT_TYPE VARIETY: Mix informational, commercial, and navigational across the batch.
CATEGORY OPTIONS (pick the most fitting per prompt): {', '.join(categories)}{existing_excerpt}

Remember: 15-25 words per prompt_text, one intent each, no brand/competitor mentions. Return ONLY a JSON array of {count} objects."""


def call_claude(
    client,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    temperature: float = 0.9,
) -> Optional[List[Dict]]:
    """Call Claude Sonnet 4.6 and parse JSON array response."""
    text = ""
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text.strip()

        # Strip markdown fences if Claude added them
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  ⚠ JSON parse error: {e}")
        print(f"  Raw response excerpt: {text[:300]}...")
        return None
    except Exception as e:
        print(f"  ⚠ API error: {e}")
        return None


# ==============================================================================
# DEDUPLICATION
# ==============================================================================

def normalize_for_dedup(text: str) -> str:
    """Normalize prompt text for duplicate detection."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def token_overlap(a: str, b: str) -> float:
    """Jaccard similarity on token sets. Cheap semantic proxy."""
    set_a = set(normalize_for_dedup(a).split())
    set_b = set(normalize_for_dedup(b).split())
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def dedup_prompts(prompts: List[Dict], threshold: float = 0.75) -> List[Dict]:
    """Remove near-duplicates. Keeps the first occurrence."""
    kept: List[Dict] = []
    seen_normalized: set = set()
    for p in prompts:
        text = p.get("prompt_text", "").strip()
        if not text:
            continue
        norm = normalize_for_dedup(text)
        if norm in seen_normalized:
            continue
        is_dup = False
        for k in kept:
            if token_overlap(text, k["prompt_text"]) >= threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append(p)
            seen_normalized.add(norm)
    return kept


# ==============================================================================
# LENGTH / SHAPE VALIDATION (tight format specific)
# ==============================================================================

def _word_count(s: str) -> int:
    return len(re.findall(r"\S+", s or ""))


def is_tight_prompt(prompt: Dict, min_words: int = 10, max_words: int = 30) -> bool:
    """
    Reject prompts that are too short, too long, or missing tight-format fields.
    The word window is slightly wider than the 15-25 target to allow for
    legitimate edge cases without throwing away too many good prompts.
    """
    text = (prompt.get("prompt_text") or "").strip()
    if not text:
        return False
    n = _word_count(text)
    if n < min_words or n > max_words:
        return False
    # intent + context are required in v2
    if not (prompt.get("intent") or "").strip():
        return False
    if not (prompt.get("context") or "").strip():
        return False
    # search_query is required
    if not (prompt.get("search_query") or "").strip():
        return False
    return True


# ==============================================================================
# GENERATION ORCHESTRATION
# ==============================================================================

def generate_for_persona_topic(
    client,
    brand_config: Dict,
    persona: Dict,
    topic: Dict,
    count: int,
    already_generated: List[str],
) -> List[Dict]:
    """Generate `count` prompts for a single (persona, topic) combination."""
    batch_size = 10
    batches_needed = (count + batch_size - 1) // batch_size
    all_generated: List[Dict] = []

    for _ in range(batches_needed):
        this_batch = min(batch_size, count - len(all_generated))
        if this_batch <= 0:
            break
        existing_sample = (
            [p["prompt_text"] for p in all_generated[-10:]]
            + random.sample(already_generated, min(5, len(already_generated)))
        )
        user_prompt = build_user_prompt(
            brand_config, persona, topic, this_batch, existing_sample
        )
        result = call_claude(client, SYSTEM_PROMPT, user_prompt)
        if result:
            for item in result:
                item["_persona_id"] = persona["id"]
                item["_persona_name"] = persona["name"]
                item["_topic_id"] = topic["id"]
                item["_topic_name"] = topic["name"]
                all_generated.append(item)
    return all_generated


def plan_generation(client_data: Dict, target_count: int) -> List[Tuple[Dict, Dict, int]]:
    """Decide how many prompts to generate per (persona, topic) combo.

    Honors topic.personas mapping (only generates for personas that care
    about a topic). Respects persona weights so high-weight personas get
    more prompts. Respects topic priority (high > medium > low).
    """
    personas = client_data["personas"]
    topics = client_data["topics"]
    personas_by_id = client_data["personas_by_id"]

    pairs = []
    priority_weight = {"high": 3, "medium": 2, "low": 1}
    for topic in topics:
        topic_personas = topic.get("personas") or [p["id"] for p in personas]
        for pid in topic_personas:
            p = personas_by_id.get(pid)
            if p:
                weight = p.get("weight", 1.0) * priority_weight.get(
                    topic.get("priority", "medium"), 2
                )
                pairs.append((p, topic, weight))

    if not pairs:
        return []

    total_weight = sum(w for _, _, w in pairs)
    plan = []
    assigned = 0
    for p, t, w in pairs:
        n = max(2, int(round(target_count * w / total_weight)))
        plan.append((p, t, n))
        assigned += n

    diff = target_count - assigned
    if plan and diff != 0:
        last = plan[-1]
        plan[-1] = (last[0], last[1], max(2, last[2] + diff))

    return plan


# ==============================================================================
# CSV BUILDING  (v2 columns: intent + context added)
# ==============================================================================

CSV_COLUMNS = [
    "prompt_id",
    "persona",
    "category",
    "intent_type",
    "intent",
    "context",
    "prompt_text",
    "search_query",
    "tone",
    "expected_visibility_score",
    "topic_cluster_id",
    "cluster_topic",
    "notes",
]


def build_csv_string(prompts: List[Dict], run_timestamp: int) -> str:
    """Serialize prompts to a CSV string (no trailing newline trimming)."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    for i, p in enumerate(prompts):
        row = {
            "prompt_id": f"gen_{run_timestamp}_{i:05d}",
            "persona": p.get("_persona_name", ""),
            "category": p.get("category", "educational"),
            "intent_type": p.get("intent_type", "informational"),
            "intent": (p.get("intent") or "").strip(),
            "context": (p.get("context") or "").strip(),
            "prompt_text": (p.get("prompt_text") or "").strip(),
            "search_query": (p.get("search_query") or "").strip(),
            "tone": p.get("tone", ""),
            "expected_visibility_score": 5.0,
            "topic_cluster_id": p.get("_topic_id", ""),
            "cluster_topic": p.get("_topic_name", ""),
            "notes": f"Regenerated {datetime.now().strftime('%Y-%m-%d')}",
        }
        writer.writerow(row)
    return buf.getvalue()


def build_meta(
    slug: str,
    version_id: str,
    prompts: List[Dict],
    predecessor: Optional[str],
    notes: Optional[str],
) -> Dict:
    """Build the version meta.json dict for this generation run."""
    personas_seen = sorted({p.get("_persona_name", "") for p in prompts if p.get("_persona_name")})
    categories_seen = sorted({p.get("category", "") for p in prompts if p.get("category")})
    return {
        "version": version_id,
        "client_slug": slug,
        "generated_at": None,  # PromptVersionManager.write_new_version fills in
        "generated_by": "scripts/regenerate_prompts.py",
        "generator_version": GENERATOR_VERSION,
        "source_model": ANTHROPIC_MODEL,
        "prompt_count": len(prompts),
        "format": FORMAT_TAG,
        "personas": personas_seen,
        "categories": categories_seen,
        "predecessor": predecessor,
        "content_hash": None,  # PromptVersionManager fills in from CSV
        "notes": notes or f"Tight Intent+Context v2 regeneration via {ANTHROPIC_MODEL}.",
    }


# ==============================================================================
# MAIN REGENERATION ROUTINE
# ==============================================================================

def regenerate_client(
    slug: str,
    target_count: int,
    version_id: str,
    *,
    dry_run: bool = False,
    upload_to_gcs: bool = False,
) -> Dict:
    print(f"\n{'=' * 70}")
    print(f"REGENERATING PROMPTS: {slug}  →  {version_id}")
    print(f"{'=' * 70}")

    client_data = load_client_data(slug)
    brand_name = client_data["brand_config"]["brand"]["name"]
    print(f"Brand: {brand_name}")
    print(f"Personas: {len(client_data['personas'])}")
    print(f"Topics: {len(client_data['topics'])}")
    print(f"Target: {target_count} prompts")

    plan = plan_generation(client_data, target_count)
    if not plan:
        print("⚠ No (persona, topic) pairs to generate. Check topics.json persona mapping.")
        return {"slug": slug, "success": False}

    print(f"Plan: {len(plan)} (persona, topic) batches")
    if dry_run:
        print("\nDRY RUN — showing plan only:")
        for p, t, n in plan[:20]:
            print(f"  {n:3d} prompts: [{p['name']}] × [{t['name']}]")
        if len(plan) > 20:
            print(f"  ... +{len(plan) - 20} more")
        return {"slug": slug, "success": True, "dry_run": True}

    # Init Anthropic client
    from anthropic import Anthropic
    api_key = load_anthropic_key()
    if os.getenv("ANTHROPIC_INSECURE_SSL") == "1":
        import httpx
        http_client = httpx.Client(verify=False, timeout=60.0)
        anthropic_client = Anthropic(api_key=api_key, http_client=http_client)
    else:
        anthropic_client = Anthropic(api_key=api_key)

    # Generate in parallel (5 concurrent workers)
    all_prompts: List[Dict] = []
    already_texts: List[str] = []
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {
            pool.submit(
                generate_for_persona_topic,
                anthropic_client,
                client_data["brand_config"],
                persona,
                topic,
                count,
                already_texts,
            ): (persona["name"], topic["name"], count)
            for persona, topic, count in plan
        }
        completed = 0
        total = len(futures)
        for fut in as_completed(futures):
            persona_name, topic_name, count = futures[fut]
            completed += 1
            try:
                batch = fut.result()
                all_prompts.extend(batch)
                already_texts.extend(p["prompt_text"] for p in batch[-5:])
                print(
                    f"  [{completed}/{total}] ✓ {len(batch):3d} / {count} prompts: "
                    f"[{persona_name}] × [{topic_name}]"
                )
            except Exception as e:
                print(
                    f"  [{completed}/{total}] ✗ FAILED: [{persona_name}] × [{topic_name}] — {e}"
                )

    gen_elapsed = time.time() - t_start
    print(f"\nGenerated {len(all_prompts)} raw prompts in {gen_elapsed:.1f}s")

    # ─── Filtering pipeline ──────────────────────────────────────────────

    # Shape / length filter (tight format)
    before = len(all_prompts)
    all_prompts = [p for p in all_prompts if is_tight_prompt(p)]
    print(
        f"Shape filter (length + required fields): {before} → {len(all_prompts)} "
        f"(removed {before - len(all_prompts)} malformed)"
    )

    # Dedup
    before = len(all_prompts)
    all_prompts = dedup_prompts(all_prompts)
    print(f"Dedup: {before} → {len(all_prompts)} (removed {before - len(all_prompts)})")

    # Brand + competitor leakage filter
    brand_aliases_raw = (
        [client_data["brand_config"]["brand"]["name"]]
        + client_data["brand_config"]["brand"].get("aliases", [])
    )
    # `competitors` has two shapes across clients:
    #   (a) dict with "expected"/"discovered" keys (OCO, Espresso, Say I Do)
    #   (b) flat list of {name, domain} objects        (UniUni, Natasha Denona)
    # Normalize both to a flat list of competitor dicts before pulling names.
    _competitors_raw = client_data["brand_config"].get("competitors", [])
    if isinstance(_competitors_raw, dict):
        _competitor_items = (
            _competitors_raw.get("expected", [])
            + _competitors_raw.get("discovered", [])
        )
    elif isinstance(_competitors_raw, list):
        _competitor_items = _competitors_raw
    else:
        _competitor_items = []
    competitor_names = [
        c.get("name", "") for c in _competitor_items if isinstance(c, dict)
    ]
    forbidden = [
        a.lower().strip() for a in (brand_aliases_raw + competitor_names) if a and a.strip()
    ]

    def clean(p: Dict) -> bool:
        t = (p.get("prompt_text", "") + " " + p.get("search_query", "")).lower()
        for alias in forbidden:
            if re.search(r"\b" + re.escape(alias) + r"\b", t):
                return False
        return True

    before = len(all_prompts)
    all_prompts = [p for p in all_prompts if clean(p)]
    print(
        f"Leakage filter (brand + competitors): {before} → {len(all_prompts)} "
        f"(removed {before - len(all_prompts)})"
    )

    # Safety guard — never overwrite a good CSV with too few prompts
    min_acceptable = min(int(target_count * 0.6), 300)
    if len(all_prompts) < min_acceptable:
        print(
            f"\n✗ ABORTING WRITE: only {len(all_prompts)} prompts survived filtering "
            f"(need at least {min_acceptable}). Existing CSV untouched."
        )
        return {
            "slug": slug,
            "success": False,
            "count": len(all_prompts),
            "error": (
                f"Too few prompts ({len(all_prompts)} < {min_acceptable}). "
                f"Likely API/network/format issue. No changes written."
            ),
        }

    # ─── Write via PromptVersionManager ──────────────────────────────────
    run_timestamp = int(time.time())
    csv_content = build_csv_string(all_prompts, run_timestamp)

    gcs_sync = None
    if upload_to_gcs:
        try:
            from src.client_manager.gcs_sync import GCSClientSync
            gcs_sync = GCSClientSync()
            print(f"✓ GCS sync enabled (bucket: {gcs_sync.bucket_name})")
        except Exception as exc:
            print(f"⚠️ GCS init failed — continuing local-only: {exc}")

    manager = PromptVersionManager(
        client_slug=slug, data_dir=DATA_DIR, gcs=gcs_sync
    )

    predecessor = manager.get_active_version_id()  # e.g. "v1.0-baseline"
    meta = build_meta(
        slug=slug,
        version_id=version_id,
        prompts=all_prompts,
        predecessor=predecessor,
        notes=None,
    )

    try:
        meta_final = manager.write_new_version(
            csv_content=csv_content,
            meta=meta,
            upload_to_gcs=upload_to_gcs and gcs_sync is not None,
        )
    except FileExistsError as e:
        print(f"\n✗ {e}")
        print("   Bump --version (e.g. v2.0.1-tight or v2.1-extra) and rerun.")
        return {"slug": slug, "success": False, "error": str(e)}

    active_csv_rel = manager.active_csv_path.relative_to(PROJECT_ROOT)
    archive_rel = manager.archive_dir(version_id).relative_to(PROJECT_ROOT)
    print(
        f"✓ Wrote {len(all_prompts)} prompts → {active_csv_rel} "
        f"(archive: {archive_rel}, hash {meta_final['content_hash'][:20]}…)"
    )

    return {
        "slug": slug,
        "success": True,
        "count": len(all_prompts),
        "version": version_id,
        "predecessor": predecessor,
        "output": str(manager.active_csv_path),
        "archive": str(manager.archive_dir(version_id)),
        "sample": random.sample(all_prompts, min(20, len(all_prompts))),
    }


def list_active_clients() -> List[str]:
    """Return active client slugs from clients.json (excludes Natasha Denona)."""
    clients_json = DATA_DIR / "clients.json"
    with open(clients_json) as f:
        data = json.load(f)
    return [c["slug"] for c in data.get("clients", []) if c["slug"] != "natasha_denona"]


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate client prompts via Claude Sonnet 4.6 in tight Intent+Context v2 format"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--client",
        help="Client slug (e.g. ontario_caregiver_organization)",
    )
    group.add_argument(
        "--all", action="store_true", help="Regenerate all active clients"
    )
    parser.add_argument(
        "--count", type=int, default=500, help="Target prompts per client (default: 500)"
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_VERSION,
        help=f"Version id for this regeneration (default: {DEFAULT_VERSION})",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show plan without calling Claude"
    )
    parser.add_argument(
        "--upload-to-gcs",
        action="store_true",
        help="Mirror the new version to GCS (needs credentials)",
    )
    parser.add_argument(
        "--sample-out",
        help="Write 20-prompt sample per client to this JSON path",
    )
    args = parser.parse_args()

    if args.all:
        slugs = list_active_clients()
    else:
        slugs = [args.client]

    print(f"Regenerating prompts for: {', '.join(slugs)}")
    print(f"Target count per client: {args.count}")
    print(f"Version id: {args.version}")
    print(f"GCS upload: {'enabled' if args.upload_to_gcs else 'disabled'}")

    results = []
    for slug in slugs:
        try:
            result = regenerate_client(
                slug,
                target_count=args.count,
                version_id=args.version,
                dry_run=args.dry_run,
                upload_to_gcs=args.upload_to_gcs,
            )
            results.append(result)
        except Exception as e:
            print(f"\n✗ {slug} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({"slug": slug, "success": False, "error": str(e)})

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    for r in results:
        status = "✓" if r.get("success") else "✗"
        count = r.get("count", "—")
        version = r.get("version") or "—"
        print(f"  {status} {r['slug']}: {count} prompts  ({version})")

    if args.sample_out and not args.dry_run:
        samples = {r["slug"]: r.get("sample", []) for r in results if r.get("success")}
        with open(args.sample_out, "w") as f:
            json.dump(samples, f, indent=2, default=str)
        print(f"\nSamples written to: {args.sample_out}")


if __name__ == "__main__":
    main()
