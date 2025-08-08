import logging
import asyncio
from .interfaces import TradingService
from ..exceptions import TradingError
from ..entities import (
    Profile,
    Signal,
    SignalType,
    TradeResult,
    InstrumentType
)
from .cotation_service import CotationService
from ..websocket import WebSocketClient

logger = logging.getLogger(__name__)


class BlitzTradeService(TradingService):
    """
    🇧🇷 Serviço para abrir e monitorar operações Blitz (opções binárias rápidas).

    Este serviço gerencia operações Blitz, utilizando mensagens WebSocket específicas,
    tratando tempos de expiração em segundos e parâmetros próprios para este tipo de operação.

    🇺🇸 Service to open and monitor Blitz trades (fast BLITZ options).

    This service manages Blitz trades using specific WebSocket messages,
    handling expiration times in seconds and parameters specific to this trade type.
    """

    def __init__(self, ws: WebSocketClient, profile: Profile) -> None:
        """
        🇧🇷 Inicializa o serviço com o cliente WebSocket e o perfil do usuário.

        🇺🇸 Initializes the service with the WebSocket client and user profile.

        Args:
            ws (WebSocketClient): Instância do cliente WebSocket para comunicação.
            profile (Profile): Perfil do usuário autenticado.
        """

        self._ws = ws
        self._profile = profile
        self._cotation = CotationService(ws)
        self._lock = asyncio.Lock()

    async def open_trade(self, signal: Signal) -> str:
        """
        🇧🇷 Abre uma operação Blitz com base no sinal fornecido.

        Envia uma mensagem via WebSocket para abrir uma opção Blitz, usando o
        tempo de expiração em segundos (expiration_size) e configurando os demais parâmetros
        necessários para a negociação.

        📋 Parâmetros:
        - signal (Signal): Sinal contendo os dados da operação, incluindo ativo, valor, direção,
          tipo (deve ser BLITZ), e expiração (como Duration).

        📤 Retorna:
        - str: ID da operação aberta, conforme retorno do servidor.

        ⚠️ Exceções:
        - TradingError: Lançado se o tipo do sinal não for BLITZ, o instrumento não suportar Blitz,
          ou se a resposta do servidor indicar erro ao abrir a operação.

        🇺🇸 Opens a Blitz trade based on the provided signal.

        Sends a WebSocket message to open a Blitz option, using expiration time in seconds
        (expiration_size) and setting the necessary parameters for trading.

        📋 Parameters:
        - signal (Signal): Signal containing trade data including instrument, amount, direction,
          type (must be BLITZ), and expiration (as Duration).

        📤 Returns:
        - str: Trade ID as returned by the server.

        ⚠️ Raises:
        - TradingError: Raised if the signal type is not BLITZ, the instrument does not support Blitz,
          or the server response indicates failure.
        """
        if signal.type != SignalType.BLITZ:
            raise TradingError("BlitzTradeService accepts only BLITZ type signals")

        if InstrumentType.BLITZ not in signal.instrument.type:
            raise TradingError("Instrument does not support BLITZ operations.")

        cotation = await self._cotation.generate(signal.instrument.id)
        if not cotation:
            raise TradingError(f"Failed to fetch candle data for instrument {signal.instrument.id}")

        async with self._lock:
            response = await self._ws.request({
                "name": "binary-options.open-option",
                "version": "2.0",
                "body": {
                    "user_balance_id": signal.balance_id,
                    "active_id": signal.instrument.id,
                    "option_type_id": 12,
                    "direction": signal.direction.value,
                    "expired": int(self._ws.current_server_time(ms=False)+signal.expiration.seconds()),
                    "refund_value": 0,
                    "price": float(signal.amount),
                    "value": cotation,
                    "profit_percent": signal.instrument.trading.profit.get("turbo", 0),
                    "expiration_size": int(signal.expiration.seconds()),
                },
            })

        if not response or not response.get("id"):
            message = response.get("message", "Unknown error") if response else "No response"
            raise TradingError(f"Error opening Blitz trade: '{message}'")

        return str(response["id"])

    async def trade_status(self, trade_id: str) -> tuple[bool, TradeResult | None]:
        """
        🇧🇷 Consulta única ao histórico para verificar se a operação Blitz foi encerrada.

        Obtém o status da operação Blitz pelo ID externo, retornando se está encerrada
        e, se disponível, os detalhes da operação.

        📋 Parâmetros:
        - trade_id (str): ID externo da operação a consultar.

        📤 Retorna:
        - tuple[bool, TradeResult | None]: Tupla onde o primeiro elemento indica se a operação foi encontrada e encerrada,
          e o segundo é o resultado da operação ou None se não encontrado.

        ⚠️ Exceções:
        - TradingError: Caso ocorra erro na consulta via WebSocket.

        🇺🇸 One-shot query to check if the Blitz trade is closed.

        Retrieves the status of a Blitz trade by its external ID, returning whether it is closed
        and, if available, the trade details.

        📋 Parameters:
        - trade_id (str): External ID of the trade to query.

        📤 Returns:
        - tuple[bool, TradeResult | None]: Tuple where the first element indicates if the trade was found and closed,
          and the second is the trade result or None if not found.

        ⚠️ Raises:
        - TradingError: If an error occurs querying the trade status.
        """
        try:
            response = await self._ws.request(
                {
                    "name": "portfolio.get-history-positions",
                    "version": "2.0",
                    "body": {
                        "user_id": self._profile.id,
                        "user_balance_id": self._profile.balance_id,
                        "instrument_types": ["blitz-option"],
                        "offset": 0,
                        "limit": 30,
                    },
                }
            )
        except Exception as e:
            raise TradingError(f"Error fetching trade status: {e}") from e

        if not response or "positions" not in response:
            return False, None

        positions = response["positions"]
        position = next(
            (p for p in positions if str(p.get("external_id")) == trade_id), None
        )

        return (bool(position), TradeResult.from_dict(position) if position else None)
