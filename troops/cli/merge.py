import os
import shutil
import subprocess
import sys
import tempfile

from . import deploy


def rev_parse(repo, rev):
    process = subprocess.Popen(
        args=[
            'git',
            '--git-dir=%s' % repo,
            'rev-parse',
            '--default',
            rev,
            ],
        close_fds=True,
        stdout=subprocess.PIPE,
        )
    sha = process.stdout.read()
    returncode = process.wait()
    if returncode != 0:
        raise RuntimeError('git rev-parse failed')
    if not sha:
        return None
    sha = sha.rstrip('\n')
    return sha


def run(args):
    head = rev_parse(repo=args.repository, rev='HEAD')
    assert head is not None
    remote = rev_parse(
        repo=args.repository,
        rev='refs/remotes/origin/HEAD',
        )
    assert remote is not None
    if remote == head:
        # no action needed
        return
    # TODO ff only
    deploy.deploy(
        temp=args.temp,
        repository=args.repository,
        rev=remote,
        )


def main(parser):
    """Deploy any changes in remote branches"""
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
