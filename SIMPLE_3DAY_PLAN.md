# Simple 3-Day GCS Migration Plan

Solo developer approach - professional without over-engineering.

---

## Day 1: Test Locally ✅

### Step 1: Backup Everything (5 minutes)

```bash
# Backup to GCS
gsutil -m cp -r data/ gs://ai-visibility-reports-dasilva/backups/$(date +%Y%m%d)/

# Git backup
git add -A
git commit -m "Backup before GCS migration"
git tag backup-$(date +%Y%m%d)
git push --tags
```

### Step 2: Build Docker Image (2 minutes)

```bash
cd ~/Claude-Projects/ai-visibility-tracker
docker build -t dashboard-test .
```

### Step 3: Run Locally with GCS (2 minutes)

```bash
# Run with your GCS credentials
docker run -p 8080:8080 \
    -v ~/.config/gcloud:/root/.config/gcloud \
    -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
    -e USE_GCS_STORAGE=true \
    dashboard-test
```

### Step 4: Test Client Creation (10 minutes)

1. Visit http://localhost:8080
2. Login (username: natasha_denona, password: natasha123)
3. Go to Client Setup tab
4. Add a test client: "Test Client Local"
5. Upload a small keyword CSV

**What to check:**
- [ ] No errors in browser console
- [ ] Success message appears
- [ ] Check GCS bucket in Cloud Console
- [ ] Files appear in `client-data/test_client_local/`

### Step 5: Test Container Restart (5 minutes)

```bash
# Stop the container (Ctrl+C)

# Start it again
docker run -p 8080:8080 \
    -v ~/.config/gcloud:/root/.config/gcloud \
    -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
    -e USE_GCS_STORAGE=true \
    dashboard-test
```

**What to check:**
- [ ] Visit http://localhost:8080
- [ ] Test client still appears in the list
- [ ] Can activate the test client
- [ ] No errors in Docker logs

### Step 6: Check Docker Logs

```bash
# In another terminal, check logs for errors
docker ps  # Get container ID
docker logs <container-id>
```

**Look for:**
- ✅ "Client data synced from GCS"
- ✅ "GCS upload SUCCESS"
- ❌ Any Python tracebacks
- ❌ GCS authentication errors

**If everything works:** ✅ Ready for Day 2!

---

## Day 2: Setup Staging Environment

### Step 1: Create Staging Cloud Run Service (10 minutes)

```bash
# Build and push image
gcloud builds submit --tag gcr.io/gen-lang-client-0243073678/ai-visibility-dashboard:staging

# Deploy to staging service
gcloud run deploy ai-visibility-dashboard-staging \
    --image gcr.io/gen-lang-client-0243073678/ai-visibility-dashboard:staging \
    --platform managed \
    --region us-east1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --set-secrets="/app/.streamlit/secrets.toml=streamlit-secrets:latest" \
    --set-env-vars="ENVIRONMENT=staging,USE_GCS_STORAGE=true,GCS_BUCKET=ai-visibility-reports-dasilva" \
    --service-account ai-visibility-dashboard@gen-lang-client-0243073678.iam.gserviceaccount.com \
    --port 8080
```

### Step 2: Get Staging URL

```bash
gcloud run services describe ai-visibility-dashboard-staging \
    --region us-east1 \
    --format='value(status.url)'
```

**Bookmark this URL!** This is your staging environment.

### Step 3: Test on Staging (30 minutes)

Visit staging URL and test:

1. **Login works**
   - [ ] Can login with credentials

2. **Client creation**
   - [ ] Add "Test Client Staging"
   - [ ] Upload keyword file
   - [ ] Success message appears
   - [ ] Check GCS bucket - files there?

3. **Container restart test**
   ```bash
   # Force a restart by redeploying same image
   gcloud run services update ai-visibility-dashboard-staging --region us-east1
   ```
   - [ ] Visit staging URL again
   - [ ] Test client still appears
   - [ ] Can activate it

4. **Existing clients work**
   - [ ] Natasha Denona client still appears
   - [ ] Can generate prompts
   - [ ] Can run reports

5. **Check logs**
   ```bash
   gcloud run logs read ai-visibility-dashboard-staging \
       --region us-east1 \
       --limit 50
   ```
   - [ ] Look for "Client data synced from GCS"
   - [ ] No errors

**If everything works:** ✅ Ready for Day 3!

---

## Day 3: Deploy to Production

### Step 1: Final Backup (5 minutes)

```bash
# One more backup before touching production
gsutil -m cp -r data/ gs://ai-visibility-reports-dasilva/backups/pre-production-$(date +%Y%m%d-%H%M)/

# Tag the current working code
git tag production-gcs-v1
git push --tags
```

### Step 2: Build Production Image (5 minutes)

```bash
# Build with production tag
gcloud builds submit --tag gcr.io/gen-lang-client-0243073678/ai-visibility-dashboard:production-gcs-v1
```

### Step 3: Deploy to Production (5 minutes)

**Keep old revision for quick rollback!**

```bash
gcloud run deploy ai-visibility-dashboard \
    --image gcr.io/gen-lang-client-0243073678/ai-visibility-dashboard:production-gcs-v1 \
    --platform managed \
    --region us-east1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --set-secrets="/app/.streamlit/secrets.toml=streamlit-secrets:latest" \
    --set-env-vars="ENVIRONMENT=production,USE_GCS_STORAGE=true,GCS_BUCKET=ai-visibility-reports-dasilva" \
    --service-account ai-visibility-dashboard@gen-lang-client-0243073678.iam.gserviceaccount.com \
    --port 8080
```

### Step 4: Test Production (15 minutes)

Visit https://dashboard.dasilvaconsulting.com

1. **Smoke tests**
   - [ ] Login works
   - [ ] Existing clients (Natasha Denona) appear
   - [ ] Can navigate all tabs
   - [ ] No obvious errors

2. **Create test client**
   - [ ] Add a small test client
   - [ ] Upload keyword file
   - [ ] Verify in GCS bucket

3. **Restart test**
   ```bash
   # Redeploy same image to force restart
   gcloud run services update ai-visibility-dashboard --region us-east1
   ```
   - [ ] Test client persists after restart

4. **Monitor for first hour**
   ```bash
   # Watch logs
   gcloud run logs read ai-visibility-dashboard \
       --region us-east1 \
       --limit 100 \
       --follow
   ```

### Step 5: Share with Yourself (Optional)

**Create a staging bookmark** for future testing:
- Production: https://dashboard.dasilvaconsulting.com
- Staging: https://ai-visibility-dashboard-staging-XXXX.run.app

Always test new features on staging first!

---

## Rollback Plan (If Needed)

### Quick Rollback (2 minutes)

```bash
# List recent revisions
gcloud run revisions list \
    --service ai-visibility-dashboard \
    --region us-east1 \
    --limit 5

# Rollback to previous revision
gcloud run services update-traffic ai-visibility-dashboard \
    --to-revisions PREVIOUS_REVISION_NAME=100 \
    --region us-east1
```

### Full Rollback to Git (5 minutes)

```bash
# Deploy old image that uses git
gcloud run services update ai-visibility-dashboard \
    --set-env-vars="USE_GCS_STORAGE=false" \
    --region us-east1
```

---

## Success Checklist

After Day 3, you should have:

- [x] Local Docker testing passed
- [x] Staging environment working
- [x] Production deployed with GCS
- [x] Backups created
- [x] Rollback plan tested
- [x] No data loss
- [x] Clients can still view reports
- [x] You can add new clients

---

## Troubleshooting

### "GCS authentication failed"
```bash
# Check service account has permissions
gcloud projects get-iam-policy gen-lang-client-0243073678 \
    --flatten="bindings[].members" \
    --filter="bindings.members:ai-visibility-dashboard@*"
```

### "Client data not persisting"
- Check GCS bucket in Cloud Console
- Verify files are actually uploading
- Check container logs for errors

### "Can't access staging URL"
```bash
# Make sure service is deployed
gcloud run services describe ai-visibility-dashboard-staging --region us-east1
```

---

## Timeline

- **Day 1 (Today):** 30 min - 1 hour
- **Day 2 (Tomorrow):** 45 min
- **Day 3 (Day after):** 30 min

**Total time investment:** ~2 hours spread over 3 days

Much better than debugging git issues forever! 🎉
