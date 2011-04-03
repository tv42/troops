import fudge
import json
import os
import re
import subprocess

from nose.tools import eq_ as eq
from cStringIO import StringIO

from troops.cli.main import main

from troops.test.util import (
    assert_raises,
    fast_import,
    maketemp,
    )

@fudge.patch('sys.stdout', 'sys.stderr')
def test_help(fake_stdout, fake_stderr):
    out = StringIO()
    fake_stdout.expects('write').calls(out.write)
    e = assert_raises(
        SystemExit,
        main,
        args=['merge', '--help'],
        )
    eq(e.code, 0)
    got = out.getvalue()
    eq(got, """\
usage: troops merge [OPTS]

Deploy any changes in remote branches

optional arguments:
  -h, --help        show this help message and exit
  --repository DIR  location of the git repository
  --temp DIR        directory to store temporary files in
""",
       'Unexpected output:\n'+got)


@fudge.patch('sys.stdout', 'sys.stderr')
def test_simple(fake_stdout, fake_stderr):
    tmp = maketemp()
    repo = os.path.join(tmp, 'repo')
    os.mkdir(repo)
    scratch = os.path.join(tmp, 'scratch')
    os.mkdir(scratch)
    flag = os.path.join(tmp, 'flag')
    subprocess.check_call(
        args=[
            'git',
            '--git-dir={0}'.format(repo),
            'init',
            '--quiet',
            '--bare',
            ],
        )
    fast_import(
        repo=repo,
        commits=[
            dict(
                message='Initial import.',
                committer='John Doe <jdoe@example.com>',
                commit_time='1216235872 +0300',
                files=[
                    dict(
                        path='requirements.txt',
                        content="""\
# pip complains if this file is left empty, so say something we know
# is easily accessible
pip
""",
                        ),
                    dict(
                        path='deploy.py',
                        content="""\
import json
import os
print "fakedeploy start"
print json.dumps(dict(cwd=os.getcwd()))
with file(FLAGPATH, "a") as f:
    f.write('xyzzy')
print "fakedeploy end"
""".replace('FLAGPATH', repr(flag)),
                        ),
                    ],
                ),
            dict(
                message='Second commit.',
                committer='Jack Smith <smitty@example.com>',
                commit_time='1216243120 +0300',
                files=[
                    dict(
                        path='deploy.py',
                        content="""\
import json
import os
print "fakedeploy2 start"
print json.dumps(dict(cwd=os.getcwd()))
with file(FLAGPATH, "a") as f:
    f.write('thud')
print "fakedeploy2 end"
""".replace('FLAGPATH', repr(flag)),
                        ),
                    ],
                ),
            ],
        )
    # cause remote to have something new for us
    subprocess.check_call(
        args=[
            'git',
            '--git-dir={0}'.format(repo),
            'update-ref',
            'refs/remotes/origin/master',
            'HEAD',
            ],
        )
    subprocess.check_call(
        args=[
            'git',
            '--git-dir={0}'.format(repo),
            'update-ref',
            'HEAD',
            'HEAD~1',
            ],
        )
    subprocess.check_call(
        args=[
            'git',
            '--git-dir={0}'.format(repo),
            'symbolic-ref',
            'refs/remotes/origin/HEAD',
            'refs/remotes/origin/master',
            ],
        )
    out = StringIO()
    fake_stdout.expects('write').calls(out.write)
    assert not os.path.exists(flag)
    main(
        args=[
            'merge',
            '--repository', repo,
            '--temp', scratch,
            ],
        )
    got = out.getvalue().splitlines()
    eq(got[0], 'fakedeploy2 start')
    eq(got[2], 'fakedeploy2 end')
    eq(got[3:], [])
    got = json.loads(got[1])
    cwd = got.pop('cwd')
    (head, tail) = os.path.split(cwd)
    eq(head, scratch)
    assert re.match(r'^troops-[a-zA-Z0-9_]{6,}$', tail), \
        "Odd cwd for deploy: {path!r}".format(path=cwd)
    eq(got, {})
    assert os.path.exists(flag)
    with file(flag) as f:
        got = f.read()
    eq(got, 'thud')


@fudge.patch('sys.stdout', 'sys.stderr')
def test_uptodate(fake_stdout, fake_stderr):
    tmp = maketemp()
    repo = os.path.join(tmp, 'repo')
    os.mkdir(repo)
    scratch = os.path.join(tmp, 'scratch')
    os.mkdir(scratch)
    flag = os.path.join(tmp, 'flag')
    subprocess.check_call(
        args=[
            'git',
            '--git-dir={0}'.format(repo),
            'init',
            '--quiet',
            '--bare',
            ],
        )
    fast_import(
        repo=repo,
        commits=[
            dict(
                message='Initial import.',
                committer='John Doe <jdoe@example.com>',
                commit_time='1216235872 +0300',
                files=[
                    dict(
                        path='requirements.txt',
                        content="""\
# pip complains if this file is left empty, so say something we know
# is easily accessible
pip
""",
                        ),
                    dict(
                        path='deploy.py',
                        content="""\
import json
import os
print "fakedeploy start"
print json.dumps(dict(cwd=os.getcwd()))
with file(FLAGPATH, "a") as f:
    f.write('xyzzy')
print "fakedeploy end"
""".replace('FLAGPATH', repr(flag)),
                        ),
                    ],
                ),
            ],
        )
    # cause remote to have something new for us
    subprocess.check_call(
        args=[
            'git',
            '--git-dir={0}'.format(repo),
            'update-ref',
            'refs/remotes/origin/master',
            'HEAD',
            ],
        )
    subprocess.check_call(
        args=[
            'git',
            '--git-dir={0}'.format(repo),
            'symbolic-ref',
            'refs/remotes/origin/HEAD',
            'refs/remotes/origin/master',
            ],
        )
    out = StringIO()
    fake_stdout.provides('write').calls(out.write)
    assert not os.path.exists(flag)
    main(
        args=[
            'merge',
            '--repository', repo,
            '--temp', scratch,
            ],
        )
    got = out.getvalue().splitlines()
    eq(got, [])
    assert not os.path.exists(flag)
