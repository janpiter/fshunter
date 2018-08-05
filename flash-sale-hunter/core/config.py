from ConfigParser import ConfigParser
import os

__author__ = 'irvan'


def set_config_file(config_file="config.conf"):
    os.environ.__delitem__("CONFIG_FILE")
    os.environ.setdefault("CONFIG_FILE", config_file)
    print "Define CONFIG_FILE={}".format(os.environ.get("CONFIG_FILE"))


def load():
    config_path = "{}/{}".format(os.environ.get("CONFIG_PATH"), os.environ.get("CONFIG_FILE"))
    config = ConfigParser()
    # with open(config_path) as f:
    #     config.readfp(f)
    config.read(config_path)

    return config
