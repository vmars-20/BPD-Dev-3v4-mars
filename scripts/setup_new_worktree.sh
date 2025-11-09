#!/usr/bin/env bash
#
# setup_new_worktree.sh - Automated worktree setup
#
# Automates the post-creation setup for new git worktrees:
# - Initializes git submodules
# - Fixes nested workspace issue in forge-vhdl
# - Syncs dependencies with uv
# - Runs diagnostic verification
#
# Usage:
#   # After creating worktree with ccmanager or git worktree add
#   cd /path/to/new/worktree
#   ./scripts/setup_new_worktree.sh
#
# Exit codes:
#   0 - Success
#   1 - Error occurred
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Main script
main() {
    print_header "Worktree Setup Automation"

    echo "This script will set up your worktree for development."
    echo "It will:"
    echo "  1. Initialize git submodules"
    echo "  2. Fix nested workspace issues"
    echo "  3. Sync dependencies with uv"
    echo "  4. Verify setup with diagnostic script"
    echo ""

    # Step 1: Check if we're in a git repository
    print_header "Step 1: Git Repository Check"

    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository!"
        echo "Please cd to your worktree directory first."
        exit 1
    fi

    print_success "In git repository"

    # Check if this is a worktree
    GIT_COMMON_DIR=$(git rev-parse --git-common-dir)
    GIT_DIR=$(git rev-parse --git-dir)

    if [ "$GIT_COMMON_DIR" != "$GIT_DIR" ]; then
        print_info "Running in a git worktree"
        WORKTREE_NAME=$(basename "$(pwd)")
        print_info "Worktree: $WORKTREE_NAME"
    else
        print_info "Running in main repository"
    fi

    BRANCH=$(git branch --show-current)
    print_info "Branch: $BRANCH"

    # Step 2: Initialize submodules
    print_header "Step 2: Git Submodules"

    # Check submodule status
    SUBMODULE_STATUS=$(git submodule status 2>&1)

    if echo "$SUBMODULE_STATUS" | grep -q "^-"; then
        print_warning "Submodules not initialized"
        echo "Initializing submodules (this may take a minute)..."

        if git submodule update --init --recursive; then
            print_success "Submodules initialized"
        else
            print_error "Failed to initialize submodules"
            exit 1
        fi
    else
        print_success "Submodules already initialized"
    fi

    # Verify key submodules exist
    for submodule in "libs/forge-vhdl" "libs/moku-models" "libs/riscure-models"; do
        if [ -f "$submodule/pyproject.toml" ]; then
            print_success "Found: $submodule"
        else
            print_warning "Missing: $submodule"
        fi
    done

    # Step 3: Fix nested workspace issue
    print_header "Step 3: Workspace Configuration"

    FORGE_VHDL_TOML="libs/forge-vhdl/pyproject.toml"

    if [ ! -f "$FORGE_VHDL_TOML" ]; then
        print_error "Cannot find $FORGE_VHDL_TOML"
        print_warning "Skipping workspace fix (submodule might not be initialized)"
    else
        # Check if [tool.uv.workspace] is uncommented
        if grep -q "^\[tool\.uv\.workspace\]" "$FORGE_VHDL_TOML"; then
            print_warning "Nested workspace detected in $FORGE_VHDL_TOML"
            echo "Fixing nested workspace issue..."

            # Create backup
            cp "$FORGE_VHDL_TOML" "$FORGE_VHDL_TOML.bak"
            print_info "Backup created: $FORGE_VHDL_TOML.bak"

            # Comment out the [tool.uv.workspace] section
            # This is a bit complex - we need to comment from [tool.uv.workspace] to the closing ]
            python3 << 'PYTHON_SCRIPT'
import re

toml_file = "libs/forge-vhdl/pyproject.toml"

with open(toml_file, 'r') as f:
    content = f.read()

# Pattern to match [tool.uv.workspace] section with its members
pattern = r'(\[tool\.uv\.workspace\]\n(?:.*\n)*?members = \[\n(?:.*\n)*?\])'

# Replacement with commented version
replacement = '''# COMMENTED OUT: Nested workspaces not supported when used as submodule
# Uncomment if using forge-vhdl standalone
#
# [tool.uv.workspace]
# # Declare Python packages as workspace members
# # uv manages these as a unified dependency graph
# members = [
#     "python/forge_cocotb",
#     "python/forge_platform",
#     "python/forge_tools",
# ]'''

# Replace
new_content = re.sub(pattern, replacement, content)

with open(toml_file, 'w') as f:
    f.write(new_content)

print("Fixed!")
PYTHON_SCRIPT

            if [ $? -eq 0 ]; then
                print_success "Nested workspace issue fixed"
            else
                print_error "Failed to fix nested workspace"
                echo "You may need to manually edit: $FORGE_VHDL_TOML"
                echo "Restore backup with: mv $FORGE_VHDL_TOML.bak $FORGE_VHDL_TOML"
                exit 1
            fi
        else
            print_success "No nested workspace issues detected"
        fi
    fi

    # Step 4: Check for uv
    print_header "Step 4: UV Package Manager"

    if ! command -v uv &> /dev/null; then
        print_error "uv not found in PATH"
        echo "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    UV_VERSION=$(uv --version)
    print_success "UV found: $UV_VERSION"

    # Step 5: Sync dependencies
    print_header "Step 5: Dependency Sync"

    echo "Running: uv sync"
    echo "(This may take a minute on first run...)"
    echo ""

    if uv sync; then
        print_success "Dependencies synced"
    else
        print_error "Failed to sync dependencies"
        echo ""
        echo "Common issues:"
        echo "  - Nested workspace error: Check libs/forge-vhdl/pyproject.toml"
        echo "  - Network error: Check internet connection"
        echo "  - SSH key error: Verify GitHub SSH access (ssh -T git@github.com)"
        exit 1
    fi

    # Step 6: Run diagnostic
    print_header "Step 6: Verification"

    if [ -f "scripts/diagnose_moku_env.py" ]; then
        echo "Running diagnostic script..."
        echo ""

        if uv run python scripts/diagnose_moku_env.py; then
            print_success "Diagnostic passed"
        else
            print_warning "Diagnostic reported issues"
            echo "Review the output above for details."
        fi
    else
        print_warning "Diagnostic script not found (scripts/diagnose_moku_env.py)"
        print_info "Skipping verification step"
    fi

    # Final summary
    print_header "Setup Complete!"

    echo "Your worktree is ready to use."
    echo ""
    echo "Next steps:"
    echo "  • Open in Claude Code: claude"
    echo "  • Open in Cursor: cursor ."
    echo "  • Open in VS Code: code ."
    echo ""
    echo "Documentation:"
    echo "  • Worktree guide: docs/CCMANAGER-WORKFLOW.md"
    echo "  • Moku fork setup: docs/MOKU-DEV-MODULE.md"
    echo "  • Multi-tool usage: docs/MULTI-AI-TOOL-SETUP.md"
    echo ""

    print_success "Done! Happy coding! 🚀"
}

# Run main function
main "$@"
