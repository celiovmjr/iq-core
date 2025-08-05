from __future__ import annotations
import aiohttp
import logging
from typing import AsyncIterator, Self
from contextlib import asynccontextmanager
from ..anotations import measure_time, handle_network_errors
from .token_service import TokenManager
from ..entities import Profile
from ..exceptions import AuthenticationError, NetworkUnavailableError
from ..websocket import WebSocketClient
from .account_service import AccountService

logger = logging.getLogger(__name__)


class AuthService:
    """
    🇧🇷 Gerencia autenticação com a IQ Option.

    📋 Parâmetros:
    - token_manager (TokenManager): Gerenciador de tokens (opcional)

    ⚠️ Exceções:
    - AuthenticationError: Erro de autenticação
    - NetworkUnavailableError: Erro de rede

    🇺🇸 Handles authentication with IQ Option.

    📋 Parameters:
    - token_manager (TokenManager): Token manager (optional)

    ⚠️ Raises:
    - AuthenticationError: Authentication error
    - NetworkUnavailableError: Network error
    """

    def __init__(self, token_manager: TokenManager | None = None) -> None:
        self._token_manager = token_manager or TokenManager()
        self._token: str | None = None
        self._session: aiohttp.ClientSession | None = None

    @property
    def session(self) -> aiohttp.ClientSession:
        """
        🇧🇷 Inicializa e retorna ClientSession aiohttp de forma lazy.

        📤 Retorna:
        - aiohttp.ClientSession: Sessão HTTP

        🇺🇸 Lazily initializes and returns aiohttp ClientSession.

        📤 Returns:
        - aiohttp.ClientSession: HTTP session
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _authenticate_ws(
        self, token: str
    ) -> tuple[WebSocketClient, Profile] | None:
        """
        🇧🇷 Autentica via WebSocket usando token e obtém perfil.

        📋 Parâmetros:
        - token (str): Token de autenticação

        📤 Retorna:
        - tuple[WebSocketClient, Profile] | None: Cliente WebSocket e perfil ou None

        ⚠️ Exceções:
        - Exception: Erro durante autenticação WebSocket

        🇺🇸 Authenticates via WebSocket using token and fetches profile.

        📋 Parameters:
        - token (str): Authentication token

        📤 Returns:
        - tuple[WebSocketClient, Profile] | None: WebSocket client and profile or None

        ⚠️ Raises:
        - Exception: Error during WebSocket authentication
        """
        try:
            ws = await WebSocketClient().connect(token)
            profile_data = await ws.receive("profile") or {}
            match profile_data.get("isSuccessful", False):
                case True:
                    profile = Profile.from_dict(profile_data["result"])
                    account_service = AccountService(ws, profile)
                    await account_service.load_balances()
                    profile.set_account(account_service)
                    return ws, profile
                case False:
                    logger.debug("WebSocket auth unsuccessful.")
                    await ws.close()
                    return None
        except Exception as e:
            logger.warning(f"WebSocket authentication failed: {e}")
            return None

    @handle_network_errors
    @measure_time
    async def login(self, email: str, password: str) -> tuple[WebSocketClient, Profile]:
        """
        🇧🇷 Login com e-mail e senha, usando token em cache se possível.

        📋 Parâmetros:
        - email (str): E-mail do usuário
        - password (str): Senha do usuário

        📤 Retorna:
        - tuple[WebSocketClient, Profile]: Cliente WebSocket e perfil do usuário

        ⚠️ Exceções:
        - AuthenticationError: Falha na autenticação
        - NetworkUnavailableError: Erro de rede

        🇺🇸 Login with email and password, using cached token if possible.

        📋 Parameters:
        - email (str): User email
        - password (str): User password

        📤 Returns:
        - tuple[WebSocketClient, Profile]: WebSocket client and user profile

        ⚠️ Raises:
        - AuthenticationError: Authentication failure
        - NetworkUnavailableError: Network error
        """
        # Try cached token first
        cached_token = self._token_manager.get_token(email)
        if cached_token:
            result = await self._authenticate_ws(cached_token)
            if result:
                logger.info("Logged in with cached token.")
                self._token = cached_token
                return result
            logger.info("Cached token invalid, proceeding with login.")

        # Perform REST login
        try:
            async with self.session.post(
                "https://auth.iqoption.com/api/v2/login",
                json={"identifier": email, "password": password},
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Content-Type": "application/json",
                },
            ) as resp:
                if resp.status != 200:
                    raise AuthenticationError(f"Login failed with status {resp.status}")
                data = await resp.json()
        except aiohttp.ClientError as e:
            logger.error("Network error during login")
            raise NetworkUnavailableError(f"Network error: {e}") from e

        token = data.get("ssid")
        if not token:
            raise AuthenticationError("Authentication token not received")

        # Authenticate WebSocket with new token
        result = await self._authenticate_ws(token)
        if not result:
            raise AuthenticationError("WebSocket authentication failed")

        self._token = token
        self._token_manager.set_token(email, token)
        logger.info("Login successful.")
        return result

    async def logout(self) -> None:
        """
        🇧🇷 Fecha sessão e limpa token.

        📋 Parâmetros:
        - Nenhum

        📤 Retorna:
        - None: Função assíncrona sem retorno

        ⚠️ Exceções:
        - Nenhuma

        🇺🇸 Closes session and clears token.

        📋 Parameters:
        - None

        📤 Returns:
        - None: Async function with no return

        ⚠️ Raises:
        - None
        """
        if self._session and not self._session.closed:
            await self._session.close()
        self._session = None
        self._token = None
        logger.info("Logged out.")

    @property
    def token(self) -> str | None:
        """
        🇧🇷 Token de autenticação atual.

        📤 Retorna:
        - str | None: Token atual ou None se não autenticado

        🇺🇸 Current authentication token.

        📤 Returns:
        - str | None: Current token or None if not authenticated
        """
        return self._token

    @property
    def is_authenticated(self) -> bool:
        """
        🇧🇷 Verifica se está autenticado.

        📤 Retorna:
        - bool: True se autenticado, False caso contrário

        🇺🇸 Checks if authenticated.

        📤 Returns:
        - bool: True if authenticated, False otherwise
        """
        return self._token is not None

    @asynccontextmanager
    async def context(self) -> AsyncIterator[Self]:
        """
        🇧🇷 Gerenciador de contexto assíncrono para AuthService.

        📋 Parâmetros:
        - Nenhum

        📤 Retorna:
        - AsyncIterator[Self]: Iterador assíncrono do próprio serviço

        ⚠️ Exceções:
        - Exception: Qualquer exceção durante o contexto

        🇺🇸 Async context manager for AuthService.

        📋 Parameters:
        - None

        📤 Returns:
        - AsyncIterator[Self]: Async iterator of the service itself

        ⚠️ Raises:
        - Exception: Any exception during context
        """
        try:
            yield self
        finally:
            await self.logout()
