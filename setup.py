from utz.setup import setup

setup(
    name="bmdf",
    version="0.1.0",
    entry_points={
        "console_scripts": [
            "bmd = bmdf.cli:bmd",
            "bmdf = bmdf.cli:bmd_f",
            "bmdff = bmdf.cli:bmd_ff",
            "bmdfff = bmdf.cli:bmd_fff",
            "mdcmd = mdcmd.cli:main",
            "mktoc = mktoc.cli:main",
        ]
    },
    url="https://github.com/runsascoded/bash-markdown-fence",
)
