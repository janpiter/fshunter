import urlparse
import requests


class Producer:
    def __init__(self, host, port, topic):
        self.base_url = "http://{}:{}".format(host, port)
        self.topic = topic

    def put_message(self, msg):
        params = {"message": msg}
        url = "{}?topic={}".format(urlparse.urljoin(self.base_url, "pub"),
                                   self.topic)
        requests.post(url, params)
