"""Test mdcmd handling of markdown list blocks."""
from os.path import join
from tempfile import TemporaryDirectory
from textwrap import dedent

from click.testing import CliRunner
from utz import cd

from mdcmd.cli import main
from test.utils import ROOT


def test_toc_command_list_block():
    """Test that TOC command works with markdown list block detection."""
    with cd(ROOT):
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            # Create a test markdown file with TOC markers
            input_md = dedent("""
                # Test Document
                
                <a id="toc"></a>
                <!-- `toc` -->
                - Old TOC entry 1
                - Old TOC entry 2
                    - Old nested entry
                <!-- /toc -->
                
                ## Section One <a id="section1"></a>
                Content here.
                
                ## Section Two <a id="section2"></a>
                More content.
                
                ### Subsection <a id="subsection"></a>
                Nested content.
            """).strip()
            
            in_path = join(tmpdir, 'test_toc.md')
            out_path = join(tmpdir, 'test_toc_out.md')
            
            with open(in_path, 'w') as f:
                f.write(input_md)
            
            # Run mdcmd to update the TOC
            res = runner.invoke(main, [in_path, out_path])
            assert res.exit_code == 0
            
            with open(out_path, 'r') as f:
                output = f.read()
            
            # Check that the TOC was updated correctly
            assert '- [Section One](#section1)' in output
            assert '- [Section Two](#section2)' in output
            assert '  - [Subsection](#subsection)' in output  # 2-space indent is default
            # Old entries should be gone
            assert 'Old TOC entry' not in output
            assert 'Old nested entry' not in output


def test_markdown_list_block_detection():
    """Test that commands producing markdown lists are handled correctly."""
    with cd(ROOT):
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            # Create a test markdown file with a command that outputs a list
            input_md = dedent("""
                # List Generation Test
                
                <!-- `printf -- "- Item 1\\n- Item 2\\n    - Subitem\\n- Item 3"` -->
                - Old list item
                - Should be replaced
                    - Including nested items
                
                Regular paragraph content here.
                
                <!-- `echo "Not a list"` -->
                
                More regular content.
            """).strip()
            
            in_path = join(tmpdir, 'test_list.md')
            out_path = join(tmpdir, 'test_list_out.md')
            
            with open(in_path, 'w') as f:
                f.write(input_md)
            
            res = runner.invoke(main, [in_path, out_path])
            assert res.exit_code == 0
            
            with open(out_path, 'r') as f:
                output = f.read()
            
            # Check that the list was replaced
            assert '- Item 1' in output
            assert '- Item 2' in output
            assert '    - Subitem' in output
            assert '- Item 3' in output
            # Old list should be gone
            assert 'Old list item' not in output
            assert 'Should be replaced' not in output
            
            # Non-list command should work with empty block
            assert 'Not a list' in output


def test_list_block_edge_cases():
    """Test edge cases in markdown list block detection."""
    with cd(ROOT):
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            # Test various list formats and edge cases
            input_md = dedent("""
                # Edge Cases
                
                <!-- `printf -- "- Single item"` -->
                - Old single item
                
                <!-- `printf -- "- Item with\\n  continuation\\n- Next item"` -->
                - Old item
                  with continuation
                - Old next item
                
                <!-- `printf -- "- Item 1\\n\\n- Item 2 after blank"` -->
                - Old item 1
                
                - Old item 2
                
                Regular content.
            """).strip()
            
            in_path = join(tmpdir, 'test_edges.md')
            out_path = join(tmpdir, 'test_edges_out.md')
            
            with open(in_path, 'w') as f:
                f.write(input_md)
            
            res = runner.invoke(main, [in_path, out_path])
            assert res.exit_code == 0
            
            with open(out_path, 'r') as f:
                output = f.read()
            
            # Check single item list
            assert '- Single item' in output
            assert 'Old single item' not in output
            
            # Check list with continuation lines
            assert '- Item with\n  continuation' in output
            assert '- Next item' in output
            
            # Check list with blank line (should stop at blank)
            assert '- Item 1' in output
            # The blank line stops the list block detection
            assert '- Item 2 after blank' in output


def test_empty_list_block():
    """Test handling of commands that produce empty output in list context."""
    with cd(ROOT):
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            input_md = dedent("""
                # Empty List Test
                
                <!-- `true` -->
                - Old list item
                - Should be replaced with empty
                
                Content after list.
            """).strip()
            
            in_path = join(tmpdir, 'test_empty.md')
            out_path = join(tmpdir, 'test_empty_out.md')
            
            with open(in_path, 'w') as f:
                f.write(input_md)
            
            res = runner.invoke(main, [in_path, out_path])
            assert res.exit_code == 0
            
            with open(out_path, 'r') as f:
                output = f.read()
            
            # Old list should be gone, replaced with empty output
            assert 'Old list item' not in output
            assert 'Should be replaced' not in output
            # Should have empty line after command
            assert '<!-- `true` -->\n\n\nContent after list' in output


def test_nested_list_indentation():
    """Test that various indentation levels in lists are handled correctly."""
    with cd(ROOT):
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            input_md = dedent("""
                # Nested List Test
                
                <!-- `printf -- "- Level 1\\n  - Level 2 (2 spaces)\\n    - Level 3 (4 spaces)\\n      - Level 4 (6 spaces)"` -->
                - Old content
                
                End of test.
            """).strip()
            
            in_path = join(tmpdir, 'test_nested.md')
            out_path = join(tmpdir, 'test_nested_out.md')
            
            with open(in_path, 'w') as f:
                f.write(input_md)
            
            res = runner.invoke(main, [in_path, out_path])
            assert res.exit_code == 0
            
            with open(out_path, 'r') as f:
                output = f.read()
            
            # Check that all indentation levels are preserved
            assert '- Level 1' in output
            assert '  - Level 2 (2 spaces)' in output
            assert '    - Level 3 (4 spaces)' in output
            assert '      - Level 4 (6 spaces)' in output
            assert 'Old content' not in output