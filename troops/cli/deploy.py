import os
import shutil
import subprocess
import sys
import tempfile


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
                ],
            cwd=source,
            env=None,
            )
        subprocess.check_call(
            args=[
                'git',
                'fetch',
                '--quiet',
                '--update-head-ok',
                '--',
                # avoid problems with ":" in path; note this syntax
                # can still do relative paths
                'file://{0}'.format(repository),
                '+refs/heads/*:refs/heads/*',
                '+refs/remotes/*:refs/remotes/*',
                ],
            cwd=source,
            env=None,
            )
        if rev is None:
            rev = 'HEAD'
        subprocess.check_call(
            args=[
                'git',
                'reset',
                '--hard',
                '--quiet',
                rev,
                '--',
                ],
            cwd=source,
            env=None,
            )

        venv = os.path.join(scratch, 'virtualenv')

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
                venv,
                ],
            cwd=scratch,
            env=None,
            )

        subprocess.check_call(
            args=[
                os.path.join(venv, 'bin', 'pip'),
                '--quiet',
                'install',
                # pip complains if the requirements file is empty, so
                # always give it something harmless to install: itself
                'pip',
                '-r', os.path.join(scratch, 'source', 'requirements.txt'),
                ],
            cwd=scratch,
            env=None,
            )

        with file('/dev/null') as devnull:
            proc = subprocess.Popen(
                args=[
                    os.path.join(venv, 'bin', 'python'),
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
        # /var/tmp/troops
        required=True,
        )
    parser.add_argument(
        '--temp',
        metavar='DIR',
        help='directory to store temporary files in',
        )
