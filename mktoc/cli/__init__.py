import re
import sys
from os.path import exists

import click
from click import UsageError

RGX = r'(?P<level>#{2,}) (?P<title>.*) <a id="(?P<id>[^"]+)"></a>'
DEFAULT_FILE = 'README.md'

TOC_START = '<!-- toc -->\n'
TOC_END = '<!-- /toc -->\n'

@click.command("mktoc")
@click.option('-i', '--in-place', 'inplace', is_flag=True, help="Edit the file in-place")
@click.option('-n', '--indent-size', type=int, default=4, help="Indent size (spaces)")
@click.argument('file', required=False)
def main(inplace, indent_size, file):
    """Build a table of contents from a markdown file."""
    if not file:
        file = DEFAULT_FILE
        if not exists(file):
            raise UsageError(f'No file provided, and {DEFAULT_FILE} not found')

    with open(file, 'r') as f:
        lines = f.readlines()

    def write_toc(lines, f):
        for line in lines:
            line = line.rstrip('\n')
            m = re.fullmatch(RGX, line)
            if not m:
                continue
            level, title, id = len(m['level']), m['title'], m['id']
            indent = ' ' * (indent_size * (level - 2))
            # Flatten links in header titles (for TOC)
            title = re.sub(r'\[([^]]+)](?:\([^)]+\))?', r'\1', title)
            f.write(f'{indent}- [{title}](#{id})\n')

    if inplace:
        with open(file, 'w') as f:
            lines_iter = iter(lines)

            def scan(find: str, name: str, write: bool = False):
                for line in lines_iter:
                    if write:
                        f.write(line)
                    if line == find:
                        return
                marker = find.rstrip('\n')
                raise RuntimeError(f"Couldn't find {name} marker: {marker}")

            scan(TOC_START, 'TOC_START', write=True)
            scan(TOC_END, 'TOC_END')

            rest = list(lines_iter)
            write_toc(rest, f)

            f.write(TOC_END)
            for line in rest:
                f.write(line)
    else:
        write_toc(lines, sys.stdout)


if __name__ == '__main__':
    main()
