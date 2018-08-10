import bs4

from fshunter.helper.general import validate, valid_url
from fshunter.helper.logger import logger


class Formatter:
    def __init__(self, data):
        self.raw_data = data
        self.data = self.convert(data)
        self.item = self._validate(self.data[next(iter(self.data))])

    @staticmethod
    def _validate(data):
        """
        :param data: string or bs4 object
        :return: string
        """
        return validate(Formatter.convert(data), data_type=bs4.element.Tag)

    @staticmethod
    def convert(data):
        """
        :param data: list or string
        :return: string
        """
        try:
            return data[0] if isinstance(data, list) else data
        except Exception:
            raise

    def format_number(self):
        """
        :return: long
        """
        result = 0
        try:
            if self.item:
                value = validate(self.item, data_type=long)
                result = value // 100000 if value > 9999999 else value
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
            result = ct.fill_arguments(mp['mp_item_url'], value)
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
            if not valid_url(self.item):
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
