# -*- coding: utf-8 -*-
import sys
from argparse import ArgumentParser

from fshunter.core.controller import Controller

reload(sys)
sys.setdefaultencoding('utf8')


def get_marketplace():
    marketplace_list = []
    ct = Controller()
    marketplaces = ct.get_marketplace()
    if marketplaces:
        marketplace_list = [mp['mp_name'].lower() for mp in marketplaces]
    return marketplace_list


def test_parser(mp_name=None):
    try:
        ct = Controller(mp_name=mp_name)
        ses = ct.get_sessions()
        print ses
    except Exception as e:
        print str(e)


if __name__ == '__main__':
    marketplace_choices = get_marketplace()

    parser = ArgumentParser(description="")
    parser.add_argument('-mp', '--marketplace', choices=marketplace_choices,
                        help='Marketplace')

    args = parser.parse_args()
    _mp = args.marketplace

    if _mp:
        test_parser(_mp)
    else:
        parser.print_help()
