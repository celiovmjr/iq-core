from enum import Enum, unique
from dataclasses import dataclass, field
from typing import Any, Literal, List
from datetime import datetime, timezone


@unique
class InstrumentType(str, Enum):
    BINARY = "binary-option"
    TURBO = "turbo-option"
    BLITZ = "blitz-option"
    DIGITAL = "digital-option"


@unique
class MarketType(str, Enum):
    FOREX = "forex"
    INDEX = "index"
    COMMODITY = "commodity"
    COMMODITIES = "commodities"
    INDICES = "indices"
    STOCK = "stock"
    CRYPTO = "crypto"
    EQUITIES = "equities"
    BONDS = "bonds"


@dataclass(frozen=True, slots=True)
class TradingInfo:
    """
    🇧🇷 Parâmetros detalhados de negociação para um instrumento digital.

    📋 Parâmetros:
    - profit (dict[str, int]): Lucros por tipo de operação
    - regulation_mode (Literal): Modo de regulamentação
    - precision (int): Precisão decimal (padrão: 6)
    - min_investment (float | None): Investimento mínimo
    - max_investment (float | None): Investimento máximo
    - allowed_expirations (list[int]): Tempos de expiração permitidos

    🇺🇸 Detailed trading parameters for a digital instrument.

    📋 Parameters:
    - profit (dict[str, int]): Profits by operation type
    - regulation_mode (Literal): Regulation mode
    - precision (int): Decimal precision (default: 6)
    - min_investment (float | None): Minimum investment
    - max_investment (float | None): Maximum investment
    - allowed_expirations (list[int]): Allowed expiration times
    """

    profit: dict[str, int] = field(default_factory=dict)
    regulation_mode: Literal[
        "only_without_regulation", "only_with_regulation", "both"
    ] = "both"
    precision: int = 6
    min_investment: float | None = None
    max_investment: float | None = None
    allowed_expirations: list[int] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Instrument:
    id: int
    name: str
    symbol: str
    group_id: int
    market: MarketType | None
    type: List[InstrumentType] | None
    is_enabled: bool
    is_suspended: bool
    image: str | None = None
    trading: TradingInfo = field(default_factory=TradingInfo)
    schedule: list[dict[str, int]] = field(default_factory=list, repr=False)

    @property
    def is_open(self) -> bool:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        return any(period[0] <= now_ts <= period[1] for period in self.schedule)

    def is_tradable(self) -> bool:
        return self.is_enabled and not self.is_suspended and self.is_open

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Instrument":
        """
        🇧🇷 Cria uma instância de Instrument a partir de um dicionário.

        📋 Parâmetros:
        - data (dict[str, Any]): Dicionário contendo os dados do instrumento, conforme recebido da API.

        📤 Retorna:
        - Instrument: Objeto Instrument preenchido com os dados do dicionário.

        ⚠️ Observações:
        - O campo `type` será mapeado para o enum InstrumentType. Se o valor não corresponder a nenhum tipo conhecido, será None.
        - O campo `market` não é preenchido neste método e deve ser configurado posteriormente, se necessário.

        🇺🇸 Creates an Instrument instance from a dictionary.

        📋 Parameters:
        - data (dict[str, Any]): Dictionary containing instrument data as received from the API.

        📤 Returns:
        - Instrument: Instrument object populated with data from the dictionary.

        ⚠️ Notes:
        - The `type` field is mapped to the InstrumentType enum. If the value does not match any known type, it will be None.
        - The `market` field is not populated in this method and should be set later if needed.
        """
        return cls(
            id=data.get("id"),
            name=data.get("name", "").replace("front.", "").replace("/", ""),
            symbol=data.get("ticker", ""),
            group_id=data["group_id"],
            market=None,
            type=data["type"],
            is_enabled=data.get("enabled", True),
            is_suspended=data.get("is_suspended", False),
            image=f"https://static.cdnpub.info/files{data.get('image', '')}".strip()
            or None,
            trading=None,
            schedule=data.get("schedule", []),
        )
