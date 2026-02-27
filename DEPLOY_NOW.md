# Deploy to Cloud Run - Quick Start

Your dashboard is ready to deploy! Follow these steps:

## Step 1: Run Setup (5-10 minutes)

```bash
./setup_cloud_run.sh
```

This will:
1. Open your browser to login to Google Cloud
2. Create a new project (or use existing)
3. Ask you to enable billing (required for Cloud Run)
4. Enable necessary Google APIs
5. Create secrets for authentication
6. Save your configuration

**What you'll need:**
- Google account (you already have one for GCS)
- Credit card for billing (free $300 credits, then ~$6-12/month)
- Your GCS bucket name: `ai-visibility-reports-dasilva`

## Step 2: Deploy (5-10 minutes)

```bash
./deploy_to_cloud_run.sh
```

This will:
1. Build your Docker container
2. Upload to Google Container Registry
3. Deploy to Cloud Run
4. Give you a permanent URL like: `https://ai-visibility-dashboard-xyz.run.app`

## Step 3: Test

Visit the URL and login with:
- **Username:** admin
- **Password:** admin123

Select "Natasha Denona" and verify the report loads.

## Step 4: Share with Clients

Give them:
- **URL:** (from deployment output)
- **Username:** natasha_denona
- **Password:** natasha123

## Future Updates

When you want to update the dashboard:
```bash
./deploy_to_cloud_run.sh
```

When you generate new reports:
```bash
python upload_reports_to_gcs.py --client "Natasha Denona"
```

The dashboard automatically picks up new reports - no redeployment needed!

---

## Troubleshooting

**"gcloud: command not found"**
→ Already installed at `/opt/homebrew/share/google-cloud-sdk/bin/gcloud`
→ The scripts handle the PATH automatically

**"Billing required"**
→ You need to add a payment method in Google Cloud Console
→ $300 free credits, then ~$6-12/month after

**"Secret not found"**
→ Make sure `.streamlit/secrets.toml` exists
→ Run `setup_cloud_run.sh` to create the secret

**"Image not found"**
→ The first deployment takes 5-10 minutes to build
→ Subsequent deployments are faster (2-3 minutes)

---

## Ready?

Run: `./setup_cloud_run.sh`
