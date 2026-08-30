# NIFTY 15-min ORB Options — Paper Trading Dashboard

A Tkinter-based **paper trading** (simulation only) tool that:
- Reads the NIFTY 50 opening range (first 15-min candle, 09:15–09:30) via the Groww API.
- On a breakout above the range high → simulates buying the ATM **Call**.
- On a breakout below the range low → simulates buying the ATM **Put**.
- Runs **7 independent virtual portfolios** in parallel, each starting with **Rs 1,00,000**, one per TP-SL combo: `1-2, 1-5, 2-5, 3-5, 5-5, 2-10, 5-10`.
- Logs every entry/exit to a daily CSV so you can compare which TP-SL combo performed best.
- **No real orders are ever placed.** Groww is used only for market data (index LTP, option chain). All positions and P&L are simulated in memory and in the CSV log.

## Files
- `config.py` — all settings (capital, TP-SL combos, timings). Read the big comment block at the top — it documents the assumptions I made about your requirements.
- `groww_client.py` — thin wrapper over the official `growwapi` SDK (read-only calls).
- `strategy_engine.py` — the ORB logic + the 7 virtual paper positions.
- `trade_logger.py` — writes `logs/trades_YYYY-MM-DD.csv`.
- `gui_app.py` — the Tkinter dashboard. **Run this file.**

## Setup
```bash
pip install growwapi
python gui_app.py
```

You'll need an active Groww Trading API subscription and an API auth token, generated from the [Groww API dashboard](https://groww.in/trade-api). Paste the token into the "API Auth Token" field in the app and click **Connect**, then **Start Strategy**.

## Assumptions you should double-check (all easy to change in `config.py`)
1. **What "1-2, 1-5, ... 5-10" means**: I assumed these are `(Stop-Loss points, Take-Profit points)` measured in **option premium points** (e.g. "2-10" = cut the loss at ₹2 below entry premium, book profit at ₹10 above). If you actually meant percentages or index points, just edit `TP_SL_COMBOS` in `config.py` — the engine logic doesn't need to change.
2. **ATM strike** = nearest strike to spot, rounded to the nearest 50.
3. **Expiry** is fetched dynamically (nearest expiry ≥ today) rather than hard-coded, since NSE has changed weekly-expiry weekdays before.
4. **Lot size** is fetched from the Groww instrument master at runtime rather than hard-coded, since NIFTY's lot size has changed more than once.
5. **One breakout per day per side** — the classic ORB rule. If you'd rather allow re-entries after a stop-out, set `ORBStrategyEngine.ONE_SHOT_PER_DAY = False`.
6. **Square-off time** is 15:20 IST — any still-open virtual position is force-closed and logged at end of day.

## Important disclaimers
- This is a decision-support / simulation tool, not investment advice, and it does not execute real trades.
- Markets and APIs can behave unexpectedly (data gaps, rate limits, holidays, expiry changes) — test thoroughly during market hours on a normal trading day before relying on the numbers, and keep an eye on the Activity Log panel for warnings.
- Options trading carries substantial risk; past or simulated performance is not indicative of future results.
