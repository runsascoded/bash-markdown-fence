#!/usr/bin/env python3
"""Generate the 'updated programmatically' notes with correct CI links.

When README_ABSOLUTE_URLS=1 is set, generates absolute GitHub URLs instead of
relative paths. This is used during PyPI package builds to ensure links work
correctly on PyPI's README display. Requires being on a git tag when this
environment variable is set.

Usage:
    # Normal usage (relative URLs for GitHub):
    python test/print-ci-yml-ref.py mdcmd

    # PyPI build (absolute URLs, must be on a tag):
    README_ABSOLUTE_URLS=1 python test/print-ci-yml-ref.py mdcmd
"""

import os
import sys
from pathlib import Path


def find_ci_step_lines(ci_path=".github/workflows/ci.yml"):
    """Find line numbers for the mdcmd CI step."""
    content = Path(ci_path).read_text()
    lines = content.splitlines()

    step_name = "Verify README examples and TOC are up to date"
    for i, line in enumerate(lines, 1):
        if f"name: {step_name}" in line:
            start = i
            # Find the end of this step
            for j in range(i+1, len(lines)+1):
                if j > len(lines):
                    return (start, j-1)
                line_j = lines[j-1]
                # Stop at next step or job
                if (line_j.strip().startswith('- name:') or
                    (line_j.strip() and not line_j.startswith('    '))):
                    return (start, j-1)
                # Update end if we find content
                if line_j.strip():
                    end = j
            return (start, end)
    return None


def find_readme_lines(tool):
    """Find line numbers for the relevant section in README.md."""
    try:
        content = Path("README.md").read_text()
        lines = content.splitlines()

        if tool == "mdcmd":
            # Find "<!-- `bmdf seq 3` -->" through first subsequent "```"
            for i, line in enumerate(lines, 1):
                if "<!-- `bmdf seq 3` -->" in line:
                    for j in range(i+1, len(lines)+1):
                        if j > len(lines) or lines[j-1] == "```":
                            return (i, j)
        elif tool == "toc":
            # Find "<!-- `toc` -->" until first subsequent empty line
            for i, line in enumerate(lines, 1):
                if "<!-- `toc` -->" in line:
                    for j in range(i+1, len(lines)+1):
                        if j > len(lines):
                            return (i, j-1)
                        if not lines[j-1].strip():
                            return (i, j-1)
    except:
        pass
    return None


def main():
    """Generate the update notes."""
    if len(sys.argv) < 2:
        print("Usage: print-ci-yml-ref.py {mdcmd|toc}", file=sys.stderr)
        sys.exit(1)

    tool = sys.argv[1]
    if tool not in ["mdcmd", "toc"]:
        print(f"Unknown tool: {tool}", file=sys.stderr)
        sys.exit(1)

    ci_lines = find_ci_step_lines()
    readme_lines = find_readme_lines(tool)

    if not ci_lines:
        print("CI step not found", file=sys.stderr)
        sys.exit(1)

    # Check env var for absolute URLs (for PyPI builds)
    # When publishing to PyPI, we need absolute URLs since PyPI doesn't resolve
    # relative GitHub paths. This requires being on a tag to ensure stable URLs.
    if os.getenv("README_ABSOLUTE_URLS"):
        import subprocess
        try:
            result = subprocess.run(
                ["git", "describe", "--exact-match", "--tags", "HEAD"],
                capture_output=True, text=True, check=True
            )
            ref = result.stdout.strip()
            if not ref:
                print("ERROR: README_ABSOLUTE_URLS=1 but not on a tag", file=sys.stderr)
                sys.exit(1)
        except subprocess.CalledProcessError:
            print("ERROR: README_ABSOLUTE_URLS=1 but not on a tag", file=sys.stderr)
            sys.exit(1)

        # Generate absolute GitHub URLs using the tag as ref (for PyPI)
        base_url = f"https://github.com/runsascoded/mdcmd/blob/{ref}"
        ci_path = f"{base_url}/.github/workflows/ci.yml"
        readme_base = f"{base_url}/README.md?plain=1"
    else:
        # Use relative URLs for normal GitHub viewing
        ci_path = ".github/workflows/ci.yml"
        readme_base = "README.md?plain=1"

    # Add line numbers if we found them
    if readme_lines:
        start, end = readme_lines
        readme_link = f"[raw README.md]({readme_base}#L{start}-L{end})"
    else:
        readme_link = f"[raw README.md]({readme_base})"

    ci_start, ci_end = ci_lines
    print("<p>\n")
    if tool == "mdcmd":
        print(f'☝️ This block is updated programmatically by [`mdcmd`] (and verified [in CI]({ci_path}#L{ci_start}-L{ci_end}); see {readme_link}).')
    else:  # tool == "toc"
        print(f'☝️ This TOC is generated programmatically by [`mdcmd`] and [`toc`] (and verified [in CI]({ci_path}#L{ci_start}-L{ci_end}); see {readme_link}).')
    print("</p>")


if __name__ == "__main__":
    main()
