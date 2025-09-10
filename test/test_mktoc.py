"""Test mktoc CLI wrapper functionality."""
from os.path import join
from tempfile import TemporaryDirectory
from textwrap import dedent

import pytest
from click.testing import CliRunner
from utz import cd

from toc.mktoc import main as mktoc_main
from test.utils import ROOT


def test_mktoc_wrapper():
    """Test that mktoc works as a wrapper around mdcmd."""
    with cd(ROOT):
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            # Create a test markdown file with TOC markers
            input_md = dedent("""
                # Test Document

                <!-- `toc` -->

                ## First Section <a id="first"></a>
                Content here.

                ## Second Section <a id="second"></a>
                More content.
            """).strip()

            in_path = join(tmpdir, 'test.md')
            out_path = join(tmpdir, 'test_out.md')

            with open(in_path, 'w') as f:
                f.write(input_md)

            # Run mktoc
            res = runner.invoke(mktoc_main, [in_path, out_path])
            assert res.exit_code == 0

            with open(out_path, 'r') as f:
                output = f.read()

            # Check that the TOC was inserted
            assert '- [First Section](#first)' in output
            assert '- [Second Section](#second)' in output


def test_mktoc_inplace():
    """Test mktoc in-place editing."""
    with cd(ROOT):
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            input_md = dedent("""
                # Test Document

                <!-- `toc` -->

                ## Section A <a id="a"></a>
                Content.

                ## Section B <a id="b"></a>
                More content.
            """).strip()

            test_path = join(tmpdir, 'test.md')

            with open(test_path, 'w') as f:
                f.write(input_md)

            # Run mktoc in-place
            res = runner.invoke(mktoc_main, ['-i', test_path])
            assert res.exit_code == 0

            with open(test_path, 'r') as f:
                output = f.read()

            # Check that the file was updated in-place
            assert '- [Section A](#a)' in output
            assert '- [Section B](#b)' in output


@pytest.mark.skip(reason="CliRunner changes working directory in complex ways")
def test_mktoc_default_readme():
    """Test mktoc with no arguments defaults to README.md."""
    with cd(ROOT):
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            with cd(tmpdir):
                # Create a README.md in the temp directory
                input_md = dedent("""
                    # README

                    <!-- `toc` -->

                    ## Installation <a id="install"></a>
                    Instructions here.

                    ## Usage <a id="usage"></a>
                    How to use.
                """).strip()

                with open('README.md', 'w') as f:
                    f.write(input_md)

                # Run mktoc with no arguments
                res = runner.invoke(mktoc_main, [])
                assert res.exit_code == 0

                with open('README.md', 'r') as f:
                    output = f.read()

                # Check that README.md was updated
                assert '- [Installation](#install)' in output
                assert '- [Usage](#usage)' in output


def test_mktoc_with_existing_toc():
    """Test mktoc replacing an existing TOC."""
    with cd(ROOT):
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            input_md = dedent("""
                # Document

                <!-- `toc` -->
                - [Old Section](#old)
                - [Outdated](#outdated)

                ## New Section <a id="new"></a>
                Content.

                ## Updated Section <a id="updated"></a>
                More content.
            """).strip()

            in_path = join(tmpdir, 'test.md')
            out_path = join(tmpdir, 'test_out.md')

            with open(in_path, 'w') as f:
                f.write(input_md)

            res = runner.invoke(mktoc_main, [in_path, out_path])
            assert res.exit_code == 0

            with open(out_path, 'r') as f:
                output = f.read()

            # Check that old TOC was replaced
            assert '[Old Section](#old)' not in output
            assert '[Outdated](#outdated)' not in output
            # New TOC should be present
            assert '- [New Section](#new)' in output
            assert '- [Updated Section](#updated)' in output