# Git Sync Setup for Cloud Run

## Problem Solved

**Issue:** Client data created in the Cloud Run dashboard disappeared after container restarts.

**Root Cause:**
- Cloud Run containers are ephemeral - the filesystem resets on restart
- Client files (personas, keywords, brand_config) were saved to local `/app/data/` directory
- No git credentials were configured, so commits/pushes failed silently
- Result: Clients appeared to be created but vanished on next deployment

**Solution:**
- Install git in the Docker container
- Configure GitHub authentication with Personal Access Token
- Sync client data via git commits on every change
- Pull latest data from GitHub on container startup

---

## How It Works Now

### 1. **Creating a Client**
When you create a client in the Cloud Run dashboard:
1. Files are created locally in `/app/data/`
2. Files are registered in `data/clients.json`
3. Git automatically commits the changes
4. Git pushes to GitHub
5. ✅ Client data persists in the repository

### 2. **Container Startup**
When Cloud Run starts/restarts:
1. Container pulls latest code from Docker image
2. Startup script (`startup.sh`) runs automatically
3. Git pulls latest client data from GitHub
4. ✅ All client data is restored

### 3. **Local Development**
When you work locally:
1. Create/modify clients as usual
2. Changes commit to local git
3. Git pushes to GitHub
4. ✅ Changes sync to Cloud Run on next deployment

---

## Setup Instructions

### Prerequisites
- GitHub account with repository access
- Google Cloud project with Cloud Run enabled
- gcloud CLI installed and authenticated

### Step 1: Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens/new
2. Name: `AI Visibility Dashboard - Cloud Run`
3. Expiration: Choose appropriate duration (recommend: 1 year)
4. Select scopes:
   - ✅ **repo** (Full control of private repositories)
5. Click "Generate token"
6. **Copy the token** (starts with `ghp_`) - you won't see it again!

### Step 2: Store Token in Google Secret Manager

Run the setup script:

```bash
./setup_git_credentials.sh
```

This script will:
- Prompt for your GitHub Personal Access Token
- Store it securely in Google Secret Manager
- Grant Cloud Run access to the secret
- Configure git user name/email

### Step 3: Deploy to Cloud Run

```bash
./deploy_to_cloud_run.sh
```

The deployment script now:
- Installs git in the Docker container
- Passes GitHub token as a secret
- Configures git credentials as environment variables
- Runs `startup.sh` on container start

### Step 4: Verify It Works

1. Visit your Cloud Run URL
2. Login as admin
3. Go to "Client Manager" → "Simple Client Setup"
4. Create a new test client
5. Check for success messages:
   - ✅ "Created and saved to GitHub!" = Git sync working
   - ⚠️ "Could not auto-commit to git" = Git sync failed

6. Verify on GitHub:
   - Go to your repository
   - Check recent commits
   - Should see: "Add new client: [Client Name]"

---

## Files Modified

### New Files
- `startup.sh` - Container startup script (configures git, pulls data)
- `setup_git_credentials.sh` - Helper script to create GitHub token secret
- `GIT_SYNC_SETUP.md` - This documentation

### Modified Files
- `Dockerfile` - Added git installation and startup script
- `deploy_to_cloud_run.sh` - Added git credentials configuration
- `prompt_generator_pages/simple_client_setup.py` - Better error reporting for git operations

---

## Troubleshooting

### "Git push failed: authentication failed"
- Check that GitHub token is valid and not expired
- Regenerate token: https://github.com/settings/tokens
- Re-run: `./setup_git_credentials.sh`

### "Git push failed: Permission denied"
- Check token has `repo` scope
- Verify you have write access to the repository
- Check repository URL in `startup.sh` matches your repo

### Clients still disappearing
- Check Cloud Run logs: `gcloud run services logs read ai-visibility-dashboard`
- Look for errors during git pull/push operations
- Verify secret is properly mounted: Check "Secrets" tab in Cloud Run console

### Local git not working
- Make sure you have git configured locally:
  ```bash
  git config user.name
  git config user.email
  ```
- If not set:
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "your@email.com"
  ```

---

## Security Notes

### GitHub Personal Access Token
- **Stored in:** Google Secret Manager (encrypted at rest)
- **Access:** Only Cloud Run service account
- **Scope:** `repo` access (required for private repositories)
- **Rotation:** Update token periodically, re-run setup script

### Git Credentials in Container
- Token is injected as environment variable at runtime
- Not stored in Docker image or source code
- Cleared when container stops

### Best Practices
- ✅ Use a dedicated bot account for Cloud Run commits
- ✅ Set token expiration (1 year recommended)
- ✅ Monitor GitHub audit log for suspicious activity
- ✅ Rotate tokens regularly
- ❌ Don't commit tokens to source code
- ❌ Don't share tokens in logs or error messages

---

## Architecture Diagram

```
┌─────────────────┐
│  Cloud Run      │
│  Container      │
│                 │
│  1. Startup     │ ──┐
│  2. Git Pull    │ ──┼──> GitHub Repository
│  3. Run App     │ ──┘      data/clients.json
│  4. User Creates│           data/*_personas.json
│     Client      │           data/*_keywords.csv
│  5. Git Commit  │ ──┐       data/*_brand_config.json
│  6. Git Push    │ ──┼──>
└─────────────────┘   │
                      │
┌─────────────────┐   │
│  Local Dev      │   │
│                 │   │
│  1. Create      │   │
│     Client      │   │
│  2. Git Commit  │ ──┤
│  3. Git Push    │ ──┼──>
└─────────────────┘   │
                      ↓
              ┌───────────────┐
              │    GitHub     │
              │   (Source of  │
              │     Truth)    │
              └───────────────┘
```

---

## Maintenance

### Update GitHub Token
When your token expires:

1. Generate new token on GitHub
2. Run: `./setup_git_credentials.sh`
3. Enter new token
4. Redeploy: `./deploy_to_cloud_run.sh`

### Check Sync Status
View git status in Cloud Run:

```bash
gcloud run services logs read ai-visibility-dashboard --region us-east1 | grep "git"
```

Look for:
- `✓ Client data synced` - Pull successful
- `✓ GitHub authentication configured` - Credentials working

### Manual Sync
If clients get out of sync:

1. Commit local changes:
   ```bash
   git add data/
   git commit -m "Sync client data"
   git push
   ```

2. Trigger Cloud Run restart:
   ```bash
   gcloud run services update ai-visibility-dashboard --region us-east1
   ```

---

## Next Steps

After setup:
1. ✅ Create clients in Cloud Run - they'll persist
2. ✅ Create clients locally - they'll sync to Cloud Run
3. ✅ Everything stays in sync via GitHub
4. ✅ No more disappearing clients!

For questions or issues, contact: tiffany@dasilvaconsulting.com
