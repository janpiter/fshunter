import datetime
import json
import re
import string
import time

from dateutil.parser import parse

URL_PATTERN = re.compile(r'^https?://', flags=re.I)
NOT_DIGIT_PATTERN = re.compile(r'\D')


def current_timestamp(milliseconds=True):
    """
    :param milliseconds:
    :return:
    """
    return int(round(time.time() * 1000)) \
        if milliseconds else int(time.time())


def date_formatter(raw_date, date_format="%Y-%m-%dT%H:%M:%S.000+07:00"):
    """
    Convert unix timestamp to readable date and time.
    :param raw_date: Unix timestamp
    :param date_format: datetime format
    :return: str
    """
    result = raw_date
    try:
        if isinstance(raw_date, int):
            result = datetime.datetime.fromtimestamp(float(raw_date))
        else:
            result = parse(raw_date)
        result = result.strftime(date_format)
    except Exception:
        raise
    finally:
        return result


def validate(data, data_type=None):
    """
    :param data:
    :param data_type:
    :return:
    """
    try:
        if data_type == dict:
            if isinstance(data, data_type):
                return data
            else:
                # noinspection PyBroadException
                try:
                    return json.loads(data)
                except ValueError:
                    return data
        elif data_type == long:
            if isinstance(data, data_type):
                return data
            else:
                # noinspection PyBroadException
                try:
                    data = NOT_DIGIT_PATTERN.sub('', str(data))
                    return long(data)
                except ValueError:
                    return data
        elif data_type == 'url':
            if URL_PATTERN.search(str(data)):
                return True
            return False
    except Exception:
        raise


def flatten(items, items_type=list):
    """
    Flattening list of dict into single key dict or
    list of list into single list.

    example:
        input:
            [{u'flash_deal|id': 1437},
             {u'other_flash_deal[]|id': [1417, 1422, 1442, 1447]}
        output:
            {u'flash_deal|id,other_flash_deal[]|id':
             [1437, 1417, 1422, 1442, 1447]}

        input:
            [1407, [1397, 1402, 1412, 1417]]
        output:
            [1407, 1397, 1402, 1412, 1417]

    :param items: list or dict
    :param items_type: list or dict
    :return:
    """
    flat_list = []
    flat_dict = dict()
    try:
        if items_type == list:
            for sublist in items:
                if isinstance(sublist, list):
                    for item in sublist:
                        if item:
                            flat_list.append(item)
                else:
                    flat_list.append(sublist)
        elif items_type == dict:
            dict_keys = set().union(*(d.keys() for d in items))
            for d in items:
                flat_list.extend(flatten(d.values(), items_type=list))
            flat_dict[",".join(list(dict_keys))] = flat_list
    except Exception:
        raise
    finally:
        return flat_list if items_type == list else flat_dict


def list_to_dict(data):
    """
    Convert list to dict wit empty value.
    :param data: list
    :return: dict
    """
    try:
        return {d: "" for d in data}
    except TypeError:
        raise


def get_arguments(data):
    """
    Checking arguments inside string.
    :param data: string
    :return: list of arguments
    """
    try:
        return [tup[1] for tup in string.Formatter().parse(data)
                if tup[1] is not None]
    except TypeError:
        raise


def remove_whitespace(data):
    """
    Remove whitespace.
    :param data: string
    :return: string
    """
    try:
        data = data\
            .replace("\r", "")\
            .replace("\t", "")\
            .replace("\n", "")\
            .replace("\f", "")\
            .replace("\v", "")\
            .strip()
    except TypeError:
        raise
    finally:
        return data
