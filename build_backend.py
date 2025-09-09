"""Custom build backend that processes README before packaging."""

import os
from pathlib import Path
from setuptools import build_meta as _orig

# Re-export all the standard hooks
get_requires_for_build_wheel = _orig.get_requires_for_build_wheel
get_requires_for_build_sdist = _orig.get_requires_for_build_sdist
prepare_metadata_for_build_wheel = _orig.prepare_metadata_for_build_wheel
prepare_metadata_for_build_editable = _orig.prepare_metadata_for_build_editable
build_editable = _orig.build_editable


def _process_readme():
    """Process README.md to use absolute URLs for PyPI builds."""
    import subprocess
    import re

    # Check if we're on a tag
    try:
        result = subprocess.run(
            ["git", "describe", "--exact-match", "--tags", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        tag = result.stdout.strip()
        if not tag:
            print("Not on a tag, skipping README processing")
            return
        print(f"Building from tag: {tag}")
    except subprocess.CalledProcessError:
        # Not on a tag
        print("Not on a tag, skipping README processing")
        return

    # Read current README
    readme_path = Path("README.md")
    if not readme_path.exists():
        return

    content = readme_path.read_text()

    # Use the tag in the URL
    base_url = f"https://github.com/runsascoded/bash-markdown-fence/blob/{tag}"

    # Replace relative .github/workflows/ci.yml links
    pattern = r'\[in CI\]\(\.github/workflows/ci\.yml(#L\d+-L\d+)\)'
    replacement = rf'[in CI]({base_url}/.github/workflows/ci.yml\1)'

    new_content = re.sub(pattern, replacement, content)

    if new_content != content:
        print(f"Updated README with absolute URLs for tag {tag}")
        readme_path.write_text(new_content)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """Build wheel with processed README."""
    original_readme = Path("README.md").read_text() if Path("README.md").exists() else None

    try:
        _process_readme()
        return _orig.build_wheel(wheel_directory, config_settings, metadata_directory)
    finally:
        # Restore original README
        if original_readme is not None:
            Path("README.md").write_text(original_readme)


def build_sdist(sdist_directory, config_settings=None):
    """Build sdist with processed README."""
    original_readme = Path("README.md").read_text() if Path("README.md").exists() else None

    try:
        _process_readme()
        return _orig.build_sdist(sdist_directory, config_settings)
    finally:
        # Restore original README
        if original_readme is not None:
            Path("README.md").write_text(original_readme)
