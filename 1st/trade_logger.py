from __future__ import annotations

import csv
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Iterable

from config import LOG_DIR


class TradeLogger:
    headers = [
        "trade_date",
        "portfolio",
        "side",
        "symbol",
        "strike",
        "expiry",
        "entry_time",
        "entry_price",
        "exit_time",
        "exit_price",
        "quantity",
        "reason",
        "gross_pnl",
        "capital_after_trade",
    ]

    def __init__(self, base_dir: str | Path = ".") -> None:
        self.base_dir = Path(base_dir)
        self.log_dir = self.base_dir / LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def daily_file(self, trade_day: date) -> Path:
        return self.log_dir / f"trades_{trade_day.isoformat()}.csv"

    def ensure_file(self, trade_day: date) -> Path:
        path = self.daily_file(trade_day)
        if not path.exists():
            with path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(self.headers)
        return path

    def log_trade(self, trade_day: date, trade_row: dict) -> Path:
        path = self.ensure_file(trade_day)
        with path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self.headers)
            writer.writerow(trade_row)
        return path

    def log_many(self, trade_day: date, rows: Iterable[dict]) -> Path:
        path = self.ensure_file(trade_day)
        with path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self.headers)
            for row in rows:
                writer.writerow(row)
        return path
