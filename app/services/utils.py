import logging
from datetime import datetime
from functools import wraps
from random import uniform
from smtplib import SMTPException
from time import sleep
from typing import Callable, Tuple, Type, Union

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def is_first_of_month() -> bool:
    """Return True if today is the first day of the month, otherwise False."""
    today = datetime.today()
    return today.day == 1


def run_today(today: int) -> bool:
    """Return true if today is that day of the month"""
    current_day = datetime.today()
    return current_day.day == today


def retry_request(
    max_attempts=3,
    backoff=1,
    exceptions=(requests.RequestException,),
    retry_if_false=False,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Ensure exceptions is a tuple
            exception_types = (
                exceptions if isinstance(exceptions, tuple) else (exceptions,)
            )

            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if retry_if_false and (result is False or result is None):
                        if attempt == max_attempts:
                            return result
                        else:
                            raise ValueError("Function returned False/None, retrying")
                    return result

                except exception_types + ((ValueError,) if retry_if_false else ()):
                    if attempt == max_attempts:
                        raise

                    sleep_time = backoff * (2 ** (attempt - 1))
                    print(f"Retry {attempt}/{max_attempts} after {sleep_time}s")
                    sleep(sleep_time)

        return wrapper

    return decorator


def retry_email(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (
        SMTPException,
        ConnectionError,
        TimeoutError,
        OSError,
    ),
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(f"Email sent successfully on attempt {attempt}")
                    return result

                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Email sending failed after {max_attempts} attempts. Last error: {e}"
                        )
                        raise

                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)), max_delay
                    )
                    if jitter:
                        delay *= uniform(0.9, 1.1)

                    logger.warning(
                        f"Email attempt {attempt} failed: {e}. Retrying in {delay:.2f}s..."
                    )
                    sleep(delay)

        return wrapper

    return decorator
