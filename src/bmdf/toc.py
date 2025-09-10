#!/usr/bin/env python3
"""Generate a table of contents for a markdown file."""

import re
import sys
from pathlib import Path


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


def main():
    """Read markdown and output TOC."""
    import os
    
    if len(sys.argv) > 1:
        # Explicit path provided
        path = Path(sys.argv[1])
    elif mdcmd_file := os.environ.get('MDCMD_FILE'):
        # Use the file being processed by mdcmd
        path = Path(mdcmd_file)
    else:
        # Default to README.md
        path = Path('README.md')
    
    if path.exists():
        content = path.read_text()
    else:
        content = sys.stdin.read()
    
    toc = generate_toc(content)
    print(toc)


if __name__ == '__main__':
    main()