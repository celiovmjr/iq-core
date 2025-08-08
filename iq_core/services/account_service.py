from typing import Any
import logging

from ..websocket import WebSocketClient
from ..entities import Profile, Account, AccountType, InstrumentType

logger = logging.getLogger(__name__)


class AccountService:
    """
    Account service - Manages balance queries and active account switching.
    Serviço de conta - Gerencia consulta de saldos e troca de conta ativa.
    """

    def __init__(self, ws: WebSocketClient, profile: Profile):
        """
        Initialize with profile and WebSocket client.
        Inicializa com o perfil e cliente WebSocket.

        Args:
            ws: WebSocket client / Cliente WebSocket
            profile: Current user profile / Perfil atual do usuário
        """
        self._profile = profile
        self._ws = ws

    async def load_balances(self) -> None:
        await self._ws.send({
            "name": "internal-billing.get-balances",
            "version": "1.0",
            "body": {
                "types_ids": [1,2,4,5,6],
                "tournaments_statuses_ids": [3,2]
            }
        })

        balances = await self._ws.receive("balances")

        if not isinstance(balances, list) or not all(
            isinstance(b, dict) for b in balances
        ):
            raise ValueError(f"Formato inesperado para balances: {balances}")

        self._profile.balances = [Account.from_dict(b) for b in balances]

    def accounts(self, balance_id: int | None = None) -> list[Account] | Account:
        """
        Returns all accounts or a specific account by ID.
        Retorna todas as contas ou uma específica pelo ID.

        Args:
            balance_id: Optional account ID / ID da conta (opcional)

        Returns:
            List of accounts or single Account instance

        Raises:
            ValueError: If balance_id not found
        """
        if balance_id is None:
            return self._profile.balances

        for account in self._profile.balances:
            if account.id == balance_id:
                return account

        raise ValueError(f"Conta com ID {balance_id} não encontrada.")

    def active_account(self) -> Account:
        """
        Returns the currently active account.
        Retorna a conta atualmente ativa.

        Raises:
            ValueError: If active account not found
        """
        for account in self._profile.balances:
            if account.id == self._profile.balance_id:
                return account

        raise ValueError("Conta ativa não definida no perfil.")

    async def switch_active_account(self, account_type: AccountType) -> None:
        """
        Switches the active account by account type.
        Troca a conta ativa pelo tipo.

        Args:
            account_type: Tipo da conta para ativar.

        Raises:
            ValueError: Se tipo de conta não existir no perfil.
        """
        logger.info("Switching to account type: %s", account_type.name)

        account = next(
            (a for a in self._profile.balances if a.type == account_type), None
        )
        if not account:
            raise ValueError(f"No account of type {account_type.name} was found.")

        await self._unsubscribe_all(self._profile.id, self._profile.balance_id)

        self._profile._balance_id = account.id

        await self._subscribe_all(self._profile.id, account.id)

        logger.info("Active account switched to ID %d", account.id)

    def _instrument_types(self) -> list[str]:
        """
        Returns list of instrument types to subscribe/unsubscribe.
        Retorna lista dos tipos de instrumento para inscrever/desinscrever.
        """
        return [inst.value for inst in InstrumentType]

    async def _unsubscribe_all(self, user_id: int, balance_id: int) -> None:
        """
        Unsubscribes position-changed for all instrument types.
        Cancela inscrição do position-changed para todos os tipos de instrumento.
        """
        for instrument in self._instrument_types():
            await self._ws.send(
                {
                    "name": "unsubscribeMessage",
                    "msg": {
                        "name": "portfolio.position-changed",
                        "version": "3.0",
                        "params": {
                            "routingFilters": {
                                "user_id": user_id,
                                "user_balance_id": balance_id,
                                "instrument_type": instrument,
                            }
                        },
                    },
                }
            )

    async def _subscribe_all(self, user_id: int, balance_id: int) -> None:
        """
        Subscribes position-changed for all instrument types.
        Inscreve no position-changed para todos os tipos de instrumento.
        """
        for instrument in self._instrument_types():
            await self._ws.send(
                {
                    "name": "subscribeMessage",
                    "msg": {
                        "name": "portfolio.position-changed",
                        "version": "3.0",
                        "params": {
                            "routingFilters": {
                                "user_id": user_id,
                                "user_balance_id": balance_id,
                                "instrument_type": instrument,
                            }
                        },
                    },
                }
            )
