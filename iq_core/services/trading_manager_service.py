from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import Mapping, Callable, Awaitable, List

from ..anotations import measure_time
from ..entities import Signal, TradeResult, TradeResultType, TradeStatus
from ..exceptions import TradingError
from .interfaces import TradingService

logger = logging.getLogger(__name__)

TradeCallback = Callable[[TradeResult, "TradingManagerService"], Awaitable[None]]


class TradingManagerService:
    """
    🇧🇷 Serviço para gerenciar a banca, operações e eventos de atualização de trades.

    📋 Parâmetros:
    - start_balance (float): Saldo inicial
    - stop_win_percent (float): Percentual de stop win
    - stop_loss_percent (float): Percentual de stop loss
    - services (Mapping[str, TradingService]): Mapeamento de serviços de trading
    - max_open_trades (int): Máximo de trades abertos simultaneamente (padrão: 5)

    ⚠️ Exceções:
    - TradingError: Erro durante execução de trades

    🇺🇸 Service to manage trading balance, operations and trade event updates.

    📋 Parameters:
    - start_balance (float): Initial balance
    - stop_win_percent (float): Stop win percentage
    - stop_loss_percent (float): Stop loss percentage
    - services (Mapping[str, TradingService]): Trading services mapping
    - max_open_trades (int): Maximum simultaneous open trades (default: 5)

    ⚠️ Raises:
    - TradingError: Error during trade execution
    """

    def __init__(
        self,
        start_balance: float,
        stop_win_percent: float,
        stop_loss_percent: float,
        services: Mapping[str, TradingService],
        max_open_trades: int = 5,
    ) -> None:
        self._start_balance = Decimal(start_balance)
        self._balance = Decimal(start_balance)
        self._stop_win = (Decimal(stop_win_percent) / 100) * self._start_balance
        self._stop_loss = (Decimal(stop_loss_percent) / 100) * self._start_balance
        self._services = services
        self._history: List[TradeResult] = []
        self._callbacks: List[TradeCallback] = []
        self._watch_tasks: dict[int, asyncio.Task[None]] = {}
        self._open_instrument_ids: set[int] = set()
        self._trade_instruments: dict[int, int] = {}
        self._max_open_trades = max_open_trades

    def __str__(self) -> str:
        return self.summary()

    async def __aenter__(self) -> TradingManagerService:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    @property
    def start_balance(self) -> Decimal:
        """
        🇧🇷 Saldo inicial.

        📤 Retorna:
        - Decimal: Saldo inicial

        🇺🇸 Start balance.

        📤 Returns:
        - Decimal: Start balance
        """
        return self._start_balance

    @property
    def balance(self) -> Decimal:
        """
        🇧🇷 Saldo atual.

        📤 Retorna:
        - Decimal: Saldo atual

        🇺🇸 Current balance.

        📤 Returns:
        - Decimal: Current balance
        """
        return self._balance

    @property
    def stop_win(self) -> Decimal:
        """
        🇧🇷 Limite de stop win em valor absoluto.

        📤 Retorna:
        - Decimal: Valor do stop win

        🇺🇸 Stop win limit in absolute value.

        📤 Returns:
        - Decimal: Stop win value
        """
        return self._stop_win

    @property
    def stop_loss(self) -> Decimal:
        """
        🇧🇷 Limite de stop loss em valor absoluto.

        📤 Retorna:
        - Decimal: Valor do stop loss

        🇺🇸 Stop loss limit in absolute value.

        📤 Returns:
        - Decimal: Stop loss value
        """
        return self._stop_loss

    @property
    def history(self) -> List[TradeResult]:
        """
        🇧🇷 Histórico de trades executados.

        📤 Retorna:
        - List[TradeResult]: Lista com resultados dos trades

        🇺🇸 History of executed trades.

        📤 Returns:
        - List[TradeResult]: List with trade results
        """
        return self._history

    @property
    def total_operations(self) -> int:
        """
        🇧🇷 Total de operações realizadas.

        📤 Retorna:
        - int: Número total de operações

        🇺🇸 Total number of executed trades.

        📤 Returns:
        - int: Total trades count
        """
        return len(self._history)

    @property
    def total_wins(self) -> int:
        """
        🇧🇷 Total de operações com lucro.

        📤 Retorna:
        - int: Número de operações vencedoras

        🇺🇸 Total profitable trades.

        📤 Returns:
        - int: Number of winning trades
        """
        return sum(1 for trade in self._history if trade.result == TradeResultType.WIN)

    @property
    def total_losses(self) -> int:
        """
        🇧🇷 Total de operações com prejuízo.

        📤 Retorna:
        - int: Número de operações perdedoras

        🇺🇸 Total losing trades.

        📤 Returns:
        - int: Number of losing trades
        """
        return sum(
            1 for trade in self._history if trade.result == TradeResultType.LOOSE
        )

    @property
    def total_draws(self) -> int:
        """
        🇧🇷 Total de operações empatadas (sem lucro nem prejuízo).

        📤 Retorna:
        - int: Número de operações neutras

        🇺🇸 Total number of draw trades (no profit or loss).

        📤 Returns:
        - int: Number of draw trades
        """
        return sum(1 for trade in self._history if trade.result == TradeResultType.DRAW)

    @property
    def profit(self) -> Decimal:
        """
        🇧🇷 Lucro relativo ao saldo inicial.

        📤 Retorna:
        - Decimal: Lucro atual

        🇺🇸 Profit relative to start balance.

        📤 Returns:
        - Decimal: Current profit
        """
        return self._balance - self._start_balance

    @property
    def gain_percent(self) -> float:
        """
        🇧🇷 Percentual de ganho.

        📤 Retorna:
        - float: Percentual de ganho

        🇺🇸 Percentage gain.

        📤 Returns:
        - float: Gain percentage
        """
        return float(max(Decimal(0), self.profit) / self._start_balance * 100)

    @property
    def loss_percent(self) -> float:
        """
        🇧🇷 Percentual de perda.

        📤 Retorna:
        - float: Percentual de perda

        🇺🇸 Percentage loss.

        📤 Returns:
        - float: Loss percentage
        """
        return float(max(Decimal(0), -self.profit) / self._start_balance * 100)

    def instrument_limit_reached(self, instrument_id: int) -> bool:
        """
        🇧🇷 Verifica se o ativo atingiu o limite de operações simultâneas.

        🇺🇸 Checks if the instrument reached the trade limit.
        """
        return instrument_id in self._open_instrument_ids

    def is_limit_reached(self) -> bool:
        """
        🇧🇷 Verifica se os limites de stop-win ou stop-loss foram atingidos.

        📋 Parâmetros:
        - Nenhum

        📤 Retorna:
        - bool: True se limite atingido, False caso contrário

        ⚠️ Exceções:
        - Nenhuma

        🇺🇸 Checks if stop-win or stop-loss limits are reached.

        📋 Parameters:
        - None

        📤 Returns:
        - bool: True if limit reached, False otherwise

        ⚠️ Raises:
        - None
        """
        return self.profit >= self._stop_win or self.profit <= -self._stop_loss

    def can_trade(self) -> bool:
        """
        🇧🇷 Indica se é permitido operar.

        📤 Retorna:
        - bool: True se permitido operar, False caso contrário

        🇺🇸 Indicates if trading is allowed.

        📤 Returns:
        - bool: True if trading allowed, False otherwise
        """
        return not self.is_limit_reached()

    def _count_open_trades(self) -> int:
        """
        🇧🇷 Conta quantos trades estão sendo monitorados atualmente.

        📤 Retorna:
        - int: Número de trades abertos e monitorados

        🇺🇸 Counts how many trades are currently being monitored.

        📤 Returns:
        - int: Number of open and monitored trades
        """
        return len(self._watch_tasks)

    def register(self, callback: TradeCallback) -> None:
        """
        🇧🇷 Registra um callback global para receber updates de trades finalizados.

        📋 Parâmetros:
        - callback (TradeCallback): Função callback a ser registrada

        📤 Retorna:
        - None: Função sem retorno

        ⚠️ Exceções:
        - Nenhuma

        🇺🇸 Registers a global callback for completed trades.

        📋 Parameters:
        - callback (TradeCallback): Callback function to register

        📤 Returns:
        - None: Function with no return

        ⚠️ Raises:
        - None
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            logger.debug(f"Subscribed callback to event: trade-finished")

    def unregister(self, callback: TradeCallback) -> None:
        """
        🇧🇷 Remove um callback global registrado.

        📋 Parâmetros:
        - callback (TradeCallback): Função callback a ser removida

        📤 Retorna:
        - None: Função sem retorno

        ⚠️ Exceções:
        - ValueError: Callback não encontrado

        🇺🇸 Unregisters a global callback.

        📋 Parameters:
        - callback (TradeCallback): Callback function to remove

        📤 Returns:
        - None: Function with no return

        ⚠️ Raises:
        - ValueError: Callback not found
        """
        try:
            self._callbacks.remove(callback)
            logger.debug(f"Undubscribed callback to event: trade-finished")
        except ValueError:
            pass

    @measure_time
    async def execute(self, signal: Signal) -> None | TradeResult:
        """
        🇧🇷 Executa uma operação baseada em sinal, monitora seu resultado e notifica callbacks.

        📋 Parâmetros:
        - signal (Signal): Sinal de entrada para a operação

        📤 Retorna:
        - None | TradeResult: None se operação bloqueada, TradeResult se executada

        ⚠️ Exceções:
        - TradingError: Tipo de operação não suportado

        🇺🇸 Executes a trade based on a signal, monitors it, and notifies callbacks.

        📋 Parameters:
        - signal (Signal): Entry signal for the trade

        📤 Returns:
        - None | TradeResult: None if trade blocked, TradeResult if executed

        ⚠️ Raises:
        - TradingError: Unsupported trade type
        """
        instrument_id = signal.instrument.id

        if not self.can_trade():
            logger.debug("STOP WIN/LOSS limit reached. Trade blocked.")
            return None

        if self._count_open_trades() >= self._max_open_trades:
            logger.debug(
                "Maximum open trades limit (%s) reached.", self._max_open_trades
            )
            return None

        if instrument_id in self._open_instrument_ids:
            logger.debug(
                "Trade already open for instrument ID %s (%s).",
                instrument_id,
                signal.instrument.name,
            )
            return None

        service = self._services.get(signal.type)
        if not service:
            raise TradingError(f"Unsupported trade type: {signal.type}")

        try:
            trade_id = await service.open_trade(signal)
            if not trade_id:
                raise TradingError("Trade was not started.")

            self._open_instrument_ids.add(instrument_id)
            self._trade_instruments[trade_id] = instrument_id
            self._balance -= Decimal(signal.amount)
            logger.info("Trade opened with ID %s on %s", trade_id, signal.instrument.name)

            task = asyncio.create_task(self._monitor_trade(trade_id, service))
            self._watch_tasks[trade_id] = task

        except (Exception, TradingError) as e:
            logger.error(f"Error executing trade: {e}")
            return None

    async def _monitor_trade(self, trade_id: int, service: TradingService) -> None:
        """
        🇧🇷 Monitora o status de um trade específico até seu fechamento,
        atualiza o saldo e notifica callbacks registrados.

        📋 Parâmetros:
        - trade_id (int): ID da operação a ser monitorada
        - service (TradingService): Serviço de trading responsável pelo trade

        📤 Retorna:
        - None: Função assíncrona sem retorno

        ⚠️ Exceções:
        - Pode capturar exceções internas para manter o monitoramento

        🇺🇸 Monitors the status of a specific trade until it closes,
        updates the balance, and notifies registered callbacks.

        📋 Parameters:
        - trade_id (int): ID of the trade to monitor
        - service (TradingService): Trading service responsible for the trade

        📤 Returns:
        - None: Async function with no return

        ⚠️ Raises:
        - Internal exceptions are caught to keep monitoring stable
        """
        logger.info("Starting trade monitoring %s...", trade_id)
        trade: TradeResult | None = None

        try:
            while True:
                status, trade = await service.trade_status(trade_id)
                if not status or trade.status != TradeStatus.CLOSED:
                    await asyncio.sleep(10)
                    continue


                invest = Decimal(str(trade.invest))
                profit = Decimal(str(trade.profit))
                is_draw = trade.result.DRAW
                is_digital = trade.instrument_type.DIGITAL

                self._balance += invest if is_draw and not is_digital else profit
                self._history.append(trade)

                logger.info(
                    "Trade finished | ID: %s | Result: %s | Profit: %.2f",
                    trade_id,
                    trade.result.name,
                    trade.profit,
                )

                for cb in self._callbacks:
                    try:
                        await cb(trade, self)
                    except Exception:
                        logger.error("Error in callback for trade %s", trade_id)

                break

        except asyncio.CancelledError:
            logger.info("Trade monitoring %s cancelled", trade_id)
        except Exception:
            logger.error("Error monitoring trade %s", trade_id)
        finally:
            self._watch_tasks.pop(trade_id, None)
            instrument_id = self._trade_instruments.pop(trade_id, None)
            if instrument_id is not None:
                self._open_instrument_ids.discard(instrument_id)

    async def close(self) -> None:
        """
        🇧🇷 Cancela o monitoramento de todos os trades ativos e aguarda seu término.

        📋 Parâmetros:
        - Nenhum

        📤 Retorna:
        - None: Função assíncrona sem retorno

        ⚠️ Exceções:
        - Nenhuma

        🇺🇸 Cancels monitoring of all active trades and awaits their completion.

        📋 Parameters:
        - None

        📤 Returns:
        - None: Async function with no return

        ⚠️ Raises:
        - None
        """
        tasks = list(self._watch_tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._watch_tasks.clear()
        self._open_instrument_ids.clear()
        self._trade_instruments.clear()
        logger.debug("Unsubscribed all callbacks from event: trade-finished")

    def summary(self) -> str:
        """
        🇧🇷 Resumo das operações realizadas, incluindo limites de stop-win e stop-loss.

        📤 Retorna:
        - str: Relatório formatado das operações

        🇺🇸 Trade summary report including stop-win and stop-loss limits.

        📤 Returns:
        - str: Formatted operations report
        """
        gain_loss_percent = (
            (self.profit / self._start_balance * 100) if self._start_balance != 0 else 0
        )

        return (
            f"📊 Trading Summary\n"
            f"────────────────────────────\n"
            f"💼 Start Balance  : R$ {self._start_balance:.2f}\n"
            f"💰 Current Balance: R$ {self.balance:.2f}\n"
            f"📈 Total Profit   : R$ {self.profit:.2f} ({gain_loss_percent:+.2f}%)\n"
            f"⚠️ Stop Win       : R$ {self.stop_win:.2f}\n"
            f"⚠️ Stop Loss      : R$ {self.stop_loss:.2f}\n"
            f"🔁 Trades         : {self.total_operations} (✅ {self.total_wins} | ❌ {self.total_losses} | ⚖️ {self.total_draws})\n"
            f"────────────────────────────"
        )
