from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Optional

from config_sim import PORTFOLIOS, SQUARE_OFF_TIME, STARTING_CAPITAL, STRATEGY_START_TIME
from market_simulator import MarketSimulator, OptionInstrument
from trade_logger_sim import TradeLogger


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
    current_price: float = 0.0
    exit_time: Optional[datetime] = None
    exit_price: float = 0.0
    quantity: int = 0
    last_reason: str = "Idle"
    realized_pnl: float = 0.0

    def mtm(self) -> float:
        if not self.is_open:
            return 0.0
        return round((self.current_price - self.entry_price) * self.quantity, 2)

    def snapshot(self) -> dict:
        return {
            "portfolio": self.portfolio_name,
            "side": self.side or "-",
            "entry": round(self.entry_price, 2),
            "ltp": round(self.current_price or self.exit_price or 0.0, 2),
            "qty": self.quantity,
            "mtm": self.mtm(),
            "realized": round(self.realized_pnl, 2),
            "capital": round(self.capital, 2),
            "status": "OPEN" if self.is_open else "IDLE",
            "reason": self.last_reason,
        }


class ORBStrategyEngine:
    ONE_SHOT_PER_DAY = False

    def __init__(self, client: MarketSimulator, logger: TradeLogger, status_cb: Callable[[str], None] | None = None) -> None:
        self.client = client
        self.logger = logger
        self.status_cb = status_cb or (lambda _msg: None)
        self.positions = [SimulatedPosition(f"SL{cfg.stop_loss_points}-TP{cfg.take_profit_points}", cfg.stop_loss_points, cfg.take_profit_points) for cfg in PORTFOLIOS]
        self.current_day: date | None = None
        self.range_high: float | None = None
        self.range_low: float | None = None
        self.last_spot: float | None = None
        self.prev_spot: float | None = None
        self.breakout_side_taken: set[str] = set()

    def reset_for_day(self, trade_day: date) -> None:
        preserve_range = self.current_day == trade_day
        prev_high, prev_low = self.range_high, self.range_low
        self.current_day = trade_day
        self.range_high = prev_high if preserve_range else None
        self.range_low = prev_low if preserve_range else None
        self.last_spot = None
        self.prev_spot = None
        self.breakout_side_taken = set()
        for pos in self.positions:
            pos.is_open = False
            pos.side = ""
            pos.instrument = None
            pos.entry_time = None
            pos.entry_price = 0.0
            pos.current_price = 0.0
            pos.exit_time = None
            pos.exit_price = 0.0
            pos.quantity = 0
            pos.last_reason = "Range armed" if (self.range_high is not None and self.range_low is not None) else "Day reset"
        self.status_cb(f"Reset strategy for {trade_day.isoformat()}")

    def set_opening_range(self, high: float, low: float) -> None:
        self.range_high = high
        self.range_low = low
        self.status_cb(f"Opening range set: high={high:.2f}, low={low:.2f}")

    def auto_set_opening_range(self, trade_day: date) -> None:
        high, low = self.client.get_opening_range_candle(trade_day)
        self.set_opening_range(high, low)

    def on_tick(self, now: datetime, spot: float) -> None:
        if self.current_day != now.date():
            self.reset_for_day(now.date())
        previous_spot = self.last_spot
        self.prev_spot = previous_spot
        self.last_spot = spot
        if self.range_high is None or self.range_low is None:
            return
        self._check_breakout(now, spot, previous_spot)
        self._manage_open_positions(now, spot)

    def _check_breakout(self, now: datetime, spot: float, previous_spot: float | None) -> None:
        if previous_spot is None:
            if spot > self.range_high:
                self._enter_positions(now, spot, "CALL")
            elif spot < self.range_low:
                self._enter_positions(now, spot, "PUT")
            return
        crossed_up = previous_spot <= self.range_high < spot
        crossed_down = previous_spot >= self.range_low > spot
        if crossed_up:
            self._enter_positions(now, spot, "CALL")
        elif crossed_down:
            self._enter_positions(now, spot, "PUT")

    def _enter_positions(self, now: datetime, spot: float, side: str) -> None:
        if self.ONE_SHOT_PER_DAY and side in self.breakout_side_taken:
            return
        instrument = self.client.get_option_instrument(spot, side)
        option_ltp = self.client.get_option_ltp(instrument, spot)
        created = 0
        for pos in self.positions:
            if pos.is_open:
                continue
            pos.is_open = True
            pos.side = side
            pos.instrument = instrument
            pos.entry_time = now
            pos.entry_price = option_ltp
            pos.current_price = option_ltp
            pos.exit_price = option_ltp
            pos.quantity = instrument.lot_size
            pos.last_reason = f"{side} breakout entry"
            created += 1
        if created:
            self.breakout_side_taken.add(side)
            self.status_cb(f"Entered {side} in {created} portfolios at {option_ltp:.2f} ({instrument.symbol})")

    def _manage_open_positions(self, now: datetime, spot: float) -> None:
        for pos in self.positions:
            if not pos.is_open or not pos.instrument:
                continue
            ltp = self.client.get_option_ltp(pos.instrument, spot)
            pos.current_price = ltp
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
        pos.current_price = exit_price
        pos.last_reason = reason
        trade_day = now.date()
        self.logger.log_trade(trade_day, {
            "trade_date": trade_day.isoformat(), "portfolio": pos.portfolio_name, "side": pos.side,
            "symbol": pos.instrument.symbol, "strike": pos.instrument.strike, "expiry": pos.instrument.expiry.isoformat(),
            "entry_time": pos.entry_time.strftime("%H:%M:%S") if pos.entry_time else "", "entry_price": round(pos.entry_price, 2),
            "exit_time": pos.exit_time.strftime("%H:%M:%S") if pos.exit_time else "", "exit_price": round(pos.exit_price, 2),
            "quantity": pos.quantity, "reason": reason, "gross_pnl": round(gross, 2), "capital_after_trade": round(pos.capital, 2),
        })
        self.status_cb(f"Exited {pos.portfolio_name} with {reason}; P&L {gross:.2f}")

    def totals(self) -> dict:
        return {
            "realized": round(sum(p.realized_pnl for p in self.positions), 2),
            "mtm": round(sum(p.mtm() for p in self.positions), 2),
            "open_count": sum(1 for p in self.positions if p.is_open),
            "spot": self.last_spot,
            "range_high": self.range_high,
            "range_low": self.range_low,
        }

    def get_rows(self) -> list[dict]:
        return [p.snapshot() for p in self.positions]
