#!/bin/bash
# Setup Google Cloud Scheduler to run monthly visibility tests automatically.
#
# This creates a Cloud Scheduler job that triggers a Cloud Run Job
# to run tests for all clients on the 1st of each month at 2 AM EST.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Cloud Run service already deployed
#   - .env.deployment file with PROJECT_ID, REGION
#
# Usage:
#   ./scripts/setup_scheduler.sh

set -e

export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH

# Load config
if [ -f ".env.deployment" ]; then
    source .env.deployment
fi

PROJECT_ID="${PROJECT_ID:-${GCP_PROJECT_ID}}"
REGION="${REGION:-${GCP_REGION:-us-east1}}"
SERVICE_NAME="${SERVICE_NAME:-ai-visibility-dashboard}"
JOB_NAME="ai-visibility-monthly-tests"

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: PROJECT_ID not set. Create .env.deployment first."
    exit 1
fi

echo "Setting up monthly test scheduler..."
echo "  Project: $PROJECT_ID"
echo "  Region:  $REGION"
echo "  Service: $SERVICE_NAME"
echo ""

# Enable Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --project=$PROJECT_ID \
    --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"

# Create a Cloud Run Job for the batch test
echo ""
echo "Creating Cloud Run Job for batch testing..."

# Get the current image
IMAGE=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --project=$PROJECT_ID \
    --format 'value(spec.template.spec.containers[0].image)')

echo "Using image: $IMAGE"

# Create/update the Cloud Run Job
gcloud run jobs create $JOB_NAME \
    --image $IMAGE \
    --region $REGION \
    --project=$PROJECT_ID \
    --memory 2Gi \
    --cpu 2 \
    --task-timeout 14400 \
    --max-retries 1 \
    --set-secrets="/app/.streamlit/secrets.toml=streamlit-secrets:latest" \
    --command "python" \
    --args "scripts/run_all_tests.py" \
    2>/dev/null || \
gcloud run jobs update $JOB_NAME \
    --image $IMAGE \
    --region $REGION \
    --project=$PROJECT_ID \
    --memory 2Gi \
    --cpu 2 \
    --task-timeout 14400 \
    --max-retries 1 \
    --set-secrets="/app/.streamlit/secrets.toml=streamlit-secrets:latest" \
    --command "python" \
    --args "scripts/run_all_tests.py"

echo "✓ Cloud Run Job created: $JOB_NAME"

# Create Cloud Scheduler job
# Runs on the 1st of every month at 2 AM EST (7 AM UTC)
echo ""
echo "Creating Cloud Scheduler job..."

# Get the compute service account
SA=$(gcloud iam service-accounts list \
    --project=$PROJECT_ID \
    --format='value(email)' \
    --filter='displayName:Compute Engine default' \
    | head -1)

gcloud scheduler jobs create http "${JOB_NAME}-scheduler" \
    --location $REGION \
    --project=$PROJECT_ID \
    --schedule "0 7 1 * *" \
    --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
    --http-method POST \
    --oauth-service-account-email $SA \
    --time-zone "America/Toronto" \
    2>/dev/null || \
gcloud scheduler jobs update http "${JOB_NAME}-scheduler" \
    --location $REGION \
    --project=$PROJECT_ID \
    --schedule "0 7 1 * *" \
    --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
    --http-method POST \
    --oauth-service-account-email $SA \
    --time-zone "America/Toronto"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   Monthly Test Scheduler Set Up Successfully! 🎉      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Schedule: 1st of every month at 2:00 AM EST"
echo ""
echo "Manual commands:"
echo "  Run now:     gcloud run jobs execute $JOB_NAME --region $REGION"
echo "  View logs:   gcloud run jobs executions list --job $JOB_NAME --region $REGION"
echo "  Pause:       gcloud scheduler jobs pause ${JOB_NAME}-scheduler --location $REGION"
echo "  Resume:      gcloud scheduler jobs resume ${JOB_NAME}-scheduler --location $REGION"
echo ""
