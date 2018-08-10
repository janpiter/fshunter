from raven import Client
from termcolor import colored
from datetime import datetime

from fshunter.core.config import load


def logger(message, level=None, color=None):
    """
    Wrapping and formatting print out and/or sending error to Sentry.
    :param message: <string> log message.
    :param level: <string> set 'Error' for capture to Sentry.
                  Default 'Message'.
    :param color: choices -> ['grey','red','green','yellow','blue',
                              'magenta','cyan','white'].
    :return: None
    """
    config = load()
    sentry_client = Client(config.get("sentry", "host"))
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if level and level.lower() == 'error':
        sentry_client.captureException()
        color = 'red'
    if color:
        print colored('[{date}] -- {message}'.format(date=current_time,
                                                     message=message), color)
    else:
        print '[{date}] -- {message}'.format(date=current_time,
                                             message=message)
