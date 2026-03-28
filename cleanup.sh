#!/bin/bash

# ============================================================
# AI Visibility Tracker — Cleanup Script
# ============================================================
# Run from: ~/claude-projects/ai-visibility-tracker
#
# PREREQUISITES:
#   - You've already backed up GCS data locally
#   - You've already backed up local files
#   - You're on the `dev` branch
#
# This script has 3 parts:
#   Part 1: Local file cleanup (safe — backed up)
#   Part 2: GCS cleanup (requires gcloud)
#   Part 3: Summary of what was removed
# ============================================================

set -e  # Stop on errors

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Make sure we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}ERROR: Run this from ~/claude-projects/ai-visibility-tracker${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          AI Visibility Tracker — Cleanup              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================
# PART 1: LOCAL FILE CLEANUP
# ============================================================

echo -e "${BLUE}━━━ PART 1: Local File Cleanup ━━━${NC}"
echo ""

# --- 1a: Remove old test_*.json files (2,100+ files!) ---
# These are NOT used by the dashboard. The dashboard reads:
#   - results_summary.csv (aggregated test log)
#   - monthly_scores.json (historical trends)
echo -e "${YELLOW}Removing old test_*.json files from data/results/...${NC}"
BEFORE_COUNT=$(find data/results/ -name "test_*.json" 2>/dev/null | wc -l | tr -d ' ')
find data/results/ -name "test_*.json" -delete 2>/dev/null
echo -e "${GREEN}  Removed $BEFORE_COUNT test JSON files${NC}"

# --- 1b: Remove the archive folder (already backed up) ---
echo -e "${YELLOW}Removing data/results/archive/...${NC}"
ARCHIVE_COUNT=$(find data/results/archive/ -type f 2>/dev/null | wc -l | tr -d ' ')
rm -rf data/results/archive/
echo -e "${GREEN}  Removed archive folder ($ARCHIVE_COUNT files)${NC}"

# --- 1c: Remove old Natasha Denona loose files from data/ root ---
# Natasha Denona is no longer an active client. Config is preserved in backup.
echo -e "${YELLOW}Removing Natasha Denona loose files from data/ root...${NC}"
rm -f data/natasha_denona_brand_config.json
rm -f data/natasha_denona_brand_config_no_web.json
rm -f data/natasha_denona_keywords.csv
rm -f data/natasha_denona_personas.json
rm -f data/generated_prompts_natasha_denona.csv
echo -e "${GREEN}  Removed 5 Natasha Denona files${NC}"

# --- 1d: Remove stale generated/temp files from data/ ---
echo -e "${YELLOW}Removing stale generated files...${NC}"
rm -f data/generated_prompts.csv
rm -f data/generated_prompts_summary.txt
rm -f data/test_prompts.csv
rm -f data/test_prompts_summary.txt
rm -f data/prompt_batches.json
rm -f data/clients.json_.gstmp
rm -f data/.DS_Store
rm -f .DS_Store
echo -e "${GREEN}  Removed temp/generated files${NC}"

# --- 1e: Remove old report files from data/reports/ ---
# These are from January testing and aren't client-facing reports
echo -e "${YELLOW}Cleaning up old report files...${NC}"
REPORT_COUNT=$(find data/reports/ -name "platform_comparison_*.txt" -o -name "summary_report_*.txt" 2>/dev/null | wc -l | tr -d ' ')
find data/reports/ -name "platform_comparison_*.txt" -delete 2>/dev/null
find data/reports/ -name "summary_report_*.txt" -delete 2>/dev/null
echo -e "${GREEN}  Removed $REPORT_COUNT old report files${NC}"

# --- 1f: Remove old documentation files from root ---
# These were generated during development and are no longer needed.
# Keeping: CLAUDE.md, README.md, STABILIZATION_STEPS.md
echo -e "${YELLOW}Removing outdated documentation files...${NC}"
rm -f CLOUD_RUN_DEPLOYMENT.md
rm -f COMPETITIVE_FEATURES_SUMMARY.md
rm -f COMPETITIVE_REPORT_UPDATE_SUMMARY.md
rm -f CRITICAL_FIXES_COMPLETED.md
rm -f CUSTOM_DOMAIN_SETUP.md
rm -f DASHBOARD_INFO.md
rm -f DEPLOYMENT_INSTRUCTIONS.md
rm -f DEPLOY_NOW.md
rm -f GCS_READY.md
rm -f GIT_SYNC_SETUP.md
rm -f GOOGLE_CLOUD_SETUP.md
rm -f GOOGLE_STYLE_IMPLEMENTATION_PLAN.md
rm -f HISTORICAL_TRACKING.md
rm -f HOW_TO_USE.md
rm -f HOW_TO_USE_COMPETITIVE_REPORTS.md
rm -f INDUSTRY_AGNOSTIC_PROMPT_SYSTEM.md
rm -f PRODUCTION_FIXES.md
rm -f QUICK_START.md
rm -f QUICK_START_GCS.md
rm -f REPORT_REDESIGN_ANALYSIS.md
rm -f SECRETS_TO_COPY.txt
rm -f SECURITY_CLEANUP_SUMMARY.md
rm -f SENTIMENT_ANALYSIS.md
rm -f SIMPLE_3DAY_PLAN.md
rm -f STAGING_SETUP.md
rm -f START_HERE.md
echo -e "${GREEN}  Removed 26 old documentation files${NC}"

# --- 1g: Remove one-off / obsolete scripts ---
# These are scripts that were used during development and aren't part of the app
echo -e "${YELLOW}Removing obsolete scripts...${NC}"
rm -f check.py
rm -f example_competitive_integration.py
rm -f generate_natasha_competitive_report.py
rm -f generate_prompts_all_clients.py
rm -f quick_upload_report.py
rm -f save_historical_data.py
rm -f sync_data_to_gcs.py
rm -f test_industry_agnostic_prompts.py
rm -f upload_reports_to_gcs.py
rm -f run_natasha_report.sh
rm -f test_git_sync.sh
rm -f setup_git_credentials.sh
rm -f simple_upload.sh
rm -f upload_to_gcs.sh
rm -f run_and_upload_report.sh
rm -f deploy_secrets.sh
rm -f run_local_test.sh
rm -f analysis_output.log
rm -f test_run.log
rm -f requirements_streamlit.txt
echo -e "${GREEN}  Removed 20 obsolete scripts and logs${NC}"

# --- 1h: Remove old backup folder in data/ ---
echo -e "${YELLOW}Removing data/backups/...${NC}"
rm -rf data/backups/
echo -e "${GREEN}  Removed old backups folder${NC}"

# --- 1i: Remove old prompt generation drafts ---
echo -e "${YELLOW}Removing old prompt generation drafts...${NC}"
rm -rf data/prompt_generation/
echo -e "${GREEN}  Removed prompt generation drafts${NC}"

echo ""
echo -e "${GREEN}━━━ Local cleanup complete! ━━━${NC}"
echo ""

# ============================================================
# PART 2: GCS CLEANUP
# ============================================================

echo -e "${BLUE}━━━ PART 2: GCS Cleanup ━━━${NC}"
echo ""
echo -e "${YELLOW}This part removes old test_*.json files from GCS.${NC}"
echo -e "${YELLOW}Your GCS data was backed up to ~/ai-visibility-backups/${NC}"
echo ""

read -p "Do you want to clean up GCS test files too? (y/n): " CLEAN_GCS

if [ "$CLEAN_GCS" = "y" ] || [ "$CLEAN_GCS" = "Y" ]; then
    export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"

    # Remove old test JSON files from GCS (keep results_summary.csv and monthly_scores.json)
    echo -e "${YELLOW}Listing test files in GCS...${NC}"

    # Get list of test_*.json files in GCS test-results folder
    GCS_TEST_FILES=$(gsutil ls "gs://ai-visibility-reports-dasilva/test-results/test_*.json" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  Found $GCS_TEST_FILES test JSON files in GCS"

    if [ "$GCS_TEST_FILES" -gt 0 ]; then
        echo -e "${YELLOW}Removing test_*.json files from GCS test-results/...${NC}"
        gsutil -o "GSUtil:parallel_process_count=1" rm "gs://ai-visibility-reports-dasilva/test-results/test_*.json" 2>/dev/null || true
        echo -e "${GREEN}  Removed GCS test files${NC}"
    fi

    # Remove old Natasha Denona data from GCS (already backed up)
    echo -e "${YELLOW}Checking for Natasha Denona files in GCS...${NC}"
    GCS_ND_FILES=$(gsutil ls "gs://ai-visibility-reports-dasilva/Natasha_Denona/**" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$GCS_ND_FILES" -gt 0 ]; then
        echo ""
        read -p "Remove $GCS_ND_FILES Natasha Denona files from GCS? (y/n): " CLEAN_ND
        if [ "$CLEAN_ND" = "y" ] || [ "$CLEAN_ND" = "Y" ]; then
            gsutil -o "GSUtil:parallel_process_count=1" rm -r "gs://ai-visibility-reports-dasilva/Natasha_Denona/" 2>/dev/null || true
            echo -e "${GREEN}  Removed Natasha Denona folder from GCS${NC}"
        else
            echo -e "${YELLOW}  Skipped Natasha Denona cleanup${NC}"
        fi
    fi

    echo ""
    echo -e "${GREEN}━━━ GCS cleanup complete! ━━━${NC}"
else
    echo -e "${YELLOW}Skipping GCS cleanup. You can run this later.${NC}"
fi

echo ""

# ============================================================
# PART 3: SUMMARY
# ============================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  Cleanup Summary                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Count what's left
REMAINING_FILES=$(find . -type f -not -path './.git/*' -not -path './.claude/*' -not -path './.devcontainer/*' | wc -l | tr -d ' ')
echo -e "  Files remaining in project: ${GREEN}$REMAINING_FILES${NC}"
echo ""
echo -e "  ${GREEN}What was preserved:${NC}"
echo "    - CLAUDE.md, README.md, STABILIZATION_STEPS.md"
echo "    - All source code (src/, dashboard_pages/)"
echo "    - Active client data (OCO, Say I Do, Espresso Capital)"
echo "    - results_summary.csv (test logs for reporting)"
echo "    - monthly_scores.json (historical trends)"
echo "    - Deploy scripts (deploy_to_cloud_run.sh, startup.sh, setup*.sh)"
echo "    - Dockerfile, requirements.txt, .env.deployment"
echo ""
echo -e "  ${YELLOW}Next step:${NC} Commit the cleanup"
echo "    git add -A"
echo "    git commit -m 'Clean up: remove 2100+ stale test files, old docs, and unused scripts'"
echo "    git push origin dev"
echo ""
