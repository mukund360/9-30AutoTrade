from dataclasses import dataclass
from datetime import time

APP_TITLE = "NIFTY 15-min ORB Options — Simulator Only"
STARTING_CAPITAL = 100000.0
ORB_START_TIME = time(9, 15)
ORB_END_TIME = time(9, 30)
STRATEGY_START_TIME = time(9, 30)
SQUARE_OFF_TIME = time(15, 20)
STRIKE_STEP = 50
POLL_INTERVAL_MS = 3000
UNDERLYING_SYMBOL = "NIFTY 50"
UNDERLYING_CODE = "NIFTY"
LOG_DIR = "logs"
ENABLE_AUTO_ORB = True
DEFAULT_LOT_SIZE = 75
#TP_SL_COMBOS = [(1, 2), (1, 5), (2, 5), (3, 5), (5, 5), (2, 10), (5, 10)]
TP_SL_COMBOS = [(1, 2)]

@dataclass(frozen=True)
class PositionConfig:
    stop_loss_points: float
    take_profit_points: float

PORTFOLIOS = [PositionConfig(sl, tp) for sl, tp in TP_SL_COMBOS]
