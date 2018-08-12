import mechanize
import urllib2
import inspect
import random


class Request:
    request_headers = {
        "Accept-Encoding": "deflate",
        "Accept-Language": "en-US,en;q=0.5",
        "User-Agent": "Mozilla/5.0"
                      " (Macintosh; Intel Mac OS X 10.13; rv:61.0)"
                      " Gecko/20100101"
                      " Firefox/61.0",
        "Accept": "text/html,application/xhtml+xml"
                  ",application/xml;q=0.9,*/*;q=0.8",
        "Referer": "google.com",
        "Connection": "keep-alive"
    }

    def __init__(self, method=None):
        self.method = method
        self.method_list = inspect.getmembers(Request,
                                              predicate=inspect.ismethod)
        self.selected_method = None

    @staticmethod
    def _mechanize(url):
        """

        :param url:
        :return:
        """
        try:
            browser = mechanize.Browser()
            response = browser.open(url, timeout=10).read()
            return response
        except mechanize.URLError:
            raise

    def _urllib(self, url):
        """

        :param url:
        :return:
        """
        try:
            request = urllib2.Request(url,
                                      headers=self.request_headers)
            response = urllib2.urlopen(request, timeout=10).read()
            return response
        except urllib2.URLError:
            raise

    def open(self, url):
        """

        :param url:
        :return:
        """
        if self.method == 'mechanize':
            return self._mechanize(url)
        elif self.method == 'urllib':
            return self._urllib(url)
        else:
            method_choices = [m for m, o in self.method_list
                              if m.startswith('_') and m != '__init__']
            self.selected_method = random.choice(method_choices)
            return getattr(self, self.selected_method)(url)
