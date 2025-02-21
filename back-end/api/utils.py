import asyncio
import logging
from asyncio.futures import Future
from typing import Any, Coroutine


class RetryError(Exception):
    """ Raised when exp_backoff fails too many times. """
    pass


async def exp_sleep(attempt: int, base: float = 2) -> None:
    if attempt < 0 or base < 0:
        raise ValueError("attempt and base must be non-negative")

    await asyncio.sleep(base ** attempt - 1)


async def exp_backoff(coro: Coroutine, attempts: int = 5,
                      timeout: float = 1, base: float = 2) -> Any:
    """ Retries a coroutine with exponential backoff. """

    for attempt in range(attempts):
        logging.info(f"Attempt {attempt}.")
        await exp_sleep(attempt, base=base)
        try:
            result = await asyncio.wait_for(asyncio.shield(coro), timeout=timeout)

        except TimeoutError:
            continue

        except Exception as e:
            raise e

        else:
            break
    else:
        raise RetryError(
            f"Unable to execute coroutine after {attempts} attempts.")

    return result
