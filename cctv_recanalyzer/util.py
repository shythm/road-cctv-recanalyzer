import os
import sys
import logging
from dotenv import load_dotenv

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s (%(name)s:%(threadName)s:%(thread)d)")
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    return logger

load_dotenv()
def get_env_force(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f'{key} is not set')
    return value

from datetime import datetime
def datetime_to_str(dt: datetime) -> str:
    # 국제 표준 포맷인 ISO 8601 형식으로 변환
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def str_to_datetime(dtstr: str) -> datetime:
    return datetime.strptime(dtstr, "%Y-%m-%dT%H:%M:%S")
