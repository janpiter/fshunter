import re
import json
import string
import datetime


URL_PATTERN = re.compile(r'^https?://', flags=re.I)


def validate(data):
    """
    Validate value if json or dict,
    if value is json then convert it into dict.
    :param data: json or dict
    :return: dict
    """
    try:
        if isinstance(data, dict):
            return data
        else:
            # noinspection PyBroadException
            try:
                return json.loads(data)
            except ValueError:
                return data
    except Exception:
        raise


def flatten_list(items):
    """
    Flattening list of list into list.
    :param items: list of list (example: [1407, [1397, 1402, 1412, 1417]])
    :return: list
    """
    flat_list = []
    for sublist in items:
        if isinstance(sublist, list):
            for item in sublist:
                flat_list.append(item)
        else:
            flat_list.append(sublist)
    return flat_list


def flatten_dict(items):
    """
    Flattening list of dict into single key dict.
    :param items: list of dict (example: [{u'flash_deal|id': 1437},
    {u'other_flash_deal[]|id': [1417, 1422, 1442, 1447]}])
    :return: dict
    """
    flat_list = []
    flat_dict = dict()

    all_keys = set().union(*(d.keys() for d in items))

    for d in items:
        flat_list.extend(flatten_list(d.values()))

    flat_dict[",".join(list(all_keys))] = flat_list

    return flat_dict


def get_arguments(value):
    """
    Checking arguments inside string.
    :param value: string
    :return: list of arguments
    """
    try:
        return [tup[1] for tup in string.Formatter().parse(value)
                if tup[1] is not None]
    except TypeError:
        raise


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


def date_formatter(raw_date, date_format="%Y-%m-%dT%H:%M:%S.000+07:00"):
    """
    Convert unix timestamp to readable date and time.
    :param raw_date: Unix timestamp
    :param date_format: datetime format
    :return: datetime
    """
    result = raw_date
    try:
        if isinstance(raw_date, int):
            result = datetime.datetime\
                .fromtimestamp(float(raw_date))\
                .strftime(date_format)
    except Exception:
        raise
    finally:
        return result


def remove_whitespace(value):
    """
    Remove whitespace.
    :param value: string
    :return: string
    """
    try:
        value = value.strip()
    except TypeError:
        raise
    finally:
        return value


def valid_url(url):
    """
    Validating url.
    :param url: string
    :return: boolean
    """
    try:
        if URL_PATTERN.search(str(url)):
            return True
        return False
    except Exception:
        raise
