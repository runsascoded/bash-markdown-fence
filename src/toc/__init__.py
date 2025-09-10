#!/usr/bin/env python3
"""Generate a table of contents for a markdown file."""

import re
import sys
from pathlib import Path

import click
from click import command, option, argument


def generate_toc(content: str, indent_size: int = 4) -> str:
    """Generate TOC from markdown content, matching mktoc's behavior."""
    lines = []
    content_lines = content.splitlines()

    # Regex patterns from mktoc
    TITLE_ID = r'(?P<title>.*) <a id="(?P<id>[^"]+)"></a>'
    MD_RGX = re.compile(r'(?P<level>#{2,}) ' + TITLE_ID)
    HTML_RGX = re.compile(r'<(?P<tag>h\d)>')
    TITLE_ID_RGX = re.compile(TITLE_ID)

    i = 0
    while i < len(content_lines):
        line = content_lines[i]

        # Check for markdown headers with <a id="..."></a>
        if m := MD_RGX.fullmatch(line):
            level = len(m['level'])
            title = m['title']
            id = m['id']
        # Check for HTML headers (e.g., <h2>)
        elif m := HTML_RGX.fullmatch(line):
            level = int(m['tag'][1])
            # Next line should have the title and id
            if i + 2 < len(content_lines):
                body = content_lines[i + 1]
                close = content_lines[i + 2]
                tag = m['tag']
                if (m2 := TITLE_ID_RGX.fullmatch(body)) and close == f'</{tag}>':
                    title = m2['title']
                    id = m2['id']
                    i += 2  # Skip the body and closing tag
                else:
                    i += 1
                    continue
            else:
                i += 1
                continue
        else:
            i += 1
            continue

        # Remove markdown links but keep link text
        title = re.sub(r'\[([^]]+)](?:\([^)]+\))?', r'\1', title)

        # Calculate indentation (level 2 headers have no indent)
        indent = ' ' * (indent_size * (level - 2))
        lines.append(f'{indent}- [{title}](#{id})')
        i += 1

    return '\n'.join(lines)


@command()
@option('-n', '--indent-size', type=int, default=4, help="Indent size (spaces)")
@argument('path', required=False, type=click.Path(exists=True))
def main(
    indent_size: int = 4,
    path: str = None,
):
    """Generate a table of contents from a markdown file.

    If no PATH is provided, will try to use $MDCMD_FILE (set by mdcmd),
    or default to README.md if that's not set.
    """
    import os

    if path:
        # Explicit path provided
        path_obj = Path(path)
    elif mdcmd_file := os.environ.get('MDCMD_FILE'):
        # Use the file being processed by mdcmd
        path_obj = Path(mdcmd_file)
    else:
        # Default to README.md
        path_obj = Path('README.md')

    if path_obj.exists():
        content = path_obj.read_text()
    else:
        content = sys.stdin.read()

    toc = generate_toc(content, indent_size=indent_size)
    print(toc)


if __name__ == '__main__':
    main()
