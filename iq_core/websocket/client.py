import asyncio
import json
import logging
from typing import (
    Any,
    Literal,
    Awaitable,
    Callable,
    Self
)
from websockets import connect
from websockets.client import WebSocketClientProtocol
from time import time, mktime
from datetime import datetime, timedelta

from ..entities import Message
from ..exceptions import IQOptionError, TradingError

logger = logging.getLogger(__name__)


class WebSocketClient:
    """
    🇧🇷 Cliente WebSocket robusto usando a entidade Message para protocolo IQ Option.

    🇺🇸 Robust WebSocket client using Message entities for IQ Option protocol.
    """

    def __init__(self) -> None:
        """
        🇧🇷 Inicializa o cliente WebSocket.

        🇺🇸 Initializes the WebSocket client.
        """
        self._ws: WebSocketClientProtocol | None = None
        self._request_id: int = 1
        self._listen_task: asyncio.Task | None = None
        self._closing: bool = False
        self._futures_by_id: dict[str, asyncio.Future] = {}
        self._futures_by_name: dict[str, list[asyncio.Future]] = {}
        self._subscribers: dict[
            str, list[Callable[[dict[str, Any]], Awaitable[None]]]
        ] = {}
        self._server_time: int | None = None
        self._connection_start_ms: int = 0

    async def connect(self, ssid: str) -> Self:
        """
        🇧🇷 Estabelece conexão WebSocket e autentica com ssid.

        📋 Parâmetros:
        - ssid (str): Token de sessão para autenticação.

        📤 Retorna:
        - Self: Instância do cliente após conexão.

        ⚠️ Exceções:
        - ConnectionError: Se a conexão falhar.

        🇺🇸 Establish WebSocket connection and authenticate with ssid.

        📋 Parameters:
        - ssid (str): Session token for authentication.

        📤 Returns:
        - Self: Client instance after connection.

        ⚠️ Raises:
        - ConnectionError: If connection fails.
        """
        self._ws = await connect(
            "wss://iqoption.com/echo/websocket",
            max_size=2**24,
            compression="deflate"
        )

        self._connection_start_ms = int(time() * 1000)
        await self.authenticate(ssid)
        self.on("timeSync", self._on_time_sync)
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("WebSocket connection established.")
        return self

    async def subscribe(
        self,
        name: str,
        version: Literal["1.0", "2.0", "3.0", "4.0", "5.0"] | None = None,
        params: dict | None = None,
    ) -> str:
        """
        🇧🇷 Assina evento por nome.

        📋 Parâmetros:
        - name (str): Nome do evento para assinatura.
        - version (str | None): Versão do evento (ex: "1.0").
        - params (dict | None): Parâmetros adicionais para assinatura.

        📤 Retorna:
        - str: ID da requisição da assinatura.

        🇺🇸 Subscribe to an event by name.

        📋 Parameters:
        - name (str): Event name to subscribe.
        - version (str | None): Event version (e.g., "1.0").
        - params (dict | None): Additional parameters for subscription.

        📤 Returns:
        - str: Subscription request ID.
        """
        request_id = self._next_request_id()
        message = Message.subscribe(
            sid=request_id, name=name, version=version, params=params
        )
        return await self._send(message)

    async def unsubscribe(
        self,
        name: str,
        version: Literal["1.0", "2.0", "3.0", "4.0", "5.0"] | None = None,
        params: dict | None = None,
    ) -> str:
        """
        🇧🇷 Cancela assinatura de evento por nome.

        📋 Parâmetros:
        - name (str): Nome do evento para cancelar assinatura.
        - version (str | None): Versão do evento.
        - params (dict | None): Parâmetros adicionais.

        📤 Retorna:
        - str: ID da requisição de cancelamento.

        🇺🇸 Unsubscribe from an event by name.

        📋 Parameters:
        - name (str): Event name to unsubscribe.
        - version (str | None): Event version.
        - params (dict | None): Additional parameters.

        📤 Returns:
        - str: Unsubscribe request ID.
        """
        request_id = self._next_request_id()
        message = Message.unsubscribe(
            sid=request_id, name=name, version=version, params=params
        )
        return await self._send(message)

    async def set_options(self, send_results: bool = True) -> str:
        """
        🇧🇷 Envia mensagem setOptions.

        📋 Parâmetros:
        - send_results (bool): Flag para envio de resultados (padrão True).

        📤 Retorna:
        - str: ID da requisição.

        🇺🇸 Send setOptions message.

        📋 Parameters:
        - send_results (bool): Flag to send results (default True).

        📤 Returns:
        - str: Request ID.
        """
        request_id = self._next_request_id()
        message = Message.set_options(request_id, send_results)
        return await self._send(message)

    async def authenticate(self, ssid: str) -> None:
        """
        🇧🇷 Autentica conexão WebSocket com ssid.

        📋 Parâmetros:
        - ssid (str): Token de sessão.

        ⚠️ Exceções:
        - ConnectionError: Se a autenticação falhar.

        🇺🇸 Authenticate WebSocket connection with ssid.

        📋 Parameters:
        - ssid (str): Session token.

        ⚠️ Raises:
        - ConnectionError: If authentication fails.
        """
        await self._send(Message.authenticate(ssid))

        await self._send(
            Message.send(
                request_id=self._next_request_id(),
                msg={"name": "core.get-profile", "version": "1.0", "body": {}},
            )
        )

    async def send(self, msg: dict[str, Any]) -> str:
        """
        🇧🇷 Envia uma mensagem genérica.

        📋 Parâmetros:
        - msg (dict): Mensagem a ser enviada.

        📤 Retorna:
        - str: ID da requisição.

        🇺🇸 Send a generic message.

        📋 Parameters:
        - msg (dict): Message to send.

        📤 Returns:
        - str: Request ID.
        """
        request_id = self._next_request_id()
        message = Message.send(request_id, msg)
        return await self._send(message)

    async def request(
        self, msg: dict[str, Any], name: str | None = None
    ) -> dict[str, Any] | None:
        """
        🇧🇷 Envia uma mensagem e aguarda a resposta correspondente.

        📋 Parâmetros:
        - msg (dict): Mensagem a ser enviada.
        - name (str | None): Nome do evento esperado na resposta.

        📤 Retorna:
        - dict | None: Dados da resposta ou None se timeout.

        ⚠️ Exceções:
        - TimeoutError: Se a resposta não chegar a tempo.

        🇺🇸 Sends a message and waits for the corresponding response.

        📋 Parameters:
        - msg (dict): Message to send.
        - name (str | None): Expected event name in response.

        📤 Returns:
        - dict | None: Response data or None if timeout.

        ⚠️ Raises:
        - TimeoutError: If response does not arrive in time.
        """
        request_id = await self.send(msg=msg)
        if name is not None:
            return await self.receive(name=name)
        return await self.receive(request_id=request_id)

    async def receive(
        self,
        name: str | None = None,
        request_id: str | None = None,
        timeout: float = 5.0,
    ) -> dict[str, Any] | None:
        """
        🇧🇷 Aguarda resposta por nome ou request_id dentro do timeout.

        📋 Parâmetros:
        - name (str | None): Nome do evento a aguardar.
        - request_id (str | None): ID da requisição a aguardar.
        - timeout (float): Tempo máximo de espera em segundos.

        📤 Retorna:
        - dict | None: Dados da resposta ou None se timeout.

        ⚠️ Exceções:
        - TimeoutError: Se a resposta não chegar a tempo.

        🇺🇸 Await a response by name or request_id within timeout.

        📋 Parameters:
        - name (str | None): Event name to wait for.
        - request_id (str | None): Request ID to wait for.
        - timeout (float): Maximum wait time in seconds.

        📤 Returns:
        - dict | None: Response data or None if timeout.

        ⚠️ Raises:
        - TimeoutError: If response does not arrive in time.
        """
        future = asyncio.get_event_loop().create_future()

        if request_id:
            self._futures_by_id[request_id] = future
        elif name:
            self._futures_by_name.setdefault(name, []).append(future)
        else:
            raise ValueError("Either 'name' or 'request_id' must be provided.")

        try:
            data = await asyncio.wait_for(future, timeout=timeout)
            if isinstance(data, dict):
                return data.get("msg") or data
            if isinstance(data, list):
                return data["msg"] if "msg" in data else data
            else:
                return data
        except asyncio.TimeoutError:
            logger.debug(f"Timeout waiting for response to '{name or request_id}'")
            return None
        finally:
            if request_id:
                self._futures_by_id.pop(request_id, None)
            elif name:
                futures = self._futures_by_name.get(name)
                if futures and future in futures:
                    futures.remove(future)
                    if not futures:
                        self._futures_by_name.pop(name, None)

    def handle(self, name: str) -> Callable[
        [Callable[[dict[str, Any]], Awaitable[None]]],
        Callable[[dict[str, Any]], Awaitable[None]],
    ]:
        """
        🇧🇷 Registra callback coroutine para evento nomeado, como decorator.

        📋 Parâmetros:
        - name (str): Nome do evento.

        📤 Retorna:
        - Callable: Decorator que registra o callback.

        🇺🇸 Register a coroutine callback for a named event, as a decorator.

        📋 Parameters:
        - name (str): Event name.

        📤 Returns:
        - Callable: Decorator registering the callback.
        """
        def decorator(
            callback: Callable[[dict[str, Any]], Awaitable[None]],
        ) -> Callable[[dict[str, Any]], Awaitable[None]]:
            self._subscribers.setdefault(name, []).append(callback)
            logger.info(f"Subscribed callback to event: {name}")
            return callback

        return decorator

    def on(
        self,
        name: str,
        callback: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        """
        🇧🇷 Registra callback coroutine para evento nomeado.

        📋 Parâmetros:
        - name (str): Nome do evento.
        - callback (Callable): Função assíncrona callback.

        🇺🇸 Register a coroutine callback for a named event.

        📋 Parameters:
        - name (str): Event name.
        - callback (Callable): Async callback function.
        """
        self._subscribers.setdefault(name, []).append(callback)
        logger.info(f"Subscribed callback to event: {name}")

    def off(
        self,
        name: str,
        callback: Callable[[dict[str, Any]], Awaitable[None]],
        reason: str | None = None,
    ) -> None:
        """
        Unregister a callback from a named event.

        Remove callback registrado de um evento.

        Args:
            name: Nome do evento.
            callback: Função callback a ser removida.
            reason: Motivo da remoção para logging.
        """
        if name in self._subscribers:
            try:
                self._subscribers[name].remove(callback)
                if not self._subscribers[name]:
                    self._subscribers.pop(name)
                if reason:
                    logger.info(f"Unsubscribed callback from event '{name}': {reason}")
                else:
                    logger.info(f"Unsubscribed callback from event: {name}")
            except (ValueError, IQOptionError):
                logger.warning(f"Callback not found for event '{name}' when trying to unsubscribe.")

    async def wait_for(
        self,
        name: str,
        condition: Callable[[dict[str, Any]], bool],
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        🇧🇷 Aguarda um evento específico que atenda uma condição.

        📋 Parâmetros:
        - name (str): Nome do evento.
        - condition (Callable): Função para avaliar a condição.
        - timeout (float): Timeout em segundos.

        📤 Retorna:
        - dict: Dados do evento que satisfaz a condição.

        ⚠️ Exceções:
        - TimeoutError: Se o timeout for atingido.

        🇺🇸 Wait for a specific event matching a condition.

        📋 Parameters:
        - name (str): Event name.
        - condition (Callable): Function to evaluate condition.
        - timeout (float): Timeout in seconds.

        📤 Returns:
        - dict: Event data satisfying the condition.

        ⚠️ Raises:
        - TimeoutError: If timeout is reached.
        """
        future = asyncio.get_event_loop().create_future()

        async def _callback(msg: dict[str, Any]) -> None:
            if not future.done() and condition(msg):
                future.set_result(msg)
                self.off(name, _callback)

        self.on(name, _callback)

        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            self.off(name, _callback)
            raise TimeoutError(f"Timeout waiting for event '{name}'")

    async def close(self) -> None:
        """
        🇧🇷 Fecha conexão WebSocket graciosamente.

        ⚠️ Exceções:
        - ConnectionError: Se a desconexão falhar.

        🇺🇸 Gracefully close WebSocket connection.

        ⚠️ Raises:
        - ConnectionError: If disconnection fails.
        """
        self._closing = True
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()
            logger.info("WebSocket connection closed.")

    async def _listen_loop(self) -> None:
        """
        🇧🇷 Loop interno para escutar e despachar mensagens recebidas.

        🇺🇸 Internal loop to listen and dispatch incoming messages.
        """
        assert self._ws
        try:
            while not self._closing:
                raw = await self._ws.recv()
                message = json.loads(raw)
                logger.debug(f"Received: {message}")
                await self._dispatch(message)
        except asyncio.CancelledError:
            logger.info("Listen loop cancelled.")
        except Exception as e:
            logger.error(f"Unexpected error in listen loop: {e}")
        finally:
            self._closing = True

    async def _dispatch(self, message: dict[str, Any]) -> None:
        """
        🇧🇷 Despacha mensagens para futures aguardando ou callbacks registrados.

        📋 Parâmetros:
        - message (dict): Mensagem recebida.

        🇺🇸 Dispatch messages to awaiting futures or event callbacks.

        📋 Parameters:
        - message (dict): Received message.
        """
        request_id = message.get("request_id")
        name = message.get("name")

        if request_id and (future := self._futures_by_id.pop(request_id, None)):
            if not future.done():
                future.set_result(message.get("msg") or message)
            return

        if name and name in self._futures_by_name:
            futures = self._futures_by_name[name]
            if futures:
                future = futures.pop(0)
                if not future.done():
                    future.set_result(message.get("msg") or message)
                if not futures:
                    self._futures_by_name.pop(name)

        for callback in self._subscribers.get(name, []):
            try:
                asyncio.create_task(callback(message.get("msg") or message))
            except Exception as e:
                logger.error(f"Error in callback for event '{name}': {e}")

    def current_server_time(self, ms: bool = True) -> int:
        """
        🇧🇷 Retorna o horário atual do servidor em milissegundos (padrão) ou segundos.

        📋 Parâmetros:
        - ms (bool): Se True, retorna em milissegundos. Caso contrário, em segundos.

        📤 Retorna:
        - int: Timestamp do servidor em ms ou s.

        🇺🇸 Returns the current server time in milliseconds (default) or seconds.

        📋 Parameters:
        - ms (bool): If True, returns milliseconds; otherwise seconds.

        📤 Returns:
        - int: Server timestamp in ms or s.
        """
        timestamp = self._server_time or int(time() * 1000)
        return timestamp if ms else timestamp // 1000

    def local_time(self) -> int:
        """
        🇧🇷 Retorna ms decorridos desde início da conexão.

        📤 Retorna:
        - int: Milissegundos desde início da conexão.

        🇺🇸 Returns ms elapsed since connection start.

        📤 Returns:
        - int: Milliseconds elapsed since connection start.
        """
        return int(time() * 1000) - self._connection_start_ms

    def get_expiration(self, duration: int) -> tuple[int, int]:
        """
        🇧🇷 Calcula a expiração ideal para a duração informada,
        replicando a lógica do painel da IQ Option e evitando
        timestamps já indisponíveis para compra.

        🇺🇸 Calculates the ideal expiration for the given duration,
        replicating IQ Option's expiration panel and avoiding
        timestamps already closed for purchase.

        Args:
            duration (int): 
                🇧🇷 Duração desejada em minutos.  
                🇺🇸 Desired duration in minutes.

        Returns:
            tuple[int, int]: 
                🇧🇷 Timestamp da expiração (epoch) e índice na lista.  
                🇺🇸 Expiration timestamp (epoch) and index.

        Raises:
            TradingError:
                🇧🇷 Se não encontrar expiração válida.  
                🇺🇸 If no valid expiration is found.
        """
        now = datetime.fromtimestamp(time())
        timestamps = []

        if now.second < 30:
            base_minute = now.replace(second=0, microsecond=0)
        else:
            base_minute = now.replace(second=0, microsecond=0) + timedelta(minutes=1)

        for i in range(5):
            ts = int((base_minute + timedelta(minutes=i + 1)).timestamp())
            timestamps.append(ts)

        temp_date = now.replace(second=0, microsecond=0)
        count = 0
        while count < 50:
            temp_date += timedelta(minutes=1)
            if temp_date.minute % 15 == 0 and (temp_date - now).total_seconds() > 300:
                ts = int(temp_date.timestamp())
                timestamps.append(ts)
                count += 1

        safe_timestamps = []
        for ts in timestamps:
            time_remaining = ts - time()

            if (ts % 900) == 0:
                if time_remaining >= 30:
                    safe_timestamps.append(ts)
            else:
                if time_remaining >= 3:
                    safe_timestamps.append(ts)

        if not safe_timestamps:
            raise TradingError("No safe expiration found")

        target_seconds = duration * 60
        differences = [abs(ts - (time() + target_seconds)) for ts in safe_timestamps]
        closest_index = differences.index(min(differences))

        return safe_timestamps[closest_index], round(closest_index, 2)

    async def _send(self, message: Message) -> str:
        """
        🇧🇷 Método interno para enviar uma entidade Message pelo WebSocket.

        📋 Parâmetros:
        - message (Message): Instância da mensagem a ser enviada.

        📤 Retorna:
        - str: ID da requisição da mensagem.

        ⚠️ Exceções:
        - ConnectionError: Se WebSocket não estiver conectado.

        🇺🇸 Internal method to send a Message entity via WebSocket.

        📋 Parameters:
        - message (Message): Message instance to send.

        📤 Returns:
        - str: Message request ID.

        ⚠️ Raises:
        - ConnectionError: If WebSocket is not connected.
        """
        if not self._ws:
            raise ConnectionError("WebSocket is not connected.")

        data = message.to_dict()
        await self._ws.send(json.dumps(data))
        logger.debug(f"Sent message: {message}")
        return message.request_id

    async def _on_time_sync(self, time_sync: int | None) -> None:
        """
        🇧🇷 Atualiza tempo do servidor no evento timeSync.

        📋 Parâmetros:
        - time_sync (int | None): Tempo do servidor em ms.

        🇺🇸 Updates server time from timeSync event.

        📋 Parameters:
        - time_sync (int | None): Server time in ms.
        """
        self._server_time = time_sync or int(time() * 1000)
        logger.debug(f"Server time updated: {self._server_time}")

    def _next_request_id(self) -> str:
        """
        🇧🇷 Gera e retorna o próximo ID de requisição único como string.

        📤 Retorna:
        - str: Próximo ID de requisição.

        🇺🇸 Generate and return the next unique request ID as a string.

        📤 Returns:
        - str: Next request ID.
        """
        current = self._request_id
        self._request_id += 1
        return str(current)
