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
    got = out.getvalue()
    eq(got, """\
usage: troops [-h] COMMAND ...

Software deployment tool

optional arguments:
  -h, --help  show this help message and exit

commands:
  COMMAND
    pull      Fetch and deploy any changes in remote repositories
    deploy    Run the latest deployment script
    merge     Deploy any changes in remote branches
""",
       'Unexpected output:\n'+got)


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
    got = err.getvalue()
    eq(got, """\
usage: troops [-h] COMMAND ...
troops: error: too few arguments
""",
       'Unexpected output:\n'+got)


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
    got = err.getvalue()
    eq(got, """\
usage: troops [-h] COMMAND ...
troops: error: argument COMMAND: invalid choice: 'bork' (choose from 'pull', 'merge', 'deploy')
""",
       'Unexpected output:\n'+got)
