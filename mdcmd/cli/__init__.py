import re
import shlex
from contextlib import contextmanager
from functools import partial
from os import environ as env, rename
from os.path import basename, join, exists
from tempfile import TemporaryDirectory
from typing import Generator, Callable, Optional, Tuple

from click import command, option, argument
from utz import process, err, check

RGX = re.compile(r'<!-- `(?P<cmd>[^`]+)` -->')
Write = Callable[[str], None]

DEFAULT_FILE_ENV_VAR = 'MDCMD_DEFAULT_PATH'
DEFAULT_FILE = 'README.md'

def process_path(
    path: str,
    dry_run: bool,
    include_rgxs: Tuple[str, ...],
    exclude_rgxs: Tuple[str, ...],
    write: Write,
):
    with open(path, 'r') as fd:
        lines = map(lambda line: line.rstrip('\n'), fd)
        for line in lines:
            write(line)
            if not (m := RGX.match(line)):
                continue

            cmd_str = m.group('cmd')
            if include_rgxs:
                if not any(re.search(rgx, cmd_str) for rgx in include_rgxs):
                    continue
            if exclude_rgxs:
                if any(re.search(rgx, cmd_str) for rgx in exclude_rgxs):
                    continue

            if dry_run:
                err(f"Would run: {cmd_str}")
                continue

            cmd = shlex.split(cmd_str)
            try:
                line = next(lines)
                if line.startswith("<details>"):
                    close_lines = ["</details>"]
                elif line.startswith("```"):
                    if cmd[0] == "bmdff":
                        close_lines = ["```"] * 3  # Skip two fences
                    else:
                        close_lines = ["```"]
                elif not line:
                    close_lines = None
                else:
                    raise ValueError(f'Unexpected block start line under cmd {cmd}: {line}')
            except StopIteration:
                close_lines = None

            while close_lines:
                close, *close_lines = close_lines
                line = next(lines)
                while line != close:
                    line = next(lines)

            output = process.output(cmd).decode().rstrip('\n')
            write(output)
            if close_lines is None:
                write("")


@contextmanager
def out_fd(
    inplace: bool,
    path: str,
    out_path: Optional[str],
) -> Generator[Write, None, None]:
    if inplace:
        if out_path:
            raise ValueError('Cannot specify both --inplace and an output path')
        with TemporaryDirectory() as tmpdir:
            tmp_path = join(tmpdir, basename(path))
            with open(tmp_path, 'w') as f:
                yield partial(print, file=f)
            rename(tmp_path, path)
    else:
        if not out_path or out_path == '-':
            yield print
        else:
            with open(out_path, 'w') as f:
                yield partial(print, file=f)


@command('mdcmd')
@option('-a', '--amend', is_flag=True, help="Squash changes onto the previous Git commit (can be used with `git rebase -x 'mdcmd -a'`)")
@option('-i/-I', '--inplace/--no-inplace', is_flag=True, default=None, help='Update the file in place')
@option('-n', '--dry-run', is_flag=True, help="Print the commands that would be run, but don't execute them")
@option('-x', '--execute', 'include_rgxs', multiple=True, help='Only execute commands that match these regular expressions')
@option('-X', '--exclude', 'exclude_rgxs', multiple=True, help="Only execute commands that don't match these regular expressions")
@argument('path', required=False)
@argument('out_path', required=False)
def main(
    amend: bool,
    inplace: Optional[bool],
    dry_run: bool,
    include_rgxs: Tuple[str, ...],
    exclude_rgxs: Tuple[str, ...],
    path: str,
    out_path: Optional[str],
):
    """Parse a Markdown file, updating blocks preceded by <!-- `[cmd...]` --> delimiters.

    If no paths are provided, will look for a README.md, and operate "in-place" (same as ``mdcmd -i README.md``).
    """
    if not path:
        path = env.get(DEFAULT_FILE_ENV_VAR, DEFAULT_FILE)
        if not exists(path):
            raise ValueError(f'{path} not found')
        if inplace is None:
            inplace = True

    if amend:
        if not check('git', 'diff', '--quiet', 'HEAD'):
            raise RuntimeError("Require clean Git worktree for `-a/--amend`")

    with out_fd(inplace, path, out_path) as write:
        process_path(
            path=path,
            dry_run=dry_run,
            include_rgxs=include_rgxs,
            exclude_rgxs=exclude_rgxs,
            write=write,
        )

    if amend:
        if not check('git', 'diff', '--quiet', 'HEAD'):
            err("Squashing changes onto HEAD")
            process.run('git', 'commit', '-a', '--amend', '--no-edit')


if __name__ == '__main__':
    main()
