# Quick Start: Google Cloud Storage

## TL;DR - Monthly Workflow

Once set up, your monthly workflow is:

```bash
# 1. Run visibility tests
./run_natasha_report.sh

# 2. Upload reports to cloud
python upload_reports_to_gcs.py --client "Natasha Denona"

# 3. Done! Reports are now in the cloud
```

## One-Time Setup (15 minutes)

### 1. Create Google Cloud Storage

Follow the detailed steps in `GOOGLE_CLOUD_SETUP.md`:
- Create GCS project and bucket
- Create service account
- Download credentials JSON
- Save as `gcs-credentials.json` in project root

### 2. Install GCS Library

```bash
source venv/bin/activate
pip install google-cloud-storage
```

### 3. Test Connection

```bash
python -c "from src.storage.gcs_manager import GCSManager; gcs = GCSManager(bucket_name='ai-visibility-reports', credentials_path='gcs-credentials.json'); print('✓ Connected to:', gcs.bucket_name)"
```

### 4. Upload Existing Reports (if any)

```bash
# Upload all clients at once
python upload_reports_to_gcs.py --all

# Or upload one client
python upload_reports_to_gcs.py --client "Natasha Denona"
```

### 5. Configure Streamlit Cloud

In your Streamlit Cloud app settings, add to secrets:

```toml
[gcs]
bucket_name = "ai-visibility-reports"
credentials = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  ... paste entire gcs-credentials.json contents ...
}
'''
```

### 6. Deploy to Streamlit Cloud

```bash
git add .
git commit -m "Add Google Cloud Storage support"
git push
# Then reboot your Streamlit Cloud app
```

## How It Works

### Local Development
- Dashboard reads from `data/reports/` (local files)
- No GCS credentials needed for local viewing

### Production (Streamlit Cloud)
- Dashboard reads from GCS bucket
- Reports are fetched from cloud storage
- Credentials stored securely in Streamlit secrets

### Running Reports Monthly

1. **Generate reports locally:**
   ```bash
   ./run_natasha_report.sh
   ```

2. **Upload to cloud:**
   ```bash
   python upload_reports_to_gcs.py --client "Natasha Denona"
   ```

3. **Client views in browser:**
   - Client logs into Streamlit Cloud app
   - Sees updated report automatically

## Folder Structure in GCS

```
ai-visibility-reports/
├── Natasha_Denona/
│   ├── visibility_report_Natasha_Denona.html     ← Latest report
│   ├── executive_summary_Natasha_Denona.pdf      ← Latest PDF
│   ├── raw_data_Natasha_Denona.csv              ← Latest data
│   └── history/
│       ├── 2026-01/                             ← Archived Jan reports
│       │   ├── visibility_report_Natasha_Denona.html
│       │   └── ...
│       └── 2026-02/                             ← Archived Feb reports
│           ├── visibility_report_Natasha_Denona.html
│           └── ...
```

## Commands Reference

### Upload Reports

```bash
# Single client
python upload_reports_to_gcs.py --client "Client Name"

# All clients
python upload_reports_to_gcs.py --all

# Custom bucket/credentials
python upload_reports_to_gcs.py --client "Client Name" \\
  --bucket my-bucket \\
  --credentials path/to/creds.json
```

### Check What's in Cloud

```python
from src.storage.gcs_manager import GCSManager

gcs = GCSManager(
    bucket_name='ai-visibility-reports',
    credentials_path='gcs-credentials.json'
)

# List all clients
clients = gcs.get_all_clients()
print("Clients:", clients)

# List reports for a client
reports = gcs.list_client_reports("Natasha Denona")
for report in reports:
    print(f"  {report['name']} ({report['size']/1024:.1f} KB)")
```

## Troubleshooting

### "Credentials file not found"
Make sure `gcs-credentials.json` is in your project root directory.

### "Permission denied" errors
Check that your service account has "Storage Object Admin" role.

### "Bucket does not exist"
Double-check the bucket name in your config matches the actual bucket.

### Dashboard shows "Report not found"
Make sure you've uploaded the reports:
```bash
python upload_reports_to_gcs.py --client "Client Name"
```

### Reports not updating on Streamlit Cloud
After uploading new reports, **reboot your Streamlit Cloud app** to clear the cache.

## Cost Estimate

For 14 clients with monthly reports:
- Storage: ~$0.50/month
- Operations: ~$0.10/month
- **Total: ~$1-2/month**

## Security

- ✅ Credentials never committed to git
- ✅ Bucket is private (not publicly accessible)
- ✅ Only service account can access files
- ✅ Streamlit Cloud stores credentials in encrypted secrets

## Need Help?

See the full setup guide: `GOOGLE_CLOUD_SETUP.md`
