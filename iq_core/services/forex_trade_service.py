from .interfaces import TradingService
from ..exceptions import TradingError
from ..entities import Signal
from ..websocket import WebSocketClient


class ForexTradeService(TradingService):
    def __init__(self, ws: WebSocketClient) -> None:
        self._ws = ws

    async def open_trade(self, signal: Signal) -> str:
        if signal.type != signal.type.FOREX:
            raise TradingError("ForexTradeService aceita somente sinais do tipo FOREX")

        payload = {
            "name": "sendMessage",
            "msg": {
                "name": "forex.open-position",
                "version": "1.0",
                "body": {
                    "active_id": signal.instrument.id,
                    "direction": signal.direction.value,
                    "amount": signal.amount,
                    "expiration": signal.expiration,
                    "timestamp": int(signal.time.timestamp()),
                },
            },
        }
        request_id = await self._ws.send(payload)
        response = await self._ws.receive(request_id=request_id, timeout=10)
        if not response or not response.get("success"):
            raise TradingError(f"Erro ao abrir operação Forex: {response}")

        trade_id = response.get("trade_id")
        if not trade_id:
            raise TradingError("Resposta não contém trade_id")

        return trade_id

    async def close_trade(self, trade_id: str) -> bool:
        payload = {
            "name": "sendMessage",
            "msg": {
                "name": "forex.close-position",
                "version": "1.0",
                "body": {"trade_id": trade_id},
            },
        }
        request_id = await self._ws.send(payload)
        response = await self._ws.receive(request_id=request_id, timeout=10)
        return response is not None and response.get("success", False)

    async def trade_status(self, trade_id: str) -> dict:
        payload = {
            "name": "sendMessage",
            "msg": {
                "name": "forex.get-position",
                "version": "1.0",
                "body": {"trade_id": trade_id},
            },
        }
        request_id = await self._ws.send(payload)
        response = await self._ws.receive(request_id=request_id, timeout=10)
        if not response or not response.get("success"):
            raise TradingError(f"Erro ao consultar operação Forex: {response}")
        return response.get("position", {})
