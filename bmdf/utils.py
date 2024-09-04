from contextlib import contextmanager
from typing import Callable

Log = Callable[..., None]


@contextmanager
def fence(typ: str = None, log: Log = print):
    log(f'```{typ or ""}')
    yield
    log('```')


@contextmanager
def details(summary: str = None, code: str = None, log: Log = print):
    if summary:
        if code:
            raise ValueError(f'Pass `summary` xor `code`')
        log(f'<details><summary>{summary}</summary>')
    else:
        log(f'<details><summary><code>{code}</code></summary>')
    log()
    yield
    log('</details>')


COPY_BINARIES = [ 'pbcopy', 'xclip', 'clip', ]


