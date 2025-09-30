import socket, functools, logging
from aiohttp import (
    ClientConnectorError,
    ClientConnectorSSLError,
    ClientConnectorDNSError,
)
from ..exceptions import NetworkUnavailableError

logger = logging.getLogger(__name__)


def handle_network_errors(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.debug(f"Network decorator caught exception: {type(e).__name__} - {e}")
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
