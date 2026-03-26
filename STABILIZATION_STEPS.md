# AI Visibility Tracker — Stabilization Steps
## Run these in your Mac terminal (not Cowork)

---

## STEP 1: Back up your GCS data (safety net)

This copies all your GCS data to a timestamped backup folder so nothing can be lost.

```bash
cd ~/claude-projects/ai-visibility-tracker
export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"

# Create a backup of everything in GCS
gsutil -m cp -r gs://ai-visibility-reports-dasilva/ gs://ai-visibility-reports-dasilva-backup-$(date +%Y%m%d)/
```

If that doesn't work (can't create new buckets easily), do a local backup instead:

```bash
mkdir -p ~/ai-visibility-backups/gcs-backup-$(date +%Y%m%d)
gsutil -m cp -r gs://ai-visibility-reports-dasilva/ ~/ai-visibility-backups/gcs-backup-$(date +%Y%m%d)/
```

**What this does:** Downloads everything from GCS to a folder on your Mac. Even if something goes wrong later, you have a full copy.

---

## STEP 2: Back up your local files too

```bash
cp -r ~/claude-projects/ai-visibility-tracker ~/ai-visibility-backups/local-backup-$(date +%Y%m%d)
```

**What this does:** Copies your entire local project. Belt and suspenders.

---

## STEP 3: Get Git into a clean state

Right now you have ~25 uncommitted changes. Let's commit everything so it's tracked.

```bash
cd ~/claude-projects/ai-visibility-tracker

# First, see what's changed
git status

# Stage everything that's modified or new
git add -A

# Commit with a clear message
git commit -m "Stabilization checkpoint: commit all local changes before workflow cleanup

Includes:
- Updated dashboard pages (competitors, historical_trends, overview, run_report)
- Updated client data (OCO brand config, personas)
- Updated core modules (main.py, gcs_sync, gcs_manager, results_tracker, etc.)
- Added CLAUDE.md project instructions
- Removed stale Natasha Denona report files"

# Push to GitHub so it's backed up remotely too
git push origin main
```

---

## STEP 4: Create the dev branch

This is the branch where ALL future changes happen. The `main` branch stays stable.

```bash
# Create and switch to dev branch
git checkout -b dev

# Push it to GitHub
git push -u origin dev
```

**From now on:**
- `main` = what's deployed and live
- `dev` = where you (and Claude Code) make changes

---

## STEP 5: Tell Claude Code to use the dev branch

Next time you open Claude Code in your terminal, paste this:

```
Before making any changes, always check which branch I'm on with `git branch`.
If I'm on `main`, switch to `dev` first with `git checkout dev`.
Never commit directly to main. Always work on dev.
When I say "deploy", that means: merge dev into main, then run ./deploy_to_cloud_run.sh
```

Or even better — this rule is already going into your CLAUDE.md (I'm updating it).

---

## Quick reference: Your new workflow

```
┌─────────────────────────────────────────────────┐
│                  YOUR WORKFLOW                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. PLAN (Cowork or terminal)                    │
│     "I want to add feature X"                    │
│         │                                        │
│         ▼                                        │
│  2. BUILD (Claude Code in terminal)              │
│     Working on `dev` branch                      │
│     Making changes, testing locally              │
│         │                                        │
│         ▼                                        │
│  3. REVIEW                                       │
│     Look at changes: git diff main..dev          │
│     Test the dashboard locally if possible        │
│         │                                        │
│         ▼                                        │
│  4. DEPLOY (Claude Code in terminal)             │
│     git checkout main                            │
│     git merge dev                                │
│     ./deploy_to_cloud_run.sh                     │
│     git checkout dev   ← go back to dev          │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## Where things live (cheat sheet)

| What | Where | Purpose |
|------|-------|---------|
| **Code** | Git (GitHub) | Version control, backup, history |
| **Client data** | GCS bucket | Permanent storage, survives deploys |
| **Secrets/API keys** | GCP Secret Manager | Secure, never in code |
| **Live app** | Cloud Run | What clients see |
| **Local files** | Your Mac | Temporary working copy |

**The rule:** Git is for code. GCS is for data. They don't cross.

---

## What NOT to do anymore

- ❌ Don't make changes directly on `main`
- ❌ Don't deploy without committing to Git first
- ❌ Don't edit files in GCS manually (use the app or scripts)
- ❌ Don't worry about local data files matching GCS — the app downloads from GCS on startup
- ❌ Don't run `git reset --hard` or force-push (you've been burned by this before)
