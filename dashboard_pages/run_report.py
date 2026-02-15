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
    tracker = HistoricalTracker()
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


def get_client_prompts_file(client_name: str) -> Optional[str]:
    """
    Find the prompts CSV file for a client.

    Args:
        client_name: Name of the client

    Returns:
        Path to prompts file, or None if not found
    """
    # Check data/generated_prompts.csv
    prompts_file = Path('data/generated_prompts.csv')

    if not prompts_file.exists():
        return None

    # Check if client has prompts in the file
    try:
        with open(prompts_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('client_name') == client_name:
                    # Found at least one prompt for this client
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
    # Convert client name to filename format (spaces to underscores, lowercase)
    client_slug = client_name.replace(' ', '_')

    # Check for brand config files
    possible_paths = [
        Path(f'data/{client_slug}_brand_config.json'),
        Path(f'data/{client_slug.lower()}_brand_config.json'),
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
            for row in reader:
                if row.get('client_name') == client_name:
                    count += 1
        return count
    except Exception:
        return 0


def run_visibility_test(client_name: str, prompts_file: str, brand_config: str) -> bool:
    """
    Run visibility test for a client using CLI.

    Args:
        client_name: Name of the client
        prompts_file: Path to prompts CSV file
        brand_config: Path to brand config JSON file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create a temporary filtered prompts file for this client
        temp_prompts = Path(f'data/temp_{client_name.replace(" ", "_")}_prompts.csv')

        # Filter prompts for this client
        with open(prompts_file, 'r') as f_in:
            reader = csv.DictReader(f_in)
            fieldnames = reader.fieldnames

            rows = [row for row in reader if row.get('client_name') == client_name]

        # Write filtered prompts
        with open(temp_prompts, 'w', newline='') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        # Run main.py with the filtered prompts
        cmd = [
            'python',
            'main.py',
            '--prompts', str(temp_prompts),
            '--analyze',
            '--brand-config', brand_config
        ]

        # Run the command and capture output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Stream output in real-time
        output_container = st.empty()
        output_lines = []

        for line in iter(process.stdout.readline, ''):
            if line:
                output_lines.append(line.rstrip())
                # Show last 20 lines
                display_lines = output_lines[-20:]
                output_container.code('\n'.join(display_lines))

        process.wait()

        # Clean up temp file
        if temp_prompts.exists():
            temp_prompts.unlink()

        return process.returncode == 0

    except Exception as e:
        st.error(f"Error running visibility test: {str(e)}")
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
        # Check if API keys are configured
        config_file = Path('config/config.json')
        has_api_keys = False

        if config_file.exists():
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

    # Run test section
    st.markdown("### 🚀 Run Test")

    st.info(f"""
    **What will happen:**
    1. Load {count_client_prompts(prompts_file, client_name)} prompts for {client_name}
    2. Test each prompt across available AI platforms (OpenAI, Anthropic, etc.)
    3. Analyze brand visibility and competitor mentions
    4. Generate HTML report, PDF summary, and CSV exports
    5. Update historical tracking data

    **Estimated time:** 5-15 minutes depending on prompt count
    """)

    if st.button("▶️ Start Visibility Test", type="primary", use_container_width=True):
        st.markdown("---")
        st.markdown("### 📊 Test Progress")

        with st.spinner("Initializing test..."):
            time.sleep(1)

        st.info("🏃 Running visibility tests... This may take several minutes.")

        # Create progress section
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Starting test execution...")
        progress_bar.progress(10)

        # Run the test
        success = run_visibility_test(client_name, prompts_file, brand_config)

        progress_bar.progress(100)

        if success:
            st.success("✅ Test completed successfully!")

            st.balloons()

            st.markdown("""
            ### 🎉 Report Generated!

            Your new visibility report has been generated and historical tracking has been updated.

            **Next steps:**
            - View your updated report on the Dashboard
            - Check Historical Trends to see month-over-month changes
            - Download exports (CSV, PDF) for your team
            """)

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
        else:
            st.error("""
            ❌ Test failed. Please check the output above for error details.

            **Common issues:**
            - API key invalid or rate limited
            - Network connectivity problems
            - Invalid brand configuration
            """)

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
