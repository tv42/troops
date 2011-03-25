def run(args):
    raise NotImplementedError('TODO')


def main(parser):
    """Run the latest deployment script"""
    parser.set_defaults(
        func=run,
        )
