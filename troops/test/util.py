import errno
import os
import shutil
import subprocess

import sys

def mkdir(*a, **kw):
    try:
        os.mkdir(*a, **kw)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

def find_test_name():
    try:
        from nose.case import Test
        from nose.suite import ContextSuite
        import types
        def get_nose_name(its_self):
            if isinstance(its_self, Test):
                file_, module, class_ = its_self.address()
                # i originally used a colon as separator here, to
                # emulate nose output, but that seems to break
                # virtualenvs placed in these temporary directories
                name = '%s.%s' % (module, class_)
                return name
            elif isinstance(its_self, ContextSuite):
                if isinstance(its_self.context, types.ModuleType):
                    return its_self.context.__name__
    except ImportError:
        # older nose
        from nose.case import FunctionTestCase, MethodTestCase
        from nose.suite import TestModule
        from nose.util import test_address
        def get_nose_name(its_self):
            if isinstance(its_self, (FunctionTestCase, MethodTestCase)):
                file_, module, class_ = test_address(its_self)
                name = '%s:%s' % (module, class_)
                return name
            elif isinstance(its_self, TestModule):
                return its_self.moduleName

    i = 0
    while True:
        i += 1
        frame = sys._getframe(i)
        # kludge, hunt callers upwards until we find our nose
        if (frame.f_code.co_varnames
            and frame.f_code.co_varnames[0] == 'self'):
            its_self = frame.f_locals['self']
            name = get_nose_name(its_self)
            if name is not None:
                return name

def maketemp():
    tmp = os.path.join(os.path.dirname(__file__), 'tmp')
    mkdir(tmp)

    name = find_test_name()
    tmp = os.path.join(tmp, name)
    try:
        shutil.rmtree(tmp)
    except OSError, e:
        if e.errno == errno.ENOENT:
            pass
        else:
            raise
    os.mkdir(tmp)
    return tmp


def assert_raises(excClass, callableObj, *args, **kwargs):
    """
    Like unittest.TestCase.assertRaises, but returns the exception.
    """
    try:
        callableObj(*args, **kwargs)
    except excClass, e:
        return e
    else:
        if hasattr(excClass,'__name__'): excName = excClass.__name__
        else: excName = str(excClass)
        raise AssertionError("%s not raised" % excName)


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
