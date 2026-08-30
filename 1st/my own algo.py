from dataclasses import dataclass
from datetime import time
from growwapi import GrowwAPI
 
api_key = "eyJraWQiOiJaTUtjVXciLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjI1NzQxNjM2NjYsImlhdCI6MTc4NTc2MzY2NiwibmJmIjoxNzg1NzYzNjY2LCJzdWIiOiJ7XCJ0b2tlblJlZklkXCI6XCIyNjc5ZTFmOS1mYThhLTRlMjktODJkMS05NGYxYzg3MWFhMzVcIixcInZlbmRvckludGVncmF0aW9uS2V5XCI6XCJlMzFmZjIzYjA4NmI0MDZjODg3NGIyZjZkODQ5NTMxM1wiLFwidXNlckFjY291bnRJZFwiOlwiY2IzNTY3NGUtZjVlNi00NGQyLTg5MDMtNTU0ODljMTFiZGY4XCIsXCJkZXZpY2VJZFwiOlwiZTg4ODIyZTktNDAyYi01NDQ1LTg1NjMtNTdjZmY0NzdhMDRlXCIsXCJzZXNzaW9uSWRcIjpcImMzMDRlMjMwLWU3ZTMtNGI4Ny1iZjk0LTU5ZWFhYzE2MDU0ZlwiLFwiYWRkaXRpb25hbERhdGFcIjpcIno1NC9NZzltdjE2WXdmb0gvS0EwYkN6QzNqSXcxZWUzQXo0QktJOStJN0pSTkczdTlLa2pWZDNoWjU1ZStNZERhWXBOVi9UOUxIRmtQejFFQisybTdRPT1cIixcInJvbGVcIjpcImF1dGgtdG90cFwiLFwic291cmNlSXBBZGRyZXNzXCI6XCIyNDAxOjQ5MDA6ODgzMTplNjUyOmUxYjQ6NjFiMTo2ZTljOmQ3YSwxNzIuNjkuODcuNjAsMzUuMjQxLjIzLjEyM1wiLFwidHdvRmFFeHBpcnlUc1wiOjI1NzQxNjM2NjY1MDAsXCJ2ZW5kb3JOYW1lXCI6XCJncm93d0FwaVwifSIsImlzcyI6ImFwZXgtYXV0aC1wcm9kLWFwcCJ9.K3yReqheMNUt3_NF89OBDbhx2GT41OgM5P1K90ocZe2E7TR44SBMGq8vGDnC4my5latFRmpUmMxzhtlFZzaLSg"
secret = "%HA&W5uuV1v-mH_Q-GTyquA8s9!uIMrD"
 
access_token = GrowwAPI.get_access_token(api_key=api_key, secret=secret)
# Use access_token to initiate GrowwAPI
groww = GrowwAPI(access_token)

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

ltp_response = groww.get_ltp(
  segment=groww.SEGMENT_CASH,
  exchange_trading_symbols="NSE_NIFTY"
)
print(ltp_response)
