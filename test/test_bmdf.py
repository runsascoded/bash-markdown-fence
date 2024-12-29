from io import StringIO

from bmdf.cli import bmd

import pytest
parametrize = pytest.mark.parametrize


@parametrize(
    "args,envs,opts,expected",
    [
        (['echo', r'\$FOO=$FOO'], ['FOO=bar'], dict(shell=True), "# $FOO=bar\n"),
        (['echo', r'\$FOO=$FOO'], ['FOO=bar'], dict(shell=False), "# \\$FOO=$FOO\n"),
        (['seq', '10', '|', 'wc', '-l'], [], dict(shell=True), "# 10\n"),
        (['seq', '10', '|', 'wc', '-l'], [], dict(shell=False), "# 10\n"),
        (['seq', '10', '|', '$WC', '-l'], ['WC=wc'], dict(shell=True), "# 10\n"),
    ],
)
def test_env_vars(args, envs, opts, expected):
    file = StringIO()
    bmd.callback(
        args,
        env_strs=envs,
        **opts,
        file=file,
    )
    assert file.getvalue() == expected
