# -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup

from fshunter.helper.general import validate, flatten, remove_whitespace
from fshunter.helper.logger import logger

IS_ARRAY = re.compile(r'([^\[]+)\[([^\]]+)?\]')


class RuleParser:
    def __init__(self, web_type='json'):
        self.result = []
        self.extract_values = []
        self.items = []
        self.type = web_type
        self.bs = None

    def json_parser(self, rule, data):
        """
        :param rule:
        :param data:
        :return:
        """
        try:
            item_index = None
            match = IS_ARRAY.search(rule)
            if match:
                rule = match.group(1)
                if match.group(2):
                    item_index = match.group(2)

            result = data[rule]
            if isinstance(result, list) and item_index:
                result = result[int(item_index)]

            return result
        except KeyError as e:
            logger('{}: KeyError: {}'.format(self.__class__.__name__, str(e)))
            return dict()

    def html_parser(self, rule, attr=None):
        """
        :param rule:
        :param attr:
        :return:
        """
        try:
            if attr:
                return self.bs.select_one(rule)[attr]
            else:
                return self.bs.select(rule)
        except Exception as e:
            logger('{}: {} ({}:{})'.format(self.__class__.__name__, str(e),
                                           rule, attr))
            return None

    def rule_parser(self, rules, data):
        """
        :param rules:
        :param data:
        :return:
        """
        rules = [r for r in rules.split('|')]
        if self.type == 'json':
            for i, r in enumerate(rules):
                if isinstance(data, list):
                    data = [self.json_parser(r, d) for d in data
                            if self.json_parser(r, d)]
                    data = data[-1] if len(data) < 2 else data
                else:
                    data = self.json_parser(r, data)
            return data
        elif self.type == 'css':
            selector, attribute = list(rules) \
                                      if len(rules) > 1 else (rules[0], None)
            data = self.html_parser(rule=selector, attr=attribute)
            return data

    def extract(self, rule, data, flattening=True):
        """
        :param flattening:
        :param rule:
        :param data:
        :return: dict
        """
        if self.type == 'json':
            data = validate(data, data_type=dict)
        elif self.type == 'css':
            if isinstance(data, str):
                self.bs = BeautifulSoup(remove_whitespace(data), 'html.parser')
            else:
                self.bs = data

        for r in rule.split(','):
            self.result = self.rule_parser(r, data)
            self.extract_values.append({r: self.result})

        if flattening:
            self.items = flatten(self.extract_values, items_type=dict)
        else:
            self.items = self.extract_values
