"""
Regenerate prompts for one or more clients using Claude Sonnet 4.6.

Replaces the template-driven fan-out generator with LLM-generated natural
conversational prompts. Produces DUAL columns per prompt:
  - prompt_text: conversational, for ChatGPT / Claude / Perplexity / Gemini / Copilot
  - search_query: keyword-style, for Google AI Overviews (SerpAPI)

Usage:
  python scripts/regenerate_prompts.py --client ontario_caregiver_organization
  python scripts/regenerate_prompts.py --all --count 500
  python scripts/regenerate_prompts.py --all --count 500 --dry-run

Reads client brand_config.json, personas.json, topics.json from data/{slug}/.
Archives old prompts.csv to archive/prompts-<timestamp>/ before writing.
Writes new CSV atomically (tmp + rename).
"""

import argparse
import csv
import json
import os
import random
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
ARCHIVE_DIR = PROJECT_ROOT / "archive" / "prompts"

# Anthropic model — matches config/config.json ("claude-sonnet-4-6" per commit f07cc3d)
ANTHROPIC_MODEL = "claude-sonnet-4-6"

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
CATEGORIES = ["educational", "business", "research", "support"]


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

    # Streamlit secrets fallback (TOML)
    secrets_path = PROJECT_ROOT / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
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
# PROMPT GENERATION (CLAUDE SONNET 4.6)
# ==============================================================================

SYSTEM_PROMPT = """You are writing realistic prompts that real people would actually type or speak into ChatGPT, Claude, Perplexity, or Gemini when seeking help about a specific topic.

CRITICAL RULES:
1. Each prompt must sound like a REAL PERSON in the described persona's situation, not a SEO keyword or a template.
2. Include specific context: relationships, locations, emotions, timelines, prior experiences.
3. Vary the opening — some prompts start with a question, some with a scenario, some mid-thought.
4. AVOID these template patterns (they are banned): "What's the best approach to X", "common challenges with X", "step by step guide for X", "requirements for X", "who qualifies for X", "companies that offer X", "local X options by region". These are exactly what we want to avoid.
5. Use natural speech — contractions are fine. First person is fine. Incomplete sentences are fine. Emotion is fine.
6. The brand being tracked must NOT appear in the prompt text. We are testing whether AI mentions the brand unprompted.
7. Do not include competitor names in the prompts either.

FOR EACH PROMPT, also produce a `search_query` — the same intent expressed as a Google search. Think: what 3–7 words would this person actually type into Google to get an AI Overview? Keyword-style, no conversational padding.

EXAMPLE (caregiving topic, adult-child-caregiver persona, frustrated tone):
{
  "prompt_text": "My dad was just discharged from Humber River in Toronto and I'm supposed to pick him up tomorrow but honestly I have no idea what to do once he's home — he can't walk stairs. Where do I even start?",
  "search_query": "hospital discharge help elderly parent ontario",
  "tone": "frustrated and overwhelmed",
  "intent_type": "informational",
  "category": "support"
}

EXAMPLE (venture debt topic, SaaS founder persona, skeptical tone):
{
  "prompt_text": "We've got about 14 months of runway left. Our lead VC is pushing us toward an inside round at flat valuation, but I keep hearing founders talk about venture debt as a way to buy time without diluting. Is it actually a good idea for a Series A SaaS doing $4M ARR?",
  "search_query": "venture debt vs inside round series a saas",
  "tone": "skeptical and comparing options",
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
    competitors = [c["name"] for c in brand_config.get("competitors", {}).get("expected", [])]

    # Pick 3 random tones for variety in this batch
    tones_for_batch = random.sample(TONES, min(3, len(TONES)))

    existing_excerpt = ""
    if existing_prompts_sample:
        existing_excerpt = (
            "\n\nAVOID generating prompts similar to these already-generated ones:\n"
            + "\n".join(f"- {p}" for p in existing_prompts_sample[:10])
        )

    return f"""Generate {count} realistic prompts about the topic "{topic['name']}" from the perspective of the following persona.

BRAND BEING TRACKED (do NOT mention in prompts): {brand_name}
Brand aliases (also do not mention): {', '.join(brand_aliases) if brand_aliases else 'none'}
Brand context: {brand_desc}
Competitors (also do not mention): {', '.join(competitors) if competitors else 'none'}

TOPIC: {topic['name']}
Topic description: {topic.get('description', '')}

PERSONA: {persona['name']}
Persona description: {persona.get('description', '')}
Their key situation: {persona.get('key_trigger', '')}
Their top barrier: {persona.get('top_barrier', '')}
Their priority topics: {', '.join(persona.get('priority_topics', []))}

TONE VARIETY: Mix these tones across the {count} prompts: {', '.join(tones_for_batch)}.
INTENT VARIETY: Mix informational, commercial, and navigational intents.{existing_excerpt}

Return ONLY a JSON array of {count} prompt objects. Each object needs: prompt_text, search_query, tone, intent_type, category."""


def call_claude(
    client,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    temperature: float = 0.9,
) -> Optional[List[Dict]]:
    """Call Claude Sonnet 4.6 and parse JSON array response."""
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
    # Weight longer tokens (reduces impact of common words)
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
    # Generate in batches of 10 to keep response sizes manageable
    batch_size = 10
    batches_needed = (count + batch_size - 1) // batch_size
    all_generated: List[Dict] = []

    for batch_idx in range(batches_needed):
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

    Honors topic.personas mapping (only generates for personas that care about a topic).
    Respects persona weights so high-weight personas get more prompts.
    Respects topic priority (high > medium > low).
    """
    personas = client_data["personas"]
    topics = client_data["topics"]
    personas_by_id = client_data["personas_by_id"]

    # Build the (persona, topic) universe
    pairs = []
    priority_weight = {"high": 3, "medium": 2, "low": 1}
    for topic in topics:
        topic_personas = topic.get("personas") or [p["id"] for p in personas]
        for pid in topic_personas:
            p = personas_by_id.get(pid)
            if p:
                weight = p.get("weight", 1.0) * priority_weight.get(topic.get("priority", "medium"), 2)
                pairs.append((p, topic, weight))

    if not pairs:
        return []

    # Normalize weights to counts summing to target_count
    total_weight = sum(w for _, _, w in pairs)
    plan = []
    assigned = 0
    for p, t, w in pairs:
        n = max(2, int(round(target_count * w / total_weight)))
        plan.append((p, t, n))
        assigned += n

    # Adjust last entry to hit target_count exactly
    diff = target_count - assigned
    if plan and diff != 0:
        last = plan[-1]
        plan[-1] = (last[0], last[1], max(2, last[2] + diff))

    return plan


# ==============================================================================
# OUTPUT
# ==============================================================================

CSV_COLUMNS = [
    "prompt_id",
    "persona",
    "category",
    "intent_type",
    "prompt_text",
    "search_query",
    "tone",
    "expected_visibility_score",
    "topic_cluster_id",
    "cluster_topic",
    "notes",
]


def archive_existing(slug: str) -> Optional[Path]:
    """Copy existing prompts.csv to archive/prompts-<timestamp>/."""
    existing_csv = DATA_DIR / slug / f"{slug}_prompts.csv"
    if not existing_csv.exists():
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_subdir = ARCHIVE_DIR / f"{timestamp}"
    archive_subdir.mkdir(parents=True, exist_ok=True)
    dest = archive_subdir / f"{slug}_prompts.csv"
    shutil.copy2(existing_csv, dest)
    return dest


def write_prompts_atomic(slug: str, prompts: List[Dict]) -> Path:
    """Write prompts CSV atomically (write to .tmp, rename)."""
    target = DATA_DIR / slug / f"{slug}_prompts.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".csv.tmp")

    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for i, p in enumerate(prompts):
            row = {
                "prompt_id": f"gen_{int(time.time())}_{i:05d}",
                "persona": p.get("_persona_name", ""),
                "category": p.get("category", "educational"),
                "intent_type": p.get("intent_type", "informational"),
                "prompt_text": p.get("prompt_text", "").strip(),
                "search_query": p.get("search_query", "").strip(),
                "tone": p.get("tone", ""),
                "expected_visibility_score": 5.0,
                "topic_cluster_id": p.get("_topic_id", ""),
                "cluster_topic": p.get("_topic_name", ""),
                "notes": f"Regenerated {datetime.now().strftime('%Y-%m-%d')}",
            }
            writer.writerow(row)

    tmp.replace(target)
    return target


# ==============================================================================
# MAIN
# ==============================================================================

def regenerate_client(slug: str, target_count: int, dry_run: bool = False) -> Dict:
    print(f"\n{'='*70}")
    print(f"REGENERATING PROMPTS: {slug}")
    print(f"{'='*70}")

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
    # Opt-in SSL bypass for sandbox/testing ONLY. Never use in production.
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
                print(f"  [{completed}/{total}] ✓ {len(batch):3d} / {count} prompts: [{persona_name}] × [{topic_name}]")
            except Exception as e:
                print(f"  [{completed}/{total}] ✗ FAILED: [{persona_name}] × [{topic_name}] — {e}")

    gen_elapsed = time.time() - t_start
    print(f"\nGenerated {len(all_prompts)} raw prompts in {gen_elapsed:.1f}s")

    # Dedup
    before = len(all_prompts)
    all_prompts = dedup_prompts(all_prompts)
    print(f"Dedup: {before} → {len(all_prompts)} (removed {before - len(all_prompts)} near-duplicates)")

    # Filter: must have both prompt_text and search_query, must not mention brand
    brand_aliases = [
        client_data["brand_config"]["brand"]["name"].lower(),
    ] + [a.lower() for a in client_data["brand_config"]["brand"].get("aliases", [])]

    def clean(p: Dict) -> bool:
        t = p.get("prompt_text", "").strip().lower()
        if not t or not p.get("search_query", "").strip():
            return False
        # Reject if any brand alias appears as a whole word
        for alias in brand_aliases:
            if alias and re.search(r"\b" + re.escape(alias) + r"\b", t):
                return False
        return True

    before = len(all_prompts)
    all_prompts = [p for p in all_prompts if clean(p)]
    print(f"Filter (brand leakage + empty): {before} → {len(all_prompts)}")

    # SAFETY GUARD: never overwrite a good CSV with too few prompts.
    # Require at least 60% of the target OR 50 minimum, whichever is lower.
    min_acceptable = min(int(target_count * 0.6), 50)
    if len(all_prompts) < min_acceptable:
        print(f"\n✗ ABORTING WRITE: only {len(all_prompts)} prompts generated "
              f"(need at least {min_acceptable}). Existing CSV untouched.")
        return {
            "slug": slug,
            "success": False,
            "count": len(all_prompts),
            "error": f"Too few prompts generated ({len(all_prompts)} < {min_acceptable}). "
                     f"Likely API/network issue. No changes written.",
        }

    # Archive old (only after safety check passes)
    archive_path = archive_existing(slug)
    if archive_path:
        print(f"Archived old prompts → {archive_path.relative_to(PROJECT_ROOT)}")

    # Write new
    output_path = write_prompts_atomic(slug, all_prompts)
    print(f"✓ Wrote {len(all_prompts)} prompts → {output_path.relative_to(PROJECT_ROOT)}")

    return {
        "slug": slug,
        "success": True,
        "count": len(all_prompts),
        "archived": str(archive_path) if archive_path else None,
        "output": str(output_path),
        "sample": random.sample(all_prompts, min(20, len(all_prompts))),
    }


def list_active_clients() -> List[str]:
    """Return active client slugs from clients.json (excludes Natasha Denona)."""
    clients_json = DATA_DIR / "clients.json"
    with open(clients_json) as f:
        data = json.load(f)
    return [c["slug"] for c in data.get("clients", []) if c["slug"] != "natasha_denona"]


def main():
    parser = argparse.ArgumentParser(description="Regenerate client prompts via Claude Sonnet 4.5")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--client", help="Client slug (e.g. ontario_caregiver_organization)")
    group.add_argument("--all", action="store_true", help="Regenerate all active clients")
    parser.add_argument("--count", type=int, default=500, help="Target prompts per client (default: 500)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without calling Claude")
    parser.add_argument("--sample-out", help="Write 20-prompt sample per client to this JSON path")
    args = parser.parse_args()

    if args.all:
        slugs = list_active_clients()
    else:
        slugs = [args.client]

    print(f"Regenerating prompts for: {', '.join(slugs)}")
    print(f"Target count per client: {args.count}")

    results = []
    for slug in slugs:
        try:
            result = regenerate_client(slug, args.count, args.dry_run)
            results.append(result)
        except Exception as e:
            print(f"\n✗ {slug} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({"slug": slug, "success": False, "error": str(e)})

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    for r in results:
        status = "✓" if r.get("success") else "✗"
        count = r.get("count", "—")
        print(f"  {status} {r['slug']}: {count} prompts")

    # Sample out
    if args.sample_out and not args.dry_run:
        samples = {r["slug"]: r.get("sample", []) for r in results if r.get("success")}
        with open(args.sample_out, "w") as f:
            json.dump(samples, f, indent=2, default=str)
        print(f"\nSamples written to: {args.sample_out}")


if __name__ == "__main__":
    main()
