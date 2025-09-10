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


def find_readme_lines(tool):
    """Find line numbers for the relevant section in README.md."""
    try:
        content = Path("README.md").read_text()
        lines = content.splitlines()

        if tool == "mdcmd":
            # 1. "<!-- `bmdf seq 3` -->" through first subsequent "```"
            for i, line in enumerate(lines, 1):
                if "<!-- `bmdf seq 3` -->" in line:
                    start = i
                    # Find first subsequent ```
                    for j in range(i+1, len(lines)+1):
                        if j > len(lines):
                            break
                        if lines[j-1] == "```":
                            return (start, j)
                    break

        elif tool in ["toc", "mktoc"]:
            # 2. "<!-- `toc` -->" until (exclusive) first subsequent empty line
            for i, line in enumerate(lines, 1):
                if "<!-- `toc` -->" in line:
                    start = i
                    # Find first subsequent empty line
                    for j in range(i+1, len(lines)+1):
                        if j > len(lines):
                            return (start, j-1)  # End of file
                        if not lines[j-1].strip():
                            return (start, j-1)  # Line before empty line
                    break

    except:
        pass
    return None


def main():
    """Generate the update notes."""
    import os

    if len(sys.argv) < 2:
        print("Usage: print-ci-yml-ref.py {mdcmd|toc}", file=sys.stderr)
        sys.exit(1)

    tool = sys.argv[1]
    lines = find_step_lines()
    readme_lines = find_readme_lines(tool)

    # When publishing to PyPI, we need absolute URLs since PyPI doesn't resolve
    # relative GitHub paths. This requires being on a tag to ensure stable URLs.
    if os.getenv("README_ABSOLUTE_URLS"):
        import subprocess
        try:
            result = subprocess.run(
                ["git", "describe", "--exact-match", "--tags", "HEAD"],
                capture_output=True,
                text=True,
                check=True
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
        # Use the plain view with line numbers for PyPI too
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

    if tool == "mdcmd" and "mdcmd" in lines:
        start, end = lines["mdcmd"]
        print("<p>\n")
        print(f'☝️ This block is updated programmatically by [`mdcmd`] (and verified [in CI]({ci_path}#L{start}-L{end}); see {readme_link}).')
        print("</p>")
    elif tool in ["mktoc", "toc"] and "mktoc" in lines:
        start, end = lines["mktoc"]
        print("<p>\n")
        print(f'☝️ This TOC is generated programmatically by [`mdcmd`] and [`toc`] (and verified [in CI]({ci_path}#L{start}-L{end}); see {readme_link}).')
        print("</p>")
    else:
        print(f"Unknown tool or not found: {tool}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
