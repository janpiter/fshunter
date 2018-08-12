import logging
from raven import Client

from fshunter.helper.config import load


def logger(message, level='Message'):
    """
    Wrapping and formatting print out and/or sending error to Sentry.
    :param message: <string> log message.
    :param level: <string> set 'Error' for capture to Sentry.
                  Default 'Message'.
    :return: None
    """
    config = load()
    sentry_client = Client(config.get("sentry", "host"))
    logging.basicConfig(format='%(asctime)s %(message)s')

    if level and level.lower() == 'error':
        sentry_client.captureException()

    logging.warning(message)
