from __future__ import annotations

import tkinter as tk
from collections import deque
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config_sim import APP_TITLE, ENABLE_AUTO_ORB, POLL_INTERVAL_MS
from market_simulator import MarketSimulator
from strategy_engine_sim import ORBStrategyEngine
from trade_logger_sim import TradeLogger


class PaperTradingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x820")
        self.minsize(1150, 720)
        self.configure(bg="#eef2f7")

        self.client = MarketSimulator()
        self.logger = TradeLogger(Path(__file__).resolve().parent)
        self.engine = ORBStrategyEngine(self.client, self.logger, self.push_status)
        self.running = False
        self.price_history = deque(maxlen=120)
        self.time_history = deque(maxlen=120)

        self.token_var = tk.StringVar(value="SIM")
        self.range_high_var = tk.StringVar()
        self.range_low_var = tk.StringVar()
        self.index_var = tk.StringVar(value="-")
        self.status_var = tk.StringVar(value="Ready")
        self.realized_var = tk.StringVar(value="₹ 0.00")
        self.mtm_var = tk.StringVar(value="₹ 0.00")
        self.open_count_var = tk.StringVar(value="0")
        self.orb_var = tk.StringVar(value="Not set")

        self._style()
        self._build_ui()
        self._refresh_table()
        self._refresh_chart()

    def _style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background="#eef2f7")
        style.configure("TLabelframe", background="#eef2f7")
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Header.TLabel", background="#eef2f7", font=("Segoe UI", 18, "bold"), foreground="#132238")
        style.configure("Sub.TLabel", background="#eef2f7", foreground="#5b6b80", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#68778d", font=("Segoe UI", 9))
        style.configure("CardValue.TLabel", background="#ffffff", foreground="#132238", font=("Segoe UI", 18, "bold"))
        style.configure("Treeview", rowheight=28, font=("Consolas", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(16, 14, 16, 8))
        header.pack(fill="x")
        ttk.Label(header, text="NIFTY ORB Simulator", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Clean view with chart and paper trades only", style="Sub.TLabel").pack(anchor="w")

        top = ttk.Frame(self, padding=(16, 6, 16, 8))
        top.pack(fill="x")

        controls = ttk.LabelFrame(top, text="Controls", padding=10)
        controls.pack(fill="x")
        ttk.Entry(controls, textvariable=self.token_var, width=10).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Connect", command=self.connect_api).pack(side="left", padx=4)
        ttk.Button(controls, text="Auto ORB", command=self.auto_set_range).pack(side="left", padx=4)
        ttk.Label(controls, text="High").pack(side="left", padx=(16, 4))
        ttk.Entry(controls, textvariable=self.range_high_var, width=10).pack(side="left", padx=4)
        ttk.Label(controls, text="Low").pack(side="left", padx=(10, 4))
        ttk.Entry(controls, textvariable=self.range_low_var, width=10).pack(side="left", padx=4)
        ttk.Button(controls, text="Set", command=self.set_range).pack(side="left", padx=4)
        ttk.Button(controls, text="Start", command=self.start_strategy).pack(side="left", padx=(18, 4))
        ttk.Button(controls, text="Stop", command=self.stop_strategy).pack(side="left", padx=4)
        ttk.Label(controls, text="Price").pack(side="left", padx=(18, 4))
        ttk.Label(controls, textvariable=self.index_var, font=("Segoe UI", 12, "bold")).pack(side="left")

        cards = ttk.Frame(self, padding=(16, 0, 16, 10))
        cards.pack(fill="x")
        self._metric_card(cards, "Realized", self.realized_var).pack(side="left", fill="x", expand=True)
        self._metric_card(cards, "MTM", self.mtm_var).pack(side="left", fill="x", expand=True, padx=10)
        self._metric_card(cards, "Open", self.open_count_var).pack(side="left", fill="x", expand=True)
        self._metric_card(cards, "ORB", self.orb_var).pack(side="left", fill="x", expand=True, padx=(10, 0))

        center = ttk.Frame(self, padding=(16, 0, 16, 10))
        center.pack(fill="both", expand=True)

        left = ttk.Frame(center)
        left.pack(side="left", fill="both", expand=True)

        chart_box = ttk.LabelFrame(left, text="Price Chart", padding=8)
        chart_box.pack(fill="both", expand=True)
        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_box)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        table_box = ttk.LabelFrame(left, text="Portfolios", padding=8)
        table_box.pack(fill="both", expand=True, pady=(10, 0))
        cols = ("portfolio", "side", "entry", "ltp", "qty", "mtm", "realized", "capital", "status")
        self.tree = ttk.Treeview(table_box, columns=cols, show="headings", height=9)
        for col in cols:
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=92, anchor="center")
        self.tree.column("portfolio", width=118)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table_box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        right = ttk.LabelFrame(center, text="Log", padding=8)
        right.pack(side="left", fill="both", padx=(10, 0))
        self.log_text = tk.Text(right, width=34, height=30, wrap="word", bg="#0f1720", fg="#d6e2f0", insertbackground="#ffffff", relief="flat")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

        status = ttk.Label(self, textvariable=self.status_var, padding=8, relief="sunken", anchor="w")
        status.pack(fill="x", side="bottom")

    def _metric_card(self, parent: ttk.Frame, title: str, variable: tk.StringVar) -> ttk.Frame:
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=variable, style="CardValue.TLabel").pack(anchor="w", pady=(6, 0))
        return card

    def _append_price(self, spot: float) -> None:
        self.price_history.append(spot)
        self.time_history.append(datetime.now().strftime("%H:%M:%S"))

    def _refresh_chart(self) -> None:
        self.ax.clear()
        self.ax.set_facecolor("#ffffff")
        self.ax.grid(True, alpha=0.18)
        prices = list(self.price_history)
        labels = list(self.time_history)
        if prices:
            x = list(range(len(prices)))
            self.ax.plot(x, prices, color="#1769aa", linewidth=2.0)
            self.ax.scatter([x[-1]], [prices[-1]], color="#d9485f", s=45, zorder=3)
            self.ax.annotate(f"{prices[-1]:.2f}", (x[-1], prices[-1]), xytext=(8, 8), textcoords="offset points", fontsize=9, color="#d9485f")
            step = max(1, len(labels) // 6)
            ticks = list(range(0, len(labels), step))
            self.ax.set_xticks(ticks)
            self.ax.set_xticklabels([labels[i] for i in ticks], rotation=0, fontsize=8)
        if self.engine.range_high is not None:
            self.ax.axhline(self.engine.range_high, color="#2e7d32", linestyle="--", linewidth=1.5)
            self.ax.text(0.01, self.engine.range_high, f" High {self.engine.range_high:.2f}", color="#2e7d32", transform=self.ax.get_yaxis_transform(), va="bottom")
        if self.engine.range_low is not None:
            self.ax.axhline(self.engine.range_low, color="#ef6c00", linestyle="--", linewidth=1.5)
            self.ax.text(0.01, self.engine.range_low, f" Low {self.engine.range_low:.2f}", color="#ef6c00", transform=self.ax.get_yaxis_transform(), va="top")
        self.ax.set_title("Spot vs ORB")
        self.ax.set_ylabel("Price")
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def push_status(self, msg: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(msg)
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self._refresh_table()
        self._refresh_metrics()
        self._refresh_chart()

    def connect_api(self) -> None:
        ok, msg = self.client.connect(self.token_var.get())
        if ok:
            self.push_status("Connected")
        else:
            messagebox.showerror("Error", msg)

    def set_range(self) -> None:
        try:
            high = float(self.range_high_var.get())
            low = float(self.range_low_var.get())
        except ValueError:
            messagebox.showerror("Invalid", "Use numeric high and low.")
            return
        if low >= high:
            messagebox.showerror("Invalid", "Low must be below high.")
            return
        self.engine.set_opening_range(high, low)
        self._refresh_metrics()
        self._refresh_chart()

    def auto_set_range(self) -> None:
        self.engine.auto_set_opening_range(date.today())
        self.range_high_var.set(f"{self.engine.range_high:.2f}")
        self.range_low_var.set(f"{self.engine.range_low:.2f}")
        self.push_status("ORB ready")

    def start_strategy(self) -> None:
        if not self.client.connected:
            messagebox.showwarning("Connect", "Click Connect first.")
            return
        if ENABLE_AUTO_ORB and self.engine.range_high is None:
            self.auto_set_range()
        self.running = True
        self.push_status("Running")
        self.after(500, self.poll_market)

    def stop_strategy(self) -> None:
        self.running = False
        self.push_status("Stopped")

    def poll_market(self) -> None:
        if not self.running:
            return
        try:
            spot = self.client.get_index_ltp()
            now = datetime.now()
            self.index_var.set(f"{spot:.2f}")
            self._append_price(spot)
            self.engine.on_tick(now, spot)
            self._refresh_table()
            self._refresh_metrics()
            self._refresh_chart()
        except Exception as exc:
            self.push_status(f"Error: {exc}")
        self.after(POLL_INTERVAL_MS, self.poll_market)

    def _refresh_metrics(self) -> None:
        totals = self.engine.totals()
        self.realized_var.set(f"₹ {totals['realized']:.2f}")
        self.mtm_var.set(f"₹ {totals['mtm']:.2f}")
        self.open_count_var.set(str(totals['open_count']))
        rh, rl = totals.get("range_high"), totals.get("range_low")
        self.orb_var.set("Not set" if rh is None or rl is None else f"{rh:.2f} / {rl:.2f}")

    def _refresh_table(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in self.engine.get_rows():
            vals = tuple(row[k] for k in ("portfolio", "side", "entry", "ltp", "qty", "mtm", "realized", "capital", "status"))
            self.tree.insert("", "end", values=vals)


if __name__ == "__main__":
    app = PaperTradingApp()
    app.mainloop()
