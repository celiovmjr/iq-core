from typing import AsyncGenerator
from contextlib import asynccontextmanager
from ..websocket import WebSocketClient


class CotationService:
    """
    🇧🇷 Serviço de cotação para obter dados de velas e extrair informações de preço.

    🇺🇸 Cotation service to fetch candle data and extract price information.
    """

    def __init__(self, ws: WebSocketClient) -> None:
        """
        🇧🇷 Inicializa com o cliente WebSocket.

        🇺🇸 Initialize with the WebSocket client.

        Args:
            ws (WebSocketClient): Cliente WebSocket com métodos async subscribe, receive e unsubscribe.
        """
        self._ws = ws

    @asynccontextmanager
    async def _subscribe(self, active_id: int, size: int = 300) -> AsyncGenerator[dict, None]:
        """
        🇧🇷 Context manager para subscrever e desinscrever do canal 'candle-generated'.

        🇺🇸 Context manager to subscribe/unsubscribe from 'candle-generated' channel.

        Yields:
            dict: Dados recebidos do WebSocket.
        """
        params = {"routingFilters": {"active_id": active_id, "size": size}}
        await self._ws.subscribe(name="candle-generated", params=params)
        try:
            yield await self._ws.receive("candle-generated", timeout=30)
        finally:
            await self._ws.unsubscribe(name="candle-generated", params=params)

    async def generate(self, active_id: int, size: int = 300) -> int | None:
        """
        🇧🇷 Obtém a parte decimal do preço de fechamento da próxima vela.

        🇺🇸 Gets the decimal part of the close price from the next candle.

        Args:
            active_id (int): ID do ativo.
            size (int): Tamanho da vela em segundos (default 300).

        Returns:
            int | None: Parte decimal do preço de fechamento, ou None se indisponível.
        """
        async with self._subscribe(active_id, size) as data:
            close = data.get("close", None)
            if close is None:
                return None

            close = str(close).split(".")[1]
            return int(close) if close else None
