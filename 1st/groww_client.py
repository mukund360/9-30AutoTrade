from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from config import STRIKE_STEP, UNDERLYING_SYMBOL

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
        self._demo_spot = 24850.0
        self._demo_option = 120.0
        self._rng = random.Random()

    def connect(self, auth_token: str) -> tuple[bool, str]:
        self.token = auth_token.strip()
        if not self.token:
            self.connected = False
            return False, "Missing API auth token."
        self.connected = True
        if self.demo_mode:
            return True, "Connected in demo mode. Install growwapi for live market data."
        return True, "Connected."

    def get_index_ltp(self) -> float:
        if self.demo_mode:
            self._demo_spot += self._rng.uniform(-18, 18)
            return round(self._demo_spot, 2)
        raise NotImplementedError(
            "Wire get_index_ltp() to the official growwapi market quote endpoint for your account."
        )

    def get_nearest_expiry(self, from_day: Optional[date] = None) -> date:
        base = from_day or date.today()
        weekday = 3
        days_ahead = (weekday - base.weekday()) % 7
        if days_ahead == 0:
            return base
        return base + timedelta(days=days_ahead)

    def get_lot_size(self, symbol: str = UNDERLYING_SYMBOL) -> int:
        if self.demo_mode:
            return 75
        raise NotImplementedError(
            "Wire get_lot_size() to the Groww instrument master lookup."
        )

    def get_atm_strike(self, spot: float) -> int:
        return int(round(spot / STRIKE_STEP) * STRIKE_STEP)

    def get_option_instrument(self, spot: float, side: str) -> OptionInstrument:
        strike = self.get_atm_strike(spot)
        expiry = self.get_nearest_expiry()
        option_type = "CE" if side.upper() == "CALL" else "PE"
        symbol = f"NIFTY{expiry.strftime('%d%b%y').upper()}{strike}{option_type}"
        return OptionInstrument(
            symbol=symbol,
            strike=strike,
            option_type=option_type,
            expiry=expiry,
            lot_size=self.get_lot_size(),
        )

    def get_option_ltp(self, instrument: OptionInstrument, spot: float) -> float:
        if self.demo_mode:
            intrinsic = max(0.0, spot - instrument.strike) if instrument.option_type == "CE" else max(0.0, instrument.strike - spot)
            time_value = max(18.0, 55 - abs(spot - instrument.strike) * 0.18)
            noise = self._rng.uniform(-2.0, 2.0)
            return round(max(5.0, intrinsic * 0.45 + time_value + noise), 2)
        raise NotImplementedError(
            "Wire get_option_ltp() to the official Groww option quote endpoint."
        )
