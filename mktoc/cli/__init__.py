import re
from os import environ as env
from os.path import exists
from typing import Optional

from click import argument, command, option, UsageError

from mdcmd.cli import out_fd, Write

RGX = r'(?P<level>#{2,}) (?P<title>.*) <a id="(?P<id>[^"]+)"></a>'
DEFAULT_FILE_ENV_VAR = 'MKTOC_DEFAULT_PATH'
DEFAULT_FILE = 'README.md'

TOC_START = '<!-- toc -->'
TOC_END = '<!-- /toc -->'

@command("mktoc")
@option('-i/-I', '--inplace/--no-inplace', is_flag=True, default=None, help="Edit the file in-place")
@option('-n', '--indent-size', type=int, default=4, help="Indent size (spaces)")
@argument('path', required=False)
@argument('out_path', required=False)
def main(
    inplace: Optional[bool],
    indent_size: int,
    path: Optional[str],
    out_path: Optional[str],
):
    """Build a table of contents from a markdown file.

    If no path is provided, will look for a README.md, and operate "in-place" (same as ``mdcmd -i README.md``).
    """
    if not path:
        path = env.get(DEFAULT_FILE_ENV_VAR, DEFAULT_FILE)
        if inplace is None:
            inplace = True

    if not exists(path):
        raise UsageError(f'{path} not found')

    with open(path, 'r') as f:
        lines = [ line.rstrip('\n') for line in f.readlines() ]

    def write_toc(lines: list[str], out: Write):
        for line in lines:
            m = re.fullmatch(RGX, line)
            if not m:
                continue
            level, title, id = len(m['level']), m['title'], m['id']
            indent = ' ' * (indent_size * (level - 2))
            # Flatten links in header titles (for TOC)
            title = re.sub(r'\[([^]]+)](?:\([^)]+\))?', r'\1', title)
            out(f'{indent}- [{title}](#{id})')

    with out_fd(inplace, path, out_path) as out:
        lines_iter = iter(lines)

        def scan(marker: str, name: str, write: bool = False):
            for line in lines_iter:
                if write:
                    out(line)
                if line == marker:
                    return
            raise RuntimeError(f"Couldn't find {name} marker: {marker}")

        scan(TOC_START, 'TOC_START', write=True)
        scan(TOC_END, 'TOC_END')

        rest = list(lines_iter)
        write_toc(rest, out)

        out(TOC_END)
        for line in rest:
            out(line)


if __name__ == '__main__':
    main()
