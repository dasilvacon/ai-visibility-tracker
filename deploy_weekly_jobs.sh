#!/bin/bash
# Deploy Cloud Run Jobs + Cloud Scheduler triggers for weekly automated runs.
#
# For each active client this script:
#   1. Builds/refreshes a shared job image (gcr.io/<project>/ai-visibility-weekly-job)
#   2. Creates/updates a Cloud Run Job   — ai-visibility-weekly-<slug>
#   3. Creates/updates a Cloud Scheduler — weekly-<slug>
#
# Re-running is idempotent: existing jobs/schedulers are updated in place.
#
# Prereqs (one-time — see "Before first run" section at the bottom):
#   • Service account  weekly-runner@<project>.iam.gserviceaccount.com
#     with: roles/storage.objectAdmin on bucket ai-visibility-reports-dasilva
#           roles/secretmanager.secretAccessor
#   • Service account  scheduler-invoker@<project>.iam.gserviceaccount.com
#     with: roles/run.invoker on each job (or project-wide)

set -e

export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH
export CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.13

# Load deployment config from the existing Cloud Run setup if present
if [ -f ".env.deployment" ]; then
    source .env.deployment
fi

# ---------- config ----------
PROJECT_ID="${PROJECT_ID:-${GCP_PROJECT_ID:-your-project-id}}"
REGION="${REGION:-${GCP_REGION:-us-east1}}"
JOB_IMAGE="gcr.io/${PROJECT_ID}/ai-visibility-weekly-job"
SERVICE_ACCOUNT="${WEEKLY_RUNNER_SA:-weekly-runner@${PROJECT_ID}.iam.gserviceaccount.com}"
SCHEDULER_SA="${SCHEDULER_SA:-scheduler-invoker@${PROJECT_ID}.iam.gserviceaccount.com}"

# 14h task timeout — 500 prompts × 5 platforms ≈ 7h at ~50s/prompt, plus
# substantial buffer for the upload step (NB's first fresh pass crashed
# right at 10h with main.py done but the GCS upload still running — we
# learned 2026-04-27 that with 3000+ test result files in tests/ the
# weekly snapshot upload can take 30+ minutes).
# DO NOT lower this without first adding resume-from-last-prompt to main.py —
# Cloud Run retries restart from scratch, so splitting a 7h workload into two
# 4h attempts completes zero work (learned 2026-04-21).
TASK_TIMEOUT="50400s"
MEMORY="2Gi"
CPU="2"

# ---------- clients + staggered weekly schedules (UTC) ----------
# Mondays, 2-hour spacing, starting 07:00 UTC (03:00 ET).
# Format: "slug|cron_spec|human_readable"
CLIENTS=(
  "ontario_caregiver_organization|0 7 * * 1|Mon 07:00 UTC (03:00 ET)"
  "dripos|0 9 * * 1|Mon 09:00 UTC (05:00 ET)"
  "lumo|0 11 * * 1|Mon 11:00 UTC (07:00 ET)"
  "uniuni|0 13 * * 1|Mon 13:00 UTC (09:00 ET)"
  "espresso_capital|0 15 * * 1|Mon 15:00 UTC (11:00 ET)"
  "say_i_do|0 17 * * 1|Mon 17:00 UTC (13:00 ET)"
  "clearevent|0 19 * * 1|Mon 19:00 UTC (15:00 ET)"
  "saint_javelin|0 21 * * 1|Mon 21:00 UTC (17:00 ET)"
  "natasha_denona|0 23 * * 1|Mon 23:00 UTC (19:00 ET)"
)

# ---------- colors ----------
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Weekly Jobs Deploy — Cloud Run Jobs + Scheduler     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Project:         ${PROJECT_ID}"
echo "  Region:          ${REGION}"
echo "  Job Image:       ${JOB_IMAGE}"
echo "  Service Account: ${SERVICE_ACCOUNT}"
echo "  Scheduler SA:    ${SCHEDULER_SA}"
echo "  Task Timeout:    ${TASK_TIMEOUT}"
echo ""

if [ "$PROJECT_ID" == "your-project-id" ]; then
    echo -e "${RED}✗ PROJECT_ID not set. Populate .env.deployment or export PROJECT_ID.${NC}"
    exit 1
fi

gcloud config set project ${PROJECT_ID}

# ---------- enable APIs ----------
echo -e "${BLUE}→ Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com
echo -e "${GREEN}✓ APIs enabled${NC}"

# ---------- build the job image ----------
echo ""
echo -e "${BLUE}→ Building job image (3-5 minutes)...${NC}"
gcloud builds submit \
    --config=cloudbuild.job.yaml \
    --substitutions=_IMAGE=${JOB_IMAGE} \
    .
echo -e "${GREEN}✓ Image built: ${JOB_IMAGE}${NC}"

# ---------- deploy one job + scheduler per client ----------
for entry in "${CLIENTS[@]}"; do
    IFS='|' read -r SLUG CRON HUMAN_TIME <<< "$entry"
    # Cloud Run names don't allow underscores
    JOB_NAME="ai-visibility-weekly-${SLUG//_/-}"
    SCHED_NAME="weekly-${SLUG//_/-}"

    echo ""
    echo -e "${BLUE}━━━ ${SLUG} ━━━${NC}"
    echo "  Job:      ${JOB_NAME}"
    echo "  Schedule: ${CRON}  (${HUMAN_TIME})"

    # ----- Cloud Run Job -----
    if gcloud run jobs describe ${JOB_NAME} --region=${REGION} &>/dev/null; then
        echo -e "  ${YELLOW}→ Updating existing Cloud Run Job${NC}"
        gcloud run jobs update ${JOB_NAME} \
            --image=${JOB_IMAGE} \
            --region=${REGION} \
            --memory=${MEMORY} \
            --cpu=${CPU} \
            --task-timeout=${TASK_TIMEOUT} \
            --max-retries=0 \
            --service-account=${SERVICE_ACCOUNT} \
            --set-env-vars="CLIENT_SLUG=${SLUG},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
            --set-secrets="/app/.streamlit/secrets.toml=streamlit-secrets:latest"
    else
        echo -e "  ${GREEN}→ Creating new Cloud Run Job${NC}"
        gcloud run jobs create ${JOB_NAME} \
            --image=${JOB_IMAGE} \
            --region=${REGION} \
            --memory=${MEMORY} \
            --cpu=${CPU} \
            --task-timeout=${TASK_TIMEOUT} \
            --max-retries=0 \
            --service-account=${SERVICE_ACCOUNT} \
            --set-env-vars="CLIENT_SLUG=${SLUG},GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
            --set-secrets="/app/.streamlit/secrets.toml=streamlit-secrets:latest"
    fi

    # ----- Cloud Scheduler -----
    JOB_URI="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"

    if gcloud scheduler jobs describe ${SCHED_NAME} --location=${REGION} &>/dev/null; then
        echo -e "  ${YELLOW}→ Updating scheduler${NC}"
        gcloud scheduler jobs update http ${SCHED_NAME} \
            --location=${REGION} \
            --schedule="${CRON}" \
            --time-zone="UTC" \
            --uri="${JOB_URI}" \
            --http-method=POST \
            --oauth-service-account-email=${SCHEDULER_SA}
    else
        echo -e "  ${GREEN}→ Creating scheduler${NC}"
        gcloud scheduler jobs create http ${SCHED_NAME} \
            --location=${REGION} \
            --schedule="${CRON}" \
            --time-zone="UTC" \
            --uri="${JOB_URI}" \
            --http-method=POST \
            --oauth-service-account-email=${SCHEDULER_SA}
    fi

    echo -e "  ${GREEN}✓ ${SLUG} wired up${NC}"
done

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           All weekly jobs deployed! 🎉                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Quick commands:${NC}"
echo "  List jobs:          gcloud run jobs list --region=${REGION}"
echo "  List schedulers:    gcloud scheduler jobs list --location=${REGION}"
echo "  Run one now (ad-hoc, skips schedule):"
echo "      gcloud run jobs execute ai-visibility-weekly-lumo --region=${REGION} --wait"
echo "  Trigger via scheduler (simulates Monday morning):"
echo "      gcloud scheduler jobs run weekly-lumo --location=${REGION}"
echo "  View job logs:"
echo "      gcloud run jobs executions list --job=ai-visibility-weekly-lumo --region=${REGION}"
echo ""
echo -e "${YELLOW}Before first run — one-time IAM setup:${NC}"
echo "  # Create the runner service account"
echo "  gcloud iam service-accounts create weekly-runner \\"
echo "      --display-name='Weekly AI Visibility Runner'"
echo ""
echo "  # Give it bucket access + secret access"
echo "  gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:objectAdmin \\"
echo "      gs://ai-visibility-reports-dasilva"
echo "  gcloud projects add-iam-policy-binding ${PROJECT_ID} \\"
echo "      --member=serviceAccount:${SERVICE_ACCOUNT} \\"
echo "      --role=roles/secretmanager.secretAccessor"
echo ""
echo "  # Create the scheduler invoker service account"
echo "  gcloud iam service-accounts create scheduler-invoker \\"
echo "      --display-name='Cloud Scheduler → Cloud Run Jobs'"
echo ""
echo "  # Let it invoke Cloud Run jobs"
echo "  gcloud projects add-iam-policy-binding ${PROJECT_ID} \\"
echo "      --member=serviceAccount:${SCHEDULER_SA} \\"
echo "      --role=roles/run.invoker"
echo ""
