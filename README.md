# `bmdf`
**B**ash **m**ark**d**own **f**ences: embed commands, their output, and tables of contents in markdown 

![](https://img.shields.io/pypi/v/bmdf?label=bmdf&color=blue)

<a id="toc"></a>
<!-- toc -->
- [Install](#install)
- [Usage](#usage)
    - [`bmdf`: embed `bash` commands in README](#bmdf)
    - [`mdcmd`: update command output](#mdcmd)
    - [`bmdfff`: &lt;details&gt; mode](#bmdfff)
    - [`mktoc`: update table of contents](#mktoc)
    - [Reference](#reference)
- [Examples](#examples)
<!-- /toc -->

This package provides 3 CLIs:
- `bmd`: run commands, wrap output in Markdown fences
- `mdcmd`: update Markdown files with command outputs
- `mktoc`: update Markdown table of contents (with custom "id" anchors)

## Install <a id="install"></a>
```bash
pip install bmdf
```

## Usage <a id="usage"></a>

### `bmdf`: embed `bash` commands in README <a id="bmdf"></a>

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
  ```
  ```
  ````

then run…

### `mdcmd`: update command output <a id="mdcmd"></a>

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

### `bmdfff`: &lt;details&gt; mode <a id="bmdfff"></a>

In some cases, it's preferable to render the command as a `<details><summary>`, with the output hidden by default.

`bmdfff` (3 `f`s, alias for `bmd -fff`) achieves this; a markdown section like this:

````
  <!-- `bmdfff seq 10` -->
  ```
  ```
````

gets replaced with this:

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
# Usage: bmd [OPTIONS] [COMMAND]...
#
#   Format a command and its output to markdown, either in a `bash`-fence or
#   <details> block, and copy it to the clipboard.
#
# Options:
#   -C, --no-copy  Disable copying output to clipboard (normally uses first
#                  available executable from ['pbcopy', 'xclip', 'clip']
#   -f, --fence    Pass 0-3x to configure output style: 0x: print output lines,
#                  prepended by "# "; 1x: print a "```bash" fence block
#                  including the <command> and commented output lines; 2x: print
#                  a bash-fenced command followed by plain-fenced output lines;
#                  3x: print a <details/> block, with command <summary/> and
#                  collapsed output lines in a plain fence.
#   --help         Show this message and exit.
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
#   -i, --inplace / -I, --no-inplace
#                                   Update the file in place
#   --help                          Show this message and exit.
```

<!-- `bmdf -- mktoc --help` -->
```bash
mktoc --help
# Usage: mktoc [OPTIONS] [PATH] [OUT_PATH]
#
#   Build a table of contents from a markdown file.
#
#   If no path is provided, will look for a README.md, and operate "in-place"
#   (same as ``mdcmd -i README.md``).
#
# Options:
#   -i, --inplace / -I, --no-inplace
#                                   Edit the file in-place
#   -n, --indent-size INTEGER       Indent size (spaces)
#   --help                          Show this message and exit.
```
(these blocks are self-hosted, using `bmdf` and `mdcmd`; likewise [the table of contents up top](#toc), via `mktoc` 😎)

## Examples <a id="examples"></a>
- [runsascoded/utz]
- [TileDB-Inc/scverse-ml-workshop-2024]


[runsascoded/utz]: https://github.com/runsascoded/utz?tab=readme-ov-file#utz
[TileDB-Inc/scverse-ml-workshop-2024]: https://github.com/TileDB-Inc/scverse-ml-workshop-2024?tab=readme-ov-file#training-models-on-atlas-scale-single-cell-datasets
