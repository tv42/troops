import fudge

from nose.tools import eq_ as eq, assert_raises
from cStringIO import StringIO

from troops.cli.main import main


class FakeExit(Exception):
    pass


@fudge.patch('sys.stdout', 'sys.stderr', 'sys.exit')
def test_help(fake_stdout, fake_stderr, fake_exit):
    out = StringIO()
    fake_stdout.expects('write').calls(out.write)
    fake_exit.expects_call().with_args(0).raises(FakeExit)
    assert_raises(
        FakeExit,
        main,
        args=['deploy', '--help'],
        )
    eq(out.getvalue(), """\
usage: troops deploy [-h]

Run the latest deployment script

optional arguments:
  -h, --help  show this help message and exit
""")
