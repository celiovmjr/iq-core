from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Self


@dataclass(frozen=True, slots=True)
class Candle:
    open: float
    close: float
    high: float
    low: float
    bid: float
    ask: float
    volume: float
    from_time: datetime
    to_time: datetime
    size: Literal[
        1,
        5,
        10,
        15,
        30,
        60,
        120,
        300,
        600,
        900,
        1800,
        3600,
        7200,
        14400,
        28800,
        43200,
        86400,
        2592000,
        604800,
    ]

    @classmethod
    def from_ws(cls, raw: dict, size: int | None = None) -> Self:
        candle_size = size if size is not None else raw.get("size")
        if candle_size is None:
            raise ValueError("Size must be provided or present in raw data.")
        return cls(
            open=raw["open"],
            close=raw["close"],
            high=raw["max"],
            low=raw["min"],
            bid=raw.get("bid", 0.0),
            ask=raw.get("ask", 0.0),
            volume=raw["volume"],
            from_time=datetime.fromtimestamp(raw["from"]),
            to_time=datetime.fromtimestamp(raw["to"]),
            size=int(candle_size),
        )
