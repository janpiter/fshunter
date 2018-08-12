# -*- coding: utf-8 -*-
from fshunter.core.model import Model
from fshunter.core.parser import RuleParser
from fshunter.core.http import Request
from fshunter.helper.general import current_timestamp


class Controller:
    def __init__(self, mp_id=None, mp_name=None):
        self.model = Model()
        self.mp = self.get_marketplace(mp_id=mp_id, mp_name=mp_name)

    @staticmethod
    def item_template():
        """
        Marketplace item template.
        :return: dict
        """
        try:
            return dict(id=dict(rule='rule_item_id',
                                value=None),
                        name=dict(rule='rule_item_name',
                                  value=None),
                        url=dict(rule='rule_item_link',
                                 value=None),
                        image=dict(rule='rule_item_picture',
                                   value=None),
                        discount=dict(rule='rule_item_discount',
                                      value=None),
                        price_before=dict(rule='rule_item_price_before',
                                          value=None),
                        price_after=dict(rule='rule_item_price_after',
                                         value=None),
                        start_time=dict(rule='rule_item_start_time',
                                        value=None),
                        end_time=dict(rule='rule_item_end_time',
                                      value=None))
        except Exception:
            raise

    @staticmethod
    def parse(rule_type='json', data=None, rules=None, flattening=True):
        """
        :param flattening:
        :param rule_type:
        :param data:
        :param rules:
        :return: list
        """
        try:
            rp = RuleParser(web_type=rule_type)
            rp.extract(rule=rules, data=data, flattening=flattening)
            return rp.items
        except Exception:
            raise

    @staticmethod
    def fill_arguments(url, arguments, offset=0, limit=100):
        """
        :param url:
        :param arguments:
        :param offset:
        :param limit:
        :return:
        """
        try:
            for key, value in arguments.iteritems():
                if key == 'limit':
                    arguments[key] = limit
                if key == 'offset':
                    arguments[key] = offset
                if key == 'timestamp':
                    arguments[key] = current_timestamp()
            return url.format(**arguments)
        except Exception:
            raise

    def get_marketplace(self, mp_id=None, mp_name=None):
        """
        Get list of marketplace.
        :param mp_id: Marketplace ID
        :param mp_name: Marketplace name
        :return: dictionary if parameter filled, list if tuple if not filled
        """
        try:
            if mp_id or mp_name:
                return self.model.marketplace(mp_id=mp_id, mp_name=mp_name)\
                    .fetchone
            else:
                return self.model.marketplace(mp_id=mp_id, mp_name=mp_name)\
                    .fetchall
        except Exception:
            raise

    def get_sessions(self, arguments=None):
        """
        :return: tuple (list of dict, html response)
        """
        try:
            rule_type = self.mp['rule_type']
            sessions_link = self.mp['mp_sessions_url']
            rules = self.mp['rule_sessions_list']

            if arguments:
                sessions_link = self.fill_arguments(sessions_link, arguments)

            req = Request(method='urllib')
            response = req.open(sessions_link)

            return self.parse(rule_type=rule_type,
                              data=response,
                              rules=rules), response
        except Exception:
            raise

    def get_items(self, request_url):
        """
        :param request_url:
        :return:
        """
        try:
            rule_type = self.mp['rule_type']
            rule_items_list = self.mp['rule_items_list']

            req = Request(method='urllib')
            response = req.open(request_url)

            return self.parse(rule_type=rule_type,
                              data=response,
                              rules=rule_items_list)
        except Exception:
            raise
