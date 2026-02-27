# AI Visibility Dashboard - Production Info

## 🌐 Live Dashboard URL

**https://ai-visibility-dashboard-96323652503.us-east1.run.app**

This URL is permanent and always available (never sleeps).

---

## 🔐 Login Credentials

### Admin Access (You)
- **Username:** `admin`
- **Password:** `admin123`
- **Access:** All clients

### Client Access (Natasha Denona)
- **Username:** `natasha_denona`
- **Password:** `natasha123`
- **Access:** Natasha Denona reports only

---

## 📊 Monthly Workflow

### 1. Generate New Report
```bash
./run_natasha_report.sh
```

### 2. Upload to Cloud Storage
```bash
python upload_reports_to_gcs.py --client "Natasha Denona"
```

**The dashboard automatically picks up new reports - no redeployment needed!**

---

## 🔄 Update Dashboard Code

If you make changes to the dashboard code:
```bash
./deploy_to_cloud_run.sh
```

Takes 2-3 minutes for updates.

---

## 💰 Monthly Costs

- **Cloud Run:** ~$5-10/month (only charges when accessed)
- **Cloud Storage:** ~$1-2/month
- **Total:** ~$6-12/month

First $300 in credits applied (free for several months).

---

## 🆕 Add New Clients

### 1. Add credentials to `.streamlit/secrets.toml`:
```toml
[passwords]
admin = "admin123"
natasha_denona = "natasha123"
new_client = "password123"  # Add this

[roles]
admin = "admin"
natasha_denona = "client"
new_client = "client"  # Add this

[clients]
admin = "ALL"
natasha_denona = "Natasha Denona"
new_client = "New Client Name"  # Add this
```

### 2. Update the secret:
```bash
export PATH=/opt/homebrew/share/google-cloud-sdk/bin:$PATH
export CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.13
gcloud secrets versions add streamlit-secrets --data-file=.streamlit/secrets.toml
```

### 3. Restart the service:
```bash
gcloud run services update ai-visibility-dashboard --region us-east1
```

### 4. Generate and upload their report:
```bash
# Run report generation
python main.py --brand "New Client Name"

# Upload to GCS
python upload_reports_to_gcs.py --client "New Client Name"
```

---

## 🔍 Monitoring

### View logs:
```bash
gcloud run services logs read ai-visibility-dashboard --region us-east1 --limit=50
```

### Check service status:
```bash
gcloud run services describe ai-visibility-dashboard --region us-east1
```

### View in Google Cloud Console:
https://console.cloud.google.com/run?project=gen-lang-client-0243073678

---

## 🛠️ Troubleshooting

### Dashboard not loading
1. Check service status: `gcloud run services list`
2. View logs: `gcloud run services logs read ai-visibility-dashboard --limit=50`
3. Restart: `gcloud run services update ai-visibility-dashboard --region us-east1`

### Reports not showing
1. Verify upload: `python -c "from src.storage.gcs_manager import GCSManager; gcs = GCSManager(); print(gcs.get_all_clients())"`
2. Check GCS bucket: https://console.cloud.google.com/storage/browser/ai-visibility-reports-dasilva

### Login not working
1. Verify secrets: `gcloud secrets versions access latest --secret=streamlit-secrets`
2. Update if needed: `gcloud secrets versions add streamlit-secrets --data-file=.streamlit/secrets.toml`

---

## 📞 Support

- **Google Cloud Project:** gen-lang-client-0243073678
- **GCS Bucket:** ai-visibility-reports-dasilva
- **Region:** us-east1
- **Service:** ai-visibility-dashboard

---

**Last Deployed:** 2026-02-21
**Status:** ✅ Live and running
