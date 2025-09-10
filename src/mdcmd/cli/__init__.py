from __future__ import annotations

import asyncio
from asyncio import gather
import re
import shlex
from contextlib import contextmanager
from functools import partial
from os import environ as env, rename, getcwd
from os.path import basename, exists, join
from tempfile import TemporaryDirectory
from typing import Any, Callable, Generator, Optional

import mistune
from click import command, option, argument
from utz import err, Patterns, proc
from utz.cli import inc_exc, multi

from bmdf.utils import amend_opt, amend_check, amend_run, inplace_opt, no_cwd_tmpdir_opt

CMD_LINE_RGX = re.compile(r'<!-- `(?P<cmd>.+)` -->')
Write = Callable[[str], None]

DEFAULT_FILE_ENV_VAR = 'MDCMD_DEFAULT_PATH'
DEFAULT_FILE = 'README.md'


def render_token(token):
    """Render a single token back to markdown."""
    t_type = token.get('type')

    if t_type == 'heading':
        level = token['attrs']['level']
        text = ''.join(render_inline(child) for child in token.get('children', []))
        return f"{'#' * level} {text}"
    elif t_type == 'paragraph':
        text = ''.join(render_inline(child) for child in token.get('children', []))
        return text
    elif t_type == 'blank_line':
        return ''
    elif t_type == 'block_code':
        marker = token.get('marker', '```')
        info = token.get('attrs', {}).get('info', '')
        code = token['raw'].rstrip('\n')
        return f"{marker}{info}\n{code}\n{marker}"
    elif t_type == 'block_html':
        return token['raw'].rstrip('\n')
    elif t_type == 'list':
        return render_list(token, 0)
    elif t_type == 'block_quote':
        text = ''.join(render_inline(child) for child in token.get('children', []))
        lines = text.split('\n')
        return '\n'.join(f"> {line}" if line else ">" for line in lines)
    elif t_type == 'thematic_break':
        return '---'
    else:
        # Fallback
        return str(token)


def render_inline(token):
    """Render inline tokens."""
    t_type = token.get('type')

    if t_type == 'text':
        return token.get('raw', '')
    elif t_type == 'emphasis':
        text = ''.join(render_inline(child) for child in token.get('children', []))
        return f"*{text}*"
    elif t_type == 'strong':
        text = ''.join(render_inline(child) for child in token.get('children', []))
        return f"**{text}**"
    elif t_type == 'link':
        text = ''.join(render_inline(child) for child in token.get('children', []))
        # Check if this is a reference link
        if 'label' in token:
            # Reference link - preserve the reference style
            label = token['label']
            return f"[{text}][{label}]" if text != label else f"[{text}]"
        else:
            # Inline link
            url = token['attrs']['url']
            return f"[{text}]({url})"
    elif t_type == 'image':
        url = token['attrs']['url']
        alt = token['attrs'].get('alt', '')
        return f"![{alt}]({url})"
    elif t_type == 'codespan':
        return f"`{token['raw']}`"
    elif t_type == 'inline_html':
        return token['raw']
    elif t_type == 'linebreak':
        return '  \n'
    elif t_type == 'softbreak':
        return '\n'
    else:
        return token.get('raw', '')


def render_list(token, depth):
    """Render list tokens."""
    lines = []
    attrs = token.get('attrs', {})
    ordered = attrs.get('ordered', False)
    start = attrs.get('start', 1)
    bullet = token.get('bullet', '-')
    indent = '    ' * depth

    for i, item in enumerate(token.get('children', [])):
        if item['type'] != 'list_item':
            continue

        if ordered:
            marker = f"{start + i}."
        else:
            marker = bullet

        # First, render the list item's own content
        for child in item.get('children', []):
            if child['type'] == 'block_text':
                text = ''.join(render_inline(c) for c in child.get('children', []))
                lines.append(f"{indent}{marker} {text}")
                break

        # Then render any sublists
        for child in item.get('children', []):
            if child['type'] == 'list':
                sublist = render_list(child, depth + 1)
                lines.append(sublist)

    return '\n'.join(lines)


async def async_text(cmd: str | list[str], env: dict | None = None) -> str:
    text = await proc.aio.text(cmd, env=env)
    return text.rstrip('\n')


def find_block_end(tokens: list[dict], start_idx: int, cmd_str: str = None) -> int:
    """Find the end index of a block following an mdcmd comment."""
    if start_idx >= len(tokens):
        return start_idx

    # Special handling for toc command
    if cmd_str and cmd_str.strip() == 'toc':
        # Look for <!-- /toc --> marker
        for i in range(start_idx, len(tokens)):
            if tokens[i].get('type') == 'block_html' and '<!-- /toc -->' in tokens[i].get('raw', ''):
                # Include the closing marker so it gets replaced
                return i + 1
        # If no closing marker found, just replace until next non-list element
        i = start_idx
        while i < len(tokens) and tokens[i].get('type') in ['list', 'blank_line']:
            i += 1
        return i

    first_token = tokens[start_idx]
    token_type = first_token.get('type')

    # Empty output - just a blank line
    if token_type == 'blank_line':
        return start_idx + 1

    # Single block elements
    if token_type in ['block_code', 'list', 'paragraph']:
        return start_idx + 1

    # HTML blocks need special handling
    if token_type == 'block_html':
        raw = first_token.get('raw', '')

        # Check for multi-part HTML structures
        if '<div' in raw:
            # Find matching </div>
            for i in range(start_idx, len(tokens)):
                if tokens[i].get('type') == 'block_html' and '</div>' in tokens[i].get('raw', ''):
                    return i + 1
        elif '<details>' in raw:
            # Find matching </details>
            for i in range(start_idx, len(tokens)):
                if tokens[i].get('type') == 'block_html' and '</details>' in tokens[i].get('raw', ''):
                    return i + 1
        elif '<table>' in raw:
            # Find matching </table>
            for i in range(start_idx, len(tokens)):
                if tokens[i].get('type') == 'block_html' and '</table>' in tokens[i].get('raw', ''):
                    return i + 1
        elif '<p>' in raw:
            # Find matching </p>
            for i in range(start_idx, len(tokens)):
                if tokens[i].get('type') == 'block_html' and '</p>' in tokens[i].get('raw', ''):
                    return i + 1

        # Single HTML block
        return start_idx + 1

    # Unknown - don't replace anything
    return start_idx


async def process_path(
    path: str,
    dry_run: bool,
    patterns: Patterns,
    write_fn: Write,
    concurrent: bool = True,
):
    with open(path, 'r') as fd:
        content = fd.read()

    # Parse to AST
    md = mistune.create_markdown(renderer=None)
    parsed = md.parse(content)
    token_list = list(parsed[0]) if parsed else []
    state = parsed[1] if len(parsed) > 1 else None

    # Find mdcmd commands
    commands = []
    i = 0
    while i < len(token_list):
        token = token_list[i]

        if token.get('type') == 'block_html':
            raw = token.get('raw', '')
            if match := CMD_LINE_RGX.search(raw):
                cmd_str = match.group('cmd')

                if patterns and not patterns(cmd_str):
                    i += 1
                    continue

                if dry_run:
                    err(f"Would run: {cmd_str}")
                    i += 1
                    continue

                # Find range to replace
                start_idx = i + 1
                end_idx = find_block_end(token_list, start_idx, cmd_str)

                commands.append({
                    'cmd_str': cmd_str,
                    'cmd': shlex.split(cmd_str),
                    'comment_idx': i,
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                })

        i += 1

    # Execute commands
    if commands:
        import os
        cmd_env = os.environ.copy()
        cmd_env['MDCMD_FILE'] = path

        if concurrent:
            outputs = await gather(*[
                async_text(cmd['cmd'], env=cmd_env)
                for cmd in commands
            ])
        else:
            outputs = []
            for cmd in commands:
                output = await async_text(cmd['cmd'], env=cmd_env)
                outputs.append(output)

        # Replace tokens in reverse order to maintain indices
        for cmd_info, output in zip(reversed(commands), reversed(outputs)):
            # Handle empty output
            if not output.strip():
                output_tokens = [{'type': 'blank_line'}]
            else:
                # Parse output based on command type
                cmd_name = cmd_info['cmd'][0] if cmd_info['cmd'] else ''

                # Special handling for certain commands
                if cmd_name in ['bmdf', 'bmdff', 'bmdfff']:
                    # These already produce markdown-formatted output
                    output_tokens = md.parse(output)[0] if md.parse(output) else []
                elif cmd_name == 'toc':
                    # TOC produces a list, need to add closing marker
                    output_tokens = md.parse(output)[0] if md.parse(output) else []
                    # Add the closing marker
                    output_tokens.append({'type': 'block_html', 'raw': '<!-- /toc -->\n'})
                else:
                    # Generic output - try to parse as markdown
                    parsed = md.parse(output)
                    if parsed and parsed[0]:
                        output_tokens = list(parsed[0])
                    else:
                        # Fallback to HTML block
                        output_tokens = [{'type': 'block_html', 'raw': output}]

            # Replace the tokens
            del token_list[cmd_info['start_idx']:cmd_info['end_idx']]
            for j, token in enumerate(output_tokens):
                token_list.insert(cmd_info['start_idx'] + j, token)

    # Render back to markdown
    lines = []

    for i, token in enumerate(token_list):
        rendered = render_token(token)

        if token.get('type') == 'blank_line':
            # Only add blank line if not at the very end
            if i < len(token_list) - 1:
                lines.append('')
        else:
            lines.append(rendered)

    # Join lines
    result = '\n'.join(lines)

    # Add reference link definitions at the end if they exist
    if state and hasattr(state, 'env') and 'ref_links' in state.env:
        ref_links = []
        for ref_data in state.env['ref_links'].values():
            label = ref_data.get('label', '')
            url = ref_data.get('url', '')
            title = ref_data.get('title')
            if title:
                ref_links.append(f"[{label}]: {url} \"{title}\"")
            else:
                ref_links.append(f"[{label}]: {url}")
        if ref_links:
            result += '\n\n' + '\n'.join(ref_links)

    # write_fn (print) will add the final newline
    write_fn(result)


@contextmanager
def out_fd(
    inplace: bool,
    path: str,
    out_path: Optional[str],
    dir: Optional[str] = None,
) -> Generator[Write, None, None]:
    if inplace:
        if out_path:
            raise ValueError('Cannot specify both --inplace and an output path')
        with TemporaryDirectory(dir=dir) as tmpdir:
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
@amend_opt
@option('-C', '--no-concurrent', is_flag=True, help='Run commands in sequence (by default, they are run concurrently)')
@inplace_opt
@option('-n', '--dry-run', is_flag=True, help="Print the commands that would be run, but don't execute them")
@no_cwd_tmpdir_opt
@inc_exc(
    multi('-x', '--execute', help='Only execute commands that match these regular expressions'),
    multi('-X', '--exclude', help="Only execute commands that don't match these regular expressions"),
)
@argument('path', required=False)
@argument('out_path', required=False)
def main(
    amend: bool,
    no_concurrent: bool,
    inplace: Optional[bool],
    dry_run: bool,
    no_cwd_tmpdir: bool,
    patterns: Patterns,
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

    amend_check(amend)

    tmpdir = None if no_cwd_tmpdir else getcwd()
    with out_fd(inplace, path, out_path, dir=tmpdir) as write:
        asyncio.run(
            process_path(
                path=path,
                dry_run=dry_run,
                patterns=patterns,
                write_fn=write,
                concurrent=not no_concurrent,
            )
        )

    amend_run(amend)


if __name__ == '__main__':
    main()
