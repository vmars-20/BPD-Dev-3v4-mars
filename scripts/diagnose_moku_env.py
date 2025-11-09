#!/usr/bin/env python3
"""
Moku Environment Diagnostic Tool

Automatically diagnoses moku library installation issues and provides quick fixes.
See docs/MOKU-DEV-MODULE.md for detailed troubleshooting.

Usage:
    uv run python scripts/diagnose_moku_env.py
    # or
    python scripts/diagnose_moku_env.py  (if venv activated)
"""

import subprocess
import sys
import json
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.END} {text}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.END} {text}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ{Colors.END} {text}")


def run_command(cmd, capture_output=True, check=False):
    """Run command and return result"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        return e


def check_uv_available():
    """Check if uv is installed and available"""
    print_header("1. UV Package Manager")

    result = run_command("which uv")
    if result.returncode == 0:
        uv_path = result.stdout.strip()
        print_success(f"UV found: {uv_path}")

        # Get uv version
        version_result = run_command("uv --version")
        if version_result.returncode == 0:
            print_info(f"Version: {version_result.stdout.strip()}")
        return True
    else:
        print_error("UV not found in PATH")
        print("\n📋 Quick Fix:")
        print("   Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("   Or see: https://github.com/astral-sh/uv")
        return False


def check_venv_exists():
    """Check if .venv exists"""
    print_header("2. Virtual Environment")

    venv_path = Path(".venv")
    if venv_path.exists():
        print_success(f"Virtual environment found: {venv_path.absolute()}")

        # Check Python version
        python_result = run_command("uv run python --version")
        if python_result.returncode == 0:
            print_info(f"Python: {python_result.stdout.strip()}")
        return True
    else:
        print_warning("Virtual environment not found")
        print("\n📋 Quick Fix:")
        print("   Run: uv sync")
        print("   This will create .venv and install all dependencies")
        return False


def check_moku_installed():
    """Check if moku package is installed"""
    print_header("3. Moku Package Installation")

    result = run_command("uv pip show moku")
    if result.returncode == 0:
        print_success("Moku package is installed")

        # Parse output
        lines = result.stdout.strip().split('\n')
        info = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()

        # Display key information
        if 'Version' in info:
            print_info(f"Version: {info['Version']}")
        if 'Location' in info:
            print_info(f"Location: {info['Location']}")

        return True, info
    else:
        print_error("Moku package not installed")
        print("\n📋 Quick Fix:")
        print("   Run: uv sync")
        print("   This will install moku from pyproject.toml")
        return False, {}


def check_moku_source(moku_info):
    """Determine if moku is from PyPI or GitHub fork"""
    print_header("4. Moku Source Detection")

    # Check for direct_url.json (pip metadata for git installs)
    try:
        result = run_command("uv run python -c \"import moku; import os; print(os.path.dirname(moku.__file__))\"")
        if result.returncode == 0:
            moku_path = Path(result.stdout.strip())
            dist_info = moku_path.parent / "moku-4.0.3.1.dist-info"
            direct_url_file = dist_info / "direct_url.json"

            if direct_url_file.exists():
                with open(direct_url_file, 'r') as f:
                    direct_url = json.load(f)

                if 'url' in direct_url and 'github.com' in direct_url['url']:
                    print_success("Using GitHub fork (LLM-annotated version)")
                    print_info(f"Repository: {direct_url['url']}")

                    if 'vcs_info' in direct_url:
                        commit = direct_url['vcs_info'].get('commit_id', 'unknown')
                        print_info(f"Commit: {commit[:8]}")

                    print("\n📚 Fork Features:")
                    print("   • @CLAUDE annotations in source code")
                    print("   • 3-tier documentation (llms.txt → CLAUDE.md → source)")
                    print("   • Session introspection guides")
                    print("   • Integration examples with moku-models")
                    print("\n📖 Fork Repository:")
                    print("   git@github.com:vmars-20/moku-3.0.4.1-llm-dev.git")
                    print("\n💡 To browse documentation:")
                    print("   git clone git@github.com:vmars-20/moku-3.0.4.1-llm-dev.git ~/Development/moku-llm-dev")
                    print("   # Then read: CLAUDE.md, llms.txt, README_LLM.md")
                    return 'github'
                else:
                    print_info("Using standard installation")
                    return 'other'
            else:
                print_info("Using PyPI package (official version)")
                print("\n💡 Note: This project is configured to use the GitHub fork.")
                print("   To switch to fork:")
                print("   1. Ensure pyproject.toml has:")
                print('      "moku @ git+ssh://git@github.com/vmars-20/moku-3.0.4.1-llm-dev.git@main"')
                print("   2. Run: uv sync")
                return 'pypi'
    except Exception as e:
        print_warning(f"Could not determine source: {e}")

    return 'unknown'


def check_submodules():
    """Check if git submodules are initialized"""
    print_header("5. Git Submodules")

    # Check if we're in a git repository
    git_check = run_command("git rev-parse --git-dir")
    if git_check.returncode != 0:
        print_info("Not in a git repository (OK if running from installed package)")
        return True

    # Check submodule status
    result = run_command("git submodule status")
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')

        all_initialized = True
        for line in lines:
            if line.strip():
                status = line[0]
                parts = line[1:].strip().split()
                if len(parts) >= 2:
                    submodule_name = parts[1]

                    if status == '-':
                        print_error(f"Not initialized: {submodule_name}")
                        all_initialized = False
                    elif status == ' ':
                        print_success(f"Initialized: {submodule_name}")
                    elif status == '+':
                        print_warning(f"Modified: {submodule_name}")

        if not all_initialized:
            print("\n📋 Quick Fix:")
            print("   Run: git submodule update --init --recursive")
            print("\n⚠️  IMPORTANT: If you're in a git worktree, you MUST run this command!")
            print("   See: docs/MOKU-DEV-MODULE.md - 'Git Worktree Workflow' section")
            return False
        else:
            print_success("All submodules initialized")
            return True

    return True


def check_moku_import():
    """Test if moku can be imported successfully"""
    print_header("6. Moku Import Test")

    result = run_command("uv run python -c \"from moku.instruments import MultiInstrument; print('OK')\"")
    if result.returncode == 0 and 'OK' in result.stdout:
        print_success("Moku imports successfully")
        print_info("MultiInstrument class available")
        return True
    else:
        print_error("Cannot import moku")
        if result.stderr:
            print(f"\n{Colors.RED}Error Details:{Colors.END}")
            print(result.stderr)

        print("\n📋 Quick Fix:")
        print("   1. Ensure .venv is created: uv sync")
        print("   2. Always use: uv run python script.py")
        print("   3. Or activate venv: source .venv/bin/activate")
        return False


def check_nested_workspace():
    """Check for nested workspace issues"""
    print_header("7. Workspace Configuration")

    forge_vhdl_toml = Path("libs/forge-vhdl/pyproject.toml")

    if not forge_vhdl_toml.exists():
        print_warning("forge-vhdl not found (submodule not initialized?)")
        return False

    # Check if [tool.uv.workspace] is commented out
    with open(forge_vhdl_toml, 'r') as f:
        content = f.read()

    # Look for uncommented [tool.uv.workspace]
    if '[tool.uv.workspace]' in content:
        # Check if it's commented
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '[tool.uv.workspace]' in line and not line.strip().startswith('#'):
                print_error("Nested workspace detected in libs/forge-vhdl/pyproject.toml")
                print("\n📋 Quick Fix:")
                print("   Comment out [tool.uv.workspace] section in:")
                print("   libs/forge-vhdl/pyproject.toml")
                print("\n   See: docs/MOKU-DEV-MODULE.md - 'Step 4: Fix Nested Workspace Issue'")
                return False

    print_success("No nested workspace issues detected")
    return True


def print_summary(results):
    """Print summary and recommendations"""
    print_header("Summary & Recommendations")

    all_checks = all(results.values())

    if all_checks:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All checks passed!{Colors.END}")
        print("\nYour moku environment is correctly configured.")
        print("\n🚀 Next Steps:")
        print("   • Import moku in your scripts: from moku.instruments import MultiInstrument")
        print("   • See examples: docs/MOKU-DEV-MODULE.md")
        if 'moku_source' in results and results['moku_source'] == 'github':
            print("   • Fork docs: git clone git@github.com:vmars-20/moku-3.0.4.1-llm-dev.git")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ Some issues detected{Colors.END}")
        print("\n📖 For detailed troubleshooting, see:")
        print("   docs/MOKU-DEV-MODULE.md")

        print("\n🔧 Most Common Fixes:")
        if not results.get('venv_exists'):
            print("   1. Run: uv sync")
        if not results.get('submodules_ok'):
            print("   2. Run: git submodule update --init --recursive")
        if not results.get('workspace_ok'):
            print("   3. Comment out [tool.uv.workspace] in libs/forge-vhdl/pyproject.toml")
        if not results.get('moku_import'):
            print("   4. Always use: uv run python script.py")


def check_git_worktree():
    """Check if we're in a git worktree"""
    print_header("0. Git Worktree Detection")

    result = run_command("git rev-parse --git-common-dir")
    if result.returncode == 0:
        common_dir = Path(result.stdout.strip())
        current_dir = Path.cwd()

        # If common-dir is different from current .git, we're in a worktree
        if not common_dir.is_relative_to(current_dir):
            print_warning("Running in a git worktree")
            print_info(f"Main repository: {common_dir}")

            # List all worktrees
            worktree_result = run_command("git worktree list")
            if worktree_result.returncode == 0:
                print("\n📋 Active Worktrees:")
                print(worktree_result.stdout)

            print(f"\n{Colors.YELLOW}⚠️  IMPORTANT for Worktrees:{Colors.END}")
            print("   Submodules are NOT automatically initialized in worktrees!")
            print("   Always run after creating a new worktree:")
            print("   → git submodule update --init --recursive")
            return True
        else:
            print_success("Running in main repository")
            return False

    print_info("Not a git repository")
    return False


def main():
    """Main diagnostic routine"""
    print(f"\n{Colors.BOLD}{'='*70}")
    print("Moku Environment Diagnostic Tool")
    print(f"{'='*70}{Colors.END}\n")

    print("This tool checks your moku library installation and environment setup.")
    print("For detailed documentation, see: docs/MOKU-DEV-MODULE.md\n")

    results = {}

    # Check if in worktree (important context)
    in_worktree = check_git_worktree()

    # Run all checks
    results['uv_available'] = check_uv_available()
    results['venv_exists'] = check_venv_exists()

    moku_installed, moku_info = check_moku_installed()
    results['moku_installed'] = moku_installed

    if moku_installed:
        results['moku_source'] = check_moku_source(moku_info)

    results['submodules_ok'] = check_submodules()
    results['workspace_ok'] = check_nested_workspace()
    results['moku_import'] = check_moku_import()

    # Print summary
    print_summary(results)

    # Exit code
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
