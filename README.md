# `bmdf`
**B**ash **m**ark**d**own **f**encing

![](https://img.shields.io/pypi/v/bmdf?label=bmdf&color=blue)

This package provides 2 CLIs:
- `bmd`: run commands, wrap output in Markdown fences
- `mdcmd`: update Markdown files with command outputs

## Install
```bash
pip install bmdf
```

## Example
Suppose you want to embed a command and its output in a README.md, like this:

<!-- `bmdf seq 3` -->
```bash
seq 3
# 1
# 2
# 3
```

(the command is `bash`-highlighted, output lines are comments).

Put a placeholder like this in your README.md:
  ````
  <!-- `bmdf seq 3` -->
  ```
  ```
  ````

Then run:
```bash
mdcmd -i README.md
```

The placeholder block will now contain `seq 3` and its output; that's how first block above is rendered!

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

and running `mdcmd -i README.md` again will rewrite the same content.

Note: `bmdf` (alias for `bmd -f`) is used because it wraps the output of whatever it's passed in a "Bash fence" block. You don't have to use it, but most commands will fail to output a Markdown "fence" block, and subsequent `mdcmd` invocations will fail to parse them.

### `bmdfff`: &lt;details&gt; mode

`bmdfff` (3 `f`s, alias for `bmd -fff`) wraps output in a &lt;details&gt; tag:

````
  <!-- `bmdfff seq 10` -->
  ```
  ```
````

Live example:

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

## Reference

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

<!-- `bmdf mdcmd` -->
```bash
mdcmd
# Usage: mdcmd [OPTIONS] PATH [OUT_PATH]
#
#   Parse a Markdown file, updating blocks preceded by <!-- `[cmd...]` -->
#   delimiters
#
# Options:
#   -i, --inplace  Update the file in place
#   --help         Show this message and exit.
```

(these blocks are self-hosted, using `bmdf` and `mdcmd` 😎)
