"""
Run Report Page - Execute visibility tests and generate reports from the dashboard.

This page allows admins to run new visibility tests directly from the web interface.
It checks for monthly limits, shows real-time progress, and updates historical tracking.
"""

import streamlit as st
import sys
import os
import json
import csv
import subprocess
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Add src to path
sys.path.insert(0, 'src')

from tracking.historical_tracker import HistoricalTracker


def get_last_test_date(client_name: str) -> Optional[datetime]:
    """
    Get the date of the last test run for a client.

    Args:
        client_name: Name of the client

    Returns:
        datetime of last test, or None if no tests have been run
    """
    client_slug = client_name.replace(' ', '_').lower()
    tracker = HistoricalTracker(client_slug=client_slug)
    history = tracker.get_client_history(client_name)

    if not history:
        return None

    # Get the most recent test date
    latest_month = max(history.keys())
    test_date_str = history[latest_month]['test_date']

    return datetime.fromisoformat(test_date_str)


def can_run_test(client_name: str) -> tuple[bool, str]:
    """
    Check if a test can be run for this client (monthly limit check).

    Args:
        client_name: Name of the client

    Returns:
        Tuple of (can_run: bool, message: str)
    """
    last_test = get_last_test_date(client_name)

    if last_test is None:
        return True, "No previous tests found. You can run your first test!"

    days_since_last_test = (datetime.now() - last_test).days

    # Allow tests if it's been at least 28 days (roughly monthly)
    if days_since_last_test >= 28:
        return True, f"Last test was {days_since_last_test} days ago. You can run a new test."

    days_remaining = 28 - days_since_last_test
    next_date = last_test + timedelta(days=28)

    return False, f"Tests are run monthly. Last test was {days_since_last_test} days ago. Next test available in {days_remaining} days ({next_date.strftime('%B %d, %Y')})."


def get_approved_prompts_from_gcs(client_name: str) -> Optional[str]:
    """
    Download the latest approved prompts CSV from GCS for a client.

    Args:
        client_name: Name of the client

    Returns:
        Path to downloaded prompts file, or None if not found
    """
    try:
        from google.cloud import storage

        bucket_name = 'ai-visibility-reports-dasilva'
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # Format client name for matching (replace spaces with underscores)
        client_slug = client_name.replace(' ', '_')

        # List blobs in prompt-data/approved/ matching this client
        prefix = 'prompt-data/approved/'
        blobs = list(bucket.list_blobs(prefix=prefix))

        # Filter for this client's approved prompts
        matching_blobs = [
            blob for blob in blobs
            if client_slug in blob.name and blob.name.endswith('.csv')
        ]

        if not matching_blobs:
            print(f"No approved prompts found in GCS for {client_name}")
            return None

        # Sort by name (includes timestamp) to get the latest
        matching_blobs.sort(key=lambda b: b.name, reverse=True)
        latest_blob = matching_blobs[0]

        # Download to temp file
        temp_path = Path(f'data/temp_approved_{client_slug}.csv')
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        latest_blob.download_to_filename(str(temp_path))

        print(f"✓ Downloaded approved prompts from GCS: {latest_blob.name}")
        return str(temp_path)

    except Exception as e:
        print(f"Could not fetch approved prompts from GCS: {e}")
        return None


def get_client_prompts_file(client_name: str) -> Optional[str]:
    """
    Find the prompts CSV file for a client.
    Priority: 1) local client-specific file, 2) GCS approved prompts, 3) generated_prompts.csv

    Args:
        client_name: Name of the client

    Returns:
        Path to prompts file, or None if not found
    """
    client_slug = client_name.replace(' ', '_').lower()

    # Priority 1: Client-specific prompts file (written by export button)
    client_prompts_file = Path(f'data/{client_slug}/{client_slug}_prompts.csv')
    if client_prompts_file.exists():
        return str(client_prompts_file)

    # Priority 2: Try to download from GCS (source of truth for cloud)
    gcs_prompts = get_approved_prompts_from_gcs(client_name)
    if gcs_prompts:
        return gcs_prompts

    # Priority 3: Check main generated_prompts.csv (legacy shared file)
    prompts_file = Path('data/generated_prompts.csv')

    if not prompts_file.exists():
        return None

    # Check if client has prompts in the shared file
    try:
        with open(prompts_file, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            if 'client_name' in fieldnames:
                for row in reader:
                    if row.get('client_name') == client_name:
                        return str(prompts_file)
            else:
                for row in reader:
                    if row.get('prompt_text'):
                        return str(prompts_file)
    except Exception:
        pass

    return None


def get_brand_config_file(client_name: str) -> Optional[str]:
    """
    Find the brand config file for a client.

    Args:
        client_name: Name of the client

    Returns:
        Path to brand config file, or None if not found
    """
    # First try to get the exact path from ClientRegistry (source of truth)
    try:
        from src.client_manager import ClientRegistry
        registry = ClientRegistry()
        client = registry.get_client(client_name)
        if client:
            brand_config_path = client.get('files', {}).get('brand_config')
            if brand_config_path and Path(brand_config_path).exists():
                return brand_config_path
    except Exception:
        pass

    # Fallback: Convert client name to filename format and try common paths
    client_slug = client_name.replace(' ', '_')

    # Check for brand config files in various locations
    possible_paths = [
        # Client subdirectory (new structure)
        Path(f'data/{client_slug.lower()}/{client_slug.lower()}_brand_config.json'),
        # Root data directory (legacy structure)
        Path(f'data/{client_slug}_brand_config.json'),
        Path(f'data/{client_slug.lower()}_brand_config.json'),
        # Brand configs directory
        Path(f'data/brand_configs/{client_slug}_brand_config.json'),
    ]

    for path in possible_paths:
        if path.exists():
            return str(path)

    return None


def count_client_prompts(prompts_file: str, client_name: str) -> int:
    """
    Count how many prompts exist for a client.

    Args:
        prompts_file: Path to prompts CSV file
        client_name: Name of the client

    Returns:
        Number of prompts for this client
    """
    try:
        count = 0
        with open(prompts_file, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            for row in reader:
                # If file has client_name column, filter by client
                if 'client_name' in fieldnames:
                    if row.get('client_name') == client_name:
                        count += 1
                else:
                    # Legacy format - count all prompts
                    if row.get('prompt_text'):
                        count += 1
        return count
    except Exception:
        return 0


def get_test_status_files(client_name: str) -> tuple:
    """Get paths for test status files (per-client isolated)."""
    client_slug = client_name.replace(' ', '_').lower()
    status_dir = Path(f'data/reports/{client_slug}')
    status_dir.mkdir(parents=True, exist_ok=True)
    log_file = status_dir / f'test_run_{client_slug}.log'
    pid_file = status_dir / f'test_run_{client_slug}.pid'
    status_file = status_dir / f'test_run_{client_slug}.status'
    return log_file, pid_file, status_file


def is_test_running(client_name: str) -> bool:
    """Check if a test is currently running for this client."""
    _, pid_file, status_file = get_test_status_files(client_name)

    if not pid_file.exists():
        return False

    try:
        pid = int(pid_file.read_text().strip())
        # Check if process is still running
        os.kill(pid, 0)  # Signal 0 just checks if process exists
        return True
    except (ProcessLookupError, ValueError, FileNotFoundError):
        # Process not running - clean up pid file
        if pid_file.exists():
            pid_file.unlink()
        return False


def get_test_progress(client_name: str) -> dict:
    """Get current test progress from log file."""
    log_file, pid_file, status_file = get_test_status_files(client_name)

    result = {
        'running': is_test_running(client_name),
        'log_lines': [],
        'completed': False,
        'success': None,
        'incomplete': False,
        'prompts_done': 0,
        'total_prompts': 0
    }

    # Check if test completed
    if status_file.exists():
        status = status_file.read_text().strip()
        if status == 'incomplete':
            result['incomplete'] = True
        else:
            result['completed'] = True
            result['success'] = (status == 'success')

    # Read log file
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                result['log_lines'] = [line.rstrip() for line in lines[-30:]]  # Last 30 lines

                # Parse progress from log
                for line in lines:
                    if 'Testing prompt:' in line and '[' in line:
                        # Parse "[X/Y] Testing prompt:"
                        try:
                            progress = line.split('[')[1].split(']')[0]
                            current, total = progress.split('/')
                            result['prompts_done'] = int(current)
                            result['total_prompts'] = int(total)
                        except:
                            pass
        except Exception:
            pass

    return result


def run_reanalysis(client_name: str, brand_config: str) -> bool:
    """
    Re-analyze existing test results without re-running AI queries.

    This discovers new competitors from saved AI responses and regenerates reports.

    Args:
        client_name: Name of the client
        brand_config: Path to brand config JSON file

    Returns:
        True if re-analysis started successfully, False otherwise
    """
    try:
        # Check if test already running
        if is_test_running(client_name):
            st.warning("⚠️ A test is already running for this client. Please wait for it to complete.")
            return False

        # Get status file paths
        log_file, pid_file, status_file = get_test_status_files(client_name)

        # Clean up old status files
        for f in [log_file, pid_file, status_file]:
            if f.exists():
                f.unlink()

        # Ensure reports directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        client_slug = client_name.replace(' ', '_')

        # Set working directory to project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)

        # Build command - just analyze, no prompts (uses existing results)
        main_cmd = f"python main.py --analyze --brand-config {brand_config}"
        client_slug_escaped = client_slug.replace("'", "'\\''").lower()
        wrapper_cmd = f'''
cd {parent_dir}
{main_cmd}
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "success" > {status_file}
    echo ">>> Uploading results and reports to GCS..."
    python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
try:
    gcs_sync = GCSClientSync()
    client_slug = '{client_slug_escaped}'
    print(f'Uploading reports for {{client_slug}}...')
    gcs_sync.upload_reports(client_slug)
    print('GCS upload complete!')
except Exception as e:
    print(f'GCS upload failed: {{e}}')
"
else
    echo "failed" > {status_file}
fi
exit $EXIT_CODE
'''

        # Pass API keys as environment variables (needed for any API calls during analysis)
        env = os.environ.copy()
        try:
            api_keys = st.secrets.get('api_keys', {})
            if api_keys.get('openai'):
                env['OPENAI_API_KEY'] = api_keys['openai']
            if api_keys.get('anthropic'):
                env['ANTHROPIC_API_KEY'] = api_keys['anthropic']
            if api_keys.get('perplexity'):
                env['PERPLEXITY_API_KEY'] = api_keys['perplexity']
            if api_keys.get('gemini'):
                env['GEMINI_API_KEY'] = api_keys['gemini']
            if api_keys.get('serpapi'):
                env['SERPAPI_API_KEY'] = api_keys['serpapi']
            if api_keys.get('copilot') or api_keys.get('azure_openai'):
                env['AZURE_OPENAI_API_KEY'] = api_keys.get('copilot', api_keys.get('azure_openai', ''))
            if api_keys.get('azure_openai_endpoint'):
                env['AZURE_OPENAI_ENDPOINT'] = api_keys['azure_openai_endpoint']
        except Exception:
            pass

        # Open log file for output
        with open(log_file, 'w') as log:
            log.write(f"=== Re-analysis started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            log.write(f"Client: {client_name}\n")
            log.write(f"Mode: Re-analyze existing results (no new AI queries)\n")
            log.write(f"{'='*60}\n\n")
            log.flush()

            # Start detached background process
            process = subprocess.Popen(
                ['bash', '-c', wrapper_cmd],
                stdout=log,
                stderr=subprocess.STDOUT,
                env=env,
                cwd=parent_dir,
                start_new_session=True
            )

        # Save PID for status checking
        pid_file.write_text(str(process.pid))

        return True

    except Exception as e:
        st.error(f"Error starting re-analysis: {str(e)}")
        return False


def run_visibility_test(client_name: str, prompts_file: str, brand_config: str) -> bool:
    """
    Start visibility test for a client as a background process.

    Args:
        client_name: Name of the client
        prompts_file: Path to prompts CSV file
        brand_config: Path to brand config JSON file

    Returns:
        True if test started successfully, False otherwise
    """
    try:
        # Check if test already running
        if is_test_running(client_name):
            st.warning("⚠️ A test is already running for this client. Please wait for it to complete.")
            return False

        # Get status file paths
        log_file, pid_file, status_file = get_test_status_files(client_name)

        # Clean up old status files
        for f in [log_file, pid_file, status_file]:
            if f.exists():
                f.unlink()

        # Ensure reports directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create a temporary filtered prompts file for this client
        client_slug = client_name.replace(' ', '_')
        temp_prompts = Path(f'data/temp_{client_slug}_prompts.csv')

        # Filter prompts for this client
        with open(prompts_file, 'r') as f_in:
            reader = csv.DictReader(f_in)
            fieldnames = reader.fieldnames or []
            all_rows = list(reader)

            # Check if file has client_name column
            if 'client_name' in fieldnames:
                # Filter by client_name
                rows = [row for row in all_rows if row.get('client_name') == client_name]
            else:
                st.error(f"⚠️ Prompts file missing 'client_name' column. Please regenerate and export prompts for {client_name}.")
                return False

        if not rows:
            st.error(f"⚠️ No prompts found for {client_name}. Please generate and export prompts first.")
            return False

        # Write filtered prompts
        with open(temp_prompts, 'w', newline='') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        # Set working directory to project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)

        # Build command with wrapper script to handle completion status
        # We use bash -c to run the command and write status on completion
        # IMPORTANT: The wrapper script MUST upload to GCS before exiting
        # because Cloud Run containers are ephemeral and data is lost otherwise
        main_cmd = f"python main.py --prompts {temp_prompts} --analyze --brand-config {brand_config}"
        client_slug_escaped = client_slug.replace("'", "'\\''").lower()
        wrapper_cmd = f'''
cd {parent_dir}

# Background process: periodically save results to GCS every 5 minutes
# This prevents losing hours of progress if the container restarts
(
    sleep 300  # Wait 5 minutes before first save
    while true; do
        python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
try:
    gcs = GCSClientSync()
    gcs.upload_test_results('{client_slug_escaped}')
    print('>>> Periodic GCS save complete for {client_slug_escaped}')
except Exception as e:
    print(f'Periodic GCS save failed: {{e}}')
" 2>&1 | head -5
        sleep 300  # Save every 5 minutes
    done
) &
SAVER_PID=$!

# Run the actual test
{main_cmd}
EXIT_CODE=$?

# Kill the background saver
kill $SAVER_PID 2>/dev/null || true

if [ $EXIT_CODE -eq 0 ]; then
    echo "success" > {status_file}
    echo ">>> Uploading final results and reports to GCS..."
    python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
try:
    gcs_sync = GCSClientSync()
    client_slug = '{client_slug_escaped}'
    print(f'Uploading test results for {{client_slug}}...')
    gcs_sync.upload_test_results(client_slug)
    print(f'Uploading reports for {{client_slug}}...')
    gcs_sync.upload_reports(client_slug)
    print('GCS upload complete!')
except Exception as e:
    print(f'GCS upload failed: {{e}}')
"
elif [ $EXIT_CODE -eq 2 ]; then
    # Exit code 2 = test incomplete (needs resume to finish)
    echo "incomplete" > {status_file}
    echo ">>> Saving partial results to GCS (test needs resume)..."
    python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
try:
    gcs = GCSClientSync()
    gcs.upload_test_results('{client_slug_escaped}')
    print('Partial results saved to GCS — resume to complete')
except Exception as e:
    print(f'Partial results save failed: {{e}}')
"
else
    echo "failed" > {status_file}
    echo ">>> Saving partial results to GCS..."
    python3 -c "
from src.client_manager.gcs_sync import GCSClientSync
try:
    gcs = GCSClientSync()
    gcs.upload_test_results('{client_slug_escaped}')
    print('Partial results saved to GCS')
except Exception as e:
    print(f'Partial results save failed: {{e}}')
"
fi
# Clean up temp prompts file
rm -f {temp_prompts}
exit $EXIT_CODE
'''

        # Pass API keys as environment variables
        env = os.environ.copy()
        try:
            api_keys = st.secrets.get('api_keys', {})
            if api_keys.get('openai'):
                env['OPENAI_API_KEY'] = api_keys['openai']
            if api_keys.get('anthropic'):
                env['ANTHROPIC_API_KEY'] = api_keys['anthropic']
            if api_keys.get('perplexity'):
                env['PERPLEXITY_API_KEY'] = api_keys['perplexity']
            if api_keys.get('gemini'):
                env['GEMINI_API_KEY'] = api_keys['gemini']
            if api_keys.get('serpapi'):
                env['SERPAPI_API_KEY'] = api_keys['serpapi']
            if api_keys.get('copilot') or api_keys.get('azure_openai'):
                env['AZURE_OPENAI_API_KEY'] = api_keys.get('copilot', api_keys.get('azure_openai', ''))
            if api_keys.get('azure_openai_endpoint'):
                env['AZURE_OPENAI_ENDPOINT'] = api_keys['azure_openai_endpoint']
        except Exception:
            pass

        # Open log file for output
        with open(log_file, 'w') as log:
            log.write(f"=== Test started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            log.write(f"Client: {client_name}\n")
            log.write(f"Prompts: {len(rows)}\n")
            log.write(f"{'='*60}\n\n")
            log.flush()

            # Start detached background process
            process = subprocess.Popen(
                ['bash', '-c', wrapper_cmd],
                stdout=log,
                stderr=subprocess.STDOUT,
                env=env,
                cwd=parent_dir,
                start_new_session=True  # Detach from parent process
            )

        # Save PID for status checking
        pid_file.write_text(str(process.pid))

        return True  # Test started successfully

    except Exception as e:
        st.error(f"Error starting visibility test: {str(e)}")
        return False


def render():
    """Render the run report page."""

    # Light theme colors
    LIGHT_BG = '#FFFFFF'
    TEXT_DARK = '#1c1c1c'
    DARK_PURPLE = '#4A4458'
    BORDER_LIGHT = '#E0E0E0'
    CREAM = '#E8D7A0'

    st.title("🚀 Run New Report")

    # Info banner
    st.markdown(f"""
    <div style='background-color: {DARK_PURPLE}; padding: 20px; border-radius: 8px; border-left: 4px solid {CREAM}; margin-bottom: 24px;'>
        <h3 style='color: white; margin-top: 0;'>📊 Monthly Visibility Testing</h3>
        <p style='color: {CREAM}; margin-bottom: 12px;'>
            Run a new visibility test to see how your brand appears in AI responses. Tests should be run <strong>monthly</strong>
            to track trends over time using the same set of prompts.
        </p>
        <ul style='color: {CREAM};'>
            <li><strong>Same prompts each month:</strong> Consistent testing shows real improvement</li>
            <li><strong>Historical tracking:</strong> Automatically tracks changes month-over-month</li>
            <li><strong>Full reports:</strong> Generates HTML reports, PDFs, and CSVs</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Get active client from session state
    client_name = st.session_state.get('brand_name')

    if not client_name:
        st.warning("⚠️ No client selected. Please select a client from the Dashboard page.")
        return

    st.markdown(f"### Testing for: **{client_name}**")

    # Check if client can run a test (monthly limit)
    can_run, message = can_run_test(client_name)

    # Display last test info
    last_test = get_last_test_date(client_name)

    col1, col2 = st.columns(2)

    with col1:
        if last_test:
            st.metric(
                "Last Test Run",
                last_test.strftime('%B %d, %Y'),
                f"{(datetime.now() - last_test).days} days ago"
            )
        else:
            st.metric("Last Test Run", "Never", "First test!")

    with col2:
        if can_run:
            st.metric("Test Status", "✅ Ready to Run", "")
        else:
            next_date = last_test + timedelta(days=28)
            st.metric("Test Status", "⏳ Too Soon", f"Wait {28 - (datetime.now() - last_test).days} days")

    st.markdown("---")

    # Pre-flight checks
    st.markdown("### Pre-Flight Checks")

    # Check for prompts file
    prompts_file = get_client_prompts_file(client_name)
    brand_config = get_brand_config_file(client_name)

    check_col1, check_col2, check_col3 = st.columns(3)

    with check_col1:
        if prompts_file:
            prompt_count = count_client_prompts(prompts_file, client_name)
            st.success(f"✅ Prompts Found")
            st.caption(f"{prompt_count} prompts ready")
        else:
            st.error("❌ No Prompts")
            st.caption("Export prompts first")

    with check_col2:
        if brand_config:
            st.success("✅ Brand Config")
            st.caption(f"Using {Path(brand_config).name}")
        else:
            st.error("❌ No Config")
            st.caption("Create brand config")

    with check_col3:
        # Check if API keys are configured (Streamlit secrets, env vars, or config file)
        config_file = Path('config/config.json')
        has_api_keys = False

        # Check Streamlit secrets first (Cloud Run deployment)
        try:
            api_keys_section = st.secrets.get('api_keys', {})
            if api_keys_section:
                has_api_keys = any(
                    key and not str(key).startswith('YOUR_')
                    for key in api_keys_section.values()
                )
        except Exception:
            pass

        # Check environment variables (Cloud Run alternative)
        if not has_api_keys:
            env_keys = [
                os.getenv('OPENAI_API_KEY'),
                os.getenv('ANTHROPIC_API_KEY'),
                os.getenv('PERPLEXITY_API_KEY'),
                os.getenv('GEMINI_API_KEY'),
                os.getenv('SERPAPI_API_KEY'),
                os.getenv('AZURE_OPENAI_API_KEY')
            ]
            has_api_keys = any(key and not key.startswith('YOUR_') for key in env_keys if key)

        # Check config file (local development)
        if not has_api_keys and config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    api_keys = config.get('api_keys', {})
                    # Check if at least one API key is configured
                    has_api_keys = any(
                        key and not key.startswith('YOUR_')
                        for key in api_keys.values()
                    )
            except Exception:
                pass

        if has_api_keys:
            st.success("✅ API Keys")
            st.caption("Ready to test")
        else:
            st.error("❌ No API Keys")
            st.caption("Configure API keys")

    # Show detailed status
    if not can_run:
        st.info(f"ℹ️ {message}")

    all_checks_pass = prompts_file and brand_config and has_api_keys and can_run

    if not all_checks_pass:
        st.markdown("---")
        st.markdown("### ⚠️ Cannot Run Test")

        if not prompts_file:
            st.warning("""
            **Missing Prompts:** Go to the Prompt Generator pages to:
            1. Create or import prompts
            2. Review and approve them
            3. Export to CSV
            """)

        if not brand_config:
            st.warning(f"""
            **Missing Brand Config:** Create a brand configuration file at:
            `data/{client_name.replace(' ', '_')}_brand_config.json`

            Use `data/brand_config_template.json` as a starting point.
            """)

        if not has_api_keys:
            st.warning("""
            **Missing API Keys:** Configure your API keys in:
            `config/config.json`
            """)

        return

    # Allow admin override for monthly limit (with warning)
    if not can_run:
        st.markdown("---")
        st.markdown("### 🔓 Admin Override")

        st.warning("""
        ⚠️ **Warning:** Running tests too frequently can:
        - Skew your monthly trend data
        - Waste API credits
        - Not reflect real monthly changes

        Only override if you're testing the system or have a specific reason.
        """)

        override = st.checkbox("I understand. Allow me to run the test anyway.")

        if not override:
            return

    st.markdown("---")

    # Check if a test is currently running
    test_running = is_test_running(client_name)
    progress = get_test_progress(client_name)

    if test_running:
        # Show running test status
        st.markdown("### 🏃 Test In Progress")

        st.info(f"""
        **Test is running in the background!**

        You can close this browser tab - the test will continue running on the server.
        Refresh this page to check progress.
        """)

        # Show progress
        if progress['total_prompts'] > 0:
            pct = int((progress['prompts_done'] / progress['total_prompts']) * 100)
            st.progress(pct / 100)
            st.caption(f"Progress: {progress['prompts_done']}/{progress['total_prompts']} prompts ({pct}%)")
        else:
            st.progress(0)
            st.caption("Initializing...")

        # Show recent log output
        st.markdown("**Recent Output:**")
        if progress['log_lines']:
            st.code('\n'.join(progress['log_lines'][-15:]))
        else:
            st.caption("Waiting for output...")

        # Refresh button
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()

        # Auto-refresh every 10 seconds
        time.sleep(10)
        st.rerun()

    elif progress['completed']:
        # Test just completed
        st.markdown("### 📊 Test Completed")

        if progress['success']:
            st.success("✅ Test completed successfully!")

            # Sync results and reports to GCS for persistence
            try:
                from src.client_manager.gcs_sync import GCSClientSync
                gcs_sync = GCSClientSync()
                client_slug = client_name.replace(' ', '_').lower()

                with st.spinner("☁️ Syncing data to cloud storage..."):
                    gcs_sync.upload_test_results(client_slug)
                    gcs_sync.upload_reports(client_slug)

                st.success("☁️ Data synced to cloud storage")
            except Exception as e:
                st.warning(f"⚠️ Could not sync to cloud: {e}")

            st.balloons()

            st.markdown("""
            ### 🎉 Report Generated!

            Your new visibility report has been generated and historical tracking has been updated.

            **Next steps:**
            - View your updated report on the Dashboard
            - Check Historical Trends to see month-over-month changes
            - Download exports (CSV, PDF) for your team
            """)

            # Show final log output
            with st.expander("📋 Full Test Log"):
                if progress['log_lines']:
                    st.code('\n'.join(progress['log_lines']))

            # Add button to go to dashboard
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📊 View Dashboard", use_container_width=True):
                    st.session_state.page = 'Dashboard'
                    st.rerun()

            with col2:
                if st.button("📈 View Historical Trends", use_container_width=True):
                    st.session_state.page = 'Historical Trends'
                    st.rerun()

            # Option to run another test
            if st.button("🔄 Clear & Run New Test"):
                # Clear status files
                log_file, pid_file, status_file = get_test_status_files(client_name)
                for f in [status_file]:
                    if f.exists():
                        f.unlink()
                st.rerun()
        else:
            st.error("❌ Test failed.")

            # Show log output for debugging
            st.markdown("**Error Log:**")
            if progress['log_lines']:
                st.code('\n'.join(progress['log_lines']))

            st.markdown("""
            **Common issues:**
            - API key invalid or rate limited
            - Network connectivity problems
            - Invalid brand configuration
            """)

            # Option to retry
            if st.button("🔄 Clear & Retry"):
                log_file, pid_file, status_file = get_test_status_files(client_name)
                for f in [log_file, pid_file, status_file]:
                    if f.exists():
                        f.unlink()
                st.rerun()

    elif progress['incomplete']:
        # Test was interrupted or timed out — partial results saved
        st.markdown("### ⏸️ Test Interrupted — Resume Available")

        # Show how much is done
        st.warning("""
        The test was interrupted before all prompts were completed. Your progress has been
        saved — click **Resume** to pick up where you left off. No prompts will be re-tested.

        Reports will only be generated once **all** prompts are complete.
        """)

        # Show log excerpt
        if progress['log_lines']:
            with st.expander("📋 Last Log Output"):
                st.code('\n'.join(progress['log_lines'][-20:]))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Resume Test", type="primary", use_container_width=True):
                # Clear status file so it can restart
                log_file, pid_file, status_file = get_test_status_files(client_name)
                for f in [status_file, pid_file]:
                    if f.exists():
                        f.unlink()
                # Re-run the test — resume logic in main.py will skip completed prompts
                with st.spinner("Resuming test..."):
                    success = run_visibility_test(client_name, prompts_file, brand_config)
                if success:
                    st.success("✅ Test resumed! Refreshing to show progress...")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Failed to resume test.")

        with col2:
            if st.button("🗑️ Discard & Start Fresh", use_container_width=True):
                # Clear status files AND results
                log_file, pid_file, status_file = get_test_status_files(client_name)
                for f in [log_file, pid_file, status_file]:
                    if f.exists():
                        f.unlink()
                # Clear partial results
                client_slug_clean = client_name.replace(' ', '_').lower()
                results_csv = Path(f'data/results/{client_slug_clean}/results_summary.csv')
                if results_csv.exists():
                    results_csv.unlink()
                # Clear JSON result files
                results_dir = Path(f'data/results/{client_slug_clean}')
                if results_dir.exists():
                    for json_file in results_dir.glob('test_*.json'):
                        json_file.unlink()
                st.success("Partial results cleared. Refresh to start a new test.")
                time.sleep(1)
                st.rerun()

    else:
        # No test running - show start button
        st.markdown("### 🚀 Run Test")

        prompt_count = count_client_prompts(prompts_file, client_name)
        # Estimate: ~5 platforms × ~8 seconds per call = ~40 seconds per prompt
        est_minutes = max(10, int(prompt_count * 40 / 60))
        est_hours = est_minutes / 60

        st.info(f"""
        **What will happen:**
        1. Load {prompt_count} prompts for {client_name}
        2. Test each prompt across available AI platforms (OpenAI, Anthropic, etc.)
        3. Analyze brand visibility and competitor mentions
        4. Generate HTML report, PDF summary, and CSV exports
        5. Update historical tracking data

        **Estimated time:** ~{est_minutes} minutes ({est_hours:.1f} hours) for {prompt_count} prompts × 5 platforms

        **Important:** The test runs on the server and saves progress to cloud storage every 5 minutes.
        You can close this tab and come back later!
        """)

        # Check if OTHER clients have tests running (warn about concurrent tests)
        try:
            from src.client_manager import ClientRegistry
            registry = ClientRegistry()
            other_running = []
            for c in registry.list_clients():
                c_name = c.get('name', '')
                if c_name != client_name and is_test_running(c_name):
                    other_running.append(c_name)
            if other_running:
                st.warning(f"""
                ⚠️ **Tests already running for:** {', '.join(other_running)}

                Running multiple tests simultaneously will cause API rate limiting and can make
                all tests take much longer. Consider waiting for the current test(s) to finish first.
                """)
        except Exception:
            pass

        if st.button("▶️ Start Visibility Test", type="primary", use_container_width=True):
            with st.spinner("Starting test..."):
                success = run_visibility_test(client_name, prompts_file, brand_config)

            if success:
                st.success("✅ Test started! Refreshing to show progress...")
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ Failed to start test. Check error messages above.")

        # Re-analyze section
        st.markdown("---")
        st.markdown("### 🔄 Re-Analyze Existing Results")

        st.info("""
        **Re-analyze without new AI queries:**

        This option re-processes your existing test results to:
        - **Discover new competitors** mentioned in AI responses
        - **Regenerate reports** with updated analysis
        - **Update competitor tracking** without spending API credits

        Use this if you've updated your competitor list or want to find competitors
        that weren't being tracked when the original test ran.
        """)

        if st.button("🔄 Re-Analyze Results", use_container_width=True):
            with st.spinner("Starting re-analysis..."):
                success = run_reanalysis(client_name, brand_config)

            if success:
                st.success("✅ Re-analysis started! Refreshing to show progress...")
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ Failed to start re-analysis. Check error messages above.")

    st.markdown("---")

    # Run All Clients section (admin only)
    user_role_check = st.session_state.get('user_role', st.session_state.get('role', ''))
    if user_role_check == 'admin':
        with st.expander("🔄 Run All Clients (Sequential)"):
            st.markdown("""
            Run visibility tests for **all clients**, one at a time. Each client's test will
            complete fully before the next one starts. Tests support resume — if interrupted,
            re-run to pick up where it left off.
            """)

            # Show all clients and their readiness
            try:
                from src.client_manager import ClientRegistry
                registry = ClientRegistry()
                all_clients = registry.list_clients()

                for c in all_clients:
                    c_name = c.get('name', '')
                    c_slug = c_name.replace(' ', '_').lower()
                    c_prompts = Path(f'data/{c_slug}/{c_slug}_prompts.csv')
                    c_config = Path(f'data/{c_slug}/{c_slug}_brand_config.json')
                    ready = c_prompts.exists() and c_config.exists()

                    if is_test_running(c_name):
                        st.markdown(f"🏃 **{c_name}** — test running")
                    elif ready:
                        st.markdown(f"✅ **{c_name}** — ready")
                    else:
                        missing = []
                        if not c_prompts.exists():
                            missing.append("prompts")
                        if not c_config.exists():
                            missing.append("brand config")
                        st.markdown(f"❌ **{c_name}** — missing: {', '.join(missing)}")

                if st.button("🚀 Start All Client Tests (Sequential)", use_container_width=True):
                    # Launch the batch test script as a background process
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    parent_dir = os.path.dirname(script_dir)
                    batch_script = os.path.join(parent_dir, 'scripts', 'run_all_tests.py')

                    if not Path(batch_script).exists():
                        st.error("Batch test script not found.")
                    else:
                        # Build env with API keys
                        env = os.environ.copy()
                        try:
                            api_keys = st.secrets.get('api_keys', {})
                            for key_name, env_name in [
                                ('openai', 'OPENAI_API_KEY'),
                                ('anthropic', 'ANTHROPIC_API_KEY'),
                                ('perplexity', 'PERPLEXITY_API_KEY'),
                                ('gemini', 'GEMINI_API_KEY'),
                                ('serpapi', 'SERPAPI_API_KEY'),
                            ]:
                                if api_keys.get(key_name):
                                    env[env_name] = api_keys[key_name]
                        except Exception:
                            pass

                        batch_log = Path(parent_dir) / 'data' / 'reports' / 'batch_test.log'
                        batch_log.parent.mkdir(parents=True, exist_ok=True)

                        with open(batch_log, 'w') as log:
                            log.write(f"=== Batch test started: {datetime.now()} ===\n")
                            subprocess.Popen(
                                [sys.executable, batch_script],
                                stdout=log,
                                stderr=subprocess.STDOUT,
                                env=env,
                                cwd=parent_dir,
                                start_new_session=True
                            )

                        st.success("✅ Batch test started for all clients! Tests will run sequentially in the background.")
                        st.info("Check back in a few hours. Each client runs one at a time to avoid rate limiting.")

            except Exception as e:
                st.error(f"Could not load client list: {e}")

    st.markdown("---")

    # Help section
    with st.expander("❓ Help & Troubleshooting"):
        st.markdown("""
        ### Frequently Asked Questions

        **Q: How often should I run tests?**
        A: Monthly. Run tests on the same schedule each month (e.g., first Monday) to track consistent trends.

        **Q: Why can't I run tests more frequently?**
        A: Historical tracking requires consistent monthly intervals. Running tests too often:
        - Skews trend data
        - Wastes API credits
        - Doesn't reflect real market changes

        **Q: What if I want to test new prompts?**
        A: Add new prompts via the Prompt Generator, but keep your core prompts consistent for historical tracking.

        **Q: Where are the report files saved?**
        A: Reports are saved to `data/reports/` and can be downloaded from the Dashboard.

        **Q: What if the test fails?**
        A: Check:
        - API keys are valid and have credits
        - Internet connection is stable
        - Brand config file is valid JSON
        - Prompts file has valid data

        ### Need Help?

        Contact support at: tiffany@dasilvaconsulting.com
        """)

    # Admin diagnostic section (only for admin users)
    user_role = st.session_state.get('user_role', '')
    if user_role == 'admin':
        with st.expander("🔧 Admin Diagnostics"):
            client_slug = client_name.replace(' ', '_').lower()

            st.markdown("**File Paths:**")
            st.code(f"""Prompts file: {prompts_file or 'NOT FOUND'}
Brand config: {brand_config or 'NOT FOUND'}
Status dir: data/reports/{client_slug}/
Client slug: {client_slug}""")

            # Check for stale status files
            log_file, pid_file, status_file = get_test_status_files(client_name)
            st.markdown("**Test Status Files:**")
            status_info = []
            if status_file.exists():
                status_info.append(f"status file EXISTS: {status_file.read_text().strip()}")
            else:
                status_info.append("status file: not present")
            if pid_file.exists():
                status_info.append(f"pid file EXISTS: {pid_file.read_text().strip()}")
            else:
                status_info.append("pid file: not present")
            if log_file.exists():
                log_size = log_file.stat().st_size
                status_info.append(f"log file EXISTS: {log_size} bytes")
            else:
                status_info.append("log file: not present")
            st.code('\n'.join(status_info))

            # Show last 20 lines of log if it exists
            if log_file.exists():
                st.markdown("**Last 20 log lines:**")
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        st.code(''.join(lines[-20:]))
                except Exception as e:
                    st.error(f"Could not read log: {e}")

            # Button to clear stale status files
            if status_file.exists() or pid_file.exists():
                if st.button("🗑️ Clear Stale Status Files", key="clear_status"):
                    for f in [status_file, pid_file]:
                        if f.exists():
                            f.unlink()
                    st.success("Status files cleared. Refresh the page.")
                    time.sleep(1)
                    st.rerun()

            # API keys check
            st.markdown("**API Keys Available:**")
            try:
                api_keys_section = st.secrets.get('api_keys', {})
                key_status = []
                for key_name in ['openai', 'anthropic', 'perplexity', 'gemini', 'serpapi']:
                    val = api_keys_section.get(key_name, '')
                    if val and not str(val).startswith('YOUR_'):
                        key_status.append(f"  {key_name}: ✅ configured ({len(str(val))} chars)")
                    else:
                        key_status.append(f"  {key_name}: ❌ missing")
                st.code('\n'.join(key_status))
            except Exception as e:
                st.error(f"Could not read secrets: {e}")
