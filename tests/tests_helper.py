# -*- coding: utf-8 -*-
import sys
from argparse import ArgumentParser

from fshunter.helper.general import list_to_dict, flatten

reload(sys)
sys.setdefaultencoding('utf8')


def test_helper(value):
    return flatten(value), flatten(value, items_type=list)


if __name__ == '__main__':
    parser = ArgumentParser(description="")
    parser.add_argument('-l', '--list', help='List of list',
                        default="[1407, [1397, 1402, 1412, 1417]]")

    args = parser.parse_args()
    _list = args.list

    if _list:
        print '-' * 100
        print _list
        print '-' * 100
        rs, rs2 = test_helper(eval(_list))
        for r in rs:
            print r
        print list_to_dict(rs)
        print '-' * 100
        for r2 in rs2:
            print r2
        print list_to_dict(rs2)
    else:
        parser.print_help()

    _dict = [{u'flash_deal|id': 1437},
             {u'other_flash_deal[]|id': [1417, 1422, 1442, 1447]}]
    print '-' * 100
    print 'dict  :', _dict
    print '-' * 100
    print 'result:', flatten(_dict, items_type=dict)
