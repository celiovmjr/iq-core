import logging
import asyncio
from datetime import datetime, timezone
from typing import Literal, Sequence, Final
from dataclasses import replace

from ..exceptions import IQOptionError
from ..anotations import measure_time
from ..entities import Instrument, TradingInfo, InstrumentType, MarketType
from ..websocket import WebSocketClient

logger = logging.getLogger(__name__)


class InstrumentService:
    """
    🇧🇷 Serviço responsável por buscar e processar instrumentos de negociação.

    🇺🇸 Service responsible for fetching and processing trading instruments.
    """

    GROUPS = Literal[
        "forex",
        "equity",
        "commodity",
        "index",
        "industrial",
        "health",
        "information",
        "consumer",
        "utility",
        "financial",
        "material",
        "energy",
        "telecommunication",
        "crypto",
        "bond",
        "stock",
        "global",
        "europe",
        "us",
        "tip",
    ]

    TYPES = Literal[
        "binary-option",
        "turbo-option",
        "blitz-option",
        "digital-option",
    ]

    def __init__(self, ws: WebSocketClient) -> None:
        """
        🇧🇷 Inicializa o serviço com uma instância de WebSocketClient.

        🇺🇸 Initializes the service with a WebSocketClient instance.

        Args:
            ws (WebSocketClient): Cliente WebSocket para comunicação.
        """
        self._ws = ws
        self._profits: dict[str, dict[int, float]] = {}
        self._raw_groups: dict[str, str] = {}
        self._binary_raw: dict | None = None
        self._digital_raw: dict | None = None

    @measure_time
    async def fetch(
        self,
        *,
        filter_by: int | str | None = None,
        limit: int | None = None,
        offset: int = 0,
        otc: bool = True,
        groups: Sequence[GROUPS] | None = None,
        types: Sequence[TYPES] | None = None,
        only_open: bool = True,
    ) -> Instrument | list[Instrument]:
        """
        🇧🇷 Busca instrumentos negociáveis aplicando filtros opcionais.

        🇺🇸 Fetch tradable instruments applying optional filters.

        Args:
            filter_by (int | str | None): Filtra por ID ou símbolo exato do instrumento.
            limit (int | None): Limita o número de instrumentos retornados.
            offset (int): Deslocamento para paginação dos resultados.
            otc (bool): Incluir instrumentos OTC (over-the-counter) ou não.
            groups (Sequence[InstrumentGroup] | None): Lista de grupos para filtrar (ex: 'forex', 'crypto').
            types (Sequence[InstrumentTypeLiteral] | None): Lista de tipos para filtrar ('binary-option', etc).
            only_open (bool): Retorna apenas instrumentos abertos para negociação no momento.

        Returns:
            Instrument | list[Instrument]: Instrumento único ou lista de instrumentos.
        
        Raises:
            IQOptionError: Se a resposta do WebSocket for nula ou inválida.
        """
        binary_resp, digital_resp, _ = await asyncio.gather(
            self._ws.request({"name": "get-initialization-data", "version": "4.0"}),
            self._ws.request({
                "name": "digital-option-instruments.get-underlying-list",
                "version": "3.0",
                "body": {"filter_suspended": True}
            }),
            self._fetch_profits(),
        )
        if binary_resp is None:
            raise IQOptionError("InstrumentService.fetch(): resposta WebSocket nula")

        self._binary_raw = binary_resp
        self._digital_raw = digital_resp
        self._raw_groups = binary_resp.get("groups", {})

        raw_data: dict[int, dict] = {}
        for key in ("binary", "blitz", "turbo"):
            raw_data.update(binary_resp.get(key, {}).get("actives", {}))

        now_ts = int(datetime.now(timezone.utc).timestamp())

        def is_open_now(schedule: list[list[int]]) -> bool:
            # 🇧🇷 Verifica se o instrumento está aberto no momento
            # 🇺🇸 Checks whether the instrument is currently open
            return any(start <= now_ts < end for start, end in schedule)

        def group_matches(group_id: int) -> bool:
            if not groups:
                return True
            group_desc = self._raw_groups.get(str(group_id), "").lower()
            return any(term.lower() in group_desc for term in groups)

        def is_otc(name: str) -> bool:
            # 🇧🇷 Detecta se o instrumento é OTC com base no sufixo do nome
            # 🇺🇸 Detects if the instrument is OTC based on its name suffix
            return name.lower().endswith("-otc")

        # 🇧🇷 Filtro inicial por grupo e status de aberto
        # 🇺🇸 Initial filter by group and open status
        filtered_raw = [
            item for item in raw_data.values()
            if not item.get("is_suspended")
            and group_matches(item.get("group_id", 0))
            and (not only_open or is_open_now(item.get("schedule", [])))
        ]

        # 🇧🇷 Aplica detecção de tipos com base no ID do instrumento
        # 🇺🇸 Detect instrument types based on their ID
        for item in filtered_raw:
            item["type"] = self._detect_types_for_instrument(item)

        # 🇧🇷 Filtro por tipos explícitos (se fornecidos)
        # 🇺🇸 Filter by explicit types (if provided)
        if types:
            types_set = {t.lower() for t in types}
            filtered_raw = [
                item for item in filtered_raw
                if any(t.value in types_set for t in item.get("type", []))
            ]

        # 🇧🇷 Filtro final para incluir/excluir OTC conforme parâmetro
        # 🇺🇸 Final OTC filtering based on input parameter
        if not otc:
            filtered_raw = [item for item in filtered_raw if not is_otc(item.get("name", ""))]

        parse_tasks = [self._parse_instrument(item) for item in filtered_raw]
        instruments = [i for i in await asyncio.gather(*parse_tasks) if i is not None]

        if filter_by is not None:
            filter_lower = str(filter_by).lower()
            instruments = [
                i for i in instruments if str(i.id) == filter_lower or i.symbol.lower() == filter_lower
            ]

        instruments = instruments[offset : offset + limit] if limit is not None else instruments[offset:]
        return instruments[0] if filter_by is not None and instruments else instruments or []

    async def _fetch_profits(self) -> None:
        """
        🇧🇷 Atualiza os lucros para cada tipo de instrumento consultando o servidor.

        🇺🇸 Updates the profit data for each instrument type by querying the server.
        """
        async def fetch(inst_type: InstrumentType) -> tuple[str, dict[int, float]]:
            try:
                resp = await self._ws.request(
                    {
                        "name": "trading-settings.get-trading-group-params",
                        "version": "2.0",
                        "body": {"instrument_type": inst_type.value},
                    }
                )
                if inst_type == InstrumentType.DIGITAL:
                    profits = {
                        sp["active_id"]: sp.get("profit", 0.0)
                        for sp in resp.get("spot_profits", [])
                    }
                else:
                    profits = {
                        sp["active_id"]: 100.0 - sp.get("value", 0.0)
                        for sp in resp.get("commissions", [])
                    }
                return inst_type.value, profits
            except Exception as e:
                logger.error(f"Error fetching profits for {inst_type.value}: {e}")
                return inst_type.value, {}

        results = await asyncio.gather(*(fetch(t) for t in InstrumentType))
        self._profits = dict(results)

    def _detect_types_for_instrument(self, item: dict) -> list[InstrumentType]:
        """
        🇧🇷 Detecta os tipos disponíveis para um instrumento com base nos dados brutos.

        🇺🇸 Detects available types for an instrument based on raw data.

        Args:
            item (dict): Dicionário com dados do instrumento.

        Returns:
            list[InstrumentType]: Lista de tipos identificados para o instrumento.
        """
        if self._binary_raw is None or self._digital_raw is None:
            return []

        ids_by_type = self.extract_instrument_type_ids(self._binary_raw, self._digital_raw)
        active_id = int(item.get("active_id", item.get("id")))
        result = []
        for inst_type, ids in ids_by_type.items():
            if active_id in ids:
                try:
                    result.append(InstrumentType(inst_type))
                except ValueError:
                    pass
        return result

    def extract_instrument_type_ids(self, binary: dict, digital: dict) -> dict[str, list[int]]:
        """
        🇧🇷 Extrai listas de IDs de instrumentos agrupados por tipo.

        🇺🇸 Extracts lists of instrument IDs grouped by type.

        Args:
            binary (dict): Dados brutos de instrumentos binários.
            digital (dict): Dados brutos de instrumentos digitais.

        Returns:
            dict[str, list[int]]: Dicionário com chave tipo e valor lista de IDs.
        """
        # Converte chaves para int para evitar inconsistências
        to_int_list = lambda d: list(map(int, d.keys()))

        return {
            InstrumentType.BINARY.value: to_int_list(binary.get("binary", {}).get("actives", {})),
            InstrumentType.TURBO.value: to_int_list(binary.get("turbo", {}).get("actives", {})),
            InstrumentType.BLITZ.value: to_int_list(binary.get("blitz", {}).get("actives", {})),
            InstrumentType.DIGITAL.value: [item["active_id"] for item in digital.get("underlying", [])],
        }

    async def _parse_instrument(self, item: dict) -> Instrument | None:
        """
        🇧🇷 Converte um dicionário cru em um objeto Instrument.

        🇺🇸 Converts a raw dictionary into an Instrument object.

        Args:
            item (dict): Dados crus do instrumento.

        Returns:
            Instrument | None: Objeto Instrument ou None em caso de erro.
        """
        try:
            instrument = Instrument.from_dict(item)
            return replace(
                instrument,
                market=self._build_market_type(item["group_id"]),
                trading=self._build_trading_info(item, instrument.id),
                type=item.get("type", []),
            )
        except Exception as err:
            logger.error(f"Error parsing instrument {item.get('id', 'unknown')}: {err}")
            return None

    def _build_trading_info(self, data: dict, instrument_id: int) -> TradingInfo:
        """
        🇧🇷 Cria objeto TradingInfo a partir dos dados brutos.

        🇺🇸 Creates a TradingInfo object from raw data.

        Args:
            data (dict): Dados crus do instrumento.
            instrument_id (int): ID do instrumento.

        Returns:
            TradingInfo: Objeto com informações de trading.
        """
        profits = {
            "digital": int(self._profits.get(InstrumentType.DIGITAL.value, {}).get(instrument_id, 0.0)),
            "binary": int(self._profits.get(InstrumentType.BINARY.value, {}).get(instrument_id, 0.0)),
            "turbo": int(self._profits.get(InstrumentType.TURBO.value, {}).get(instrument_id, 0.0)),
        }

        return TradingInfo(
            profit=profits,
            regulation_mode=data.get("regulation_mode", "both"),
            precision=data.get("precision", 6),
            min_investment=float(data.get("minimal_bet")),
            max_investment=float(data.get("maximal_bet")),
            allowed_expirations=[int(t) for t in data.get("option", {}).get("expiration_times", {})],
        )

    def _build_market_type(self, group_id: int) -> MarketType:
        """
        🇧🇷 Converte o group_id para o tipo de mercado (MarketType).

        🇺🇸 Converts group_id to market type (MarketType).

        Args:
            group_id (int): ID do grupo.

        Returns:
            MarketType: Tipo do mercado.
        """
        key = (
            self._raw_groups.get(str(group_id), "")
            .replace("front.", "")
            .strip()
            .split(" ")[0]
            .lower()
        )
        return MarketType(key)
