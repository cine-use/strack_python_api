# coding=utf8
# Copyright (c) 2016 Strack

import os
import sys
import time
import logging
import logging.handlers


def strack_log(logger_name=None, level=logging.DEBUG,
               log_format='%(asctime)s - STRACK API - %(filename)s:%(lineno)s - %(message)s'):

    time_code = time.time()
    LOG_FILE = os.path.join(os.environ.get("TMP"), 'STRACK_API_%s.log' % time_code)

    if not logger_name:
        logger_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024, backupCount=5)  # 实例化handler

    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)

    logger = logging.getLogger(logger_name)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


if __name__ == "__main__":
    test_log = strack_log()
    test_log.debug("test debug")
    test_log.info("test info")
    test_log.warning("test warning")
    test_log.error("test error")
    test_log.critical("test critical")
