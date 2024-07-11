import sys
import logging

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s (%(name)s:%(threadName)s:%(thread)d)")
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    return logger
