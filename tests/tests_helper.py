# -*- coding: utf-8 -*-
import sys
from argparse import ArgumentParser

from fshunter.helper.general import flatten_list, list_to_dict

reload(sys)
sys.setdefaultencoding('utf8')


def test_helper(value):
    return flatten_list(value)


if __name__ == '__main__':
    parser = ArgumentParser(description="")
    parser.add_argument('-l', '--list', help='List of list',
                        default="[1407, [1397, 1402, 1412, 1417]]")

    args = parser.parse_args()
    _list = args.list

    if _list:
        rs = test_helper(eval(_list))
        for r in rs:
            print r
        print list_to_dict(rs)
    else:
        parser.print_help()
