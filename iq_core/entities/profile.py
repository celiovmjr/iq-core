from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Self, TYPE_CHECKING
from .account import Account

if TYPE_CHECKING:
    from ..services.account_service import AccountService


@dataclass
class Profile:
    """
    🇧🇷 Representa o perfil de usuário na IQ Option.

    📋 Parâmetros:
    - id (int): ID do usuário
    - name (str): Nome do usuário
    - email (str): E-mail do usuário
    - currency (str): Moeda da conta
    - _balance_id (int): ID do saldo principal
    - is_activated (bool): Status de ativação da conta
    - balances (List[Account]): Lista de contas/saldos
    - nickname (str | None): Apelido do usuário (opcional)
    - _account (AccountService | None): Serviço de conta (opcional)

    🇺🇸 Represents a user profile in IQ Option.

    📋 Parameters:
    - id (int): User ID
    - name (str): User name
    - email (str): User email
    - currency (str): Account currency
    - _balance_id (int): Main balance ID
    - is_activated (bool): Account activation status
    - balances (List[Account]): List of accounts/balances
    - nickname (str | None): User nickname (optional)
    - _account (AccountService | None): Account service (optional)
    """

    id: int
    name: str
    email: str
    currency: str
    _balance_id: int
    is_activated: bool
    balances: List[Account] = field(default_factory=list)
    nickname: str | None = None
    _account: AccountService | None = None

    @property
    def balance(self) -> float:
        """
        🇧🇷 Retorna o valor numérico do saldo atual da conta principal.

        📤 Retorna:
        - int | None: Saldo atual ou None se conta não encontrada

        🇺🇸 Returns the current numeric balance amount of the main account.

        📤 Returns:
        - int | None: Current balance or None if account not found
        """
        account = next(
            (acc for acc in self.balances if acc.id == self._balance_id), None
        )
        if account is None:
            return None
        return account.amount

    @property
    def balance_id(self) -> int:
        """
        🇧🇷 Retorna o ID da conta/balance principal.

        📤 Retorna:
        - int: ID da conta principal

        🇺🇸 Returns the ID of the main balance/account.

        📤 Returns:
        - int: Main account ID
        """
        return self._balance_id

    @property
    def account(self) -> AccountService:
        """
        🇧🇷 Retorna o serviço associado à conta.

        📤 Retorna:
        - AccountService: Serviço de conta

        ⚠️ Exceções:
        - RuntimeError: AccountService não inicializado

        🇺🇸 Returns the associated AccountService.

        📤 Returns:
        - AccountService: Account service

        ⚠️ Raises:
        - RuntimeError: AccountService not initialized
        """
        if self._account is None:
            raise RuntimeError(
                "AccountService not initialized. Possible authentication failure or missing token"
            )
        return self._account

    def set_account(self, account_service: AccountService) -> None:
        self._account = account_service

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """
        🇧🇷 Cria uma instância de Profile a partir de um dicionário.

        📋 Parâmetros:
        - data (dict): Dicionário com dados do perfil

        📤 Retorna:
        - Profile: Objeto Profile construído

        ⚠️ Exceções:
        - KeyError: Chave obrigatória ausente no dicionário

        🇺🇸 Creates a Profile instance from a dictionary.

        📋 Parameters:
        - data (dict): Dictionary with profile data

        📤 Returns:
        - Profile: Fully constructed Profile object

        ⚠️ Raises:
        - KeyError: Required key missing in dictionary
        """
        return cls(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            currency=data["currency"],
            _balance_id=data["balance_id"],
            is_activated=data.get("is_activated", False),
            nickname=data.get("nickname"),
        )
