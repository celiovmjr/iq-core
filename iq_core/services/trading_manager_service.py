from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import Mapping, Callable, Awaitable, List, Literal
from dataclasses import replace

from ..anotations import measure_time
from ..entities import Signal, TradeResult, TradeResultType, TradeStatus
from ..exceptions import TradingError
from .interfaces import TradingService

logger = logging.getLogger(__name__)

TradeCallback = Callable[[TradeResult, "TradingManagerService"], Awaitable[None]]


class TradingManagerService:
    """
    🇧🇷 Serviço para gerenciar a banca, operações e eventos de atualização de trades,
    com suporte a estratégias de Martingale e Soros por tipo de ativo.

    🇺🇸 Service to manage trading balance, operations and trade event updates,
    with support for Martingale and Soros strategies per instrument type.

    📋 Parâmetros:
    - start_balance (float): Saldo inicial
    - stop_win_percent (float): Percentual de stop win
    - stop_loss_percent (float): Percentual de stop loss
    - services (Mapping[str, TradingService]): Mapeamento de serviços de trading
    - max_open_trades (int): Máximo de trades abertos simultaneamente (padrão: 5)
    - martingale (int): Número máximo de passos do Martingale (padrão: 0)
    - soros (int): Número máximo de passos do Soros (padrão: 0)

    ⚠️ Exceções:
    - TradingError: Erro durante execução de trades
    """

    def __init__(
        self,
        start_balance: float,
        stop_win_percent: float,
        stop_loss_percent: float,
        services: Mapping[str, TradingService],
        max_open_trades: int = 5,
        martingale: int = 0,
        soros: int = 0,
    ) -> None:
        self._start_balance = Decimal(str(start_balance))
        self._balance = Decimal(str(start_balance))
        self._stop_win = (Decimal(str(stop_win_percent)) / 100) * self._start_balance
        self._stop_loss = (Decimal(str(stop_loss_percent)) / 100) * self._start_balance
        self._services = services
        self._history: List[TradeResult] = []
        self._callbacks: List[TradeCallback] = []
        self._watch_tasks: dict[int, asyncio.Task[None]] = {}
        self._open_instrument_ids: set[int] = set()
        self._trade_instruments: dict[int, int] = {}
        self._max_open_trades = max_open_trades
        self._martingale_max = martingale
        self._soros_max = sor

        # Estruturas de controle de estado para Martingale e Soros
        self._martingale_control: dict[str, tuple[int, Decimal]] = {}
        self._soros_control: dict[str, tuple[int, Decimal]] = {}
        # Novo atributo para rastrear o nível atual de Soros, para exibição no resumo
        self._soros_current_level: dict[str, int] = {}

    def __str__(self) -> str:
        return self.summary()

    async def __aenter__(self) -> TradingManagerService:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    @property
    def start_balance(self) -> Decimal:
        return self._start_balance

    @property
    def balance(self) -> Decimal:
        return self._balance

    @property
    def stop_win(self) -> Decimal:
        return self._stop_win

    @property
    def stop_loss(self) -> Decimal:
        return self._stop_loss

    @property
    def history(self) -> List[TradeResult]:
        return self._history

    @property
    def total_operations(self) -> int:
        return len(self._history)

    @property
    def total_wins(self) -> int:
        return sum(1 for trade in self._history if trade.result == TradeResultType.WIN)

    @property
    def total_losses(self) -> int:
        return sum(
            1 for trade in self._history if trade.result == TradeResultType.LOOSE
        )

    @property
    def total_draws(self) -> int:
        return sum(1 for trade in self._history if trade.result == TradeResultType.DRAW)

    @property
    def profit(self) -> Decimal:
        return self._balance - self._start_balance

    @property
    def gain_percent(self) -> float:
        return float(max(Decimal(0), self.profit) / self._start_balance * 100)

    @property
    def loss_percent(self) -> float:
        return float(max(Decimal(0), -self.profit) / self._start_balance * 100)

    def can_trade(self) -> bool:
        return -self._stop_loss <= self.profit <= self._stop_win

    def _count_open_trades(self) -> int:
        return len(self._watch_tasks)

    @measure_time
    async def execute(self, signal: Signal) -> None | int:
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
            strategy: Literal["martingale", "soros"] | None = None
            level = 0
            amount = Decimal(str(signal.amount))

            if signal.type in self._martingale_control:
                level, control_value = self._martingale_control.pop(signal.type)
                amount = control_value
                strategy = "martingale"
                self._soros_current_level.pop(signal.type, None) # Limpa o estado de Soros quando Martingale é ativado
                logger.info(
                    "Executing Martingale level %d for %s with amount %.2f",
                    level,
                    signal.type,
                    amount,
                )

            elif signal.type in self._soros_control:
                level, control_value = self._soros_control.pop(signal.type)
                amount = control_value
                strategy = "soros"
                logger.info(
                    "Executing Soros level %d for %s with amount %.2f",
                    level,
                    signal.type,
                    amount,
                )
            else:
                self._soros_current_level.pop(signal.type, None) # Reseta o estado de Soros quando não há ciclo ativo

            signal_to_use = replace(signal, amount=amount)

            if signal_to_use.amount > self._balance:
                logger.warning(
                    "Trade amount (%.2f) is greater than current balance (%.2f). Trade blocked.",
                    signal_to_use.amount,
                    self._balance
                )
                return None
            
            trade_id = await service.open_trade(signal_to_use)

            if not trade_id:
                raise TradingError("Trade was not started.")

            self._open_instrument_ids.add(instrument_id)
            self._trade_instruments[trade_id] = instrument_id
            self._balance -= Decimal(str(signal_to_use.amount))

            task = asyncio.create_task(
                self._monitor_trade(trade_id, service, signal_to_use, strategy, level)
            )
            self._watch_tasks[trade_id] = task
            return trade_id

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None

    async def _monitor_trade(
        self,
        trade_id: int,
        service: TradingService,
        signal: Signal,
        strategy: Literal["martingale", "soros"] | None,
        level: int,
    ) -> None:
        trade: TradeResult | None = None

        try:
            while True:
                status, trade = await service.trade_status(trade_id)
                if not status or trade.status != TradeStatus.CLOSED:
                    await asyncio.sleep(10)
                    continue

                profit = Decimal(str(trade.profit - trade.invest))
                self._balance += profit
                self._history.append(trade)

                logger.info(
                    "Trade finished | ID: %s | Result: %s | Profit: %.2f | New balance: %.2f",
                    trade_id,
                    trade.result.name,
                    trade.profit,
                    self.balance,
                )

                for cb in self._callbacks:
                    try:
                        await cb(trade, self)
                    except Exception:
                        logger.error("Error in callback for trade %s", trade_id)
                
                break

        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Error monitoring trade %s", trade_id)
        finally:
            self._watch_tasks.pop(trade_id, None)
            instrument_id = self._trade_instruments.pop(trade_id, None)
            if instrument_id:
                self._open_instrument_ids.discard(instrument_id)
            
            if trade:
                await self._queue_recovery(signal, trade, strategy, level)

    async def _queue_recovery(
        self,
        signal: Signal,
        trade: TradeResult,
        strategy: Literal["martingale", "soros"] | None,
        level: int,
    ) -> None:
        trade_type = signal.type
        initial_amount = Decimal(str(signal.amount))

        if trade.result == TradeResultType.LOOSE and self._martingale_max > 0:
            if level < self._martingale_max:
                new_level = level + 1
                next_amount = initial_amount + Decimal(str(trade.profit))
                self._martingale_control[trade_type] = (new_level, next_amount)
                self._soros_control.pop(trade_type, None)
                self._soros_current_level.pop(trade_type, None)
                logger.info(
                    "Martingale level %d queued for %s. Next amount: %.2f",
                    new_level,
                    trade_type,
                    next_amount,
                )
            else:
                self._martingale_control.pop(trade_type, None)
                self._soros_control.pop(trade_type, None)
                self._soros_current_level.pop(trade_type, None)

        elif trade.result == TradeResultType.WIN and self._soros_max > 0:
            if level < self._soros_max:
                new_level = level + 1
                next_amount = Decimal(str(trade.profit))
                if next_amount > 0:
                    self._soros_control[trade_type] = (new_level, next_amount)
                    self._martingale_control.pop(trade_type, None)
                    self._soros_current_level[trade_type] = new_level
                    logger.info(
                        "Soros level %d queued for %s. Next amount: %.2f",
                        new_level,
                        trade_type,
                        next_amount,
                    )
            else:
                self._soros_control.pop(trade_type, None)
                self._soros_current_level.pop(trade_type, None)

        else:
            self._martingale_control.pop(trade_type, None)
            self._soros_control.pop(trade_type, None)
            self._soros_current_level.pop(trade_type, None)

    def register(self, callback: TradeCallback) -> None:
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            logger.debug("Subscribed callback to event: trade-finished")

    def unregister(self, callback: TradeCallback) -> None:
        try:
            self._callbacks.remove(callback)
            logger.debug("Unsubscribed callback to event: trade-finished")
        except ValueError:
            pass

    async def close(self) -> None:
        tasks = list(self._watch_tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._watch_tasks.clear()
        self._open_instrument_ids.clear()
        self._trade_instruments.clear()
        self._martingale_control.clear()
        self._soros_control.clear()
        self._soros_current_level.clear()
        logger.debug("All monitoring tasks and strategy controls have been cleared.")

    def summary(self) -> str:
        """
        🇧🇷 Resumo das operações realizadas, incluindo limites de stop-win e stop-loss.
        🇺🇸 Trade summary report including stop-win and stop-loss limits.
        """
        gain_loss_percent = (
            (self.profit / self._start_balance * 100) if self._start_balance != 0 else 0
        )

        martingale_state = "\n".join(
            [f"    - {k}: {v[0]}/{self._martingale_max}" for k, v in self._martingale_control.items()]
        ) or "N/A"
        
        soros_state = "\n".join(
            [f"    - {k}: {v}/{self._soros_max}" for k, v in self._soros_current_level.items()]
        ) or "N/A"

        return (
            f"📊 Trading Summary\n"
            f"────────────────────────────\n"
            f"💼 Start Balance      : R$ {self._start_balance:.2f}\n"
            f"💰 Current Balance    : R$ {self.balance:.2f}\n"
            f"📈 Total Profit       : R$ {self.profit:.2f} ({gain_loss_percent:+.2f}%)\n"
            f"⚠️ Stop Win           : R$ {self.stop_win:.2f}\n"
            f"⚠️ Stop Loss          : R$ {self.stop_loss:.2f}\n"
            f"🔁 Trades             : {self.total_operations} (✅ {self.total_wins} | ❌ {self.total_losses} | ⚖️ {self.total_draws})\n"
            f"🔄 Martingale Cycles  :\n{martingale_state}\n"
            f"🚀 Soros Cycles       :\n{soros_state}\n"
            f"────────────────────────────"
        )