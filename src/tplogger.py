#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

def getTPLogger(filename, level):
    logger = logging.getLogger(filename)
    logger.setLevel(level)
    form = logging.Formatter(
            "%(asctime)s %(filename)s:%(lineno)s:%(funcName)s " +
            "%(levelname)s %(message)s")
    handler = logging.FileHandler(filename, "w", encoding=None, delay=False)
    handler.setFormatter(form)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

