from enum import Enum, unique
from dataclasses import dataclass
from typing import Any
from decimal import Decimal
from .instrument import InstrumentType


@unique
class TradeStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"
    CANCELED = "canceled"


@unique
class TradeResultType(str, Enum):
    WIN = "win"
    LOOSE = "loose"
    DRAW = "draw"

    @classmethod
    def _missing_(cls, value: object) -> "TradeResultType":
        if value == "equal":
            return cls.DRAW
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")


@dataclass(frozen=True, slots=True)
class TradeResult:
    id: int
    status: TradeStatus
    result: TradeResultType
    invest: Decimal
    profit: Decimal
    pnl: Decimal
    open: float
    close: float
    open_time: int
    close_time: int
    instrument_type: InstrumentType

    @property
    def is_win(self) -> bool:
        return self.result == TradeResultType.WIN

    @property
    def duration_seconds(self) -> int:
        return (self.close_time - self.open_time) // 1000

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TradeResult":
        raw_event = data.get("raw_event", {}).get("binary_options_option_changed1", {})
        return cls(
            id=data.get("external_id", 0),
            status=TradeStatus(data.get("status")),
            result=TradeResultType(raw_event.get("result")),
            invest=Decimal(str(data.get("invest", "0.0"))),
            profit=Decimal(str(data.get("close_profit", "0.0"))),
            pnl=Decimal(str(data.get("pnl", 0.0))),
            open=float(data.get("open_quote", 0.0)),
            close=float(data.get("close_quote", 0.0)),
            open_time=int(data.get("open_time", 0)),
            close_time=int(data.get("close_time", 0)),
            instrument_type=InstrumentType(data.get("instrument_type")),
        )
