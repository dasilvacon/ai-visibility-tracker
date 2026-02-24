# Deploy to Google Cloud Run - Step by Step Guide

Your dashboard will be **always available** at a permanent URL like:
`https://ai-visibility-dashboard-xyz.run.app`

**Cost:** ~$6-12/month total
- Cloud Run: ~$5-10/month (only charges when in use)
- Cloud Storage: ~$1-2/month

---

## Prerequisites

- [ ] Google Cloud account (free tier available)
- [ ] Credit card (required by Google, but stays within free tier limits initially)
- [ ] `gcloud` CLI installed

---

## Step 1: Install Google Cloud CLI (5 minutes)

### Mac (using Homebrew)
```bash
brew install google-cloud-sdk
```

### Or download from Google
1. Go to: https://cloud.google.com/sdk/docs/install
2. Download for your OS
3. Run installer
4. Follow prompts

### Verify installation
```bash
gcloud --version
```

---

## Step 2: Login to Google Cloud (2 minutes)

```bash
gcloud auth login
```

This opens your browser - sign in with your Google account.

---

## Step 3: Create Google Cloud Project (3 minutes)

### Option A: Using Console (Easier)
1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Name: `ai-visibility-tracker`
4. Click "Create"
5. Copy the Project ID (it will be something like `ai-visibility-tracker-123456`)

### Option B: Using CLI
```bash
gcloud projects create ai-visibility-tracker-$(date +%s) --name="AI Visibility Tracker"

# List projects to get the ID
gcloud projects list
```

### Set the project
```bash
# Replace with your project ID
gcloud config set project ai-visibility-tracker-123456

# Set environment variable for scripts
export GCP_PROJECT_ID="ai-visibility-tracker-123456"
```

---

## Step 4: Enable Billing (Required)

1. Go to https://console.cloud.google.com/billing
2. Link a billing account to your project
3. You get $300 free credits for 90 days
4. After credits, costs are ~$6-12/month

---

## Step 5: Create Cloud Storage Bucket (5 minutes)

### Using Console
1. Go to https://console.cloud.google.com/storage
2. Click "Create Bucket"
3. **Name:** `ai-visibility-reports-[your-company]` (must be globally unique)
4. **Location:** Multi-region (or choose your nearest region)
5. **Storage class:** Standard
6. **Access control:** Uniform
7. **Public access:** Do NOT allow
8. Click "Create"

### Using CLI
```bash
# Replace with a unique bucket name
BUCKET_NAME="ai-visibility-reports-dasilva"

gsutil mb -p ${GCP_PROJECT_ID} -l us-east1 gs://${BUCKET_NAME}
```

---

## Step 6: Create Service Account & Credentials (5 minutes)

### Using Console
1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "Create Service Account"
3. **Name:** `ai-visibility-uploader`
4. **Description:** "Manages visibility reports in Cloud Storage"
5. Click "Create and Continue"
6. **Role:** "Storage Object Admin"
7. Click "Continue" → "Done"

### Download credentials
1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON"
5. Click "Create"
6. **Save the file as:** `gcs-credentials.json` in your project root

```bash
# Move downloaded file to project
mv ~/Downloads/ai-visibility-tracker-*.json gcs-credentials.json
```

---

## Step 7: Configure Local Secrets (3 minutes)

Create `.streamlit/secrets.toml`:

```bash
mkdir -p .streamlit
```

Add your GCS configuration to `.streamlit/secrets.toml`:

```toml
# Authentication credentials (your existing ones)
[passwords]
tiffany = "your-password"
client1 = "client-password"

[roles]
tiffany = "admin"
client1 = "client"

[clients]
tiffany = "ALL"
client1 = "Natasha Denona"

# Add GCS configuration
[gcs]
bucket_name = "ai-visibility-reports-dasilva"  # Your bucket name
credentials_file = "gcs-credentials.json"
```

**IMPORTANT:** Make sure `.streamlit/secrets.toml` is in `.gitignore`!

---

## Step 8: Install Dependencies (2 minutes)

```bash
source venv/bin/activate
pip install google-cloud-storage
```

---

## Step 9: Test GCS Connection (1 minute)

```bash
python -c "
from src.storage.gcs_manager import GCSManager
gcs = GCSManager()
print('✓ Successfully connected to Google Cloud Storage!')
print('Bucket:', gcs.bucket_name)
"
```

If this works, you're ready to deploy!

---

## Step 10: Upload Existing Reports (5 minutes)

```bash
# Upload all existing reports
python upload_reports_to_gcs.py --all

# Or upload one client
python upload_reports_to_gcs.py --client "Natasha Denona"
```

---

## Step 11: Create Cloud Secret for Deployment (2 minutes)

```bash
# Create secret from your secrets file
gcloud secrets create streamlit-secrets --data-file=.streamlit/secrets.toml

# Verify
gcloud secrets list
```

---

## Step 12: Deploy to Cloud Run! (5-10 minutes)

```bash
./deploy_to_cloud_run.sh
```

This script will:
1. ✓ Enable required Google Cloud APIs
2. ✓ Build your Docker container
3. ✓ Upload to Google Container Registry
4. ✓ Deploy to Cloud Run
5. ✓ Give you a permanent URL

**First deployment takes 5-10 minutes. Subsequent deployments: 2-3 minutes.**

---

## Step 13: Get Your Dashboard URL

After deployment completes, you'll see:

```
Your dashboard is now live at:
https://ai-visibility-dashboard-xyz.run.app
```

**Share this URL with your clients!** It's permanent and always available.

---

## Step 14: Test Your Dashboard

1. Visit the URL in your browser
2. Login with your credentials
3. Select a brand
4. Verify the report loads

---

## Ongoing: Monthly Workflow

### Generate and upload new reports

```bash
# Run report for a client
./run_natasha_report.sh

# Upload to GCS
python upload_reports_to_gcs.py --client "Natasha Denona"
```

**The dashboard automatically picks up new reports - no redeployment needed!**

---

## Optional: Add Custom Domain

1. Go to Cloud Run console: https://console.cloud.google.com/run
2. Click on your service: `ai-visibility-dashboard`
3. Click "Manage Custom Domains"
4. Click "Add Mapping"
5. Choose your domain (e.g., `dashboard.dasilvaconsulting.com`)
6. Follow instructions to add DNS records

---

## Troubleshooting

### "gcloud: command not found"
→ Install Google Cloud CLI (see Step 1)

### "Permission denied" during deployment
→ Make sure you have Owner or Editor role on the project

### "Bucket not found"
→ Check bucket name in `.streamlit/secrets.toml` matches actual bucket

### Dashboard loads but no reports
→ Upload reports: `python upload_reports_to_gcs.py --all`

### "Module not found: google.cloud.storage"
→ The Dockerfile installs it automatically, but if testing locally: `pip install google-cloud-storage`

### Need to update the dashboard code
```bash
# Make your changes, then redeploy
./deploy_to_cloud_run.sh
```

---

## Cost Breakdown

### Free Tier (First 90 days)
- $300 in credits
- Easily covers several months

### After Free Tier
**Cloud Run:**
- First 2 million requests/month: FREE
- 180,000 vCPU-seconds/month: FREE
- 360,000 GiB-seconds/month: FREE
- After that: ~$0.00002400 per vCPU-second

**For your use case (14 clients checking monthly):**
- Requests: ~500/month (well under 2M)
- **Estimated: $5-10/month**

**Cloud Storage:**
- Storage: ~$0.02/GB/month
- ~50-100MB per client = 1-2GB total
- **Estimated: $1-2/month**

**Total: ~$6-12/month** (often less with free tier usage)

---

## Security Notes

✅ **What's secure:**
- Dashboard requires login
- Reports stored in private GCS bucket
- Credentials stored in Secret Manager
- HTTPS encryption

❌ **Never commit:**
- `gcs-credentials.json`
- `.streamlit/secrets.toml`
- Any files with passwords

---

## Support

- **Google Cloud Run docs:** https://cloud.google.com/run/docs
- **Streamlit on Cloud Run:** https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker
- **Cloud Storage docs:** https://cloud.google.com/storage/docs

---

## Quick Reference Commands

```bash
# Check deployment status
gcloud run services list

# View logs
gcloud run services logs read ai-visibility-dashboard --limit=50

# Update deployment
./deploy_to_cloud_run.sh

# Upload new reports
python upload_reports_to_gcs.py --all

# Delete service (if needed)
gcloud run services delete ai-visibility-dashboard --region=us-east1
```

---

🎉 **Your dashboard is now production-ready and always available!**
