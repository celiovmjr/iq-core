from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self


@dataclass(frozen=True, slots=True)
class CandleStream:
    active_id: int
    size: int
    at: int
    from_time: datetime
    to_time: datetime
    id: int
    open: float
    close: float
    min: float
    max: float
    ask: float
    bid: float
    volume: float
    phase: Optional[str]

    @classmethod
    def from_ws(cls, raw: dict) -> Self:
        return cls(
            active_id=raw["active_id"],
            size=raw["size"],
            at=raw["at"],
            from_time=datetime.fromtimestamp(raw["from"]),
            to_time=datetime.fromtimestamp(raw["to"]),
            id=raw["id"],
            open=raw["open"],
            close=raw["close"],
            min=raw["min"],
            max=raw["max"],
            ask=raw["ask"],
            bid=raw["bid"],
            volume=raw["volume"],
            phase=raw.get("phase"),
        )
