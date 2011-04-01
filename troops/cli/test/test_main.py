import fudge

from nose.tools import eq_ as eq
from cStringIO import StringIO

from troops.cli.main import main
from troops.test.util import assert_raises

@fudge.patch('sys.stdout', 'sys.stderr')
def test_help(fake_stdout, fake_stderr):
    out = StringIO()
    fake_stdout.expects('write').calls(out.write)
    e = assert_raises(
        SystemExit,
        main,
        args=['--help'],
        )
    eq(e.code, 0)
    eq(out.getvalue(), """\
usage: troops [-h] {deploy} ...

Software deployment tool

optional arguments:
  -h, --help  show this help message and exit

commands:
  {deploy}
    deploy    Run the latest deployment script
""")


@fudge.patch('sys.stdout', 'sys.stderr')
def test_no_args(fake_stdout, fake_stderr):
    err = StringIO()
    fake_stderr.expects('write').calls(err.write)
    e = assert_raises(
        SystemExit,
        main,
        args=[],
        )
    eq(e.code, 2)
    eq(err.getvalue(), """\
usage: troops [-h] {deploy} ...
troops: error: too few arguments
""")


@fudge.patch('sys.stdout', 'sys.stderr')
def test_bad_args(fake_stdout, fake_stderr):
    err = StringIO()
    fake_stderr.expects('write').calls(err.write)
    e = assert_raises(
        SystemExit,
        main,
        args=['bork'],
        )
    eq(e.code, 2)
    eq(err.getvalue(), """\
usage: troops [-h] {deploy} ...
troops: error: invalid choice: 'bork' (choose from 'deploy')
""")
