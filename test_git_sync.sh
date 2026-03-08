#!/bin/bash
# Test Git Sync Functionality

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Testing Git Sync for Client Data          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Check git installation
echo -e "${BLUE}Test 1: Git Installation${NC}"
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo -e "${GREEN}✓ Git installed: $GIT_VERSION${NC}"
else
    echo -e "${RED}✗ Git not installed${NC}"
    exit 1
fi
echo ""

# Test 2: Check git configuration
echo -e "${BLUE}Test 2: Git Configuration${NC}"
GIT_USER=$(git config user.name 2>/dev/null || echo "")
GIT_EMAIL=$(git config user.email 2>/dev/null || echo "")

if [ -n "$GIT_USER" ] && [ -n "$GIT_EMAIL" ]; then
    echo -e "${GREEN}✓ Git user configured${NC}"
    echo "  Name: $GIT_USER"
    echo "  Email: $GIT_EMAIL"
else
    echo -e "${RED}✗ Git not configured${NC}"
    echo "  Run: git config --global user.name \"Your Name\""
    echo "  Run: git config --global user.email \"your@email.com\""
    exit 1
fi
echo ""

# Test 3: Check git remote
echo -e "${BLUE}Test 3: Git Remote${NC}"
if git remote -v &> /dev/null; then
    REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
    if [ -n "$REMOTE_URL" ]; then
        echo -e "${GREEN}✓ Git remote configured${NC}"
        echo "  Origin: $REMOTE_URL"

        # Check if using SSH or HTTPS
        if [[ "$REMOTE_URL" == git@github.com* ]]; then
            echo -e "${YELLOW}⚠  Using SSH (git@github.com)${NC}"
            echo "  Cloud Run will use HTTPS with token"
        else
            echo -e "${GREEN}✓ Using HTTPS${NC}"
        fi
    else
        echo -e "${RED}✗ No remote configured${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Not a git repository${NC}"
    exit 1
fi
echo ""

# Test 4: Check for uncommitted changes
echo -e "${BLUE}Test 4: Git Status${NC}"
if git diff --quiet && git diff --cached --quiet; then
    echo -e "${GREEN}✓ Working directory clean${NC}"
else
    echo -e "${YELLOW}⚠  Uncommitted changes detected${NC}"
    echo ""
    git status --short
fi
echo ""

# Test 5: Test file creation and commit
echo -e "${BLUE}Test 5: Test Commit${NC}"
TEST_FILE="data/.git_sync_test_$(date +%s).tmp"
echo "Git sync test - $(date)" > "$TEST_FILE"

if [ -f "$TEST_FILE" ]; then
    echo -e "${GREEN}✓ Test file created: $TEST_FILE${NC}"
else
    echo -e "${RED}✗ Could not create test file${NC}"
    exit 1
fi

# Try to add the file
if git add "$TEST_FILE"; then
    echo -e "${GREEN}✓ File staged${NC}"
else
    echo -e "${RED}✗ Could not stage file${NC}"
    rm "$TEST_FILE"
    exit 1
fi

# Try to commit
if git commit -m "Test: Git sync verification" -q; then
    echo -e "${GREEN}✓ Commit created${NC}"
    COMMIT_HASH=$(git rev-parse --short HEAD)
    echo "  Commit: $COMMIT_HASH"
else
    echo -e "${RED}✗ Could not create commit${NC}"
    git reset HEAD "$TEST_FILE" &> /dev/null
    rm "$TEST_FILE"
    exit 1
fi
echo ""

# Test 6: Test push (dry-run)
echo -e "${BLUE}Test 6: Push Test (Dry-Run)${NC}"
if git push --dry-run 2>&1 | grep -q "Everything up-to-date\|Would update"; then
    echo -e "${GREEN}✓ Push would succeed (dry-run)${NC}"

    # Actually push the test commit
    echo -e "${BLUE}→ Pushing test commit to GitHub...${NC}"
    if git push; then
        echo -e "${GREEN}✓ Push successful!${NC}"
    else
        echo -e "${RED}✗ Push failed${NC}"
        echo "  This might be due to authentication issues"

        # Rollback the commit
        echo -e "${YELLOW}→ Rolling back test commit...${NC}"
        git reset --soft HEAD~1
        git reset HEAD "$TEST_FILE"
        rm "$TEST_FILE"
        exit 1
    fi
else
    echo -e "${RED}✗ Push would fail${NC}"

    # Rollback the commit
    git reset --soft HEAD~1
    git reset HEAD "$TEST_FILE"
    rm "$TEST_FILE"
    exit 1
fi
echo ""

# Cleanup: Remove test file and commit
echo -e "${BLUE}Cleanup: Removing test commit...${NC}"
git rm "$TEST_FILE" -q
git commit -m "Cleanup: Remove git sync test file" -q
git push -q

echo -e "${GREEN}✓ Test file cleaned up${NC}"
echo ""

# Summary
echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         All Git Sync Tests Passed! ✓              ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Local git sync is working correctly!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Run: ./setup_git_credentials.sh"
echo "  2. Create GitHub Personal Access Token when prompted"
echo "  3. Deploy: ./deploy_to_cloud_run.sh"
echo "  4. Test client creation in Cloud Run dashboard"
echo ""
