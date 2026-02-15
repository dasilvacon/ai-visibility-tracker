# ✅ Google Cloud Storage Integration - Ready!

Your AI Visibility Tracker is now set up to use Google Cloud Storage for all 14 clients.

## What's Been Added

### 1. **GCS Manager** (`src/storage/gcs_manager.py`)
- Handles all uploads and downloads from Google Cloud Storage
- Supports both Streamlit Cloud (secrets) and local development
- Automatic folder structure: `Client_Name/reports/` + `Client_Name/history/2026-01/`

### 2. **Upload Script** (`upload_reports_to_gcs.py`)
- Upload single client: `python upload_reports_to_gcs.py --client "Client Name"`
- Upload all clients: `python upload_reports_to_gcs.py --all`
- Automatic history archiving by month

### 3. **Complete Workflow Script** (`run_and_upload_report.sh`)
- One command to run tests + upload: `./run_and_upload_report.sh "Client Name"`
- Checks for required files
- Filters prompts by client
- Uploads to cloud automatically

### 4. **Updated Dashboard** (`streamlit_app_html.py`)
- Automatically detects if GCS is configured
- Reads from cloud storage when available
- Falls back to local files if GCS not configured
- Works in both local and Streamlit Cloud environments

### 5. **Documentation**
- **`GOOGLE_CLOUD_SETUP.md`** - Detailed setup guide
- **`QUICK_START_GCS.md`** - Quick reference for daily use
- **`GCS_READY.md`** - This file

## Next Steps (Do These Once)

### Step 1: Create Google Cloud Storage (15 min)

Follow the guide in `GOOGLE_CLOUD_SETUP.md`:

1. Create GCS project and bucket named `ai-visibility-reports`
2. Create service account with "Storage Object Admin" role
3. Download credentials JSON
4. Save as `gcs-credentials.json` in project root
5. **NEVER commit this file to git** (already in .gitignore)

### Step 2: Install GCS Library

```bash
source venv/bin/activate
pip install google-cloud-storage
```

### Step 3: Test Connection

```bash
python -c "from src.storage.gcs_manager import GCSManager; gcs = GCSManager(bucket_name='ai-visibility-reports', credentials_path='gcs-credentials.json'); print('✓ Connected!')"
```

### Step 4: Upload Existing Reports (if any)

If you have reports already generated:

```bash
# Upload all at once
python upload_reports_to_gcs.py --all

# Or upload one by one
python upload_reports_to_gcs.py --client "Natasha Denona"
```

### Step 5: Configure Streamlit Cloud

1. Go to your Streamlit Cloud app
2. Click Settings → Secrets
3. Add (paste entire contents of `gcs-credentials.json`):

```toml
[gcs]
bucket_name = "ai-visibility-reports"
credentials = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...",
  ...
}
'''
```

### Step 6: Push to GitHub & Redeploy

```bash
git add .
git commit -m "Add Google Cloud Storage integration"
git push
```

Then **reboot your Streamlit Cloud app** to pick up the changes.

## Monthly Workflow (After Setup)

### Option A: Full Workflow (Recommended)
```bash
./run_and_upload_report.sh "Client Name"
```

This single command:
1. Runs visibility tests
2. Generates all reports
3. Uploads to Google Cloud Storage
4. Archives to history folder

### Option B: Separate Steps
```bash
# 1. Run tests
./run_natasha_report.sh

# 2. Upload to cloud
python upload_reports_to_gcs.py --client "Natasha Denona"
```

### For All 14 Clients

Run reports one by one, then:
```bash
python upload_reports_to_gcs.py --all
```

## How It Works

### Before GCS (Old Way)
- ❌ Reports committed to git (large files)
- ❌ Git history bloats over time
- ❌ Streamlit Cloud app has size limits

### After GCS (New Way)
- ✅ Reports stored in Google Cloud Storage
- ✅ Git stays clean and fast
- ✅ Unlimited storage ($1-2/month)
- ✅ Historical tracking by month
- ✅ Clients see latest reports automatically

## File Structure

### Local (Your Computer)
```
ai-visibility-tracker/
├── gcs-credentials.json              ← Never commit!
├── run_and_upload_report.sh          ← Run this monthly
├── upload_reports_to_gcs.py          ← Or run this after tests
├── data/
│   ├── reports/                      ← Generated locally
│   │   ├── visibility_report_*.html
│   │   ├── executive_summary_*.pdf
│   │   └── ...
│   └── generated_prompts.csv         ← Your prompts
└── src/
    └── storage/
        └── gcs_manager.py            ← GCS integration
```

### Google Cloud Storage
```
ai-visibility-reports/              ← Your GCS bucket
├── Natasha_Denona/
│   ├── visibility_report_Natasha_Denona.html    ← Latest
│   ├── executive_summary_Natasha_Denona.pdf
│   ├── raw_data_Natasha_Denona.csv
│   └── history/
│       ├── 2026-01/                ← Jan archive
│       ├── 2026-02/                ← Feb archive
│       └── 2026-03/                ← Mar archive
├── Client_2/
├── Client_3/
└── ... (all 14 clients)
```

## Cost

For 14 clients with monthly reports:
- **Storage:** $0.02/GB/month
- **Operations:** $0.05 per 10,000 ops
- **Estimated total:** ~$1-2/month

## Security

- ✅ Bucket is private (not publicly accessible)
- ✅ Only your service account can access
- ✅ Credentials never committed to git
- ✅ Streamlit Cloud stores secrets encrypted

## Troubleshooting

### "Credentials file not found"
Make sure `gcs-credentials.json` is in your project root.

### "Permission denied"
Check that service account has "Storage Object Admin" role in GCS.

### Reports not showing on Streamlit Cloud
1. Confirm reports uploaded: `python upload_reports_to_gcs.py --all`
2. Check Streamlit Cloud secrets are configured
3. **Reboot the Streamlit Cloud app** to clear cache

### Want to see what's in the cloud?
```python
from src.storage.gcs_manager import GCSManager

gcs = GCSManager(
    bucket_name='ai-visibility-reports',
    credentials_path='gcs-credentials.json'
)

# List all clients
print("Clients:", gcs.get_all_clients())

# List reports for a client
reports = gcs.list_client_reports("Natasha Denona")
for r in reports:
    print(f"  {r['name']} - {r['updated']}")
```

## Questions?

- **Setup:** See `GOOGLE_CLOUD_SETUP.md`
- **Daily use:** See `QUICK_START_GCS.md`
- **Need help?** tiffany@dasilvaconsulting.com

---

🎉 **You're all set!** Once you complete the one-time setup, your monthly workflow is just one command:

```bash
./run_and_upload_report.sh "Client Name"
```
