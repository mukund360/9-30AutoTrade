'''
all the configuration parameters for the NIFTY 15-min ORB Options Paper Trading Dashboard 
if sl tp combos are changed, update the PORTFOLIOS list accordingly
'''
from dataclasses import dataclass
from datetime import time

APP_TITLE = "NIFTY 15-min ORB Options — Paper Trading Dashboard v2"
STARTING_CAPITAL = 100000.0
ORB_START_TIME = time(9, 15)
ORB_END_TIME = time(9, 30)
STRATEGY_START_TIME = time(9, 30)
SQUARE_OFF_TIME = time(15, 20)
STRIKE_STEP = 50
POLL_INTERVAL_MS = 3000
UNDERLYING_SYMBOL = "NIFTY 50"
UNDERLYING_CODE = "NIFTY"
INDEX_EXCHANGE = "NSE"
OPTION_EXCHANGE = "NFO"
LOG_DIR = "logs"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
ENABLE_AUTO_ORB = True
DEFAULT_LOT_SIZE = 65
TP_SL_COMBOS = [
    (1, 2),
    (1, 5),
    (2, 5),
    (3, 5),
    (5, 5),
    (2, 10),
    (5, 10),
    (10, 10),
]

@dataclass(frozen=True)
class PositionConfig:
    stop_loss_points: float
    take_profit_points: float

PORTFOLIOS = [PositionConfig(sl, tp) for sl, tp in TP_SL_COMBOS]

README_ASSUMPTIONS = """
Assumptions baked into this implementation:
1. TP-SL combos are in option premium points.
2. ATM strike is rounded to nearest 50.
3. The app is paper-trading only; no order endpoints are used.
4. One breakout per day per side by default.
5. Positions are force-closed at 15:20 IST.
6. Auto ORB uses the first completed 15-minute candle when historical OHLC is available.
""".strip()
