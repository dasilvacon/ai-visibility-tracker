"""
Export page for prompt generator app.
"""

import streamlit as st
import pandas as pd
import csv
import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, 'src')


def render():
    """Render the export page."""
    st.title("📤 Export Prompts")

    if not st.session_state.generated_prompts:
        st.warning("No prompts generated yet. Go to **Generate** to create prompts first.")
        return

    # Get approval manager
    approval_mgr = st.session_state.approval_manager
    stats = approval_mgr.get_approval_stats()

    # Export summary
    st.markdown("### Export Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Prompts", stats['total'])

    with col2:
        st.metric("Approved (Ready to Export)", stats['approved'])

    with col3:
        st.metric("Pending Review", stats['pending'])

    if stats['approved'] == 0:
        st.warning("⚠ No approved prompts to export. Go to **Review & Approve** to approve some prompts first.")
        return

    st.markdown("---")

    # Get approved prompts
    approved_prompts = approval_mgr.get_prompts_by_status('approved')

    # Breakdown charts
    st.markdown("### Approved Prompts Breakdown")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### By Persona")
        persona_counts = {}
        for p in approved_prompts:
            persona = p['persona']
            persona_counts[persona] = persona_counts.get(persona, 0) + 1

        for persona, count in sorted(persona_counts.items(), key=lambda x: -x[1]):
            st.markdown(f"- **{persona}:** {count}")

    with col2:
        st.markdown("#### By Category")
        category_counts = {}
        for p in approved_prompts:
            category = p['category']
            category_counts[category] = category_counts.get(category, 0) + 1

        for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            st.markdown(f"- **{category}:** {count}")

    with col3:
        st.markdown("#### By Intent")
        intent_counts = {}
        for p in approved_prompts:
            intent = p['intent_type']
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
            st.markdown(f"- **{intent}:** {count}")

    st.markdown("---")

    # Export options
    st.markdown("### Export Options")

    # CSV Export for Dashboard
    with st.expander("📊 CSV Export (for Dashboard Import)", expanded=True):
        st.markdown("Export approved prompts to CSV format that can be imported into the main AI Visibility Dashboard.")

        export_mode = st.radio(
            "Export Mode",
            ["Append to existing generated_prompts.csv", "Replace generated_prompts.csv", "Export to custom location"],
            index=0,
            help="Choose how to save the approved prompts"
        )

        # Preview
        st.markdown("#### Preview (First 10 Approved Prompts)")
        preview_df = pd.DataFrame(approved_prompts[:10])[['prompt_id', 'persona', 'category', 'intent_type', 'prompt_text', 'expected_visibility_score', 'notes']]
        st.dataframe(preview_df, use_container_width=True)

        # Export button
        if st.button("📥 Export CSV", key="export_csv", type="primary"):
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # Create approved directory
                approved_dir = Path('data/prompt_generation/approved')
                approved_dir.mkdir(parents=True, exist_ok=True)

                # Save to approved directory first
                approved_file = approved_dir / f"approved_{timestamp}.csv"

                with open(approved_file, 'w', newline='') as f:
                    fieldnames = ['prompt_id', 'persona', 'category', 'intent_type', 'prompt_text', 'expected_visibility_score', 'notes']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for prompt in approved_prompts:
                        row = {k: prompt.get(k, '') for k in fieldnames}
                        writer.writerow(row)

                st.success(f"✅ Saved to {approved_file}")

                # Handle export mode
                if export_mode == "Append to existing generated_prompts.csv":
                    main_csv = Path('data/generated_prompts.csv')

                    if main_csv.exists():
                        # Read existing prompts
                        existing_prompts = []
                        with open(main_csv, 'r') as f:
                            reader = csv.DictReader(f)
                            existing_prompts = list(reader)

                        # Check for duplicate IDs
                        existing_ids = {p['prompt_id'] for p in existing_prompts}
                        new_prompts = [p for p in approved_prompts if p['prompt_id'] not in existing_ids]

                        if len(new_prompts) < len(approved_prompts):
                            duplicates = len(approved_prompts) - len(new_prompts)
                            st.warning(f"⚠ Skipped {duplicates} prompts with duplicate IDs")

                        # Append new prompts
                        with open(main_csv, 'a', newline='') as f:
                            fieldnames = ['prompt_id', 'persona', 'category', 'intent_type', 'prompt_text', 'expected_visibility_score', 'notes']
                            writer = csv.DictWriter(f, fieldnames=fieldnames)

                            for prompt in new_prompts:
                                row = {k: prompt.get(k, '') for k in fieldnames}
                                writer.writerow(row)

                        st.success(f"✅ Appended {len(new_prompts)} prompts to {main_csv}")
                    else:
                        # File doesn't exist, create it
                        with open(main_csv, 'w', newline='') as f:
                            fieldnames = ['prompt_id', 'persona', 'category', 'intent_type', 'prompt_text', 'expected_visibility_score', 'notes']
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()

                            for prompt in approved_prompts:
                                row = {k: prompt.get(k, '') for k in fieldnames}
                                writer.writerow(row)

                        st.success(f"✅ Created new {main_csv} with {len(approved_prompts)} prompts")

                elif export_mode == "Replace generated_prompts.csv":
                    if st.checkbox("⚠ I understand this will delete all existing prompts in generated_prompts.csv"):
                        main_csv = Path('data/generated_prompts.csv')

                        with open(main_csv, 'w', newline='') as f:
                            fieldnames = ['prompt_id', 'persona', 'category', 'intent_type', 'prompt_text', 'expected_visibility_score', 'notes']
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()

                            for prompt in approved_prompts:
                                row = {k: prompt.get(k, '') for k in fieldnames}
                                writer.writerow(row)

                        st.success(f"✅ Replaced {main_csv} with {len(approved_prompts)} prompts")
                    else:
                        st.warning("Please check the confirmation box to replace the file.")

                else:  # Custom location
                    # Provide download button
                    csv_data = []
                    fieldnames = ['prompt_id', 'persona', 'category', 'intent_type', 'prompt_text', 'expected_visibility_score', 'notes']

                    csv_content = ','.join(fieldnames) + '\n'
                    for prompt in approved_prompts:
                        row = [str(prompt.get(k, '')) for k in fieldnames]
                        csv_content += ','.join(f'"{v}"' for v in row) + '\n'

                    st.download_button(
                        label="💾 Download CSV",
                        data=csv_content,
                        file_name=f"approved_prompts_{timestamp}.csv",
                        mime="text/csv"
                    )

            except Exception as e:
                st.error(f"❌ Error exporting CSV: {str(e)}")
                st.exception(e)

    # JSON Export
    with st.expander("📋 JSON Export (Full Metadata)"):
        st.markdown("Export approved prompts to JSON format with complete metadata.")

        json_data = json.dumps(approved_prompts, indent=2, default=str)

        st.download_button(
            label="💾 Download JSON",
            data=json_data,
            file_name=f"approved_prompts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

    # HTML Report Export
    with st.expander("📄 HTML Sortable Report"):
        st.markdown("Generate an interactive HTML report with sortable/filterable tables.")

        st.info("🚧 HTML export with interactive tables coming soon! For now, use CSV export.")

        # Placeholder for future HTML exporter integration
        # if st.button("Generate HTML Report", key="export_html"):
        #     from src.prompt_generator.html_exporter import HTMLExporter
        #     exporter = HTMLExporter()
        #     html_file = exporter.generate_report(approved_prompts, stats)
        #     st.success(f"✅ HTML report generated: {html_file}")

    st.markdown("---")

    # Archive management
    st.markdown("### Previous Exports")

    approved_dir = Path('data/prompt_generation/approved')
    if approved_dir.exists():
        csv_files = sorted(approved_dir.glob('approved_*.csv'), reverse=True)

        if csv_files:
            for csv_file in csv_files[:10]:  # Show last 10 exports
                # Extract timestamp from filename
                timestamp_str = csv_file.stem.replace('approved_', '')

                # Count prompts in file
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    count = sum(1 for _ in reader)

                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.text(f"📄 {csv_file.name}")

                with col2:
                    st.text(f"{count} prompts")

                with col3:
                    with open(csv_file, 'r') as f:
                        st.download_button(
                            label="⬇ Download",
                            data=f.read(),
                            file_name=csv_file.name,
                            mime="text/csv",
                            key=f"download_{csv_file.name}"
                        )
        else:
            st.info("No previous exports found.")
    else:
        st.info("No approved exports directory found.")
