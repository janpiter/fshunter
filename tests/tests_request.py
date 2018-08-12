# -*- coding: utf-8 -*-
import sys
from argparse import ArgumentParser

from fshunter.core.http import Request

reload(sys)
sys.setdefaultencoding('utf8')


def test_request(url):
    req = Request()
    print req.open(url)
    print req.selected_method


if __name__ == '__main__':
    parser = ArgumentParser(description="")
    parser.add_argument('-u', '--url', help='Url')

    args = parser.parse_args()
    _url = args.url

    if _url:
        test_request(url=_url)
    else:
        parser.print_help()
