# Staging Environment Setup

## Why We Need Staging

We just made a **major architectural change**: replacing git auto-commit with Google Cloud Storage for client data.

**Risk:** If this breaks in production, you could lose access to client data.

**Solution:** Test in staging first, validate it works, THEN deploy to production.

## Staging Environment Plan

### Option 1: Separate Cloud Run Service (Recommended)

**Deploy to staging URL:**
```bash
# Deploy with staging suffix
gcloud run deploy ai-visibility-dashboard-staging \
    --image gcr.io/gen-lang-client-0243073678/ai-visibility-dashboard:latest \
    --region us-east1 \
    --allow-unauthenticated \
    ... (same config as production)
```

**Test at:** `https://ai-visibility-dashboard-staging-XXXX.run.app`

**Benefits:**
- Separate from production
- Can test thoroughly without risk
- Same GCS bucket (client data is same)
- When validated, deploy to production service

### Option 2: Use Revisions with Traffic Splitting

**Deploy as new revision with no traffic:**
```bash
gcloud run deploy ai-visibility-dashboard \
    --image gcr.io/.../ai-visibility-dashboard:latest \
    --no-traffic  # Don't send traffic yet
    --tag staging  # Tag this revision as "staging"
```

**Test at:** `https://staging---ai-visibility-dashboard-XXXX.run.app`

**Benefits:**
- Same service, different revision
- Can gradually shift traffic (0% → 10% → 50% → 100%)
- Easy rollback if issues

### Option 3: Test Locally First

**Run the Docker image locally:**
```bash
# Build image
docker build -t ai-visibility-tracker .

# Run locally with GCS credentials
docker run -p 8080:8080 \
    -v ~/.config/gcloud:/root/.config/gcloud \
    -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
    ai-visibility-tracker
```

**Test at:** `http://localhost:8080`

**Benefits:**
- Fastest testing
- No cloud deployment needed
- Can debug easily

## Recommended Testing Flow

1. **Test locally** - Validate GCS sync works
2. **Deploy to staging service** - Test in real Cloud Run environment
3. **Validate:**
   - Adding new client works
   - Files appear in GCS bucket
   - Restarting container preserves client data
   - No git errors
4. **Deploy to production** - Update main service
5. **Monitor** - Watch for any issues

## What to Test

- [ ] Add a new test client
- [ ] Verify files uploaded to GCS (check bucket in console)
- [ ] Restart container (redeploy)
- [ ] Verify client still appears after restart
- [ ] Check no git errors in logs
- [ ] Test "Backup to Cloud" button
- [ ] Verify existing clients (Natasha Denona) still work

## Rollback Plan

If GCS approach fails:

1. **Immediate:** Revert to previous revision in Cloud Run
2. **Code:** `git revert HEAD` to undo GCS changes
3. **Redeploy:** Build and deploy previous git-based version

## Next Steps

**Choose your approach:**
- Local testing? (fastest)
- Staging service? (most realistic)
- Traffic splitting? (safest)

**Then:** Run through test checklist before touching production
