# -*- coding: utf-8 -*-
import sys
from argparse import ArgumentParser

from fshunter.core.controller import Controller
from fshunter.core.formatter import Formatter
from fshunter.core.exporter import Export
from fshunter.core.publisher import Nsq
from fshunter.helper.logger import logger
from fshunter.helper.general import get_arguments, list_to_dict, \
    date_formatter, remove_whitespace

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


def run(mp_name=None, output=None, file_path=None, file_name=None,
        publish=None, debug=None):
    """
    :param mp_name: market place name
    :param output: type of file for output
    :param file_path: file path
    :param file_name: file name
    :param publish: publish data to NSQ
    :param debug:
    :return: list of dict
    """
    try:
        shop_items = []
        start_time = end_time = None

        ct = Controller(mp_name=mp_name)
        marketplace = ct.mp

        session_arguments = list_to_dict(
            get_arguments(marketplace['mp_sessions_url']))
        ses, html = ct.get_sessions(arguments=session_arguments)

        items_url = marketplace['mp_item_index_url']
        items_arguments = list_to_dict(get_arguments(items_url))

        # Get start & end flash sale date from index page
        if marketplace['period_source'] == 'root':
            ft = Formatter(data=html)
            start_time = ft.format_date(
                key='start_time',
                rules=marketplace['rule_item_start_time'],
                mp=marketplace,
                ct=ct)
            end_time = ft.format_date(
                key='end_time',
                rules=marketplace['rule_item_end_time'],
                mp=marketplace,
                ct=ct)

        for s in ses[next(iter(ses))]:
            items_arguments['id'] = s
            target_url = ct.fill_arguments(items_url, items_arguments)
            items = ct.get_items(target_url)

            for item in items[next(iter(items))]:
                shop_item = dict()
                template = ct.item_template()
                shop_item['marketplace'] = mp_name

                for t_key, t_value in template.iteritems():
                    value = ct.parse(rule_type=marketplace['rule_type'],
                                     data=item,
                                     rules=marketplace[t_value['rule']],
                                     flattening=False)
                    if len(value):
                        ft = Formatter(value)

                        if len(value) > 1 and t_key == 'url':
                            value = ft.format_item_url(mp=marketplace, ct=ct)
                        else:
                            raw_value = value[0]
                            value = raw_value[next(iter(raw_value))]
                            if t_key == 'image':
                                value = ft.format_image_url(key=t_key,
                                                            mp=marketplace,
                                                            ct=ct)
                            else:
                                if t_key in ['start_time', 'end_time']:
                                    value = date_formatter(value)
                                elif t_key in ['price_before', 'price_after',
                                               'discount']:
                                    value = ft.format_number(key=t_key,
                                                             mp=marketplace)
                                else:
                                    value = ft.item

                        if t_key in ['image', 'url']:
                            value = ft.build_url(value, mp=marketplace)

                        shop_item[t_key] = remove_whitespace(value)

                if not shop_item['start_time']:
                    shop_item['start_time'] = date_formatter(start_time)

                if not shop_item['end_time']:
                    shop_item['end_time'] = date_formatter(end_time)

                shop_items.append(shop_item)

        if output:
            if file_path:
                file_name = file_name if file_name else mp_name
                return Export(data=shop_items, file_path=file_path,
                              output_format=output, file_name=file_name).save
            else:
                raise Exception('File path required')

        if publish:
            nsq = Nsq(debug=debug)
            for item in shop_items:
                nsq.publish(item)

        return shop_items

    except Exception as e:
        logger(str(e), level='error')


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
                        help='Output file path (default: /tmp).',
                        default='/tmp')
    parser.add_argument('--file_name',
                        help='Output file name (default: marketplace name).')
    parser.add_argument('--publish',
                        choices=['True', 'False'],
                        default='False',
                        help='Publish data to NSQ.')
    parser.add_argument('--debug',
                        choices=['True', 'False'],
                        default='False')

    args = parser.parse_args()
    _marketplace = args.marketplace
    _output = args.output
    _file_path = args.file_path
    _file_name = args.file_name
    _publish = eval(args.publish)
    _debug = eval(args.debug)

    if _marketplace:
        run(mp_name=_marketplace, output=_output,
            file_path=_file_path, file_name=_file_name,
            publish=_publish, debug=_debug)
    else:
        parser.print_help()
