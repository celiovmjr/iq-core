from abc import ABC, abstractmethod
from typing import Coroutine, Any
from ...entities import Signal, TradeResult


class TradingService(ABC):
    """
    Interface base para serviços de negociação.
    Define contrato para abrir e checar operações.
    """

    @abstractmethod
    async def open_trade(self, signal: Signal) -> str:
        """
        Abre uma operação baseada no sinal fornecido.
        """
        pass

    @abstractmethod
    async def trade_status(
        self, trade_id: int
    ) -> Coroutine[Any, Any, tuple[bool, TradeResult]]:
        """
        Consulta o status de uma operação aberta.
        """
        pass
