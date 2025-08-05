from typing import Tuple
from datetime import datetime, timezone

from ..exceptions import TradingError
from ..websocket import WebSocketClient
from ..entities import Signal


class InstrumentResolver:
    """
    # pt-br: Resolve o instrumento e símbolo baseado no Signal e expiração.
    # eng: Resolves instrument and symbol based on Signal and expiration.
    """

    def __init__(self, ws: WebSocketClient):
        self._ws = ws

    async def resolve(self, signal: Signal) -> Tuple[dict, str]:
        """
        # pt-br: Resolve instrumento e símbolo para o Signal dado, validando expirações.
        # eng: Resolves instrument and symbol for the given Signal, validating expirations.

        Parameters:
            signal (Signal): signal containing instrument, direction and expiration

        Returns:
            Tuple[dict, str]: instrument and symbol for placing digital order

        Raises:
            TradingError: if expiration is not allowed or no valid symbol is found
        """

        if not signal.instrument.is_open:
            raise TradingError("Instrument is closed. Skipping signal.")

        expiration = signal.expiration.seconds()
        if expiration not in signal.instrument.trading.allowed_expirations:
            raise TradingError(
                f"Expiration {signal.expiration}min ({expiration}s) not allowed for instrument ID {signal.instrument.id}."
            )

        response = await self._ws.request({
            "name": "digital-option-instruments.get-instruments",
            "version": "3.0",
            "body": {
                "instrument_type": "digital-option",
                "asset_id": signal.instrument.id,
            },
        })

        instruments = response.get("instruments", [])
        if not instruments:
            raise TradingError(f"No instruments found for asset ID {signal.instrument.id}.")

        now_ts = int(datetime.now(timezone.utc).timestamp())
        expiration_ts_limit = now_ts + expiration

        # pt-br: Filtra o instrumento com o período correto e expiração próxima
        # eng: Filter instrument with matching period and near expiration
        instrument = next(
            (
                i for i in instruments
                if i["period"] == expiration
                and now_ts <= i["expiration"] <= expiration_ts_limit
            ),
            None,
        )

        if instrument is None:
            raise TradingError(
                f"No valid instrument with period={expiration}s and expiration within {expiration}s from now."
            )

        data = instrument.get("data", [])
        direction = signal.direction.value

        # pt-br: Tenta primeiro o strike "SPT" (mais recente e confiável)
        # eng: Try "SPT" strike first (most recent and reliable)
        spt_entry = next(
            (p for p in data if p.get("strike") == "SPT" and direction in p),
            None
        )
        if spt_entry:
            return instrument, spt_entry[direction]["symbol"]

        # pt-br: Fallback — tenta os N últimos strikes mais altos para a direção
        # eng: Fallback — try last N highest strikes for the given direction
        MAX_STRIKES_TO_TRY = 3
        candidates = sorted(
            (
                p for p in data
                if p.get("direction") == direction and "symbol" in p
            ),
            key=lambda x: x.get("value", 0),  # pt-br: ajuste se campo de valor for diferente / eng: adjust if strike field is different
            reverse=True
        )

        for entry in candidates[:MAX_STRIKES_TO_TRY]:
            symbol = entry.get("symbol")
            if symbol:
                return instrument, symbol

        raise TradingError(
            f"No symbol found for direction '{direction}' in the last {MAX_STRIKES_TO_TRY} strikes."
        )
