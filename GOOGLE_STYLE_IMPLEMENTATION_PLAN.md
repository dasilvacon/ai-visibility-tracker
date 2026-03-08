# Google-Style Implementation Plan: Git → GCS Migration

Following Google SRE best practices for safe, reliable infrastructure changes.

---

## Phase 0: Preparation (Week 1)

### 0.1 Setup Testing Infrastructure

```bash
# Project structure
ai-visibility-tracker/
├── tests/
│   ├── unit/
│   │   ├── test_gcs_sync.py
│   │   ├── test_client_registry.py
│   │   └── test_storage_backend.py
│   ├── integration/
│   │   ├── test_client_lifecycle.py
│   │   └── test_container_restart.py
│   └── e2e/
│       └── test_full_workflow.py
├── pytest.ini
└── requirements-test.txt
```

**Files to create:**
- [ ] `tests/unit/test_gcs_sync.py` - Test GCS operations
- [ ] `tests/integration/test_client_lifecycle.py` - Test full flow
- [ ] `pytest.ini` - Test configuration
- [ ] `requirements-test.txt` - Test dependencies
- [ ] `.github/workflows/test.yml` - Automated testing

### 0.2 Add Observability

```python
# src/observability/logger.py - Structured logging
# src/observability/metrics.py - Metrics collection
```

**Implement:**
- [ ] Structured logging (JSON format)
- [ ] Metrics collection (counters, histograms)
- [ ] Error tracking integration
- [ ] Request tracing

### 0.3 Create Feature Flag System

```python
# config/feature_flags.py
class FeatureFlags:
    USE_GCS_STORAGE = os.getenv('USE_GCS_STORAGE', 'false').lower() == 'true'
    GCS_DUAL_WRITE = os.getenv('GCS_DUAL_WRITE', 'false').lower() == 'true'
```

---

## Phase 1: Abstraction Layer (Week 1-2)

### 1.1 Create Storage Interface

Instead of directly calling git or GCS, create an abstraction:

```python
# src/storage/interface.py

from abc import ABC, abstractmethod
from typing import Dict, List

class ClientStorageBackend(ABC):
    """Abstract interface for client data storage."""

    @abstractmethod
    def save_client(self, client_slug: str, files: Dict[str, str]) -> bool:
        """Save client files."""
        pass

    @abstractmethod
    def load_clients(self) -> List[Dict]:
        """Load all clients."""
        pass

    @abstractmethod
    def save_registry(self) -> bool:
        """Save client registry."""
        pass

# src/storage/git_backend.py
class GitStorageBackend(ClientStorageBackend):
    """Git-based storage (current implementation)."""

    def save_client(self, client_slug: str, files: Dict[str, str]) -> bool:
        # Existing git commit/push logic
        pass

# src/storage/gcs_backend.py
class GCSStorageBackend(ClientStorageBackend):
    """GCS-based storage (new implementation)."""

    def save_client(self, client_slug: str, files: Dict[str, str]) -> bool:
        # GCS upload logic
        pass

# src/storage/dual_write_backend.py
class DualWriteBackend(ClientStorageBackend):
    """Writes to BOTH git and GCS for safe migration."""

    def __init__(self):
        self.git = GitStorageBackend()
        self.gcs = GCSStorageBackend()

    def save_client(self, client_slug: str, files: Dict[str, str]) -> bool:
        # Write to both, log any discrepancies
        git_success = self.git.save_client(client_slug, files)
        gcs_success = self.gcs.save_client(client_slug, files)

        # Log results
        logger.info("dual_write_result",
            client_slug=client_slug,
            git_success=git_success,
            gcs_success=gcs_success
        )

        # Primary is still git (for now)
        return git_success

# src/storage/factory.py
def get_storage_backend() -> ClientStorageBackend:
    """Factory to select storage backend based on feature flags."""

    if FeatureFlags.GCS_DUAL_WRITE:
        return DualWriteBackend()
    elif FeatureFlags.USE_GCS_STORAGE:
        return GCSStorageBackend()
    else:
        return GitStorageBackend()  # Default (current behavior)
```

**Why this matters:**
- Can switch backends without changing application code
- Can test both in parallel (dual-write)
- Easy rollback (just change feature flag)
- Follows Google's "Interface Design" principles

---

## Phase 2: Testing (Week 2)

### 2.1 Unit Tests

```python
# tests/unit/test_gcs_backend.py

import pytest
from unittest.mock import Mock, patch
from src.storage.gcs_backend import GCSStorageBackend

class TestGCSBackend:

    @pytest.fixture
    def gcs_backend(self):
        """Create GCS backend with mocked client."""
        with patch('google.cloud.storage.Client'):
            backend = GCSStorageBackend()
            return backend

    def test_save_client_success(self, gcs_backend):
        """Test successful client save to GCS."""
        files = {
            'keywords': 'data/test_keywords.csv',
            'personas': 'data/test_personas.json'
        }

        result = gcs_backend.save_client('test_client', files)

        assert result == True
        # Verify GCS upload was called

    def test_save_client_handles_failure(self, gcs_backend):
        """Test graceful failure handling."""
        with patch.object(gcs_backend, '_upload_file', side_effect=Exception("GCS Error")):
            result = gcs_backend.save_client('test_client', {})

            assert result == False
            # Verify error was logged

# tests/unit/test_dual_write_backend.py

class TestDualWriteBackend:

    def test_writes_to_both_backends(self):
        """Test that dual-write writes to both git and GCS."""
        with patch('src.storage.git_backend.GitStorageBackend') as mock_git, \
             patch('src.storage.gcs_backend.GCSStorageBackend') as mock_gcs:

            backend = DualWriteBackend()
            backend.save_client('test_client', {})

            # Verify both were called
            mock_git.return_value.save_client.assert_called_once()
            mock_gcs.return_value.save_client.assert_called_once()

    def test_logs_discrepancies(self):
        """Test that differences between git and GCS are logged."""
        # Mock git succeeds, GCS fails
        # Verify warning is logged
        pass
```

### 2.2 Integration Tests

```python
# tests/integration/test_client_lifecycle.py

import pytest
from pathlib import Path
import tempfile

class TestClientLifecycle:

    @pytest.fixture
    def test_env(self):
        """Setup test environment with real GCS (test bucket)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['GCS_BUCKET'] = 'test-bucket-visibility-tracker'
            os.environ['DATA_DIR'] = tmpdir
            yield tmpdir

    def test_full_client_creation_and_retrieval(self, test_env):
        """Test creating a client and retrieving it."""
        # 1. Create client via API
        client_data = {
            'name': 'Test Client',
            'keywords': ['test', 'keywords']
        }

        backend = get_storage_backend()
        success = backend.save_client('test_client', client_data)

        assert success == True

        # 2. Verify files exist in GCS
        gcs_client = storage.Client()
        bucket = gcs_client.bucket('test-bucket-visibility-tracker')
        blob = bucket.blob('client-data/test_client/keywords.csv')
        assert blob.exists()

        # 3. Simulate container restart (clear local cache)
        shutil.rmtree(test_env)
        os.makedirs(test_env)

        # 4. Load clients (should download from GCS)
        clients = backend.load_clients()

        # 5. Verify test client is present
        assert any(c['slug'] == 'test_client' for c in clients)
```

### 2.3 End-to-End Tests

```python
# tests/e2e/test_streamlit_flow.py

from selenium import webdriver
from selenium.webdriver.common.by import By

class TestStreamlitClientCreation:

    @pytest.fixture
    def browser(self):
        """Setup headless browser."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()

    def test_create_client_via_ui(self, browser, streamlit_app):
        """Test creating a client through the Streamlit UI."""
        browser.get('http://localhost:8501')

        # Fill in client form
        browser.find_element(By.ID, 'client_name').send_keys('E2E Test Client')
        browser.find_element(By.ID, 'submit_button').click()

        # Wait for success message
        success_msg = browser.find_element(By.CLASS_NAME, 'success')
        assert 'created successfully' in success_msg.text

        # Verify in GCS
        # ...
```

---

## Phase 3: Monitoring & Alerts (Week 2)

### 3.1 Structured Logging

```python
# src/observability/logger.py

import structlog
import logging
from google.cloud import logging as cloud_logging

# Configure structured logging
def setup_logging():
    """Setup structured logging for Google Cloud."""

    # Use Google Cloud Logging in production
    if os.getenv('ENVIRONMENT') == 'production':
        client = cloud_logging.Client()
        client.setup_logging()

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Usage in code
logger = structlog.get_logger(__name__)

def save_client(client_slug, files):
    logger.info(
        "client_save_started",
        client_slug=client_slug,
        file_count=len(files),
        backend="gcs"
    )

    try:
        # Save logic
        logger.info(
            "client_save_success",
            client_slug=client_slug,
            duration_ms=elapsed_time
        )
    except Exception as e:
        logger.error(
            "client_save_failed",
            client_slug=client_slug,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise
```

### 3.2 Metrics Collection

```python
# src/observability/metrics.py

from opentelemetry import metrics
from opentelemetry.exporter.cloud_monitoring import CloudMonitoringMetricsExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Setup Google Cloud Monitoring
exporter = CloudMonitoringMetricsExporter()
reader = PeriodicExportingMetricReader(exporter)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter(__name__)

# Define metrics
client_save_counter = meter.create_counter(
    "client_saves_total",
    description="Total number of client save operations",
    unit="1"
)

client_save_duration = meter.create_histogram(
    "client_save_duration_ms",
    description="Duration of client save operations",
    unit="ms"
)

gcs_upload_errors = meter.create_counter(
    "gcs_upload_errors_total",
    description="Total number of GCS upload errors",
    unit="1"
)

# Usage
def save_client_with_metrics(client_slug, files):
    start_time = time.time()

    try:
        result = gcs_backend.save_client(client_slug, files)

        # Record success
        client_save_counter.add(1, {"status": "success", "backend": "gcs"})

        # Record duration
        duration_ms = (time.time() - start_time) * 1000
        client_save_duration.record(duration_ms, {"backend": "gcs"})

        return result

    except Exception as e:
        # Record failure
        client_save_counter.add(1, {"status": "error", "backend": "gcs"})
        gcs_upload_errors.add(1, {"error_type": type(e).__name__})
        raise
```

### 3.3 Alerts Configuration

```yaml
# monitoring/alerts.yaml

alertPolicies:
  - displayName: "GCS Upload Failure Rate High"
    conditions:
      - displayName: "GCS upload errors > 5% for 5 minutes"
        conditionThreshold:
          filter: |
            metric.type="custom.googleapis.com/gcs_upload_errors_total"
            resource.type="cloud_run_revision"
          comparison: COMPARISON_GT
          thresholdValue: 0.05
          duration: 300s
    notificationChannels:
      - projects/YOUR_PROJECT/notificationChannels/EMAIL
      - projects/YOUR_PROJECT/notificationChannels/SLACK

  - displayName: "Client Data Loss Prevention"
    conditions:
      - displayName: "Client count decreased"
        conditionThreshold:
          filter: |
            metric.type="custom.googleapis.com/client_count"
            resource.type="cloud_run_revision"
          comparison: COMPARISON_LT
          thresholdValue: -1  # Alert if count drops
          duration: 60s
    notificationChannels:
      - projects/YOUR_PROJECT/notificationChannels/PAGERDUTY
```

---

## Phase 4: Infrastructure as Code (Week 2-3)

### 4.1 Terraform Configuration

```hcl
# terraform/environments/staging/main.tf

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "ai-visibility-terraform-state"
    prefix = "staging"
  }
}

# Cloud Run Service
resource "google_cloud_run_service" "dashboard" {
  name     = "ai-visibility-dashboard-staging"
  location = var.region

  template {
    spec {
      containers {
        image = var.container_image

        env {
          name  = "ENVIRONMENT"
          value = "staging"
        }

        env {
          name  = "USE_GCS_STORAGE"
          value = "true"
        }

        env {
          name  = "GCS_BUCKET"
          value = google_storage_bucket.client_data_staging.name
        }
      }

      service_account_name = google_service_account.dashboard.email
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# GCS Bucket for client data
resource "google_storage_bucket" "client_data_staging" {
  name          = "ai-visibility-client-data-staging"
  location      = var.region
  force_destroy = false  # Prevent accidental deletion

  versioning {
    enabled = true  # Keep version history
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 10  # Keep last 10 versions
    }
  }
}

# Service Account
resource "google_service_account" "dashboard" {
  account_id   = "dashboard-staging"
  display_name = "AI Visibility Dashboard Staging"
}

# IAM permissions
resource "google_storage_bucket_iam_member" "dashboard_gcs" {
  bucket = google_storage_bucket.client_data_staging.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.dashboard.email}"
}

# Monitoring
resource "google_monitoring_alert_policy" "gcs_errors" {
  display_name = "GCS Upload Errors (Staging)"
  combiner     = "OR"

  conditions {
    display_name = "GCS upload error rate > 5%"

    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/gcs_upload_errors_total\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]
}

# terraform/environments/production/main.tf
# Similar but for production
```

```bash
# Deploy infrastructure
cd terraform/environments/staging
terraform init
terraform plan
terraform apply

cd terraform/environments/production
terraform init
terraform plan
# Don't apply production yet!
```

---

## Phase 5: CI/CD Pipeline (Week 3)

### 5.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml

name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PROJECT_ID: gen-lang-client-0243073678
  REGION: us-east1

jobs:
  # Job 1: Run tests
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: pytest tests/unit -v --cov=src --cov-report=xml

      - name: Run integration tests
        run: pytest tests/integration -v
        env:
          GCS_BUCKET: test-bucket

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  # Job 2: Build Docker image
  build:
    name: Build Docker Image
    needs: test
    runs-on: ubuntu-latest

    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Configure Docker for GCR
        run: gcloud auth configure-docker gcr.io

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: gcr.io/${{ env.PROJECT_ID }}/ai-visibility-dashboard
          tags: |
            type=sha,prefix={{branch}}-
            type=ref,event=branch
            type=semver,pattern={{version}}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Job 3: Deploy to staging
  deploy-staging:
    name: Deploy to Staging
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'

    environment:
      name: staging
      url: https://staging.dasilvaconsulting.com

    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ai-visibility-dashboard-staging \
            --image ${{ needs.build.outputs.image_tag }} \
            --region ${{ env.REGION }} \
            --platform managed \
            --allow-unauthenticated \
            --set-env-vars="ENVIRONMENT=staging,USE_GCS_STORAGE=true" \
            --service-account dashboard-staging@${{ env.PROJECT_ID }}.iam.gserviceaccount.com

      - name: Run smoke tests
        run: |
          # Wait for deployment
          sleep 30

          # Test health endpoint
          curl -f https://staging.dasilvaconsulting.com/_health || exit 1

          # Test basic functionality
          python tests/e2e/smoke_test.py --env staging

  # Job 4: Deploy to production (manual approval required)
  deploy-production:
    name: Deploy to Production
    needs: [build, deploy-staging]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    environment:
      name: production
      url: https://dashboard.dasilvaconsulting.com

    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to Cloud Run (canary)
        run: |
          # Deploy new revision with no traffic
          gcloud run deploy ai-visibility-dashboard \
            --image ${{ needs.build.outputs.image_tag }} \
            --region ${{ env.REGION }} \
            --no-traffic \
            --tag canary

          # Get canary URL
          CANARY_URL=$(gcloud run services describe ai-visibility-dashboard \
            --region ${{ env.REGION }} \
            --format 'value(status.traffic[0].url)')

          echo "Canary deployed at: $CANARY_URL"

      - name: Run production smoke tests on canary
        run: |
          python tests/e2e/smoke_test.py --url $CANARY_URL

      - name: Gradual traffic rollout
        run: |
          # 10% traffic to canary
          gcloud run services update-traffic ai-visibility-dashboard \
            --to-tags canary=10 \
            --region ${{ env.REGION }}

          echo "Monitoring for 5 minutes..."
          sleep 300

          # Check error rate
          ERROR_RATE=$(gcloud monitoring read \
            --filter 'metric.type="run.googleapis.com/request_count" AND metric.label.response_code_class="5xx"' \
            --format json | jq '.[] | .points[0].value.int64Value' | awk '{sum+=$1} END {print sum}')

          if [ "$ERROR_RATE" -gt 10 ]; then
            echo "Error rate too high! Rolling back..."
            gcloud run services update-traffic ai-visibility-dashboard \
              --to-revisions LATEST=100 \
              --region ${{ env.REGION }}
            exit 1
          fi

          # 50% traffic
          gcloud run services update-traffic ai-visibility-dashboard \
            --to-tags canary=50 \
            --region ${{ env.REGION }}

          sleep 300

          # 100% traffic
          gcloud run services update-traffic ai-visibility-dashboard \
            --to-tags canary=100 \
            --region ${{ env.REGION }}

          echo "Deployment complete!"
```

---

## Phase 6: Migration Execution (Week 4)

### 6.1 Pre-Migration Checklist

```bash
# Create pre-migration checklist script
# scripts/pre_migration_checklist.sh

#!/bin/bash

echo "🔍 Pre-Migration Checklist"
echo "=========================="

# 1. Backup current state
echo "✓ Backing up current data..."
gsutil -m cp -r data/ gs://ai-visibility-backups/pre-gcs-migration-$(date +%Y%m%d)/

# 2. Git commit everything
echo "✓ Committing all changes to git..."
git add -A
git commit -m "Pre-GCS migration backup $(date +%Y%m%d)"
git tag v1.0-pre-gcs-migration
git push --tags

# 3. Verify all tests pass
echo "✓ Running test suite..."
pytest tests/ -v

# 4. Check GCS credentials
echo "✓ Verifying GCS access..."
python -c "from google.cloud import storage; client = storage.Client(); print('GCS access OK')"

# 5. Verify monitoring is working
echo "✓ Checking monitoring setup..."
gcloud monitoring dashboards list --project=$PROJECT_ID

# 6. Verify rollback plan
echo "✓ Verifying rollback capability..."
gcloud run revisions list --service ai-visibility-dashboard --region us-east1 --limit 5

echo ""
echo "✅ Pre-migration checklist complete!"
echo "Ready to proceed with migration."
```

### 6.2 Migration Script

```python
# scripts/migrate_to_gcs.py

"""
One-time migration script: Upload all existing client data to GCS

This script:
1. Reads all clients from local filesystem
2. Uploads each to GCS
3. Verifies upload success
4. Generates migration report
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from src.client_manager.client_registry import ClientRegistry
from src.storage.gcs_backend import GCSStorageBackend
from src.observability.logger import logger

def migrate():
    """Execute migration from git to GCS."""

    print("=" * 60)
    print("GCS Migration Script")
    print("=" * 60)
    print()

    # Initialize
    registry = ClientRegistry()
    gcs_backend = GCSStorageBackend()

    clients = registry.get_all_clients()

    if not clients:
        print("⚠️  No clients found. Nothing to migrate.")
        return

    print(f"Found {len(clients)} client(s) to migrate:")
    for client in clients:
        print(f"  - {client['name']} ({client['slug']})")
    print()

    # Confirm
    response = input("Proceed with migration? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        return

    # Execute migration
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }

    for i, client in enumerate(clients, 1):
        print(f"\n[{i}/{len(clients)}] Migrating {client['name']}...")

        try:
            # Check if files exist
            missing_files = []
            for file_type, file_path in client['files'].items():
                if not Path(file_path).exists():
                    missing_files.append(file_path)

            if missing_files:
                print(f"  ⚠️  Missing files: {missing_files}")
                results['skipped'].append({
                    'client': client['name'],
                    'reason': 'missing_files',
                    'missing': missing_files
                })
                continue

            # Upload to GCS
            success = gcs_backend.save_client(
                client_slug=client['slug'],
                files=client['files']
            )

            if success:
                print(f"  ✅ Successfully migrated {client['name']}")
                results['success'].append(client['name'])
            else:
                print(f"  ❌ Failed to migrate {client['name']}")
                results['failed'].append({
                    'client': client['name'],
                    'reason': 'upload_failed'
                })

        except Exception as e:
            print(f"  ❌ Error migrating {client['name']}: {e}")
            logger.error("migration_error", client=client['name'], error=str(e))
            results['failed'].append({
                'client': client['name'],
                'reason': str(e)
            })

    # Upload registry
    print("\nUploading client registry...")
    if gcs_backend.save_registry():
        print("✅ Registry uploaded successfully")
    else:
        print("❌ Failed to upload registry")

    # Generate report
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'total_clients': len(clients),
        'successful': len(results['success']),
        'failed': len(results['failed']),
        'skipped': len(results['skipped']),
        'results': results
    }

    report_path = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total clients:     {report['total_clients']}")
    print(f"✅ Successful:     {report['successful']}")
    print(f"❌ Failed:         {report['failed']}")
    print(f"⚠️  Skipped:        {report['skipped']}")
    print(f"\nFull report saved to: {report_path}")

    if results['failed']:
        print("\n⚠️  Some clients failed to migrate. Review the report.")
        return 1

    print("\n🎉 Migration completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(migrate())
```

### 6.3 Post-Migration Validation

```python
# scripts/validate_migration.py

"""
Validate that migration was successful by comparing local and GCS data.
"""

def validate():
    """Validate migration success."""

    print("Validating migration...")

    # 1. Count clients locally
    local_registry = ClientRegistry()
    local_clients = local_registry.get_all_clients()

    # 2. Download from GCS to temp directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        gcs_backend = GCSStorageBackend()
        gcs_backend.download_all_client_data(tmpdir)

        # Load from downloaded data
        gcs_registry = ClientRegistry(registry_path=f"{tmpdir}/clients.json")
        gcs_clients = gcs_registry.get_all_clients()

    # 3. Compare
    local_slugs = set(c['slug'] for c in local_clients)
    gcs_slugs = set(c['slug'] for c in gcs_clients)

    missing_in_gcs = local_slugs - gcs_slugs
    extra_in_gcs = gcs_slugs - local_slugs

    if missing_in_gcs:
        print(f"❌ Clients missing in GCS: {missing_in_gcs}")
        return False

    if extra_in_gcs:
        print(f"⚠️  Extra clients in GCS: {extra_in_gcs}")

    print(f"✅ All {len(local_clients)} clients successfully migrated to GCS")
    return True

if __name__ == '__main__':
    success = validate()
    sys.exit(0 if success else 1)
```

---

## Phase 7: Rollout Plan (Week 4-5)

### Week 4: Dual-Write Mode

```bash
# Deploy with dual-write enabled
export GCS_DUAL_WRITE=true
export USE_GCS_STORAGE=false  # Still reading from git

# Deploy to staging
gcloud run deploy ai-visibility-dashboard-staging \
    --set-env-vars="GCS_DUAL_WRITE=true,USE_GCS_STORAGE=false"

# Monitor for 1 week
# Check logs for any discrepancies between git and GCS
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.dual_write_result" --limit 100
```

### Week 5: Read from GCS (Canary)

```bash
# Deploy to 1% of production traffic
export USE_GCS_STORAGE=true

gcloud run deploy ai-visibility-dashboard \
    --set-env-vars="USE_GCS_STORAGE=true,GCS_DUAL_WRITE=true" \
    --no-traffic \
    --tag canary

# Route 1% traffic
gcloud run services update-traffic ai-visibility-dashboard \
    --to-tags canary=1

# Monitor closely for 24 hours
# Check:
# - Error rates
# - Client data integrity
# - User reports
```

### Week 5-6: Gradual Increase

```bash
# Day 1: 1%
# Day 2: 5%
# Day 3: 10%
# Day 4: 25%
# Day 5: 50%
# Day 6: 75%
# Day 7: 100%

# Each step: Monitor for 24 hours before increasing
```

### Week 6: Cleanup

```bash
# Once 100% on GCS for 1 week with no issues:
# 1. Remove git dependencies from Dockerfile
# 2. Remove GitStorageBackend code
# 3. Update documentation
```

---

## Success Metrics

Track these metrics throughout the rollout:

1. **Reliability**
   - GCS upload success rate > 99.9%
   - Zero data loss incidents
   - Rollback capability tested and working

2. **Performance**
   - Client save latency < 500ms (p95)
   - Container startup time < 30s
   - GCS download time < 10s

3. **Operational**
   - Zero manual interventions required
   - Automated tests passing
   - Monitoring alerts working

---

## Rollback Plan

At ANY point, if issues arise:

```bash
# Immediate rollback (< 5 minutes)
gcloud run services update-traffic ai-visibility-dashboard \
    --to-revisions PREVIOUS_REVISION=100

# Or via feature flag
gcloud run services update ai-visibility-dashboard \
    --set-env-vars="USE_GCS_STORAGE=false"
```

---

## Timeline Summary

- **Week 1:** Setup testing, observability, abstraction layer
- **Week 2:** Write comprehensive tests, setup monitoring
- **Week 3:** Build CI/CD pipeline, Infrastructure as Code
- **Week 4:** Execute migration, deploy dual-write mode
- **Week 5:** Gradual rollout to production (1% → 100%)
- **Week 6:** Cleanup old code, documentation

**Total: 6 weeks for safe, Google-style migration**

---

## Next Steps

Ready to start? Let's begin with:

1. [ ] Create test infrastructure
2. [ ] Implement storage abstraction layer
3. [ ] Write comprehensive tests
4. [ ] Setup CI/CD pipeline

Which would you like to tackle first?
