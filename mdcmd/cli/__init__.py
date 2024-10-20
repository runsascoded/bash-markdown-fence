import re
import shlex
from contextlib import contextmanager
from fileinput import close
from functools import partial
from os import environ as env, rename
from os.path import basename, join, exists
from tempfile import TemporaryDirectory
from typing import Generator, Callable, Optional

from click import command, option, argument
from utz import process

RGX = re.compile(r'<!-- `(?P<cmd>[^`]+)` -->')
Write = Callable[[str], None]

DEFAULT_FILE_ENV_VAR = 'MDCMD_DEFAULT_PATH'
DEFAULT_FILE = 'README.md'

def process_path(
    path: str,
    write: Write,
):
    with open(path, 'r') as lines:
        lines = map(lambda line: line.rstrip('\n'), lines)
        for line in lines:
            write(line)
            m = RGX.match(line)
            if m:
                cmd = shlex.split(m.group('cmd'))
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

                while close_lines:
                    close = close_lines.pop(0)
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
@option('-i/-I', '--inplace/--no-inplace', is_flag=True, default=None, help='Update the file in place')
@argument('path', required=False)
@argument('out_path', required=False)
def main(
    inplace: Optional[bool],
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

    with out_fd(inplace, path, out_path) as out:
        process_path(path, out)


if __name__ == '__main__':
    main()
