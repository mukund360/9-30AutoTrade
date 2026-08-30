from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Callable, Optional

from config import PORTFOLIOS, SQUARE_OFF_TIME, STARTING_CAPITAL, STRATEGY_START_TIME
from groww_client import GrowwClient, OptionInstrument
from trade_logger import TradeLogger


@dataclass
class SimulatedPosition:
    portfolio_name: str
    stop_loss_points: float
    take_profit_points: float
    capital: float = STARTING_CAPITAL
    is_open: bool = False
    side: str = ""
    instrument: Optional[OptionInstrument] = None
    entry_time: Optional[datetime] = None
    entry_price: float = 0.0
    exit_time: Optional[datetime] = None
    exit_price: float = 0.0
    quantity: int = 0
    last_reason: str = ""
    realized_pnl: float = 0.0

    def snapshot(self) -> dict:
        mtm = 0.0
        if self.is_open and self.quantity:
            mtm = (self.exit_price or self.entry_price) - self.entry_price
            mtm *= self.quantity
        return {
            "portfolio": self.portfolio_name,
            "side": self.side or "-",
            "entry_price": self.entry_price or 0.0,
            "last_price": self.exit_price or self.entry_price or 0.0,
            "quantity": self.quantity,
            "capital": round(self.capital, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "status": "OPEN" if self.is_open else "IDLE",
            "reason": self.last_reason,
        }


class ORBStrategyEngine:
    ONE_SHOT_PER_DAY = True

    def __init__(self, client: GrowwClient, logger: TradeLogger, status_cb: Callable[[str], None] | None = None) -> None:
        self.client = client
        self.logger = logger
        self.status_cb = status_cb or (lambda _msg: None)
        self.positions = [
            SimulatedPosition(f"SL{cfg.stop_loss_points}-TP{cfg.take_profit_points}", cfg.stop_loss_points, cfg.take_profit_points)
            for cfg in PORTFOLIOS
        ]
        self.current_day: date | None = None
        self.range_high: float | None = None
        self.range_low: float | None = None
        self.breakout_side_taken: set[str] = set()
        self.active_instrument: Optional[OptionInstrument] = None

    def reset_for_day(self, trade_day: date) -> None:
        self.current_day = trade_day
        self.range_high = None
        self.range_low = None
        self.breakout_side_taken = set()
        self.active_instrument = None
        for pos in self.positions:
            pos.is_open = False
            pos.side = ""
            pos.instrument = None
            pos.entry_time = None
            pos.entry_price = 0.0
            pos.exit_time = None
            pos.exit_price = 0.0
            pos.quantity = 0
            pos.last_reason = "Day reset"
        self.status_cb(f"Reset strategy for {trade_day.isoformat()}")

    def set_opening_range(self, high: float, low: float) -> None:
        self.range_high = high
        self.range_low = low
        self.status_cb(f"Opening range locked: high={high:.2f}, low={low:.2f}")

    def on_tick(self, now: datetime, spot: float) -> None:
        if self.current_day != now.date():
            self.reset_for_day(now.date())
        if self.range_high is None or self.range_low is None:
            return
        self._check_breakout(now, spot)
        self._manage_open_positions(now, spot)

    def _check_breakout(self, now: datetime, spot: float) -> None:
        if now.time() < STRATEGY_START_TIME:
            return
        if spot > self.range_high:
            self._enter_positions(now, spot, "CALL")
        elif spot < self.range_low:
            self._enter_positions(now, spot, "PUT")

    def _enter_positions(self, now: datetime, spot: float, side: str) -> None:
        if self.ONE_SHOT_PER_DAY and side in self.breakout_side_taken:
            return
        instrument = self.client.get_option_instrument(spot, side)
        option_ltp = self.client.get_option_ltp(instrument, spot)
        for pos in self.positions:
            if pos.is_open:
                continue
            qty = instrument.lot_size
            pos.is_open = True
            pos.side = side
            pos.instrument = instrument
            pos.entry_time = now
            pos.entry_price = option_ltp
            pos.exit_price = option_ltp
            pos.quantity = qty
            pos.last_reason = f"{side} breakout entry"
        self.active_instrument = instrument
        self.breakout_side_taken.add(side)
        self.status_cb(f"Entered {side} across portfolios at {option_ltp:.2f} in {instrument.symbol}")

    def _manage_open_positions(self, now: datetime, spot: float) -> None:
        for pos in self.positions:
            if not pos.is_open or not pos.instrument:
                continue
            ltp = self.client.get_option_ltp(pos.instrument, spot)
            pos.exit_price = ltp
            pnl_per_unit = ltp - pos.entry_price
            if pnl_per_unit >= pos.take_profit_points:
                self._exit_position(pos, now, ltp, "Take Profit")
            elif pnl_per_unit <= -pos.stop_loss_points:
                self._exit_position(pos, now, ltp, "Stop Loss")
            elif now.time() >= SQUARE_OFF_TIME:
                self._exit_position(pos, now, ltp, "Time Square Off")

    def _exit_position(self, pos: SimulatedPosition, now: datetime, exit_price: float, reason: str) -> None:
        gross = (exit_price - pos.entry_price) * pos.quantity
        pos.capital += gross
        pos.realized_pnl += gross
        pos.is_open = False
        pos.exit_time = now
        pos.exit_price = exit_price
        pos.last_reason = reason
        trade_day = now.date()
        self.logger.log_trade(
            trade_day,
            {
                "trade_date": trade_day.isoformat(),
                "portfolio": pos.portfolio_name,
                "side": pos.side,
                "symbol": pos.instrument.symbol,
                "strike": pos.instrument.strike,
                "expiry": pos.instrument.expiry.isoformat(),
                "entry_time": pos.entry_time.strftime("%H:%M:%S") if pos.entry_time else "",
                "entry_price": round(pos.entry_price, 2),
                "exit_time": pos.exit_time.strftime("%H:%M:%S") if pos.exit_time else "",
                "exit_price": round(pos.exit_price, 2),
                "quantity": pos.quantity,
                "reason": reason,
                "gross_pnl": round(gross, 2),
                "capital_after_trade": round(pos.capital, 2),
            },
        )
        self.status_cb(f"Exited {pos.portfolio_name} with {reason}; P&L {gross:.2f}")

    def get_rows(self) -> list[dict]:
        return [p.snapshot() for p in self.positions]
