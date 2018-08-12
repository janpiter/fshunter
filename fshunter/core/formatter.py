import bs4
import inspect

from fshunter.helper.logger import logger
from fshunter.helper.general import validate, current_timestamp, date_formatter


class Formatter:
    def __init__(self, data):
        self.raw_data = data
        self.data = self.convert(data)
        self.item = self._validate(self.data)

    @staticmethod
    def _validate(data):
        """
        :param data: string or bs4 object
        :return: string
        """
        data = data[next(iter(data))] if isinstance(data, dict) else data
        return Formatter.extractor(data)

    @staticmethod
    def convert(data):
        """
        :param data: list or string
        :return: string
        """
        try:
            return data[0] if data and isinstance(data, list) else data
        except Exception:
            raise

    @staticmethod
    def extractor(data):
        """
        Extracting bs4.element.* to text.
        :param data: bs4.* or other type.
        :return: string
        """
        try:
            if isinstance(data, list):
                t = []
                for d in data:
                    if d is not None:
                        if isinstance(d, bs4.element.Tag) \
                                or isinstance(d, bs4.element.NavigableString):
                            d = d.find_all(text=True)[-1]
                        t.append(d)
                data = "".join(t)
        except Exception as e:
            logger('{}: {}'.format(inspect.currentframe().f_code.co_name,
                                   str(e)))
        finally:
            return data

    def build_url(self, url, mp):
        """
        :param url:
        :param mp:
        :return:
        """
        try:
            if not validate(url, data_type='url') and url.startswith('/'):
                url = '{}{}'.format(mp['mp_link'], url)
        except Exception as e:
            logger('{}: {}'.format(self.__class__.__name__, str(e)))
        finally:
            return url

    def format_number(self, key, mp):
        """
        :return: long
        """
        result = 0
        try:
            if self.item:
                result = validate(self.item, data_type=long)
                if key in ['price_before', 'price_after']:
                    result = result // mp['price_divider']
        except Exception as e:
            logger('{}: {}'.format(self.__class__.__name__, str(e)))
        finally:
            return result

    def format_item_url(self, mp=None, ct=None):
        """
        :param mp: Marketplace config
        :param ct: Object Controller
        :return: string
        """
        result = self.item
        try:
            value = dict(pair for d in self.raw_data for pair in d.items())
            result = ct.fill_arguments(mp['mp_item_url'], arguments=value)
        except Exception as e:
            logger('{}: {}'.format(self.__class__.__name__, str(e)))
        finally:
            return result

    def format_image_url(self, key, mp=None, ct=None):
        """
        :param key: Rule key
        :param mp: Marketplace config
        :param ct: Object Controller
        :return: string
        """
        image_url = self.item
        try:
            if not validate(self.item, data_type='url'):
                if mp['mp_item_image_url']:
                    image_url = ct.fill_arguments(
                        mp['mp_item_image_url'],
                        {key: self.convert(self.item)}
                    )
                else:
                    image_url = self.convert(self.item)
        except Exception as e:
            logger('{}: {}'.format(self.__class__.__name__, str(e)))
        finally:
            return image_url

    def format_date(self, key, rules, mp=None, ct=None):
        """
        :param key:
        :param rules:
        :param mp:
        :param ct:
        :return:
        """
        result_date = None
        try:
            if rules == 'TODAY':
                if key == 'start_time':
                    result_date = date_formatter(
                        current_timestamp(milliseconds=False),
                        date_format="%Y-%m-%dT00:00:00.000+07:00")
                else:
                    result_date = date_formatter(
                        current_timestamp(milliseconds=False),
                        date_format="%Y-%m-%dT23:59:59.000+07:00")
            else:
                raw_date = ct.parse(rule_type=mp['rule_type'],
                                    data=self.raw_data,
                                    rules=rules,
                                    flattening=False)
                if raw_date:
                    result_date = self.convert(raw_date).values()[0]
        except Exception as e:
            logger('{}: {}'.format(self.__class__.__name__, str(e)))
        finally:
            return result_date
