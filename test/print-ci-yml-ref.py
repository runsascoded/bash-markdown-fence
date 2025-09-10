#!/usr/bin/env python3
"""Generate the 'updated programmatically' notes with correct CI links."""

import sys
from pathlib import Path

def find_step_lines(ci_path=".github/workflows/ci.yml"):
    """Find line numbers for mdcmd and mktoc CI steps."""
    content = Path(ci_path).read_text()
    lines = content.splitlines()

    results = {}
    steps = {
        "mdcmd": "Verify README examples are up to date",
        "mktoc": "Verify README TOC is up to date"
    }

    for key, name in steps.items():
        for i, line in enumerate(lines, 1):
            if f"name: {name}" in line:
                # Start from the name: line itself
                start = i
                # Find the end of this step (next step or end of job)
                end = start
                for j in range(i+1, len(lines)+1):
                    if j > len(lines):
                        break
                    line_j = lines[j-1]
                    # Stop at next step
                    if line_j.strip().startswith('- name:'):
                        break
                    # Stop at next job or end of file
                    if line_j.strip() and not line_j.startswith('    '):
                        break
                    # Update end to include content lines
                    if line_j.strip():
                        end = j
                results[key] = (start, end)
                break

    return results


def main():
    """Generate the update notes."""
    import os

    if len(sys.argv) < 2:
        print("Usage: print-ci-yml-ref.py {mdcmd|toc}", file=sys.stderr)
        sys.exit(1)

    tool = sys.argv[1]
    lines = find_step_lines()

    # Check env var for absolute URLs (for PyPI builds)
    if os.getenv("BMDF_ABSOLUTE_URLS"):
        # Check if we're on a tag
        import subprocess
        try:
            result = subprocess.run(
                ["git", "describe", "--exact-match", "--tags", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            tag = result.stdout.strip()
            ref = tag if tag else "main"
        except subprocess.CalledProcessError:
            ref = "main"

        base_url = f"https://github.com/runsascoded/bash-markdown-fence/blob/{ref}"
        ci_path = f"{base_url}/.github/workflows/ci.yml"
    else:
        # Use relative URLs by default
        ci_path = ".github/workflows/ci.yml"

    if tool == "mdcmd" and "mdcmd" in lines:
        start, end = lines["mdcmd"]
        print("<p>\n")
        print(f'☝️ This block is updated programmatically (by [`mdcmd`]), and verified [in CI]({ci_path}#L{start}-L{end}).')
        print("</p>")
    elif tool == "mktoc" and "mktoc" in lines:
        start, end = lines["mktoc"]
        print("<p>\n")
        print(f'☝️ This TOC is generated programmatically (by [`mdcmd`] and [`toc`]), and verified [in CI]({ci_path}#L{start}-L{end}).')
        print("</p>")
    else:
        print(f"Unknown tool or not found: {tool}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
