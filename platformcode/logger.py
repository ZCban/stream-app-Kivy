# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import inspect
import os
import sys
import logging
from platformcode import config

# Logging setup
DEBUG_ENABLED = config.get_setting("debug", default=False)
PLUGIN_NAME = getattr(config, "PLUGIN_NAME", "Plugin")

LOG_FORMAT = '{addname}[{filename}.{function}:{line}]{sep} {message}'

# Setup logger
logger = logging.getLogger(PLUGIN_NAME)
logger.setLevel(logging.DEBUG if DEBUG_ENABLED else logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.handlers = [handler]

def _format_log_message(msg, frame):
    filename = os.path.basename(frame.f_code.co_filename).split('.')[0]
    return LOG_FORMAT.format(
        addname=PLUGIN_NAME,
        filename=filename,
        line=frame.f_lineno,
        sep=':' if msg else '',
        function=frame.f_code.co_name,
        message=msg
    )

def info(*args):
    log(*args, level="info")

def debug(*args):
    if DEBUG_ENABLED:
        log(*args, level="debug")

def error(*args):
    log("######## ERROR #########", level="error")
    log(*args, level="error")

def log(*args, level="info"):
    msg = ' '.join(str(arg) for arg in args)
    frame = inspect.currentframe().f_back.f_back
    formatted_msg = _format_log_message(msg, frame)

    if level == "debug":
        logger.debug(formatted_msg)
    elif level == "error":
        logger.error(formatted_msg)
    else:
        logger.info(formatted_msg)

class WebErrorException(Exception):
    def __init__(self, url, channel, *args, **kwargs):
        self.url = url
        self.channel = channel
        Exception.__init__(self, *args, **kwargs)

class ChannelScraperException(Exception):
    pass
