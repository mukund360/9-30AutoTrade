from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta

from config_sim import DEFAULT_LOT_SIZE, STRIKE_STEP


@dataclass
class OptionInstrument:
    symbol: str
    strike: int
    option_type: str
    expiry: date
    lot_size: int


class MarketSimulator:
    def __init__(self, seed: int | None = None) -> None:
        self.connected = False
        self._rng = random.Random(seed)
        self._spot = 24850.0

    def connect(self, auth_token: str = "SIMULATOR") -> tuple[bool, str]:
        self.connected = True
        return True, "Connected to simulator mode. No real API is used."

    def get_index_ltp(self) -> float:
        self._spot += self._rng.uniform(-18, 18)
        return round(self._spot, 2)

    def get_opening_range_candle(self, trade_day: date | None = None) -> tuple[float, float]:
        base = 24840 + self._rng.uniform(-40, 40)
        high = round(base + self._rng.uniform(25, 60), 2)
        low = round(base - self._rng.uniform(25, 60), 2)
        return max(high, low), min(high, low)

    def get_nearest_expiry(self, from_day: date | None = None) -> date:
        base = from_day or date.today()
        weekday = 3
        days_ahead = (weekday - base.weekday()) % 7
        return base if days_ahead == 0 else base + timedelta(days=days_ahead)

    def get_lot_size(self) -> int:
        return DEFAULT_LOT_SIZE

    def get_atm_strike(self, spot: float) -> int:
        return int(round(spot / STRIKE_STEP) * STRIKE_STEP)

    def get_option_instrument(self, spot: float, side: str) -> OptionInstrument:
        strike = self.get_atm_strike(spot)
        expiry = self.get_nearest_expiry()
        option_type = "CE" if side.upper() == "CALL" else "PE"
        symbol = f"NIFTY{expiry.strftime('%d%b%y').upper()}{strike}{option_type}"
        return OptionInstrument(symbol=symbol, strike=strike, option_type=option_type, expiry=expiry, lot_size=self.get_lot_size())

    def get_option_ltp(self, instrument: OptionInstrument, spot: float) -> float:
        intrinsic = max(0.0, spot - instrument.strike) if instrument.option_type == "CE" else max(0.0, instrument.strike - spot)
        time_value = max(18.0, 55 - abs(spot - instrument.strike) * 0.18)
        noise = self._rng.uniform(-2.5, 2.5)
        return round(max(5.0, intrinsic * 0.45 + time_value + noise), 2)

    def integration_notes(self) -> str:
        return "Simulator mode is active. No Groww API setup is required."
