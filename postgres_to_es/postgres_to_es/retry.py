import logging
import time
from functools import wraps


def backoff(
        exc=Exception,
        start_sleep_time: float = 0.1,
        factor: int = 2,
        border_sleep_time: int = 10,
        command: str = None,
        logger: logging.Logger = None,
):
    """
    Retry decorator with exp() formula.
    Args:
        exc: one Exception or tuple[Exceptions, ...]
        start_sleep_time: float
        factor: int
        border_sleep_time: int
        command: str Name of callable to call if exc occurs.
        logger: logger.warning(fmt, delay) will be called on failed attempts.
                   default: None, logging is disabled.
    Returns:
        Wrapped func result.
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            n = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exc:
                    t = start_sleep_time * factor ** n
                    if t > border_sleep_time:
                        t = border_sleep_time
                    if logger is not None:
                        logger.warning("Retry operation in %s seconds.", t)
                    time.sleep(t)
                    if command:
                        try:
                            cls = args[0]
                            method = getattr(cls, command)
                            method()
                        except Exception as e:
                            logger.error(e)
                    n += 1

        return inner

    return func_wrapper
