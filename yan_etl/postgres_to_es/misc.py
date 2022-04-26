import logging
import time
from functools import wraps

logger = logging.getLogger()


def backoff(exception, start_sleep_time=0.1, factor=2, border_sleep_time=10, retry_limit=100):
    """
    A function to re-execute the function after a while if an error occurs.
    Uses a naive exponential growth of the retry time (factor) to the border timeout (border_sleep_time)
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            delay = start_sleep_time
            retry = 0
            while True:
                try:
                    connection = func(*args, **kwargs)
                    return connection
                except exception as e:
                    logger.exception(f"Retry {retry} up connection after delay {delay} seconds\nError message: {e}")
                    if delay >= border_sleep_time:
                        delay = border_sleep_time
                    else:
                        delay += start_sleep_time * 2 ** factor
                    time.sleep(delay)
                    retry += 1
                if retry == retry_limit:
                    raise exception

        return inner

    return func_wrapper
