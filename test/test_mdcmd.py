from os.path import join, relpath
from tempfile import TemporaryDirectory

from click.testing import CliRunner
from utz import cd

from mdcmd.cli import main
from test.utils import DATA, ROOT


def test_mdcmd():
    with cd(ROOT):
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            in_path = join(DATA, 'README.md')
            out_path = join(tmpdir, 'README.md')
            res = runner.invoke(main, [in_path, out_path])
            assert res.exit_code == 0
            with (
                open(in_path, 'r', encoding='utf-8') as in_fd,
                open(out_path, 'r', encoding='utf-8') as out_fd,
            ):
                assert in_fd.read() == out_fd.read()
