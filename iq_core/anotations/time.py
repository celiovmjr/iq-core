import asyncio
import time
import logging
from functools import wraps
from typing import Callable, Concatenate, ParamSpec, TypeVar

# Tipos genéricos
P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


def measure_time(
    func: Callable[Concatenate[object, P], R],
) -> Callable[Concatenate[object, P], R]:
    """
    Decorator to log execution time in seconds with high precision.
    Works for both sync and async methods.

    Decorador para registrar o tempo de execução em segundos com alta precisão.
    Funciona com métodos síncronos e assíncronos.
    """
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start
            logger.debug(f"{func.__qualname__} executed in {duration:.3f} s")
            return result

        return async_wrapper  # type: ignore

    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        logger.debug(f"{func.__qualname__} executed in {duration:.3f} s")
        return result

    return sync_wrapper
