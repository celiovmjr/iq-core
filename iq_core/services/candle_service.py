import asyncio
import logging
from typing import Any, Dict, List, AsyncIterator
from asyncio import Lock
from datetime import datetime, timezone

from ..websocket import WebSocketClient
from ..entities import Candle, CandleStream

logger = logging.getLogger(__name__)


class CandleService:
    """
    🇧🇷 Serviço para obter candles históricos e stream de candles em tempo real via WebSocket.

    📋 Parâmetros:
    - ws (WebSocketClient): Cliente WebSocket para comunicação

    ⚠️ Exceções:
    - asyncio.TimeoutError: Timeout ao aguardar candles
    - Exception: Erro ao recuperar candles

    🇺🇸 Service to fetch historical and real-time candles via WebSocket.

    📋 Parameters:
    - ws (WebSocketClient): WebSocket client for communication

    ⚠️ Raises:
    - asyncio.TimeoutError: Timeout waiting for candles
    - Exception: Error retrieving candles
    """

    def __init__(self, ws: WebSocketClient) -> None:
        self._ws = ws
        self._lock = Lock()

    async def get_candles(
        self,
        active_id: int,
        quantity: int = 30,
        size: int = 300,
        from_time: datetime | None = None,
    ) -> List[Candle]:
        """
        🇧🇷 Retorna candles históricos para um ativo a partir de um horário específico (opcional).

        📋 Parâmetros:
        - active_id (int): ID do ativo
        - quantity (int): Quantidade de candles (padrão: 30)
        - size (int): Duração do candle em segundos (padrão: 300)
        - from_time (datetime | None): Horário UTC para o candle mais recente (opcional)

        📤 Retorna:
        - List[Candle]: Lista de candles ordenada do mais antigo ao mais recente

        ⚠️ Exceções:
        - asyncio.TimeoutError: Timeout ao aguardar candles
        - Exception: Erro ao recuperar candles

        🇺🇸 Returns historical candles for an asset from a specific time (optional).

        📋 Parameters:
        - active_id (int): Asset ID
        - quantity (int): Number of candles (default: 30)
        - size (int): Candle duration in seconds (default: 300)
        - from_time (datetime | None): UTC datetime for the most recent candle (optional)

        📤 Returns:
        - List[Candle] | None: Ordered list of candles from oldest to newest or None

        ⚠️ Raises:
        - asyncio.TimeoutError: Timeout waiting for candles
        - Exception: Error retrieving candles
        """
        try:
            to_timestamp = (
                int(from_time.replace(tzinfo=timezone.utc).timestamp())
                if from_time
                else self._ws.current_server_time()
            )

            response = await self._ws.request(
                {
                    "name": "get-candles",
                    "version": "2.0",
                    "body": {
                        "active_id": active_id,
                        "split_normalization": True,
                        "size": size,
                        "to": to_timestamp,
                        "count": quantity,
                    },
                }
            )

            raw_candles = response.get("candles", None)
            if not raw_candles:
                return None
            return [Candle.from_ws({**data, "size": int(size)}) for data in raw_candles]
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for candles for asset {active_id}")
        except Exception as e:
            logger.error(f"Error retrieving candles for asset {active_id}: {e}")

        return []

    async def stream(self, active_id: int, size: int) -> AsyncIterator[CandleStream]:
        """
        🇧🇷 Stream assíncrono de candles em tempo real para ativo e timeframe.

        📋 Parâmetros:
        - active_id (int): ID do ativo
        - size (int): Duração do candle em segundos

        📤 Retorna:
        - AsyncIterator[CandleStream]: Stream de candles fechados com dados OHLC

        ⚠️ Exceções:
        - Exception: Erro ao processar candle

        🇺🇸 Async stream of real-time candles for asset and timeframe.

        📋 Parameters:
        - active_id (int): Asset ID
        - size (int): Candle duration in seconds

        📤 Returns:
        - AsyncIterator[CandleStream]: Stream of closed candles with OHLC data

        ⚠️ Raises:
        - Exception: Error processing candle
        """
        params = {"routingFilters": {"active_id": active_id, "size": size}}
        queue: asyncio.Queue[CandleStream] = asyncio.Queue()

        @self._ws.handle("candle-generated")
        async def callback(data: Dict[str, Any]) -> None:
            try:
                await queue.put(item=CandleStream.from_ws(data))
            except Exception as e:
                logger.warning(f"Error processing candle: {e}")

        async with self._lock:
            await self._ws.subscribe(name="candle-generated", params=params)

        try:
            while True:
                candle = await queue.get()
                yield candle
        finally:
            async with self._lock:
                self._ws.off("candle-generated", callback)
                await self._ws.subscribe(name="candle-generated", params=params)
