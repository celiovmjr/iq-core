import socket, functools
from aiohttp import (
    ClientConnectorError,
    ClientConnectorSSLError,
    ClientConnectorDNSError,
)
from ..exceptions import NetworkUnavailableError


def handle_network_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            print(f"Decorador capturou exceção: {type(e)} - {e}")
            if isinstance(
                e,
                (
                    socket.gaierror,
                    ClientConnectorError,
                    ClientConnectorSSLError,
                    ClientConnectorDNSError,
                ),
            ):
                raise NetworkUnavailableError(
                    "Connection error: please check your internet connection."
                ) from e
            raise

    return wrapper
