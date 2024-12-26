# `bmdf`
**B**ash **m**ark**d**own **f**ences: embed commands, their output, and tables of contents in markdown

[![](https://img.shields.io/pypi/v/bmdf?label=bmdf&color=blue)][bmdf]

<a id="toc"></a>
<!-- toc -->
- [Install](#install)
- [Usage](#usage)
    - [`bmd`: format `bash` command and output as Markdown](#bmd)
        - [`bmdf` (`bmd -f`): command+output mode](#bmdf)
        - [`bmdff` (`bmd -ff`): two-fence mode](#bmdff)
        - [`bmdfff` (`bmd -fff`): &lt;details&gt; mode](#bmdfff)
        - [Piping](#piping)
        - [Env vars](#env-vars)
    - [`mdcmd`: update commands embedded in Markdown files](#mdcmd)
    - [`mktoc`: update table of contents](#mktoc)
    - [Reference](#reference)
- [Examples](#examples)
<!-- /toc -->

This package provides 3 CLIs:
- `bmd`: run Bash commands, wrap output for Markdown embedding
  - [`bmdf`](#bmdf), [`bmdff`](#bmdff), [`bmdfff`](#bmdfff): different levels of "fencing" for command output
- `mdcmd`: find `bmd` blocks in Markdown files, execute commands, update Markdown files with output
- `mktoc`: update Markdown table of contents (with custom "id" anchors)

## Install <a id="install"></a>
```bash
pip install bmdf
```

## Usage <a id="usage"></a>

### `bmd`: format `bash` command and output as Markdown <a id="bmd"></a>

`bmd` (and aliases [`bmdf`](#bmdf), [`bmdff`](#bmdff), [`bmdfff`](#bmdfff)) takes a `bash` command as input, and renders the command and/or its output in various Markdown-friendly formats:

#### `bmdf` (`bmd -f`): command+output mode <a id="bmdf"></a>

Suppose you want to embed a command and its output in a README.md, like this:

<!-- `bmdf seq 3` -->
```bash
seq 3
# 1
# 2
# 3
```

(Note how the command is `bash`-highlighted, and output lines are rendered as comments)

Put a placeholder like this in your README.md:
  ````
  <!-- `bmdf seq 3` -->
  ````

then [run `mdcmd`](#mdcmd) to update your README containing this embedded command block.

#### `bmdff` (`bmd -ff`): two-fence mode <a id="bmdff"></a>
`bmdff` (alias for `bmd -ff`) renders two code fences, one with the Bash command (syntax-highlighted appropriately), and a second (non-highlighted) block with the output, e.g.:

  ````
  <!-- `bmdff seq 5` -->
  ````

becomes:

<!-- `bmdff seq 5` -->
```bash
seq 5
```
```
1
2
3
4
5
```

#### `bmdfff` (`bmd -fff`): &lt;details&gt; mode <a id="bmdfff"></a>

When a command's output is large, rendering it as a `<details><summary>` (with the output collapsed, by default) may be preferable.

`bmdfff` (3 `f`s, alias for `bmd -fff`) transforms placeholders like this:

  ````
  <!-- `bmdfff seq 10` -->
  ````

to:

<!-- `bmdfff seq 10` -->
<details><summary><code>seq 10</code></summary>

```
1
2
3
4
5
6
7
8
9
10
```
</details>

#### Piping <a id="piping"></a>
Piping works too, e.g.:

  ````
  <!-- `bmdf -- seq 10 | wc -l` -->
  ````

will become:

<!-- `bmdf -- seq 10 | wc -l` -->
```bash
seq 10 | wc -l
# 10
```

(the `--` is needed so that that `-l` isn't parsed as an opt to `bmdf`)

#### Env vars <a id="env-vars"></a>
By default, `shell=True` is passed to `subprocess` calls (but can be disabled via `-S`).

This means env vars are expanded; they can also be set via `-E`, e.g.:

  ````
  <!-- `bmdf -E FOO=bar echo $FOO` -->
  ````

yields:
<!-- `bmdf -E FOO=bar echo $FOO` -->
```bash
FOO=bar echo '$FOO'
# bar
```

<details>
<summary>
More examples of quoting/splitting behavior
</summary>

Quoting `"$FOO"`:
  ````
  <!-- `bmdf -E FOO=bar echo "$FOO"` -->
  ````

yields:
<!-- `bmdf -E FOO=bar echo "$FOO"` -->
```bash
FOO=bar echo '$FOO'
# bar
```

Arg with spaces:
  ````
  <!-- `bmdf -E FOO=bar echo "FOO: $FOO"` -->
  ````
yields:
<!-- `bmdf -E FOO=bar echo "FOO: $FOO"` -->
```bash
FOO=bar echo 'FOO: $FOO'
# FOO: bar
```

Escaping `$`:
  ````
  <!-- `bmdf -E FOO=bar echo "\$FOO=$FOO"` -->
  ````
yields:
<!-- `bmdf -E FOO=bar echo "\$FOO=$FOO"` -->
```bash
FOO=bar echo '\$FOO=$FOO'
# $FOO=bar
```

</details>

### `mdcmd`: update commands embedded in Markdown files <a id="mdcmd"></a>

```bash
# Modify README.md in-place
mdcmd -i README.md
# Same as above; no args defaults to `-i README.md`
mdcmd
```

The placeholder block above will now contain `seq 3` and its output; that's how first block above is rendered!

The full README.md block will now look like:
  ````
  <!-- `bmdf seq 3` -->
  ```bash
  seq 3
  # 1
  # 2
  # 3
  ```
  ````

and running `mdcmd` again will rewrite the same content.

Note: `bmdf` (alias for `bmd -f`) is used because it wraps the output of whatever it's passed in a "Bash fence" block. You don't have to use it, but most commands will fail to output a Markdown "fence" block, and subsequent `mdcmd` invocations will fail to parse them.

### `mktoc`: update table of contents <a id="mktoc"></a>
Put a block like this in your README.md:
````
<!-- toc -->
<!-- /toc -->
````

Then put empty `<a>` tags next to the headings you want to include, e.g.:

 ```markdown
 ## My section heading <a id="my-section"></a>
 ```

(This allows for customizing and shortening the `id`s, as well as skipping sections)

Then run:
```bash
# Modify README.md in-place
mktoc -i README.md
# Same as above; no args defaults to `-i README.md`
mktoc
```

And the `<!-- toc  -->` section will have a table of contents injected (like the one at the top of this file).

### Reference <a id="reference"></a>

<!-- `bmdf bmd` -->
```bash
bmd
# Usage: bmd [OPTIONS] COMMAND...
#
#   Format a command and its output to markdown, either in a `bash`-fence or
#   <details> block, and copy it to the clipboard.
#
# Options:
#   -C, --no-copy                Disable copying output to clipboard (normally
#                                uses first available executable from ['pbcopy',
#                                'xclip', 'clip']
#   -e, --error-fmt TEXT         If the wrapped command exits non-zero, append a
#                                line of output formatted with this string. One
#                                "%d" placeholder may be used, for the
#                                returncode. Defaults to $BMDF_ERR_FMT
#   -E, --env TEXT               k=v env vars to set, for the wrapped command
#   -f, --fence                  Pass 0-3x to configure output style: 0x: print
#                                output lines, prepended by "# "; 1x: print a
#                                "```bash" fence block including the <command>
#                                and commented output lines; 2x: print a bash-
#                                fenced command followed by plain-fenced output
#                                lines; 3x: print a <details/> block, with
#                                command <summary/> and collapsed output lines
#                                in a plain fence.
#   -s, --strip-ansi             Strip ANSI escape sequences from output
#   -S, --no-shell               Disable "shell" mode for the command
#   -t, --fence-type TEXT        When -f/--fence is 2 or 3, this customizes the
#                                fence syntax type that the output is wrapped in
#   -x, --shell-executable TEXT  `shell_executable` to pass to Popen pipelines
#                                (default: $SHELL)
#   --help                       Show this message and exit.
```

<!-- `bmdf -- mdcmd --help` -->
```bash
mdcmd --help
# Usage: mdcmd [OPTIONS] [PATH] [OUT_PATH]
#
#   Parse a Markdown file, updating blocks preceded by <!-- `[cmd...]` -->
#   delimiters.
#
#   If no paths are provided, will look for a README.md, and operate "in-place"
#   (same as ``mdcmd -i README.md``).
#
# Options:
#   -a, --amend                     Squash changes onto the previous Git commit;
#                                   suitable for use with `git rebase -x`
#   -i, --inplace / -I, --no-inplace
#                                   Edit the file in-place
#   -n, --dry-run                   Print the commands that would be run, but
#                                   don't execute them
#   -T, --no-cwd-tmpdir             In in-place mode, use a system temporary-
#                                   directory (instead of the current workdir,
#                                   which is the default)
#   -x, --execute TEXT              Only execute commands that match these
#                                   regular expressions
#   -X, --exclude TEXT              Only execute commands that don't match these
#                                   regular expressions
#   --help                          Show this message and exit.
```

<!-- `bmdf -- mktoc --help` -->
```bash
mktoc --help
# Usage: mktoc [OPTIONS] [PATH] [OUT_PATH]
#
#   Insert a table of contents (TOC) in a markdown file.
#
#   Looks for a pair of sentinel lines to insert or update the TOC between:
#   ``<!-- toc -->``, ``<!-- /toc -->``.
#
#   If an empty line follows the opening ``<!-- toc -->`` line, the TOC will be
#   inserted there (along with the closing sentinel); this is useful when
#   initially generating a TOC.
#
#   If no ``out_path`` is provided, will operate "in-place" on ``README.md`` (as
#   if ``mktoc -i README.md`` was passed).
#
# Options:
#   -a, --amend                     Squash changes onto the previous Git commit;
#                                   suitable for use with `git rebase -x`
#   -i, --inplace / -I, --no-inplace
#                                   Edit the file in-place
#   -n, --indent-size INTEGER       Indent size (spaces)
#   -T, --no-cwd-tmpdir             In in-place mode, use a system temporary-
#                                   directory (instead of the current workdir,
#                                   which is the default)
#   --help                          Show this message and exit.
```

(these blocks are self-hosted, using `bmdf` and `mdcmd`; likewise [the table of contents up top](#toc), via `mktoc` 😎)

## Examples <a id="examples"></a>
These repos' READMEs use `bmdf` / `mdcmd` / `mktoc` to execute README examples (and in some cases are verified by GitHub Actions):

- [runsascoded/juq]
- [runsascoded/utz]
- [runsascoded/dvc-utils]
- [ryan-williams/dvc-helpers] ([GHA][dvc-helpers GHA])
- [ryan-williams/git-helpers]
- [ryan-williams/parquet-helpers] ([GHA][pqt-helpers GHA])
- [ryan-williams/tdbs-dask]
- [TileDB-Inc/scverse-ml-workshop-2024]

[runsascoded/utz]: https://github.com/runsascoded/utz?tab=readme-ov-file#utz
[TileDB-Inc/scverse-ml-workshop-2024]: https://github.com/TileDB-Inc/scverse-ml-workshop-2024?tab=readme-ov-file#training-models-on-atlas-scale-single-cell-datasets
[ryan-williams/tdbs-dask]: https://github.com/ryan-williams/tdbs-dask?tab=readme-ov-file#tdbs-dask
[ryan-williams/dvc-helpers]: https://github.com/ryan-williams/dvc-helpers?tab=readme-ov-file#dvc-helpers
[dvc-helpers GHA]: https://github.com/ryan-williams/dvc-helpers/actions
[ryan-williams/git-helpers]: https://github.com/ryan-williams/git-helpers?tab=readme-ov-file#git-helpers
[ryan-williams/parquet-helpers]: https://github.com/ryan-williams/parquet-helpers
[pqt-helpers GHA]: https://github.com/ryan-williams/parquet-helpers/actions/
[runsascoded/dvc-utils]: https://github.com/runsascoded/dvc-utils
[runsascoded/juq]: https://github.com/runsascoded/juq

[bmdf]: https://pypi.org/project/bmdf/
