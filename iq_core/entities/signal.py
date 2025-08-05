from dataclasses import dataclass
from .instrument import Instrument
from .duration import Duration
from ..exceptions import ValidationError
from enum import Enum
from decimal import Decimal


class SignalType(str, Enum):
    BINARY = "binary"
    BLITZ = "blitz"
    DIGITAL = "digital"
    FOREX = "forex"


class Direction(str, Enum):
    CALL = "call"
    PUT = "put"

    @classmethod
    def from_str(cls, value: str) -> "Direction":
        value = value.lower()
        if value in cls._value2member_map_:
            return cls(value)
        raise ValueError(f"Invalid direction: {value}")


@dataclass(frozen=True, slots=True)
class Signal:
    """
    🇧🇷 Representa um sinal de entrada para abrir uma operação.

    📋 Parâmetros:
    - instrument (Instrument): Ativo a ser operado
    - account_id (int): ID da conta que abrirá a operação
    - direction (Direction): Direção da operação (CALL ou PUT)
    - amount (Decimal): Valor investido (positivo)
    - expiration (Duration): Duração da operação (segundos ou minutos)
    - type (SignalType): Tipo de operação (binary, digital, forex)

    ⚠️ Exceções:
    - ValueError: Valor ou expiração inválidos

    🇺🇸 Represents an entry signal to open a trade.

    📋 Parameters:
    - instrument (Instrument): Asset to be traded
    - account_id (int): Account ID that will open the trade
    - direction (Direction): Trade direction (CALL or PUT)
    - amount (Decimal): Investment amount (positive)
    - expiration (Duration): Trade duration (seconds or minutes)
    - type (SignalType): Trade type (binary, digital, forex)

    ⚠️ Raises:
    - ValueError: Invalid amount or expiration
    """
    instrument: Instrument
    account_id: int
    direction: Direction
    amount: Decimal
    expiration: Duration
    type: SignalType

    def __post_init__(self) -> None:
        if not isinstance(self.expiration, Duration):
            raise TypeError("Expiration must be a Duration instance")

        if self.amount <= 0:
            raise ValidationError("Amount must be positive")

        if self.expiration.seconds() <= 0:
            raise ValidationError("Expiration must be positive (greater than 0 seconds)")
