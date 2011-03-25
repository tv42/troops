import argparse
import pkg_resources


def main(args=None):
    parser = argparse.ArgumentParser(
        # provide explicit prog or tests will see nosetests as
        # sys.arvg[0]
        prog='troops',
        description='Software deployment tool',
        )
    subparsers = parser.add_subparsers(
        title='commands',
        )

    for entry_point in pkg_resources.iter_entry_points('troops.cli'):
        fn = entry_point.load()
        kwargs = {}
        if fn.__doc__ is not None:
            kwargs['help'] = fn.__doc__
        p = subparsers.add_parser(entry_point.name, **kwargs)
        fn(p)
        # it's clumsy for a function to access its own docstring, so
        # help it by using that as the default for the description
        if p.description is None:
            p.description = fn.__doc__

    args = parser.parse_args(args=args)
    args.func(args)
