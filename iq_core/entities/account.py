from typing import Self
from dataclasses import dataclass
from enum import IntEnum


class AccountType(IntEnum):
    REAL = 1
    TOURNAMENT = 2
    PRACTICE = 4
    BTC = 5
    ETH = 6

    def __str__(self) -> str:
        return self.name.lower()


@dataclass(frozen=True, kw_only=True, slots=True)
class Account:
    id: str | int
    type: AccountType
    amount: float
    currency: str
    is_fiat: bool
    is_marginal: bool

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(
            id=data["id"],
            type=AccountType(data["type"]),
            amount=data["amount"],
            currency=data["currency"],
            is_fiat=data["is_fiat"],
            is_marginal=data["is_marginal"],
        )
