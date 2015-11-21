import logging

def getTPLogger(filename: str, level) -> logging.Logger:
    logger = logging.getLogger(filename)
    logger.setLevel(level)
    form = logging.Formatter(
            "%(asctime)s %(filename)s:%(lineno)s:%(funcName)s " +
            "%(levelname)s %(message)s")
    handler = logging.FileHandler(filename, "a", encoding=None, delay=False)
    handler.setFormatter(form)
    logger.addHandler(handler)

