import logging
from typing import Tuple
from datetime import datetime, timezone

from .interfaces import TradingService
from .instrument_resolver import InstrumentResolver
from ..exceptions import TradingError
from ..entities import Profile, Signal, TradeResult, InstrumentType
from ..websocket import WebSocketClient

logger = logging.getLogger(__name__)


class DigitalTradeService(TradingService):
    def __init__(self, ws: WebSocketClient, profile: Profile) -> None:
        self._ws = ws
        self._profile = profile
        self._resolver = InstrumentResolver(ws)

    async def open_trade(self, signal: Signal) -> str:
        """
        🇧🇷 Abre uma operação digital baseada em um sinal.
        
        📋 Parâmetros:
        - signal (Signal): Sinal de entrada

        📤 Retorna:
        - str: ID da operação

        ⚠️ Exceções:
        - TradingError: Em caso de falha na resolução ou execução

        🇺🇸 Opens a digital trade based on a trading signal.
        
        📋 Parameters:
        - signal (Signal): Input trade signal

        📤 Returns:
        - str: Trade operation ID

        ⚠️ Raises:
        - TradingError: On resolution or execution failure
        """
        if signal.type != signal.type.DIGITAL:
            raise TradingError("Only DIGITAL signals are supported.")

        if InstrumentType.DIGITAL not in signal.instrument.type:
            raise TradingError("Instrument does not support DIGITAL operations.")

        instrument, symbol = await self._resolver.resolve(signal)

        if not instrument or not symbol:
            raise TradingError(
                f"[Resolver Error] Instrument not found for asset_id={signal.instrument.id}, "
                f"expiration={signal.expiration.minutes()}min, direction={signal.direction.value.upper()}"
            )

        response = await self._ws.request({
            "name": "digital-options.place-digital-option",
            "version": "3.0",
            "body": {
                "user_balance_id": signal.account_id,
                "instrument_id": symbol,
                "amount": str(int(signal.amount)),
                "instrument_index": instrument.get("index"),
                "asset_id": signal.instrument.id,
            },
        })

        if not response or not response.get("id"):
            message = response.get("message", "Unknown error")
            raise TradingError(
                f"Failed to place digital trade: {message} | symbol={symbol} | {datetime.now(timezone.utc).strftime('A%Y%m%dD%H%M') + '00'}"
            )
        
        logger.debug(f"symbol={symbol} | {datetime.now(timezone.utc).strftime('A%Y%m%dD%H%M') + '00'}")
        return str(response["id"])

    async def trade_status(self, trade_id: str) -> Tuple[bool, TradeResult | None]:
        """
        🇧🇷 Verifica se a operação foi encerrada.
        🇺🇸 Checks if the trade is closed.

        📋 Parâmetros / Parameters:
        - trade_id (str): ID da operação

        📤 Retorna / Returns:
        - Tuple[bool, TradeResult | None]: True + resultado se encerrada, senão False
        """
        response = await self._ws.request({
            "name": "portfolio.get-history-positions",
            "version": "2.0",
            "body": {
                "user_id": self._profile.id,
                "user_balance_id": self._profile.balance_id,
                "instrument_types": ["digital-option"],
                "offset": 0,
                "limit": 30,
            },
        })

        if not response or "positions" not in response:
            logger.warning(f"No positions returned while querying trade status for ID {trade_id}")
            return False, None

        positions = response["positions"]
        position = next(
            (
                p
                for p in positions
                for oid in p.get("raw_event", {})
                            .get("digital_options_position_changed1", {})
                            .get("order_ids", [])
                if oid == trade_id
            ),
            None
        )

        return (
            (False, None) if not position else (True, TradeResult.from_dict(position))
        )
