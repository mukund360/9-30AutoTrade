# NIFTY ORB Simulator-Only Build

This package is a pure market simulator version of the strategy. It does not use the real Groww API at all.

## Files
- `config_sim.py`
- `market_simulator.py`
- `strategy_engine_sim.py`
- `trade_logger_sim.py`
- `gui_app_sim.py`

## Run simulator-only build
```bash
python gui_app_sim.py
```

## How to activate simulator in your previous v2 files
Your previous v2 files already have simulator behavior built in as demo mode. In `groww_client_v2.py`, the client switches to demo mode automatically when `growwapi` is not installed.

To use that simulator mode in the old v2 build:
1. Do not install `growwapi`, or uninstall it.
2. Run `python gui_app_v2.py`.
3. Enter any text in the token box.
4. Click `Connect`.
5. Click `Auto ORB` or manually set the ORB.
6. Click `Start Strategy`.

When demo mode is active, the app uses simulated index and option prices and does not call a live API.
