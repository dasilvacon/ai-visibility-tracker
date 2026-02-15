# Google Cloud Storage Setup Guide

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name it: `ai-visibility-tracker`
4. Click "Create"

## Step 2: Enable Cloud Storage API

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Cloud Storage API"
3. Click "Enable"

## Step 3: Create Storage Bucket

1. Go to [Cloud Storage](https://console.cloud.google.com/storage)
2. Click "Create Bucket"
3. **Bucket name:** `ai-visibility-reports` (must be globally unique - add your company name if taken)
4. **Location type:** Region (choose closest to you, e.g., `us-east1`)
5. **Storage class:** Standard
6. **Access control:** Uniform
7. **Public access:** Do NOT allow public access
8. Click "Create"

## Step 4: Create Service Account

1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. **Name:** `ai-visibility-uploader`
4. **Description:** "Uploads visibility reports to Cloud Storage"
5. Click "Create and Continue"
6. **Role:** Select "Storage Object Admin"
7. Click "Continue" → "Done"

## Step 5: Create Service Account Key

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON" format
5. Click "Create"
6. **Save the downloaded JSON file as:** `gcs-credentials.json` in your project root
7. ⚠️ **IMPORTANT:** Add to `.gitignore` - NEVER commit this file!

## Step 6: Add to .gitignore

Make sure your `.gitignore` includes:
```
gcs-credentials.json
*.json  # If you want to ignore all JSON (careful with config files)
```

## Step 7: Update .streamlit/secrets.toml (Local)

Add to your local secrets file:
```toml
[gcs]
bucket_name = "ai-visibility-reports"
credentials_file = "gcs-credentials.json"
```

## Step 8: Configure Streamlit Cloud Secrets

In Streamlit Cloud app settings, add:
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
  "client_id": "...",
  ...
}
'''
```
(Copy the entire contents of your downloaded JSON file)

## Cost Estimate

- **Storage:** $0.02/GB/month (Standard storage)
- **Operations:** $0.05 per 10,000 operations
- **Expected cost for 14 clients with monthly reports:** ~$1-2/month

## Bucket Structure

Your bucket will be organized like this:
```
ai-visibility-reports/
├── Natasha_Denona/
│   ├── visibility_report_Natasha_Denona.html
│   ├── executive_summary_Natasha_Denona.pdf
│   ├── raw_data_Natasha_Denona.csv
│   └── history/
│       ├── 2026-01/
│       │   ├── visibility_report_Natasha_Denona.html
│       │   └── executive_summary_Natasha_Denona.pdf
│       └── 2026-02/
│           ├── visibility_report_Natasha_Denona.html
│           └── executive_summary_Natasha_Denona.pdf
├── Client_2/
│   └── ...
└── Client_3/
    └── ...
```

## Security Notes

- Service account JSON file contains sensitive credentials
- Never commit to git
- Keep it secure on your local machine
- Use Streamlit Cloud secrets for deployment
- Bucket is private by default (only accessible with credentials)
