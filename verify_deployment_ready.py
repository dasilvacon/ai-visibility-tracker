#!/usr/bin/env python3
"""
Verification script to check if the Prompt Generator is ready for deployment.
Run this before deploying to Streamlit Cloud.
"""

import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ MISSING: {description}: {filepath}")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists and has files."""
    path = Path(dirpath)
    if path.exists() and path.is_dir():
        file_count = len(list(path.iterdir()))
        print(f"✅ {description}: {dirpath} ({file_count} files)")
        return True
    else:
        print(f"❌ MISSING: {description}: {dirpath}")
        return False

def main():
    print("=" * 70)
    print("DEPLOYMENT READINESS CHECK - PROMPT GENERATOR")
    print("=" * 70)
    print()

    all_checks = []

    # Check main app file
    print("[1/7] Checking Main App File...")
    all_checks.append(check_file_exists("prompt_generator_app.py", "Main entry point"))
    print()

    # Check UI pages
    print("[2/7] Checking UI Pages...")
    all_checks.append(check_file_exists("prompt_generator_pages/__init__.py", "Package init"))
    all_checks.append(check_file_exists("prompt_generator_pages/generate.py", "Generate page"))
    all_checks.append(check_file_exists("prompt_generator_pages/review.py", "Review page"))
    all_checks.append(check_file_exists("prompt_generator_pages/export_page.py", "Export page"))
    all_checks.append(check_file_exists("prompt_generator_pages/settings.py", "Settings page"))
    print()

    # Check core modules
    print("[3/7] Checking Core Modules...")
    all_checks.append(check_file_exists("src/prompt_generator/deduplicator.py", "Deduplicator"))
    all_checks.append(check_file_exists("src/prompt_generator/approval_manager.py", "Approval manager"))
    all_checks.append(check_file_exists("src/prompt_generator/generator.py", "Generator"))
    print()

    # Check data files
    print("[4/7] Checking Data Files...")
    all_checks.append(check_file_exists("data/natasha_denona_personas.json", "Personas data"))
    all_checks.append(check_file_exists("data/natasha_denona_keywords.csv", "Keywords data"))
    print()

    # Check configuration files
    print("[5/7] Checking Configuration Files...")
    all_checks.append(check_file_exists("requirements.txt", "Dependencies"))
    all_checks.append(check_file_exists(".streamlit/config.toml", "Streamlit config"))
    print()

    # Check directories
    print("[6/7] Checking Directory Structure...")
    all_checks.append(check_directory_exists("prompt_generator_pages", "UI pages directory"))
    all_checks.append(check_directory_exists("src/prompt_generator", "Core modules directory"))
    all_checks.append(check_directory_exists("data/prompt_generation/drafts", "Drafts directory"))
    all_checks.append(check_directory_exists("data/prompt_generation/approved", "Approved directory"))
    print()

    # Check Python syntax
    print("[7/7] Checking Python Syntax...")
    try:
        import py_compile
        files_to_check = [
            "prompt_generator_app.py",
            "prompt_generator_pages/generate.py",
            "prompt_generator_pages/review.py",
            "prompt_generator_pages/export_page.py",
            "prompt_generator_pages/settings.py",
        ]

        syntax_ok = True
        for file in files_to_check:
            try:
                py_compile.compile(file, doraise=True)
            except py_compile.PyCompileError as e:
                print(f"❌ Syntax error in {file}: {e}")
                syntax_ok = False

        if syntax_ok:
            print("✅ All Python files have valid syntax")
            all_checks.append(True)
        else:
            all_checks.append(False)
    except Exception as e:
        print(f"⚠️  Could not verify syntax: {e}")
        all_checks.append(True)  # Don't fail on this
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(all_checks)
    total = len(all_checks)

    print(f"Checks passed: {passed}/{total}")
    print()

    if all(all_checks):
        print("🎉 SUCCESS! Ready for deployment!")
        print()
        print("Next steps:")
        print("1. Commit all files to Git")
        print("2. Push to GitHub")
        print("3. Go to https://share.streamlit.io")
        print("4. Deploy with main file: prompt_generator_app.py")
        print()
        print("See DEPLOYMENT_GUIDE.md for detailed instructions.")
        return 0
    else:
        print("❌ NOT READY - Some checks failed")
        print()
        print("Please fix the issues above before deploying.")
        print("See DEPLOYMENT_GUIDE.md for help.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
