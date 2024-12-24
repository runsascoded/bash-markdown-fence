import re
from contextlib import contextmanager
from typing import Callable

from click import option
from utz import check, process, err

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


amend_opt = option('-a', '--amend', is_flag=True, help="Squash changes onto the previous Git commit; suitable for use with `git rebase -x`")
inplace_opt = option('-i/-I', '--inplace/--no-inplace', is_flag=True, default=None, help="Edit the file in-place")
no_cwd_tmpdir_opt = option('-T', '--no-cwd-tmpdir', is_flag=True, help="In in-place mode, use a system temporary-directory (instead of the current workdir, which is the default)")


def amend_check(amend: bool):
    if amend:
        if not check('git', 'diff', '--quiet', 'HEAD'):
            raise RuntimeError("Require clean Git worktree for `-a/--amend`")


def amend_run(amend: bool) -> None:
    if amend:
        if not check('git', 'diff', '--quiet', 'HEAD'):
            err("Squashing changes onto HEAD")
            process.run('git', 'commit', '-a', '--amend', '--no-edit')
        else:
            err("No changes found")


def strip_ansi(text):
    return re.sub(r'\x1b\[[^m]*m|\x1b\[\d*[ABCDEFGJKST]', '', text)
