import re
import shlex
from contextlib import contextmanager
from functools import partial
from os import rename
from os.path import basename, join
from tempfile import TemporaryDirectory
from typing import Generator, Callable, Optional

from click import command, option, argument
from utz import process

RGX = re.compile(r'<!-- `(?P<cmd>[^`]+)` -->')
Write = Callable[..., None]


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
                    close = "</details>"
                elif line.startswith("```"):
                    close = "```"
                else:
                    raise ValueError(f'Unexpected block start line under cmd {cmd}: {line}')
                while line != close:
                    line = next(lines)
                output = process.output(cmd).decode().rstrip('\n')
                write(output)


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


@command(no_args_is_help=True)
@option('-i', '--inplace', is_flag=True, help='Update the file in place')
@argument('path')
@argument('out_path', required=False)
def main(
    inplace: bool,
    path: str,
    out_path: Optional[str],
):
    """Parse a Markdown file, updating blocks preceded by <!-- `[cmd...]` --> delimiters"""
    with out_fd(inplace, path, out_path) as out:
        process_path(path, out)


if __name__ == '__main__':
    main()
