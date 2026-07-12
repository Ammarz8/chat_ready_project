import time
import random
import logging
from functools import wraps
from typing import Callable, Any, TypeVar, Tuple
import requests

logger = logging.getLogger(__name__)

T = TypeVar("T")

def retry_api_request(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    A decorator for retrying API requests with exponential backoff, jitter,
    and customized handling for HTTP 429 (Rate Limiting).
    
    Args:
        max_retries (int): Maximum number of retry attempts.
        base_delay (float): The initial sleep delay in seconds.
        max_delay (float): The maximum delay limit in seconds.
        retryable_status_codes (tuple): HTTP status codes that warrant a retry.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = base_delay
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as http_err:
                    status_code = (
                        http_err.response.status_code 
                        if http_err.response is not None 
                        else None
                    )
                    
                    # If the status code is not retryable (e.g. 400, 401, 403), raise immediately
                    if status_code not in retryable_status_codes:
                        logger.error(
                            f"Non-retryable HTTP status code ({status_code}) encountered. "
                            f"Aborting execution. Error: {http_err}"
                        )
                        raise http_err

                    if attempt == max_retries:
                        logger.error(
                            f"Max retry attempts ({max_retries}) exhausted for HTTP error. "
                            f"Aborting execution. Error: {http_err}"
                        )
                        raise http_err

                    # Special handling for HTTP 429 (Rate Limit Exceeded)
                    if status_code == 429:
                        sleep_time = 10.0  # Default fallback wait
                        if http_err.response is not None:
                            retry_after_header = http_err.response.headers.get("Retry-After")
                            if retry_after_header:
                                try:
                                    sleep_time = float(retry_after_header)
                                    logger.warning(
                                        f"HTTP 429 Rate Limit hit. Respecting Retry-After header: "
                                        f"sleeping for {sleep_time} seconds."
                                    )
                                except ValueError:
                                    logger.warning(
                                        f"HTTP 429 Rate Limit hit. Invalid Retry-After header value "
                                        f"('{retry_after_header}'). Falling back to {sleep_time} seconds."
                                    )
                        else:
                            logger.warning(
                                f"HTTP 429 Rate Limit hit. No response object found. "
                                f"Sleeping for {sleep_time} seconds."
                            )
                        time.sleep(sleep_time)
                        continue

                    # Exponential backoff with random jitter for other codes (e.g. 500, 502)
                    jitter = random.uniform(0, 0.5 * delay)
                    sleep_time = min(delay + jitter, max_delay)
                    logger.warning(
                        f"Attempt {attempt} failed with HTTP status code {status_code}. "
                        f"Retrying in {sleep_time:.2f} seconds..."
                    )
                    time.sleep(sleep_time)
                    delay *= 2

                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as net_err:
                    if attempt == max_retries:
                        logger.error(
                            f"Max retry attempts ({max_retries}) exhausted for network error. "
                            f"Aborting execution. Error: {net_err}"
                        )
                        raise net_err

                    # Exponential backoff with random jitter for connection errors/timeouts
                    jitter = random.uniform(0, 0.5 * delay)
                    sleep_time = min(delay + jitter, max_delay)
                    logger.warning(
                        f"Attempt {attempt} failed due to connection/timeout error: {net_err}. "
                        f"Retrying in {sleep_time:.2f} seconds..."
                    )
                    time.sleep(sleep_time)
                    delay *= 2
            
            # Safe fallback if loop exits without throwing/returning
            raise RuntimeError("Exponential backoff retry loop terminated unexpectedly.")
        return wrapper
    return decorator
