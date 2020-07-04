import logging
import logzero
import os
from decouple import config

APP_PORT = config("APP_PORT")
MONGO_URI = config("MONGO_URI")
MONGO_DB = config("MONGO_DB")


def config_logs():
    logzero.logfile("logfile.log", maxBytes=1000000, backupCount=3, loglevel=logging.ERROR)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')

    logzero.formatter(formatter)