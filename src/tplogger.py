#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

def getTPLogger(filename: str, level) -> logging.Logger:
    logger = logging.getLogger(filename)
    if logger.hasHandlers():
        # this logger was already initialized
        return logger
    logger.setLevel(level)
    form = logging.Formatter(
            "%(asctime)s %(filename)s:%(lineno)s:%(funcName)s " +
            "%(levelname)s %(message)s")
    handler = logging.FileHandler(filename, "a", encoding=None, delay=False)
    handler.setFormatter(form)
    logger.addHandler(handler)
    return logger

