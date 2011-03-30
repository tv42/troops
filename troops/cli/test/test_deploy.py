import fudge
import json
import os
import re
import subprocess

from nose.tools import eq_ as eq, assert_raises
from cStringIO import StringIO

from troops.cli.main import main

from troops.test.util import maketemp


class FakeExit(Exception):
    pass


def fast_import(
    repo,
    commits,
    ref=None,
    ):
    """
    Create an initial commit.
    """
    if ref is None:
        ref = 'refs/heads/master'
    child = subprocess.Popen(
        args=[
            'git',
            '--git-dir=%s' % repo,
            'fast-import',
            '--quiet',
            ],
        stdin=subprocess.PIPE,
        close_fds=True,
        )

    for commit in commits:
        files = list(commit['files'])
        for index, filedata in enumerate(files):
            child.stdin.write("""\
blob
mark :%(mark)d
data %(len)d
%(content)s
""" % dict(
                mark=index+1,
                len=len(filedata['content']),
                content=filedata['content'],
                ))
        child.stdin.write("""\
commit %(ref)s
author %(author)s %(author_time)s
committer %(committer)s %(commit_time)s
data %(commit_msg_len)d
%(commit_msg)s
""" % dict(
                ref=ref,
                author=commit.get('author', commit['committer']),
                author_time=commit.get('author_time', commit['commit_time']),
                committer=commit['committer'],
                commit_time=commit['commit_time'],
                commit_msg_len=len(commit['message']),
                commit_msg=commit['message'],
                ))
        parent = commit.get('parent')
        if parent is not None:
            assert not parent.startswith(':')
            child.stdin.write("""\
from %(parent)s
""" % dict(
                    parent=parent,
                    ))
        for index, filedata in enumerate(files):
            child.stdin.write(
                'M %(mode)s :%(index)d %(path)s\n' % dict(
                    mode=filedata.get('mode', '100644'),
                    index=index+1,
                    path=filedata['path'],
                    ),
                )

    child.stdin.close()
    returncode = child.wait()
    if returncode != 0:
        raise RuntimeError(
            'git fast-import failed', 'exit status %d' % returncode)


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
    got = out.getvalue()
    eq(got, """\
usage: troops deploy [OPTS]

Run the latest deployment script

optional arguments:
  -h, --help        show this help message and exit
  --repository DIR  location of the git repository
  --temp DIR        directory to store temporary files in
""",
       'Unexpected output:\n'+got)


@fudge.patch('sys.stdout', 'sys.stderr', 'sys.exit')
def test_simple(fake_stdout, fake_stderr, fake_exit):
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
with file(FLAGPATH, "w") as f:
    f.write('xyzzy')
print "fakedeploy end"
""".replace('FLAGPATH', repr(flag)),
                        ),
                    ],
                ),
            ],
        )
    out = StringIO()
    fake_stdout.expects('write').calls(out.write)
    assert not os.path.exists(flag)
    main(
        args=[
            'deploy',
            '--repository', repo,
            '--temp', scratch,
            ],
        )
    assert os.path.exists(flag)
    with file(flag) as f:
        got = f.read()
    eq(got, 'xyzzy')
    got = out.getvalue().splitlines()
    eq(got[0], 'fakedeploy start')
    eq(got[2], 'fakedeploy end')
    eq(got[3:], [])
    got = json.loads(got[1])
    cwd = got.pop('cwd')
    (head, tail) = os.path.split(cwd)
    eq(head, scratch)
    assert re.match(r'^troops-[a-zA-Z0-9]{6,}$', tail)
    eq(got, {})
