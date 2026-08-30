from dataclasses import dataclass
from datetime import time

APP_TITLE = "NIFTY 15-min ORB Options — Paper Trading Dashboard"
STARTING_CAPITAL = 100000.0
ORB_START_TIME = time(9, 15)
ORB_END_TIME = time(9, 30)
STRATEGY_START_TIME = time(9, 30)
SQUARE_OFF_TIME = time(15, 20)
STRIKE_STEP = 50
POLL_INTERVAL_MS = 1000
UNDERLYING_SYMBOL = "NIFTY"
INDEX_EXCHANGE = "NSE"
OPTION_EXCHANGE = "NFO"
LOG_DIR = "logs"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
TP_SL_COMBOS = [
    (1, 2),
    (1, 5),
    (2, 5),
    (3, 5),
    (5, 5),
    (2, 10),
    (5, 10),
]

@dataclass(frozen=True)
class PositionConfig:
    stop_loss_points: float
    take_profit_points: float

PORTFOLIOS = [PositionConfig(sl, tp) for sl, tp in TP_SL_COMBOS]

README_ASSUMPTIONS = """
Assumptions baked into this starter implementation:
1. TP-SL combos are in option premium points.
2. ATM strike is rounded to nearest 50.
3. Nearest expiry and lot size are fetched dynamically via the data client.
4. One breakout per day per side by default.
5. Positions are force-closed at 15:20 IST.
6. This app never places real orders.
""".strip()
