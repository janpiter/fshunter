# -*- coding: utf-8 -*-
import sys
from argparse import ArgumentParser

from fshunter.core.controller import Controller
from fshunter.core.output import Export
from fshunter.helper.general import get_arguments, list_to_dict, \
    date_formatter, remove_whitespace, valid_url

reload(sys)
sys.setdefaultencoding('utf8')


def get_marketplace():
    """
    Get marketplace list.
    :return: list
    """
    marketplace_list = []
    ct = Controller()
    marketplaces = ct.get_marketplace()
    if marketplaces:
        marketplace_list = [mp['mp_name'].lower() for mp in marketplaces]
    return marketplace_list


def run(mp_name=None, output=None, file_path=None, file_name=None):
    """
    :param mp_name: market place name
    :param output: type of file for output
    :param file_path: file path
    :param file_name: file name
    :return: list of dict
    """
    try:
        ct = Controller(mp_name=mp_name)
        ses = ct.get_sessions()
        items_url = ct.mp['mp_item_index_url']
        arguments = list_to_dict(get_arguments(items_url))
        marketplace = ct.mp
        shop_items = []

        for s in ses[next(iter(ses))]:
            arguments['id'] = s
            target_url = ct.fill_arguments(items_url, arguments)
            items = ct.get_items(target_url)

            for item in items[next(iter(items))]:

                shop_item = dict()
                template = ct.item_template()
                for t_key, t_value in template.iteritems():

                    value = ct.parse(data=item, rules=ct.mp[t_value['rule']],
                                     flattening=False)

                    if len(value):
                        if len(value) > 1:
                            if t_key == 'url':
                                value = dict(pair for d in value
                                             for pair in d.items())
                                value = ct.fill_arguments(
                                    marketplace['mp_item_url'],
                                    value)
                        else:
                            raw_value = value[0]
                            value = raw_value[next(iter(raw_value))]
                            if t_key == 'image':
                                value = value[0]
                                if not valid_url(value):
                                    if marketplace['mp_item_image_url']:
                                        value = ct.fill_arguments(
                                            marketplace['mp_item_image_url'],
                                            {
                                                t_key: value[0] if
                                                isinstance(value, list)
                                                else value
                                            }
                                        )
                            else:
                                if t_key in ['start_time', 'end_time']:
                                    value = date_formatter(value)
                                elif t_key in ['price_before', 'price_after']:
                                    if value:
                                        value = value // 100000 \
                                            if value > 9999999 else value
                                    else:
                                        value = 0
                                else:
                                    value = value[0] \
                                        if isinstance(value, list) else value

                        shop_item[t_key] = remove_whitespace(value)

                shop_item['marketplace'] = mp_name
                shop_items.append(shop_item)

        if output:
            if file_path:
                file_name = file_name if file_name else mp_name
                return Export(data=shop_items, file_path=file_path,
                              output_format=output, file_name=file_name).save
            else:
                raise Exception('File path required')
        return shop_items

    except Exception as e:
        print e


if __name__ == '__main__':
    output_choices = ['csv', 'json', 'xls', 'xlsx']
    marketplace_choices = get_marketplace()

    parser = ArgumentParser(description="Marketplace flash sale crawler.")
    parser.add_argument('--marketplace',
                        choices=marketplace_choices,
                        help='Marketplace name.',
                        required=True)
    parser.add_argument('--output',
                        choices=output_choices,
                        help='Type of file for output (csv, json, xls, xlsx).')
    parser.add_argument('--file_path',
                        help='File path (default: /tmp).',
                        default='/tmp')
    parser.add_argument('--file_name',
                        help='File name (default: marketplace name).')

    args = parser.parse_args()
    _marketplace = args.marketplace
    _output = args.output
    _file_path = args.file_path
    _file_name = args.file_name

    if _marketplace:
        run(mp_name=_marketplace, output=_output,
            file_path=_file_path, file_name=_file_name)
    else:
        parser.print_help()
