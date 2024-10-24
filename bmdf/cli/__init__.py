from os import environ as env
import shlex
import sys
from subprocess import PIPE, Popen, CalledProcessError
from typing import Optional, Tuple

from click import argument, command, option, get_current_context, echo
from utz import process

from bmdf.utils import COPY_BINARIES, details, fence

BMDF_ERR_FMT_VAR = 'BMDF_ERR_FMT'
BMDF_ERR_FMT = env.get(BMDF_ERR_FMT_VAR)
BMDF_ERR_FMT_HELP_STR = f' ("{BMDF_ERR_FMT}")' if BMDF_ERR_FMT else ''


@command("fence", no_args_is_help=True)
@option('-C', '--no-copy', is_flag=True, help=f'Disable copying output to clipboard (normally uses first available executable from {COPY_BINARIES}')
@option('-e', '--error-fmt', default=BMDF_ERR_FMT, help=f'If the wrapped command exits non-zero, append a line of output formatted with this string. One "%d" placeholder may be used, for the returncode. Defaults to ${BMDF_ERR_FMT_VAR}{BMDF_ERR_FMT_HELP_STR}')
@option('-f', '--fence', 'fence_level', count=True, help='Pass 0-3x to configure output style: 0x: print output lines, prepended by "# "; 1x: print a "```bash" fence block including the <command> and commented output lines; 2x: print a bash-fenced command followed by plain-fenced output lines; 3x: print a <details/> block, with command <summary/> and collapsed output lines in a plain fence.')
@argument('command', required=True, nargs=-1)
def bmd(
    no_copy: bool,
    error_fmt: Optional[str],
    fence_level: int,
    command: Tuple[str, ...],
):
    """Format a command and its output to markdown, either in a `bash`-fence or <details> block, and copy it to the clipboard."""
    if not command:
        ctx = get_current_context()
        echo(ctx.get_help())
        ctx.exit()

    if command[0] == 'time':
        # Without `-p`, `time`'s output is not POSIX-compliant, doesn't get parsed properly
        if len(command) > 1 and not command[1].startswith('-'):
            command = [ command[0], '-p', *command[1:] ]

    try:
        output = process.output(*command, log=None, both=True)
        returncode = 0
    except CalledProcessError as e:
        output = e.output
        returncode = e.returncode

    lines = [
        line.rstrip('\n')
        for line in
        output.decode().split('\n')
    ]
    if lines and not lines[-1]:
        lines = lines[:-1]
    if returncode and error_fmt:
        try:
            error_line = error_fmt % returncode
        except TypeError:
            error_line = error_fmt
        lines.append(error_line)

    cmd_str = shlex.join(command)

    out_lines = []

    def log(line=''):
        out_lines.append(line)

    def print_commented_lines():
        for line in lines:
            log(f'# {line}' if line else '#')

    def print_fenced_lines():
        with fence(log=log):
            for line in lines:
                log(line)

    if not fence_level:
        print_commented_lines()
    elif fence_level == 1:
        with fence('bash', log=log):
            log(cmd_str)
            print_commented_lines()
    elif fence_level == 2:
        with fence('bash', log=log):
            log(cmd_str)
        print_fenced_lines()
    elif fence_level == 3:
        with details(code=cmd_str, log=log):
            print_fenced_lines()
    else:
        raise ValueError(f"Pass -f/--fence at most 3x")

    output = '\n'.join(out_lines)
    if not no_copy:
        copy_cmd = None
        for cmd in COPY_BINARIES:
            if process.check('which', cmd, log=None):
                copy_cmd = cmd
                break
        if copy_cmd:
            p = Popen([copy_cmd], stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
            p.communicate(input=output)
    print(output)


def bmd_f():
    sys.argv.insert(1, '-f')
    bmd()


def bmd_ff():
    sys.argv.insert(1, '-ff')
    bmd()


def bmd_fff():
    sys.argv.insert(1, '-fff')
    bmd()


if __name__ == '__main__':
    bmd()
