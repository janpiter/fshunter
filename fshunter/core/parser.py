import re
from fshunter.helper.general import validate, flatten_dict

IS_ARRAY = re.compile(r'\[\]')


class RuleParser:
    def __init__(self, web_type='json'):
        self.result = []
        self.extract_values = []
        self.items = []
        self.type = web_type

    @staticmethod
    def json_parser(rule, data):
        """

        :param rule:
        :param data:
        :return:
        """
        try:
            return data[rule]
        except Exception:
            raise

    def rule_parser(self, rules, data):
        """

        :param rules:
        :param data:
        :return:
        """
        rules = [r for r in rules.split('|')]
        for i, r in enumerate(rules):
            r = IS_ARRAY.sub("", r)
            if isinstance(data, list):
                data = [self.json_parser(r, d) for d in data]
            else:
                data = self.json_parser(r, data)
        return data

    def extract(self, rule, data, flattening=True):
        """

        :param flattening:
        :param rule:
        :param data:
        :return: dict
        """
        if self.type == 'json':
            data = validate(data)
            for r in rule.split(','):
                self.result = self.rule_parser(r, data)
                self.extract_values.append({r: self.result})
        if flattening:
            self.items = flatten_dict(self.extract_values)
        else:
            self.items = self.extract_values
