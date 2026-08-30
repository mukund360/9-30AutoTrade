from __future__ import annotations

import tkinter as tk
from datetime import date, datetime, time
from pathlib import Path
from tkinter import messagebox, ttk

from config_v2 import APP_TITLE, ENABLE_AUTO_ORB, POLL_INTERVAL_MS
from groww_client_v2 import GrowwClient
from strategy_engine_v2 import ORBStrategyEngine
from trade_logger_v2 import TradeLogger


class PaperTradingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1260x780")
        self.minsize(1100, 680)
        self.configure(bg="#eef2f7")

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
        self.realized_var = tk.StringVar(value="0.00")
        self.mtm_var = tk.StringVar(value="0.00")
        self.open_count_var = tk.StringVar(value="0")
        self.orb_var = tk.StringVar(value="Not set")

        self._style()
        self._build_ui()
        self._refresh_table()

    def _style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background="#eef2f7")
        style.configure("TLabelframe", background="#eef2f7")
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Header.TLabel", background="#eef2f7", font=("Segoe UI", 20, "bold"), foreground="#132238")
        style.configure("Muted.TLabel", background="#eef2f7", foreground="#5b6b80")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#5b6b80", font=("Segoe UI", 9))
        style.configure("CardValue.TLabel", background="#ffffff", foreground="#132238", font=("Segoe UI", 18, "bold"))
        style.configure("Treeview", rowheight=28, font=("Consolas", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        #header = ttk.Frame(self, padding=(18, 16, 18, 8))
        #header.pack(fill="x")
        #ttk.Label(header, text="NIFTY ORB Paper Dashboard", style="Header.TLabel").pack(anchor="w")
        #ttk.Label(header, text="Groww market-data template + simulation engine", style="Muted.TLabel").pack(anchor="w", pady=(2, 0))

        top = ttk.Frame(self, padding=(18, 8, 18, 8))
        top.pack(fill="x")

        conn = ttk.LabelFrame(top, text="Connection", padding=12)
        conn.pack(side="left", fill="x", expand=True)
        ttk.Label(conn, text="API Auth Token").grid(row=0, column=0, sticky="w")
        ttk.Entry(conn, textvariable=self.token_var, width=42, show="*").grid(row=0, column=1, padx=8)
        ttk.Button(conn, text="Connect", command=self.connect_api).grid(row=0, column=2, padx=4)
        ttk.Label(conn, textvariable=self.mode_var, style="Muted.TLabel").grid(row=0, column=3, padx=12)
        ttk.Button(conn, text="Integration Notes", command=self.show_integration_notes).grid(row=0, column=4, padx=4)

        orb = ttk.LabelFrame(top, text="Opening Range", padding=12)
        orb.pack(side="left", fill="x", expand=True, padx=(12, 0))
        ttk.Label(orb, text="Range High").grid(row=0, column=0, sticky="w")
        ttk.Entry(orb, textvariable=self.range_high_var, width=10).grid(row=0, column=1, padx=6)
        ttk.Label(orb, text="Range Low").grid(row=0, column=2, sticky="w")
        ttk.Entry(orb, textvariable=self.range_low_var, width=10).grid(row=0, column=3, padx=6)
        ttk.Button(orb, text="Set ORB", command=self.set_range).grid(row=0, column=4, padx=4)
        ttk.Button(orb, text="Auto ORB", command=self.auto_set_range).grid(row=0, column=5, padx=4)

        control = ttk.LabelFrame(self, text="Run Control", padding=12)
        control.pack(fill="x", padx=18, pady=(0, 10))
        ttk.Button(control, text="Start Strategy", command=self.start_strategy).pack(side="left", padx=4)
        ttk.Button(control, text="Stop", command=self.stop_strategy).pack(side="left", padx=4)
        ttk.Label(control, text="Index LTP:").pack(side="left", padx=(18, 4))
        ttk.Label(control, textvariable=self.index_var, font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Label(control, text="ORB:").pack(side="left", padx=(18, 4))
        ttk.Label(control, textvariable=self.orb_var).pack(side="left")

        cards = ttk.Frame(self, padding=(18, 0, 18, 10))
        cards.pack(fill="x")
        self._metric_card(cards, "Realized P&L", self.realized_var).pack(side="left", fill="x", expand=True)
        self._metric_card(cards, "Open MTM", self.mtm_var).pack(side="left", fill="x", expand=True, padx=10)
        self._metric_card(cards, "Open Positions", self.open_count_var).pack(side="left", fill="x", expand=True)

        middle = ttk.Frame(self, padding=(18, 0, 18, 10))
        middle.pack(fill="both", expand=True)

        table_wrap = ttk.LabelFrame(middle, text="Portfolio Monitor", padding=10)
        table_wrap.pack(side="left", fill="both", expand=True)
        cols = ("portfolio", "side", "entry", "ltp", "qty", "mtm", "realized", "capital", "status", "reason")
        self.tree = ttk.Treeview(table_wrap, columns=cols, show="headings", height=18)
        for col in cols:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=95, anchor="center")
        self.tree.column("portfolio", width=120)
        self.tree.column("reason", width=180, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        right = ttk.LabelFrame(middle, text="Activity Log", padding=10)
        right.pack(side="left", fill="both", padx=(10, 0))
        self.log_text = tk.Text(right, width=42, height=25, wrap="word", bg="#0f1720", fg="#d6e2f0", insertbackground="#ffffff")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

        status = ttk.Label(self, textvariable=self.status_var, padding=10, relief="sunken", anchor="w")
        status.pack(fill="x", side="bottom")

    def _metric_card(self, parent: ttk.Frame, title: str, variable: tk.StringVar) -> ttk.Frame:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=variable, style="CardValue.TLabel").pack(anchor="w", pady=(8, 0))
        return card

    def push_status(self, msg: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(msg)
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self._refresh_table()
        self._refresh_metrics()

    def connect_api(self) -> None:
        ok, msg = self.client.connect(self.token_var.get())
        self.mode_var.set("Demo mode" if self.client.demo_mode else "Live mode")
        if ok:
            self.push_status(msg)
        else:
            messagebox.showerror("Connection Error", msg)

    def show_integration_notes(self) -> None:
        messagebox.showinfo("Groww Integration Template", self.client.integration_notes())

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
        self._refresh_metrics()

    def auto_set_range(self) -> None:
        try:
            self.engine.auto_set_opening_range(date.today())
            if self.engine.range_high is not None:
                self.range_high_var.set(f"{self.engine.range_high:.2f}")
            if self.engine.range_low is not None:
                self.range_low_var.set(f"{self.engine.range_low:.2f}")
            self._refresh_metrics()
        except Exception as exc:
            messagebox.showerror("Auto ORB Error", str(exc))

    def start_strategy(self) -> None:
        if not self.client.connected:
            messagebox.showwarning("Not Connected", "Connect the API first.")
            return
        if ENABLE_AUTO_ORB and self.engine.range_high is None:
            try:
                self.auto_set_range()
            except Exception:
                pass
        self.running = True
        self.push_status("Strategy started")
        self.after(500, self.poll_market)

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
            self._refresh_metrics()
        except Exception as exc:
            self.push_status(f"Polling error: {exc}")
        self.after(POLL_INTERVAL_MS, self.poll_market)

    def _refresh_metrics(self) -> None:
        totals = self.engine.totals()
        self.realized_var.set(f"₹ {totals['realized']:.2f}")
        self.mtm_var.set(f"₹ {totals['mtm']:.2f}")
        self.open_count_var.set(str(totals['open_count']))
        rh, rl = totals.get('range_high'), totals.get('range_low')
        self.orb_var.set("Not set" if rh is None or rl is None else f"H {rh:.2f} / L {rl:.2f}")

    def _refresh_table(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.engine.get_rows():
            self.tree.insert("", "end", values=tuple(row.values()))


if __name__ == "__main__":
    app = PaperTradingApp()
    app.mainloop()
