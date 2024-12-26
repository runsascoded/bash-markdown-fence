import shlex
import sys
from os import environ as env
from subprocess import PIPE, Popen, CalledProcessError
from typing import Optional, Tuple

from click import argument, command, option, get_current_context, echo
from utz import proc
from utz.process import pipeline

from bmdf import utils
from bmdf.utils import COPY_BINARIES, details, fence

BMDF_ERR_FMT_VAR = 'BMDF_ERR_FMT'
BMDF_ERR_FMT = env.get(BMDF_ERR_FMT_VAR)
BMDF_ERR_FMT_HELP_STR = f' ("{BMDF_ERR_FMT}")' if BMDF_ERR_FMT else ''


@command("fence", no_args_is_help=True)
@option('-C', '--no-copy', is_flag=True, help=f'Disable copying output to clipboard (normally uses first available executable from {COPY_BINARIES}')
@option('-e', '--error-fmt', default=BMDF_ERR_FMT, help=f'If the wrapped command exits non-zero, append a line of output formatted with this string. One "%d" placeholder may be used, for the returncode. Defaults to ${BMDF_ERR_FMT_VAR}{BMDF_ERR_FMT_HELP_STR}')
@option('-E', '--env', 'env_strs', multiple=True, help="k=v env vars to set, for the wrapped command")
@option('-f', '--fence', 'fence_level', count=True, help='Pass 0-3x to configure output style: 0x: print output lines, prepended by "# "; 1x: print a "```bash" fence block including the <command> and commented output lines; 2x: print a bash-fenced command followed by plain-fenced output lines; 3x: print a <details/> block, with command <summary/> and collapsed output lines in a plain fence.')
@option('-s', '--strip-ansi', is_flag=True, help='Strip ANSI escape sequences from output')
@option('-S', '--no-shell', is_flag=True, help='Disable "shell" mode for the command')
@option('-t', '--fence-type', help="When -f/--fence is 2 or 3, this customizes the fence syntax type that the output is wrapped in")
@option('-x', '--shell-executable', help="`shell_executable` to pass to Popen pipelines (default: $SHELL)")
@argument('command', required=True, nargs=-1)
def bmd(
    no_copy: bool,
    error_fmt: Optional[str],
    env_strs: Tuple[str, ...],
    fence_level: int,
    strip_ansi: bool,
    no_shell: bool,
    fence_type: Optional[str],
    shell_executable: Optional[str],
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

    commands: list[list[str]] = []
    start_idx = 0
    for idx, arg in enumerate(command):
        if arg == "|":
            cmd = command[start_idx:idx]
            commands.append(cmd)
            start_idx = idx + 1
    if start_idx < len(command):
        commands.append(command[start_idx:])

    if shell_executable is None:
        shell_executable = env.get('SHELL')

    env_opts = dict(
        kv.split('=', 1)
        for kv in env_strs
    )
    proc_env = {
        **env,
        **env_opts,
    }
    try:
        shell = not no_shell
        if len(commands) == 1:
            args = [' '.join(command)] if shell else commands
            output = proc.output(*args, log=None, both=True, env=proc_env, shell=shell).decode()
            returncode = 0
        else:
            cmds = [ ' '.join(cmd) for cmd in commands ] if shell else commands
            output = pipeline(cmds, shell_executable=shell_executable, env=proc_env, shell=shell)
            returncode = 0
    except CalledProcessError as e:
        output = e.output.decode()
        returncode = e.returncode

    lines = [
        line.rstrip('\n')
        for line in
        output.split('\n')
    ]
    if lines and not lines[-1]:
        lines = lines[:-1]
    if returncode and error_fmt:
        try:
            error_line = error_fmt % returncode
        except TypeError:
            error_line = error_fmt
        lines.append(error_line)

    if len(commands) == 1:
        cmd_str = shlex.join(command)
    else:
        cmd_str = " | ".join([ shlex.join(cmd) for cmd in commands ])
    cmd_str = " ".join([
        *[
            f'"{env_str}"' if ' ' in env_str else env_str
            for env_str in env_strs
        ],
        cmd_str,
    ])

    out_lines = []

    def log(line=''):
        out_lines.append(utils.strip_ansi(line) if strip_ansi else line)

    def print_commented_lines():
        for line in lines:
            log(f'# {line}' if line else '#')

    def print_fenced_lines(typ: str = None):
        with fence(typ=typ, log=log):
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
        print_fenced_lines(typ=fence_type)
    elif fence_level == 3:
        with details(code=cmd_str, log=log):
            print_fenced_lines(typ=fence_type)
    else:
        raise ValueError(f"Pass -f/--fence at most 3x")

    output = '\n'.join(out_lines)
    if not no_copy:
        copy_cmd = None
        for cmd in COPY_BINARIES:
            if proc.check('which', cmd, log=None):
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
