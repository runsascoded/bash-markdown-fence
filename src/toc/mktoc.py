from __future__ import annotations

import sys
from os import environ as env
from os.path import exists
from typing import Optional

from click import argument, command, option, UsageError, Context

from bmdf.utils import amend_opt, inplace_opt, no_cwd_tmpdir_opt

DEFAULT_FILE_ENV_VAR = 'MKTOC_DEFAULT_PATH'
DEFAULT_FILE = 'README.md'

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

    This is a convenience wrapper around ``mdcmd -x '^toc$'``.

    Looks for ``<!-- `toc` -->`` markers and replaces the content after them with a generated TOC.

    If no ``out_path`` is provided, will operate "in-place" on ``README.md`` (as if ``mktoc -i README.md`` was passed).
    """
    # Import mdcmd.cli locally to avoid circular imports
    from mdcmd.cli import main as mdcmd_main

    if not path:
        path = env.get(DEFAULT_FILE_ENV_VAR, DEFAULT_FILE)
        if inplace is None:
            inplace = True

    # Don't check exists() here - let mdcmd handle it
    # This allows for proper error messages and handling in different directories

    # Build mdcmd arguments
    args = ['-x', '^toc$']
    if amend:
        args.append('-a')
    if inplace:
        args.append('-i')
    if no_cwd_tmpdir:
        args.append('-T')
    args.append(path)
    if out_path:
        args.append(out_path)

    # Note: indent_size is currently ignored since the toc command
    # in bmdf.toc uses its own default of 4 spaces

    # Call mdcmd with the appropriate arguments
    mdcmd_main(args, standalone_mode=False)


if __name__ == '__main__':
    main()
