import logging
import asyncio
from .interfaces import TradingService
from ..exceptions import TradingError
from ..entities import Profile, Signal, TradeResult, InstrumentType
from .cotation_service import CotationService
from ..websocket import WebSocketClient

logger = logging.getLogger(__name__)


class BinaryTradeService(TradingService):
    def __init__(self, ws: WebSocketClient, profile: Profile) -> None:
        self._ws = ws
        self._profile = profile
        self._cotation = CotationService(ws)
        self._lock = asyncio.Lock()

    async def open_trade(self, signal: Signal) -> str:
        if signal.type != signal.type.BINARY:
            raise TradingError("BinaryTradeService accepts only BINARY type signals")
        
        if InstrumentType.BINARY not in signal.instrument.type:
            raise TradingError("Instrument does not support BINARY operations.")

        cotation = await self._cotation.generate(signal.instrument.id)
        if not cotation:
            raise TradingError(f"Failed to fetch candle data for instrument {signal.instrument.id}")

        expiration, _ = self._ws.get_expiration(signal.expiration.minutes())
        idx = (expiration - self._ws.current_server_time(ms=False)) / 60
        type_id = 3 if idx < 5 else 1

        response = await self._ws.request({
            "name": "binary-options.open-option",
            "version": "1.0",
            "body": {
                "user_balance_id": signal.account_id,
                "active_id": signal.instrument.id,
                "option_type_id": type_id,
                "direction": signal.direction.value,
                "expired": expiration,
                "refund_value": 0,
                "price": float(signal.amount),
                "value": cotation,
                "profit_percent": signal.instrument.trading.profit.get("turbo" if type_id == 3 else "binary")
            },
        })

        if not response or not response.get("id", None):
            message = (
                response["message"]
                if response and "message" in response
                else "Unknown error"
            )
            raise TradingError(f"Error opening Binary trade: '{message}'")

        return str(response.get("id"))

    async def trade_status(self, trade_id: str) -> tuple[bool, TradeResult | None]:
        """
        🇧🇷 Consulta única ao histórico para verificar se a operação foi encerrada.

        📋 Parâmetros:
        - trade_id (str): ID externo da operação

        📤 Retorna:
        - tuple[bool, TradeResult | None]: (True, TradeResult) se encontrada e encerrada; (False, None) caso contrário

        ⚠️ Exceções:
        - TradingError: Erro ao consultar status da operação

        🇺🇸 One-shot query to check if the trade is already closed.

        📋 Parameters:
        - trade_id (str): External ID of the trade

        📤 Returns:
        - tuple[bool, TradeResult | None]: (True, TradeResult) if found and closed; (False, None) otherwise

        ⚠️ Raises:
        - TradingError: Error querying trade status
        """
        response = await self._ws.request({
            "name": "portfolio.get-history-positions",
            "version": "2.0",
            "body": {
                "user_id": self._profile.id,
                "user_balance_id": self._profile.balance_id,
                "instrument_types": [
                    "turbo-option",
                    "binary-option",
                ],
                "offset": 0,
                "limit": 30,
            },
        })

        if not response or "positions" not in response:
            logger.error(f"No positions returned while querying trade status for ID {trade_id}")
            return (False, None)

        positions = response["positions"]
        position = next(
            (p for p in positions if p.get("external_id") == int(trade_id)), None
        )

        return (
            (False, None) if not position else (True, TradeResult.from_dict(position))
        )
