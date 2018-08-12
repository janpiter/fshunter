# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup

from fshunter.core.formatter import Formatter


def test_formatter(data):
    ft = Formatter(data)
    rs = ft.extractor(data)
    return rs


if __name__ == '__main__':
    dt = '<div><p class="price notranslate"> ' \
         '<del> Rp 62.000</del>Rp 11.000   </p></div>'
    dt = BeautifulSoup(dt, 'html.parser').select('div')
    print test_formatter(dt)
