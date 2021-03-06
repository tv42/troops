import logging
import os
import shutil
import subprocess
import sys
import tempfile

import troops

log = logging.getLogger(__name__)

def deploy(temp, repository, rev=None):
    scratch = tempfile.mkdtemp(
        prefix='troops-',
        dir=temp,
        )
    try:
        source = os.path.join(scratch, 'source')
        os.mkdir(source)
        subprocess.check_call(
            args=[
                'git',
                'init',
                '--quiet',
                '--',
                source,
                ],
            env=None,
            )
        subprocess.check_call(
            args=[
                'git',
                '--git-dir={source}/.git'.format(source=source),
                'fetch',
                '--quiet',
                '--update-head-ok',
                '--',
                # this will fail if the path has ":" in it; i have no
                # good workaround for this; git's file:// syntax
                # cannot cope with relative pathnames that have
                # slashes in them
                repository,
                '+refs/heads/*:refs/heads/*',
                '+refs/remotes/*:refs/remotes/*',
                ],
            env=None,
            )
        if rev is None:
            rev = 'HEAD'
        subprocess.check_call(
            args=[
                'git',
                '--git-dir={source}/.git'.format(source=source),
                '--work-tree={source}'.format(source=source),
                'reset',
                '--hard',
                '--quiet',
                rev,
                '--',
                ],
            env=None,
            )

        subprocess.check_call(
            args=[
                # make sure we use the python inside our current
                # virtualenv, if any
                sys.executable,
                '-m',
                'virtualenv',
                '--no-site-packages',
                '--distribute',
                '--quiet',
                '--',
                'virtualenv',
                ],
            cwd=scratch,
            env=None,
            )

        subprocess.check_call(
            args=[
                # call python explicitly to avoid hitting shebang line
                # maximum length
                './virtualenv/bin/python',
                './virtualenv/bin/pip',
                '--quiet',
                'install',
                # pip complains if the requirements file is empty, so
                # always give it something harmless to install: itself
                'pip',
                '-r', 'source/requirements.txt',
                ],
            cwd=scratch,
            env=None,
            )

        # we need to install troops in the virtualenv, to provide the
        # .role etc deploy-time functionality. as we don't necessarily
        # have a source package or an egg around, we can't pip install
        # it for real. instead, cheat and just symlink the modules
        # that are needed.
        os.symlink(
            os.path.dirname(troops.__file__),
            os.path.join(
                scratch,
                'virtualenv',
                'lib',
                'python{ver}'.format(ver=sys.version[:3]),
                'site-packages',
                'troops',
                ),
            )

        with file('/dev/null') as devnull:
            proc = subprocess.Popen(
                args=[
                    './virtualenv/bin/python',
                    '--',
                    os.path.join('source', 'deploy.py'),
                    ],
                cwd=scratch,
                env=None,
                stdin=devnull,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                )
        for line in proc.stdout:
            sys.stdout.write(line)
        returncode = proc.wait()
        if returncode < 0:
            raise RuntimeError(
                'deploy script failed with signal {sig}'.format(
                    sig=-returncode,
                    ),
                )
        elif returncode > 0:
            raise RuntimeError(
                'deploy script failed with exit code {code}'.format(
                    code=returncode,
                    ),
                )

    finally:
        shutil.rmtree(scratch)


def run(args):
    deploy(
        temp=args.temp,
        repository=args.repository,
        )


def main(parser):
    """Run the latest deployment script"""
    parser.usage = '%(prog)s [OPTS]'
    parser.set_defaults(
        func=run,
        )
    parser.add_argument(
        '--repository',
        metavar='DIR',
        help='location of the git repository',
        # TODO this is meant to be temporary, until we have logic for
        # /var/lib/troops
        required=True,
        )
    parser.add_argument(
        '--temp',
        metavar='DIR',
        help='directory to store temporary files in',
        # TODO this is meant to be temporary, until we have logic for
        # /var/tmp/troops
        required=True,
        )
