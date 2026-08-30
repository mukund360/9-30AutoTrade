from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from config import APP_TITLE
from groww_client import GrowwClient
from strategy_engine import ORBStrategyEngine
from trade_logger import TradeLogger


class PaperTradingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1120x720")
        self.minsize(980, 620)

        self.client = GrowwClient()
        self.logger = TradeLogger(Path(__file__).resolve().parent)
        self.engine = ORBStrategyEngine(self.client, self.logger, self.push_status)
        self.running = False

        self.token_var = tk.StringVar()
        self.range_high_var = tk.StringVar()
        self.range_low_var = tk.StringVar()
        self.index_var = tk.StringVar(value="-")
        self.mode_var = tk.StringVar(value="Demo mode" if self.client.demo_mode else "Live mode")
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
        self._refresh_table()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")

        ttk.Label(top, text="API Auth Token").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.token_var, width=48, show="*").grid(row=0, column=1, padx=8)
        ttk.Button(top, text="Connect", command=self.connect_api).grid(row=0, column=2, padx=4)
        ttk.Button(top, text="Start Strategy", command=self.start_strategy).grid(row=0, column=3, padx=4)
        ttk.Button(top, text="Stop", command=self.stop_strategy).grid(row=0, column=4, padx=4)
        ttk.Label(top, textvariable=self.mode_var, foreground="#0b6b6b").grid(row=0, column=5, padx=16)

        range_frame = ttk.LabelFrame(self, text="Opening Range", padding=12)
        range_frame.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Label(range_frame, text="Range High").grid(row=0, column=0, sticky="w")
        ttk.Entry(range_frame, textvariable=self.range_high_var, width=12).grid(row=0, column=1, padx=8)
        ttk.Label(range_frame, text="Range Low").grid(row=0, column=2, sticky="w")
        ttk.Entry(range_frame, textvariable=self.range_low_var, width=12).grid(row=0, column=3, padx=8)
        ttk.Button(range_frame, text="Set ORB", command=self.set_range).grid(row=0, column=4, padx=8)
        ttk.Label(range_frame, text="Index LTP").grid(row=0, column=5, padx=(24, 4))
        ttk.Label(range_frame, textvariable=self.index_var, font=("Segoe UI", 12, "bold")).grid(row=0, column=6)

        cols = ("portfolio", "side", "entry_price", "last_price", "quantity", "capital", "realized_pnl", "status", "reason")
        table_frame = ttk.Frame(self, padding=(12, 0, 12, 12))
        table_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=16)
        for col in cols:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, anchor="center", width=110)
        self.tree.column("reason", width=220, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        log_frame = ttk.LabelFrame(self, text="Activity Log", padding=12)
        log_frame.pack(fill="both", padx=12, pady=(0, 12))
        self.log_text = tk.Text(log_frame, height=8, wrap="word")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

        status = ttk.Label(self, textvariable=self.status_var, padding=10, relief="sunken", anchor="w")
        status.pack(fill="x", side="bottom")

    def push_status(self, msg: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(msg)
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self._refresh_table()

    def connect_api(self) -> None:
        ok, msg = self.client.connect(self.token_var.get())
        self.mode_var.set("Demo mode" if self.client.demo_mode else "Live mode")
        if ok:
            self.push_status(msg)
        else:
            messagebox.showerror("Connection Error", msg)

    def set_range(self) -> None:
        try:
            high = float(self.range_high_var.get())
            low = float(self.range_low_var.get())
        except ValueError:
            messagebox.showerror("Invalid ORB", "Enter numeric values for range high and low.")
            return
        if low >= high:
            messagebox.showerror("Invalid ORB", "Range low must be less than range high.")
            return
        self.engine.set_opening_range(high, low)
        self._refresh_table()

    def start_strategy(self) -> None:
        if not self.client.connected:
            messagebox.showwarning("Not Connected", "Connect the API first.")
            return
        self.running = True
        self.push_status("Strategy started")
        self.after(1000, self.poll_market)

    def stop_strategy(self) -> None:
        self.running = False
        self.push_status("Strategy stopped")

    def poll_market(self) -> None:
        if not self.running:
            return
        try:
            spot = self.client.get_index_ltp()
            now = datetime.now()
            self.index_var.set(f"{spot:.2f}")
            self.engine.on_tick(now, spot)
            self._refresh_table()
        except Exception as exc:
            self.push_status(f"Polling error: {exc}")
        self.after(3000, self.poll_market)

    def _refresh_table(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.engine.get_rows():
            self.tree.insert("", "end", values=tuple(row.values()))


if __name__ == "__main__":
    app = PaperTradingApp()
    app.mainloop()
