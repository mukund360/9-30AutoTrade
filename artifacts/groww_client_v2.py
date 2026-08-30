from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional

from config_v2 import DEFAULT_LOT_SIZE, STRIKE_STEP, UNDERLYING_CODE

try:
    import growwapi  # type: ignore
except Exception:
    growwapi = None


@dataclass
class OptionInstrument:
    symbol: str
    strike: int
    option_type: str
    expiry: date
    lot_size: int


class GrowwClient:
    def __init__(self) -> None:
        self.connected = False
        self.token: Optional[str] = None
        self.demo_mode = growwapi is None
        self._rng = random.Random()
        self._demo_spot = 24850.0

    def connect(self, auth_token: str) -> tuple[bool, str]:
        self.token = auth_token.strip()
        if not self.token:
            self.connected = False
            return False, "Missing API auth token."
        self.connected = True
        if self.demo_mode:
            return True, "Connected in demo mode. Install growwapi and wire endpoints for live data."
        return True, "Connected."

    def get_index_ltp(self) -> float:
        if self.demo_mode:
            self._demo_spot += self._rng.uniform(-18, 18)
            return round(self._demo_spot, 2)
        raise NotImplementedError("Implement Groww SDK quote lookup for live NIFTY LTP.")

    def get_opening_range_candle(self, trade_day: Optional[date] = None) -> tuple[float, float]:
        day = trade_day or date.today()
        if self.demo_mode:
            base = 24840 + self._rng.uniform(-40, 40)
            high = round(base + self._rng.uniform(25, 60), 2)
            low = round(base - self._rng.uniform(25, 60), 2)
            return max(high, low), min(high, low)
        raise NotImplementedError(
            "Implement Groww historical candle fetch for the 09:15-09:30 NIFTY candle and return (high, low)."
        )

    def get_nearest_expiry(self, from_day: Optional[date] = None) -> date:
        base = from_day or date.today()
        weekday = 3
        days_ahead = (weekday - base.weekday()) % 7
        return base if days_ahead == 0 else base + timedelta(days=days_ahead)

    def get_lot_size(self, symbol: str = UNDERLYING_CODE) -> int:
        if self.demo_mode:
            return DEFAULT_LOT_SIZE
        raise NotImplementedError("Implement Groww instrument master lookup for lot size.")

    def get_atm_strike(self, spot: float) -> int:
        return int(round(spot / STRIKE_STEP) * STRIKE_STEP)

    def get_option_instrument(self, spot: float, side: str) -> OptionInstrument:
        strike = self.get_atm_strike(spot)
        expiry = self.get_nearest_expiry()
        option_type = "CE" if side.upper() == "CALL" else "PE"
        symbol = f"NIFTY{expiry.strftime('%d%b%y').upper()}{strike}{option_type}"
        return OptionInstrument(symbol=symbol, strike=strike, option_type=option_type, expiry=expiry, lot_size=self.get_lot_size())

    def get_option_ltp(self, instrument: OptionInstrument, spot: float) -> float:
        if self.demo_mode:
            intrinsic = max(0.0, spot - instrument.strike) if instrument.option_type == "CE" else max(0.0, instrument.strike - spot)
            time_value = max(18.0, 55 - abs(spot - instrument.strike) * 0.18)
            noise = self._rng.uniform(-2.5, 2.5)
            return round(max(5.0, intrinsic * 0.45 + time_value + noise), 2)
        raise NotImplementedError("Implement Groww option quote lookup for selected option instrument.")

    def integration_notes(self) -> str:
        return (
            "Live integration template: connect auth token, fetch NIFTY LTP, fetch 15-minute OHLC for 09:15-09:30, "
            "resolve nearest expiry, resolve lot size, build option symbol, fetch option LTP."
        )
