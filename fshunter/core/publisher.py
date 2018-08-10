import json

from fshunter.core.config import load
from fshunter.helper.nsq import Producer
from fshunter.helper.logger import logger


class Nsq:
    def __init__(self, debug=False):
        self.config = load()
        self.debug = debug
        self.producer = Producer(self.config.get("nsq", "host"),
                                 self.config.get("nsq", "http_port"),
                                 self.config.get("nsq", "topic_items"))

    def publish(self, data):
        """
        :param data:
        :return:
        """
        try:
            self.producer.put_message(json.dumps(data))
            if self.debug:
                logger(message=data)
        except Exception:
            raise
