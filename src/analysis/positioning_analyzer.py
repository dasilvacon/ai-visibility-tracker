"""
Positioning Analyzer — Phase 4 qualitative analysis.

Surfaces the *language* AI uses about a brand and its competitors, the
phrases AI repeats verbatim, and the co-mention "neighborhood" each brand
sits in. Everything here is deterministic text extraction over the actual
response text — no LLM calls, no inferred narrative — so every claim the
report makes can be traced back to specific recurring phrases or counts.

Three primary outputs (all return-then-render, no side effects):

    extract_recurring_phrases() — n-grams (3–6 words) containing a brand
    name that occur ≥ min_occurrences times across responses. These are
    essentially AI's "headlines" for each brand: language patterns it
    has internalized.

    extract_positioning_descriptors() — counts of common positioning
    adjectives (premium, affordable, popular, beginner, advanced, …)
    within a token window of each brand mention. Light, additive signal.

    build_co_mention_network() — for each brand observed, how often each
    OTHER brand also appears in the same response. Reveals the mental
    neighborhood AI groups brands into.

The orchestrator analyze_positioning() bundles all three for one client.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional


# ---------------------------------------------------------------------------
# Lightweight positioning adjective list
# ---------------------------------------------------------------------------
# Curated, intentionally small. Every word here is the kind of descriptor
# that says something useful about market positioning: pricing tier,
# audience, ease, polish, scope. We deliberately avoid generic positive/
# negative words ("great", "amazing", "bad") — those are sentiment, not
# positioning, and the existing sentiment tab already handles that.
#
# Words are stored lowercase; case-insensitive matching at extraction time.
POSITIONING_DESCRIPTORS: Dict[str, List[str]] = {
    'pricing':         ['premium', 'luxury', 'high-end', 'expensive', 'affordable',
                        'cheap', 'budget', 'free', 'cost-effective', 'value'],
    'audience':        ['beginner', 'professional', 'expert', 'enterprise',
                        'small-business', 'startup', 'consumer', 'b2b', 'b2c',
                        'individual', 'personal', 'institutional'],
    'ease':            ['easy', 'simple', 'intuitive', 'user-friendly', 'complex',
                        'complicated', 'powerful', 'flexible', 'customizable'],
    'maturity':        ['established', 'leading', 'popular', 'emerging', 'new',
                        'trusted', 'innovative', 'modern', 'traditional'],
    'scope':           ['comprehensive', 'all-in-one', 'specialized', 'niche',
                        'focused', 'general', 'broad', 'narrow'],
    'aesthetic':       ['minimal', 'minimalist', 'elegant', 'clean', 'colorful',
                        'bold', 'classic', 'trendy', 'modern', 'sophisticated'],
    'reliability':     ['reliable', 'robust', 'stable', 'proven', 'trusted',
                        'unreliable', 'buggy', 'inconsistent'],
}

# Flatten for fast lookup
_DESCRIPTOR_TO_BUCKET: Dict[str, str] = {}
for bucket, words in POSITIONING_DESCRIPTORS.items():
    for w in words:
        _DESCRIPTOR_TO_BUCKET[w.lower()] = bucket


# Small stopword list used to drop low-content phrases. Kept tiny on purpose:
# we WANT phrases like "is the most popular" to surface — those carry meaning.
# We only drop phrases that are entirely structural.
_PHRASE_STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'of', 'to', 'for', 'in', 'on',
    'at', 'by', 'with', 'as', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'has', 'have', 'had', 'do', 'does', 'did', 'this', 'that',
    'these', 'those', 'it', 'its', 'they', 'them', 'their', 'there',
}


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Split text into lowercase word tokens, keeping hyphens within words."""
    if not text:
        return []
    # Drop URLs (they pollute n-grams with garbage like "https-www-example-com")
    text = re.sub(r'https?://\S+', ' ', text)
    # Drop markdown formatting marks
    text = text.replace('**', ' ').replace('##', ' ')
    # Tokenize: words including internal hyphens/apostrophes
    tokens = re.findall(r"[A-Za-z][A-Za-z'\-]*", text.lower())
    return tokens


def _find_brand_token_indices(tokens: List[str], brand_name: str) -> List[int]:
    """
    Return start indices of every occurrence of brand_name in tokens.

    Handles single-word and multi-word brand names. Returns the index of
    the FIRST token of each occurrence so callers can window around it.
    """
    if not tokens or not brand_name:
        return []
    brand_tokens = _tokenize(brand_name)
    if not brand_tokens:
        return []

    n = len(brand_tokens)
    hits = []
    for i in range(len(tokens) - n + 1):
        if tokens[i:i + n] == brand_tokens:
            hits.append(i)
    return hits


# ---------------------------------------------------------------------------
# Recurring phrases
# ---------------------------------------------------------------------------

def extract_recurring_phrases(
    response_texts: Iterable[str],
    brand_name: str,
    *,
    min_occurrences: int = 3,
    n_min: int = 3,
    n_max: int = 6,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Extract n-gram phrases containing brand_name that recur ≥ min_occurrences
    times across response_texts.

    The same response is counted at most once per phrase (duplicate
    occurrences within one response don't inflate the count) — this prevents
    a single chatty response from skewing the rankings.

    Returns a list of dicts sorted by occurrence count desc, then n desc:
        {phrase: str, count: int, n: int}
    """
    if not response_texts or not brand_name:
        return []
    brand_tokens = _tokenize(brand_name)
    if not brand_tokens:
        return []
    bn = len(brand_tokens)

    # phrase -> set of response indices that contained it
    phrase_responses: Dict[str, set] = defaultdict(set)

    for response_idx, text in enumerate(response_texts):
        tokens = _tokenize(text)
        # For each occurrence of the brand, generate n-grams of varying
        # lengths that *contain* the brand span. We slide a window of
        # length n over positions where the brand fits inside it.
        brand_starts = _find_brand_token_indices(tokens, brand_name)
        if not brand_starts:
            continue

        for n in range(n_min, n_max + 1):
            if n < bn:
                continue
            for bs in brand_starts:
                # The window must include the brand span
                # i.e. window [w_start, w_start+n) must contain [bs, bs+bn)
                w_start_min = max(0, bs + bn - n)
                w_start_max = min(len(tokens) - n, bs)
                if w_start_max < w_start_min:
                    continue
                for w_start in range(w_start_min, w_start_max + 1):
                    window = tokens[w_start:w_start + n]
                    # Skip if the entire window outside the brand span is stopwords
                    non_brand = [
                        w for j, w in enumerate(window)
                        if not (w_start + j >= bs and w_start + j < bs + bn)
                    ]
                    if not non_brand or all(w in _PHRASE_STOPWORDS for w in non_brand):
                        continue
                    phrase = ' '.join(window)
                    phrase_responses[phrase].add(response_idx)

    # Filter to recurring phrases
    results: List[Dict[str, Any]] = []
    for phrase, response_set in phrase_responses.items():
        cnt = len(response_set)
        if cnt < min_occurrences:
            continue
        results.append({
            'phrase': phrase,
            'count': cnt,
            'n': len(phrase.split()),
        })

    # Sort: most frequent first, then longer phrases (more informative)
    results.sort(key=lambda r: (-r['count'], -r['n'], r['phrase']))

    # Deduplicate phrases that are substrings of higher-ranked phrases —
    # if "the most popular wedding website" recurs 4 times, drop the
    # 3-word "most popular wedding" that recurs 4 times too.
    deduped: List[Dict[str, Any]] = []
    seen_supersets = []
    for r in results:
        is_substring = any(
            r['phrase'] in s and s != r['phrase'] for s in seen_supersets
        )
        if is_substring:
            continue
        deduped.append(r)
        seen_supersets.append(r['phrase'])
        if len(deduped) >= max_results:
            break

    return deduped


# ---------------------------------------------------------------------------
# Positioning descriptors
# ---------------------------------------------------------------------------

def extract_positioning_descriptors(
    response_texts: Iterable[str],
    brand_name: str,
    *,
    window_tokens: int = 12,
) -> Dict[str, Any]:
    """
    Count positioning descriptors that appear within `window_tokens` of any
    brand mention.

    Returns:
        {
            'descriptors': Counter of word -> count,
            'by_bucket':   dict bucket -> Counter of word -> count,
            'mention_count': int  # how many brand-mention windows we scanned
        }
    """
    if not response_texts or not brand_name:
        return {'descriptors': Counter(), 'by_bucket': {}, 'mention_count': 0}

    descriptors: Counter = Counter()
    by_bucket: Dict[str, Counter] = defaultdict(Counter)
    mention_count = 0

    for text in response_texts:
        tokens = _tokenize(text)
        if not tokens:
            continue
        brand_starts = _find_brand_token_indices(tokens, brand_name)
        for bs in brand_starts:
            mention_count += 1
            # Window: window_tokens tokens before AND after brand mention
            ws = max(0, bs - window_tokens)
            we = min(len(tokens), bs + window_tokens + 1)
            window_words = tokens[ws:we]
            for w in window_words:
                bucket = _DESCRIPTOR_TO_BUCKET.get(w)
                if bucket:
                    descriptors[w] += 1
                    by_bucket[bucket][w] += 1

    return {
        'descriptors': descriptors,
        'by_bucket': {k: dict(v) for k, v in by_bucket.items()},
        'mention_count': mention_count,
    }


# ---------------------------------------------------------------------------
# Co-mention network
# ---------------------------------------------------------------------------

def build_co_mention_network(
    scored_results: List[Dict[str, Any]],
    brand_name: str,
    *,
    min_co_occurrence: int = 2,
    max_neighbors_per_brand: int = 8,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    For each brand that appears in any response (the user's brand + each
    competitor), build a list of OTHER brands it most frequently appears
    alongside.

    Args:
        scored_results: list of result dicts with .visibility.competitors_mentioned
                        (list of competitor names) and .visibility.brand_mentioned.
        brand_name:     the user's brand name — added to the universe alongside
                        all competitors observed.

    Returns:
        Dict mapping brand → list of {neighbor: str, co_count: int, co_rate: float}
        sorted by co_count desc. Only neighbors meeting min_co_occurrence are
        included; only top max_neighbors_per_brand are returned.
    """
    if not scored_results:
        return {}

    # First pass: build the universe + count appearances
    brand_appearances: Counter = Counter()
    pair_counts: Dict[tuple, int] = defaultdict(int)

    for result in scored_results:
        vis = result.get('visibility', {}) or {}
        names_in_response = list(vis.get('competitors_mentioned') or [])
        if vis.get('brand_mentioned'):
            names_in_response.append(brand_name)
        # Dedupe within a single response so a brand named 5x in one response
        # doesn't inflate co-mention counts
        unique_names = list({n for n in names_in_response if n})
        for n in unique_names:
            brand_appearances[n] += 1
        # All unordered pairs in this response
        for i in range(len(unique_names)):
            for j in range(i + 1, len(unique_names)):
                a, b = sorted([unique_names[i], unique_names[j]])
                pair_counts[(a, b)] += 1

    # Build the network output
    network: Dict[str, List[Dict[str, Any]]] = {}
    for brand in brand_appearances:
        neighbors = []
        own_appearances = brand_appearances[brand]
        if own_appearances == 0:
            continue
        for (a, b), co_count in pair_counts.items():
            if a == brand:
                other = b
            elif b == brand:
                other = a
            else:
                continue
            if co_count < min_co_occurrence:
                continue
            co_rate = co_count / own_appearances * 100
            neighbors.append({
                'neighbor': other,
                'co_count': co_count,
                'co_rate': round(co_rate, 1),
            })
        neighbors.sort(key=lambda n: (-n['co_count'], n['neighbor']))
        if neighbors:
            network[brand] = neighbors[:max_neighbors_per_brand]

    return network


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def analyze_positioning(
    scored_results: List[Dict[str, Any]],
    brand_name: str,
    competitor_names: Optional[List[str]] = None,
    *,
    top_competitors_to_profile: int = 5,
) -> Dict[str, Any]:
    """
    Run the full Phase 4 positioning analysis.

    Args:
        scored_results: full list of scored results from this run.
        brand_name: the client's brand.
        competitor_names: full list of expected competitors. If None, we
            derive the top N by mention frequency from scored_results.
        top_competitors_to_profile: how many competitors to deep-profile
            with their own descriptor + phrase extraction.

    Returns:
        {
            'brand_profile':    {phrases, descriptors, mention_count},
            'competitor_profiles': {competitor_name: {phrases, descriptors, mention_count}},
            'co_mention_network': {brand: [{neighbor, co_count, co_rate}]},
            'sample_size': int  # total prompts analyzed
        }
    """
    if not scored_results:
        return {
            'brand_profile': {'phrases': [], 'descriptors': {}, 'by_bucket': {}, 'mention_count': 0},
            'competitor_profiles': {},
            'co_mention_network': {},
            'sample_size': 0,
        }

    # Pull all response_texts once
    all_responses = [
        (r.get('response_text') or r.get('response') or '')
        for r in scored_results
    ]

    # If competitors weren't passed, derive top competitors by mention frequency
    if not competitor_names:
        comp_counter: Counter = Counter()
        for r in scored_results:
            for c in (r.get('visibility', {}).get('competitors_mentioned') or []):
                comp_counter[c] += 1
        competitor_names = [c for c, _ in comp_counter.most_common(top_competitors_to_profile)]

    # Brand profile
    brand_phrases = extract_recurring_phrases(all_responses, brand_name)
    brand_desc = extract_positioning_descriptors(all_responses, brand_name)
    brand_profile = {
        'phrases': brand_phrases,
        'descriptors': dict(brand_desc['descriptors']),
        'by_bucket': brand_desc['by_bucket'],
        'mention_count': brand_desc['mention_count'],
    }

    # Per-competitor profile (only profile the top N — keeps the report
    # focused; deeper analysis available via raw data if needed)
    competitor_profiles: Dict[str, Any] = {}
    for comp in competitor_names[:top_competitors_to_profile]:
        c_phrases = extract_recurring_phrases(all_responses, comp)
        c_desc = extract_positioning_descriptors(all_responses, comp)
        if c_desc['mention_count'] == 0 and not c_phrases:
            # Skip competitors that don't actually appear in responses —
            # they're configured but not surfaced by AI this run.
            continue
        competitor_profiles[comp] = {
            'phrases': c_phrases,
            'descriptors': dict(c_desc['descriptors']),
            'by_bucket': c_desc['by_bucket'],
            'mention_count': c_desc['mention_count'],
        }

    # Co-mention network
    network = build_co_mention_network(scored_results, brand_name)

    return {
        'brand_profile': brand_profile,
        'competitor_profiles': competitor_profiles,
        'co_mention_network': network,
        'sample_size': len(scored_results),
    }
