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
        args=['--help'],
        )
    eq(out.getvalue(), """\
usage: troops [-h] {deploy} ...

Software deployment tool

optional arguments:
  -h, --help  show this help message and exit

commands:
  {deploy}
    deploy    Run the latest deployment script
""")


@fudge.patch('sys.stdout', 'sys.stderr', 'sys.exit')
def test_no_args(fake_stdout, fake_stderr, fake_exit):
    err = StringIO()
    fake_stderr.expects('write').calls(err.write)
    fake_exit.expects_call().with_args(2).raises(FakeExit)
    assert_raises(
        FakeExit,
        main,
        args=[],
        )
    eq(err.getvalue(), """\
usage: troops [-h] {deploy} ...
troops: error: too few arguments
""")

@fudge.patch('sys.stdout', 'sys.stderr', 'sys.exit')
def test_bad_args(fake_stdout, fake_stderr, fake_exit):
    err = StringIO()
    fake_stderr.expects('write').calls(err.write)
    fake_exit.expects_call().with_args(2).raises(FakeExit)
    assert_raises(
        FakeExit,
        main,
        args=['bork'],
        )
    eq(err.getvalue(), """\
usage: troops [-h] {deploy} ...
troops: error: invalid choice: 'bork' (choose from 'deploy')
""")
