import os
import shutil
import subprocess
import sys
import tempfile

from . import merge


def run(args):
    subprocess.check_call(
        args=[
            'git',
            '--git-dir={repo}'.format(repo=args.repository),
            'fetch',
            '--quiet',
            '--all',
            '--prune',
            ],
        env=None,
        )
    return merge.run(args)

def main(parser):
    """Fetch and deploy any changes in remote repositories"""
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
