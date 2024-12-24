from __future__ import annotations

import re
from os import environ as env, getcwd
from os.path import exists
from typing import Optional

from click import argument, command, option, UsageError

from bmdf.utils import amend_opt, amend_check, amend_run, inplace_opt, no_cwd_tmpdir_opt
from mdcmd.cli import out_fd, Write

RGX = r'(?P<level>#{2,}) (?P<title>.*) <a id="(?P<id>[^"]+)"></a>'
DEFAULT_FILE_ENV_VAR = 'MKTOC_DEFAULT_PATH'
DEFAULT_FILE = 'README.md'

TOC_START = '<!-- toc -->'
TOC_END = '<!-- /toc -->'

@command("mktoc")
@amend_opt
@inplace_opt
@option('-n', '--indent-size', type=int, default=4, help="Indent size (spaces)")
@no_cwd_tmpdir_opt
@argument('path', required=False)
@argument('out_path', required=False)
def main(
    amend: bool,
    inplace: Optional[bool],
    indent_size: int,
    no_cwd_tmpdir: bool,
    path: Optional[str],
    out_path: Optional[str],
):
    """Insert a table of contents (TOC) in a markdown file.

    Looks for a pair of sentinel lines to insert or update the TOC between: ``<!-- toc -->``, ``<!-- /toc -->``.

    If an empty line follows the opening ``<!-- toc -->`` line, the TOC will be inserted there (along with the closing
    sentinel); this is useful when initially generating a TOC.

    If no ``out_path`` is provided, will operate "in-place" on ``README.md`` (as if ``mktoc -i README.md`` was passed).
    """
    if not path:
        path = env.get(DEFAULT_FILE_ENV_VAR, DEFAULT_FILE)
        if inplace is None:
            inplace = True

    if not exists(path):
        raise UsageError(f'{path} not found')

    amend_check(amend)

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

    tmpdir = None if no_cwd_tmpdir else getcwd()
    with out_fd(inplace, path, out_path, dir=tmpdir) as out:
        lines_iter = iter(lines)

        def scan(markers: str | list[str], name: str, write: bool = False):
            if isinstance(markers, str):
                markers = [markers]
            for line in lines_iter:
                if write:
                    out(line)
                if line in markers:
                    return line
            raise RuntimeError(f"Couldn't find {name} markers: {markers}")

        scan(TOC_START, 'TOC_START', write=True)
        end_line = scan(['', TOC_END], 'TOC_END')

        rest = list(lines_iter)
        write_toc(rest, out)

        out(TOC_END)
        if not end_line:
            out('')

        for line in rest:
            out(line)

    amend_run(amend)


if __name__ == '__main__':
    main()
