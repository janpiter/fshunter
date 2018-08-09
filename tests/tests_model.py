from pprint import pprint
from argparse import ArgumentParser

from fshunter.core.model import Model


def tests_model(mp_name=None):
    model = Model()
    data = model.marketplace(mp_name=mp_name)
    return data


if __name__ == '__main__':
    parser = ArgumentParser(description="Marketplace crawler")
    parser.add_argument('-mp', '--marketplace', help='Marketplace')

    args = parser.parse_args()
    _mp = args.marketplace

    if _mp:
        _data = tests_model()
        if _data:
            print '=' * 100
            print
            for _d in _data.fetchall:
                print 'fetchall:', pprint(_d)
                print
            print '=' * 100
            print
            print 'fetchone:', pprint(_data.fetchone)
            print
            print '=' * 100
            print
            print 'rows_count:', _data.rows_count
            print
    else:
        parser.print_help()
