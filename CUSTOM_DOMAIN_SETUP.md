# Custom Domain Setup for AI Visibility Dashboard

## Current Status

✅ **Service Deployed:** ai-visibility-dashboard (revision 00015-bsf)
✅ **DNS Configured:** dashboard.dasilvaconsulting.com → ghs.googlehosted.com
✅ **Region:** us-east1
⏳ **Domain Mapping:** Needs to be completed

## Quick Setup via Google Cloud Console

Since the DNS is already pointing to Google's hosted service, you just need to map the domain:

### Option 1: Cloud Console (Recommended - 2 minutes)

1. **Go to Cloud Run:**
   https://console.cloud.google.com/run/detail/us-east1/ai-visibility-dashboard/metrics?project=gen-lang-client-0243073678

2. **Click "Manage Custom Domains"** at the top

3. **Add Mapping:**
   - Click "ADD MAPPING"
   - Select service: `ai-visibility-dashboard`
   - Enter domain: `dashboard.dasilvaconsulting.com`
   - Click "CONTINUE"

4. **Verify Domain Ownership** (if prompted):
   - You may need to verify via Google Search Console
   - Or add a TXT record to your DNS

5. **Wait for Certificate:**
   - Google will automatically provision an SSL certificate
   - This takes 15-60 minutes

### Option 2: Command Line

```bash
# Map the custom domain
gcloud beta run domain-mappings create \
  --service=ai-visibility-dashboard \
  --domain=dashboard.dasilvaconsulting.com \
  --region=us-east1 \
  --platform=managed

# Check status
gcloud beta run domain-mappings describe \
  dashboard.dasilvaconsulting.com \
  --region=us-east1
```

## DNS Configuration

Your DNS is already correctly configured:

```
dashboard.dasilvaconsulting.com → CNAME → ghs.googlehosted.com
```

**Current DNS Response:**
```
Server:		192.168.0.1
dashboard.dasilvaconsulting.com	canonical name = ghs.googlehosted.com
Address: 142.250.139.121
```

## What Happens Next

1. **Domain Mapping:** Cloud Run will register your custom domain
2. **SSL Certificate:** Google automatically provisions a free SSL cert
3. **Traffic Routing:** Requests to dashboard.dasilvaconsulting.com will route to your service
4. **Certificate Propagation:** 15-60 minutes for HTTPS to work

## Verification

Once mapping is complete, test:

```bash
# Check HTTP (may redirect to HTTPS)
curl -I http://dashboard.dasilvaconsulting.com

# Check HTTPS (wait 15-60 min for cert)
curl -I https://dashboard.dasilvaconsulting.com
```

## Troubleshooting

### If Domain Verification Fails:

Add this TXT record to your DNS:

```
Name: dashboard.dasilvaconsulting.com
Type: TXT
Value: [Google will provide this]
```

### If Certificate Doesn't Provision:

1. Ensure CNAME points to `ghs.googlehosted.com` (✅ already done)
2. Wait up to 60 minutes
3. Check Cloud Run console for status

## Current Service Details

- **Project:** gen-lang-client-0243073678
- **Service:** ai-visibility-dashboard
- **Region:** us-east1
- **Current URL:** https://ai-visibility-dashboard-96323652503.us-east1.run.app
- **Target URL:** https://dashboard.dasilvaconsulting.com

## Expected Result

After mapping completes:

✅ https://dashboard.dasilvaconsulting.com → AI Visibility Dashboard
✅ Automatic SSL certificate
✅ All new report features live on custom domain
✅ Previous URL still works (both URLs serve same service)
