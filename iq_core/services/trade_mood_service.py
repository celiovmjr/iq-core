import asyncio
import logging
from typing import AsyncIterator, Any, Callable

logger = logging.getLogger(__name__)

class TraderMoodService:
    """
    🇧🇷 Serviço para assinatura reativa e contínua do humor do trader por instrumento.

    📋 Parâmetros:
    - ws (WebSocketClient): Cliente WebSocket para comunicação

    ⚠️ Exceções:
    - Exception: Erro durante processamento de dados

    🇺🇸 Service for reactive and continuous trader mood subscription by instrument.

    📋 Parameters:
    - ws (WebSocketClient): WebSocket client for communication

    ⚠️ Raises:
    - Exception: Error during data processing
    """

    def __init__(self, ws: Any) -> None:
        self._ws = ws
        self._lock = asyncio.Lock()

    async def subscribe(self, instrument_id: int) -> AsyncIterator[int]:
        """
        🇧🇷 Async generator que emite continuamente os valores de humor do trader.

        📋 Parâmetros:
        - instrument_id (int): ID do instrumento para filtrar

        📤 Retorna:
        - AsyncIterator[int]: Valores de humor do trader (0 a 100)

        ⚠️ Exceções:
        - Exception: Erro durante processamento de dados

        🇺🇸 Async generator that continuously emits trader mood values.

        📋 Parameters:
        - instrument_id (int): Instrument ID to filter

        📤 Returns:
        - AsyncIterator[int]: Trader mood values (0 to 100)

        ⚠️ Raises:
        - Exception: Error during data processing
        """
        queue: asyncio.Queue[int] = asyncio.Queue()

        @self._ws.handle("traders-mood-changed")
        async def callback(data: dict[str, Any]) -> None:
            if int(data.get("asset_id", -1)) == instrument_id:
                try:
                    value = int(float(data.get("value", 0)) * 100)
                    value = max(0, min(value, 100))
                except Exception:
                    value = 0
                await queue.put(value)

        async with self._lock:
            await self._ws.subscribe(
                name="traders-mood-changed",
                params={
                    "routingFilters": {
                        "instrument": "turbo-option",
                        "asset_id": str(instrument_id),
                    }
                },
            )

        try:
            while True:
                mood = await queue.get()
                yield mood
        finally:
            self._ws.off("traders-mood-changed", callback)
            await self._ws.unsubscribe(
                name="traders-mood-changed",
                params={
                    "routingFilters": {
                        "instrument": "turbo-option",
                        "asset_id": str(instrument_id),
                    }
                },
            )
            logger.info(f"Unsubscribed trader mood for instrument {instrument_id}")
