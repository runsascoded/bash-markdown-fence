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

    # Run mdcmd with BMDF_ABSOLUTE_URLS=1 to regenerate all content with absolute URLs
    print("Regenerating README content with absolute URLs...")
    try:
        env = os.environ.copy()
        env['BMDF_ABSOLUTE_URLS'] = '1'

        # Install package in editable mode first so mdcmd is available
        install_result = subprocess.run(
            ["python", "-m", "pip", "install", "-e", "."],
            capture_output=True,
            text=True,
            check=False  # Don't fail if this doesn't work
        )

        # Try to run mdcmd
        result = subprocess.run(
            ["python", "-m", "mdcmd.cli", "-i", "README.md"],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        print("Successfully updated README with absolute URLs")
    except subprocess.CalledProcessError as e:
        print(f"Failed to update README: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        # Continue with build even if this fails


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
