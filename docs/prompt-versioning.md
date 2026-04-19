# Prompt-Set Versioning

## Why this exists

When we regenerate a client's prompt set (e.g. v1 legacy → v2 Intent+Context
format), test results from the new set are not directly comparable to results
from the old set. The questions being asked have changed.

Without versioning:
- OCO's visibility rate could jump from 30% → 45% with no way to tell whether
  the brand actually got more visible or the new prompts are just easier
- Historical reports become un-auditable; there's no way to recreate the
  exact prompt set that produced a given result
- Clients lose trust in month-over-month trends

Versioning solves this by:
1. Keeping an immutable archive of every prompt set we have ever deployed
2. Stamping every test result with the version of the prompt set that
   produced it
3. Surfacing version context in dashboards and reports so a clean break is
   visible ("v2 prompts introduced 2026-04-20")

## File layout

### Active prompts (unchanged for app readers)

```
client-data/{slug}/
  {slug}_prompts.csv              # active version, the app reads from here
  {slug}_prompts.meta.json        # metadata sidecar describing the active version
```

The active path is stable. No consumer of prompts needs to know versions
exist; they just read `{slug}_prompts.csv` as today.

### Archive (new)

```
prompt-archive/{slug}/
  v1.0-baseline/
    prompts.csv
    meta.json
  v2.0-intent-context/
    prompts.csv
    meta.json
```

Every version ever deployed lives here, read-only. Rolling back is a copy
from archive → active.

## meta.json schema

```json
{
  "version": "v2.0-intent-context",
  "client_slug": "ontario_caregiver_organization",
  "generated_at": "2026-04-20T15:30:00Z",
  "generated_by": "scripts/regenerate_prompts.py",
  "generator_version": "2.0",
  "source_model": "claude-sonnet-4-6",
  "prompt_count": 300,
  "format": "intent_context_v2",
  "personas": ["Adult Child Caregiver (50+)", "Spousal Caregiver", "..."],
  "categories": ["educational", "commercial", "navigational"],
  "predecessor": "v1.0-baseline",
  "content_hash": "sha256:a7f3c91...",
  "notes": "First tight Intent+Context format rollout; 300 prompts."
}
```

All fields required except `notes` (optional) and `predecessor` (null for
the first version).

## Version identifier format

`v{MAJOR}.{MINOR}-{tag}`

- **MAJOR** bumps when the prompt generation *method* changes. Results
  across major versions are NOT directly comparable.
  Examples: v1 legacy format → v2 Intent+Context format → v3 web-search-aware
- **MINOR** bumps for same-method tweaks. Results ARE comparable to other
  versions with the same MAJOR.
  Examples: v2.0 → v2.1 (added 20 new prompts), v2.1 → v2.2 (fixed typos)
- **tag** is a human-readable slug. Lowercase, hyphenated, no spaces.

Examples: `v1.0-baseline`, `v2.0-intent-context`, `v2.1-fanout-expanded`

## Results linkage

Every row in `data/results/{slug}/results_summary.csv` gets a new column:

- `prompts_version` — the version string (e.g. `v2.0-intent-context`) that
  was active when the test ran

Every per-test JSON embeds the full meta object under `prompts_version_meta`
so it is self-contained even if archive meta is later edited.

Dashboards that compute aggregates over time should group by
`prompts_version` and either:
- Show each version as a separate trend line, or
- Show a vertical "version bump" marker on a single line

Computing trends across major versions without a version bump marker is
misleading and should be avoided.

## Write atomicity

When writing a new version (e.g. during regeneration):

1. Compute the new `prompts.csv` content and its `meta.json` (including
   `content_hash` of the CSV)
2. Upload both files to `prompt-archive/{slug}/{new_version}/` first
3. Overwrite `client-data/{slug}/{slug}_prompts.csv` and
   `{slug}_prompts.meta.json` with the new active version

This order guarantees that if step 3 fails, the archive still contains the
new version (recoverable), and the live path still serves the previous
version (no outage).

## Rollback

To roll a client back from v2 to v1:

```
gsutil cp gs://.../prompt-archive/{slug}/v1.0-baseline/prompts.csv \
          gs://.../client-data/{slug}/{slug}_prompts.csv
gsutil cp gs://.../prompt-archive/{slug}/v1.0-baseline/meta.json \
          gs://.../client-data/{slug}/{slug}_prompts.meta.json
```

Subsequent test results will be stamped `v1.0-baseline` again.

## Migration from current unversioned state

One-time script: `scripts/migrate_to_v1_baseline.py`

For each active client (OCO, UniUni, Say I Do, Espresso Capital, Natasha
Denona):

1. Read the current `{slug}_prompts.csv`
2. Generate `meta.json` labeled `v1.0-baseline` with:
   - `generated_by`: "pre-versioning-migration"
   - `predecessor`: null
   - `content_hash`: SHA256 of the CSV
3. Upload both to `prompt-archive/{slug}/v1.0-baseline/`
4. Write the same `meta.json` to `client-data/{slug}/{slug}_prompts.meta.json`
5. Append a `prompts_version` column to the existing
   `data/results/{slug}/results_summary.csv` (if it exists), backfilling
   every row as `v1.0-baseline`

The script is idempotent: re-running it does nothing if v1.0-baseline is
already archived.

## Implementation files

- `src/prompt_generator/version_manager.py` — `PromptVersionManager` class
  that handles all reads/writes to active + archive locations
- `src/tracking/results_tracker.py` — stamps each result row with
  `prompts_version`
- `scripts/migrate_to_v1_baseline.py` — one-time migration entry point
- `scripts/regenerate_prompts.py` — uses `PromptVersionManager` to archive
  the previous version before writing a new one
