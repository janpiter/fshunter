from ConfigParser import ConfigParser
import os

__author__ = 'irvan'


def load(config_file="config.conf"):
    config_path = "{}/{}".format(os.getcwd(), config_file)
    config = ConfigParser()
    config.read(config_path)
    return config
