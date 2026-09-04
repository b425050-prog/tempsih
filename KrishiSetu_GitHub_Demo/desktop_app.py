"""High-DPI native desktop interface for the KrishiSetu Model-1 prototype."""

from __future__ import annotations

import ctypes
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from offline_database import (
    database_counts,
    get_calibration_samples,
    get_coefficients,
    get_preset,
    initialize_database,
    recent_runs,
    save_run,
    table_rows,
)
from model_1_implementation import (
    ModelInput,
    Prediction,
    calibrate_coefficients,
    evaluate_calibration,
    predict_fair_price,
)


COLORS = {
    "ink": "#17231c",
    "muted": "#6f7b72",
    "green": "#1d432f",
    "green_2": "#2f6347",
    "green_soft": "#e7eee3",
    "lime": "#dff172",
    "cream": "#f5f3eb",
    "paper": "#fffefb",
    "line": "#dfe2d7",
    "white": "#ffffff",
}


def money(value: float) -> str:
    return f"₹{value:,.0f}"


def enable_high_dpi() -> None:
    """Request crisp per-monitor rendering before Tk creates a window."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base.joinpath(*parts)


def compute_ui_scale(screen_width: int, screen_height: int) -> float:
    """Scale a 1920x1080 reference layout up to native 8K dimensions."""
    return max(
        1.0,
        min(4.0, min(screen_width / 1920.0, screen_height / 1080.0)),
    )


class ScrollFrame(tk.Frame):
    def __init__(self, master: tk.Misc, background: str):
        super().__init__(master, bg=background)
        self.canvas = tk.Canvas(self, bg=background, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas, bg=background)
        self.window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.body.bind(
            "<Configure>",
            lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(self.window, width=event.width),
        )
        self.canvas.bind_all("<MouseWheel>", self._wheel)

    def _wheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")


class KrishiSetuApp(tk.Tk):
    def __init__(self) -> None:
        enable_high_dpi()
        super().__init__()
        initialize_database()
        self.coefficients = get_coefficients()
        self.preset = get_preset()
        self.calibration_samples = get_calibration_samples()
        self.recovered_coefficients = calibrate_coefficients(self.calibration_samples)
        self.calibration_report = evaluate_calibration(
            self.calibration_samples, self.coefficients
        )
        self.latest_result = predict_fair_price(self.preset, self.coefficients)
        self._configure_window()
        self._configure_styles()
        self._build_shell()
        self.show_decision_desk()

    def _configure_window(self) -> None:
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.ui_scale = compute_ui_scale(screen_width, screen_height)
        self.tk.call("tk", "scaling", (96.0 / 72.0) * self.ui_scale)
        self.title("KrishiSetu — Fair Mandi Price")
        self.geometry(f"{self.px(1440)}x{self.px(900)}")
        self.minsize(self.px(1120), self.px(720))
        self.configure(bg=COLORS["cream"])
        self._load_window_icon()
        try:
            self.state("zoomed")
        except tk.TclError:
            pass

    def px(self, value: float) -> int:
        return max(1, round(value * self.ui_scale))

    def _load_window_icon(self) -> None:
        source = tk.PhotoImage(file=str(resource_path("assets", "farmer-emblem.png")))
        factor = max(1, round(source.width() / self.px(96)))
        self.window_icon = source.subsample(factor, factor)
        self.iconphoto(True, self.window_icon)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Input.TEntry",
            fieldbackground=COLORS["paper"],
            foreground=COLORS["ink"],
            padding=self.px(9),
            relief="flat",
            bordercolor=COLORS["line"],
            lightcolor=COLORS["line"],
            darkcolor=COLORS["line"],
        )
        style.configure(
            "Input.TCombobox",
            fieldbackground=COLORS["paper"],
            background=COLORS["paper"],
            foreground=COLORS["ink"],
            padding=self.px(8),
            arrowsize=self.px(14),
        )
        style.map("Input.TCombobox", fieldbackground=[("readonly", COLORS["paper"])])
        style.configure(
            "Data.Treeview",
            background=COLORS["paper"],
            fieldbackground=COLORS["paper"],
            foreground=COLORS["ink"],
            rowheight=self.px(32),
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Data.Treeview.Heading",
            background=COLORS["green_soft"],
            foreground=COLORS["green"],
            relief="flat",
            font=("Segoe UI Semibold", 9),
        )

    def _build_shell(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = tk.Frame(self, bg=COLORS["green"], width=self.px(230))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.content = tk.Frame(self, bg=COLORS["cream"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self._build_sidebar()

    def _build_sidebar(self) -> None:
        brand = tk.Frame(self.sidebar, bg=COLORS["green"])
        brand.pack(fill="x", padx=self.px(18), pady=(self.px(20), self.px(34)))
        logo_source = tk.PhotoImage(file=str(resource_path("assets", "farmer-emblem.png")))
        factor = max(1, round(logo_source.width() / self.px(52)))
        self.sidebar_logo = logo_source.subsample(factor, factor)
        logo = tk.Label(brand, image=self.sidebar_logo, bg=COLORS["green"], bd=0)
        logo.pack(side="left", padx=(0, self.px(11)))
        words = tk.Frame(brand, bg=COLORS["green"])
        words.pack(side="left", fill="x")
        tk.Label(
            words,
            text="KrishiSetu",
            bg=COLORS["green"],
            fg=COLORS["white"],
            font=("Segoe UI Semibold", 14),
        ).pack(anchor="w")
        tk.Label(
            words,
            text="DECISION INTELLIGENCE",
            bg=COLORS["green"],
            fg="#a9c1b3",
            font=("Segoe UI", 7, "bold"),
        ).pack(anchor="w")

        self.nav_buttons: dict[str, tk.Button] = {}
        nav = [
            ("Decision desk", "⌁", self.show_decision_desk),
            ("Markets & routes", "⌖", self.available_soon),
            ("My lots", "▦", self.available_soon),
            ("FPO matching", "◇", self.available_soon),
            ("Transactions", "▤", self.available_soon),
            ("Model lab", "△", self.show_model_details),
            ("Data console", "▱", self.show_data_console),
        ]
        for label, symbol, command in nav:
            button = tk.Button(
                self.sidebar,
                text=f"  {symbol}   {label}",
                command=command,
                anchor="w",
                bg=COLORS["green"],
                fg="#dbe7df",
                activebackground="#365d48",
                activeforeground=COLORS["white"],
                bd=0,
                relief="flat",
                font=("Segoe UI", 10),
                padx=self.px(15),
                pady=self.px(12),
                cursor="hand2",
            )
            button.pack(fill="x", padx=self.px(12), pady=self.px(2))
            self.nav_buttons[label] = button

        status = tk.Frame(self.sidebar, bg=COLORS["green"])
        status.pack(side="bottom", fill="x", padx=self.px(18), pady=self.px(24))
        tk.Frame(status, height=self.px(1), bg="#3d614f").pack(
            fill="x", pady=(0, self.px(16))
        )
        tk.Label(
            status,
            text="●  MODEL 1 READY",
            bg=COLORS["green"],
            fg=COLORS["lime"],
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w")
        tk.Label(
            status,
            text="Local database · This device",
            bg=COLORS["green"],
            fg="#9fb7aa",
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(self.px(6), 0))

    def _set_active_nav(self, name: str) -> None:
        for label, button in self.nav_buttons.items():
            if label == name:
                button.configure(bg="#3b634d", fg=COLORS["white"])
            else:
                button.configure(bg=COLORS["green"], fg="#dbe7df")

    def _clear_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

    def _primary_button(self, parent: tk.Misc, text: str, command) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=COLORS["green_2"],
            fg=COLORS["white"],
            activebackground=COLORS["green"],
            activeforeground=COLORS["white"],
            bd=0,
            padx=self.px(18),
            pady=self.px(11),
            font=("Segoe UI Semibold", 10),
            cursor="hand2",
        )

    def _secondary_button(self, parent: tk.Misc, text: str, command) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            activebackground=COLORS["green_soft"],
            bd=1,
            relief="solid",
            highlightbackground=COLORS["line"],
            padx=self.px(15),
            pady=self.px(10),
            font=("Segoe UI Semibold", 9),
            cursor="hand2",
        )

    def _card(self, parent: tk.Misc, bg: str | None = None) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=bg or COLORS["paper"],
            highlightbackground=COLORS["line"],
            highlightthickness=1,
            bd=0,
        )

    def available_soon(self) -> None:
        messagebox.showinfo(
            "Available soon",
            "This feature will be available soon.\n\nThe current prototype includes only the Model-1 fair mandi price predictor and its local data console.",
            parent=self,
        )

    def show_decision_desk(self) -> None:
        self._set_active_nav("Decision desk")
        self._clear_content()
        scroll = ScrollFrame(self.content, COLORS["cream"])
        scroll.pack(fill="both", expand=True)
        body = scroll.body
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=self.px(295))
        body.configure(padx=self.px(42), pady=self.px(28))

        self._build_header(body)
        self._build_signal_strip(body)
        self._build_result_cards(body)
        self._build_inputs(body)
        self._build_calculation_panel(body)
        self._build_history(body)
        self._build_access_cards(body)
        tk.Label(
            body,
            text="Illustrative handbook values · Local prototype · Confirm market data before field use",
            bg=COLORS["cream"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).grid(
            row=7,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, self.px(28)),
        )

    def _build_header(self, parent: tk.Frame) -> None:
        header = tk.Frame(parent, bg=COLORS["cream"])
        header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, self.px(20)),
        )
        header.grid_columnconfigure(0, weight=1)
        left = tk.Frame(header, bg=COLORS["cream"])
        left.grid(row=0, column=0, sticky="w")
        tk.Label(
            left,
            text="GOOD MORNING, VISITOR",
            bg=COLORS["cream"],
            fg=COLORS["muted"],
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w")
        tk.Label(
            left,
            text="Turn today’s harvest into a fair price.",
            bg=COLORS["cream"],
            fg=COLORS["ink"],
            font=("Georgia", 27),
        ).pack(anchor="w", pady=(self.px(6), 0))
        actions = tk.Frame(header, bg=COLORS["cream"])
        actions.grid(row=0, column=1, sticky="e")
        self._secondary_button(actions, "Local data", self.show_data_console).pack(
            side="left", padx=self.px(5)
        )

    def _build_signal_strip(self, parent: tk.Frame) -> None:
        strip = tk.Frame(
            parent, bg="#ebeae2", padx=self.px(14), pady=self.px(11)
        )
        strip.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, self.px(14)),
        )
        labels = [
            ("CROP", "Tomato"),
            ("YESTERDAY", "₹2,200/q"),
            ("ARRIVALS", "500 q"),
            ("CALIBRATION", "15 local rows"),
            ("DATA", "Stored locally"),
        ]
        for index, (label, value) in enumerate(labels):
            cell = tk.Frame(strip, bg="#ebeae2")
            cell.pack(
                side="left",
                padx=(0 if index == 0 else self.px(22), self.px(18)),
            )
            tk.Label(cell, text=label, bg="#ebeae2", fg="#849086", font=("Segoe UI", 7, "bold")).pack(side="left")
            tk.Label(cell, text=f"  {value}", bg="#ebeae2", fg=COLORS["green"], font=("Segoe UI Semibold", 9)).pack(side="left")

    def _build_result_cards(self, parent: tk.Frame) -> None:
        card = self._card(parent)
        card.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=(0, self.px(12)),
            pady=(0, self.px(14)),
        )
        card.configure(padx=self.px(26), pady=self.px(24))
        top = tk.Frame(card, bg=COLORS["paper"])
        top.pack(fill="x")
        tk.Label(
            top,
            text="FAIR PRICE BASELINE",
            bg=COLORS["lime"],
            fg=COLORS["green"],
            padx=self.px(11),
            pady=self.px(5),
            font=("Segoe UI Semibold", 8),
        ).pack(side="left")
        tk.Label(
            top,
            text="Model-1 · deterministic calculation",
            bg=COLORS["paper"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(side="right")
        tk.Label(
            card,
            text="Today’s predicted fair mandi price for Tomato",
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            font=("Georgia", 20),
        ).pack(anchor="w", pady=(self.px(16), self.px(4)))
        tk.Label(
            card,
            text="A transparent baseline before the farmer enters any negotiation.",
            bg=COLORS["paper"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w")
        metrics = tk.Frame(card, bg="#f6f6f0", highlightbackground=COLORS["line"], highlightthickness=1)
        metrics.pack(fill="x", pady=(self.px(20), self.px(14)))
        metrics.grid_columnconfigure((0, 1, 2), weight=1)
        self.price_value = self._metric(metrics, 0, "PREDICTED FAIR PRICE", money(self.latest_result.fair_price) + "/q")
        self.previous_value = self._metric(metrics, 1, "YESTERDAY’S PRICE", money(self.preset.previous_price) + "/q")
        self.change_value = self._metric(metrics, 2, "MODEL CHANGE", self._change_text(self.latest_result, self.preset.previous_price))
        tags = tk.Frame(card, bg=COLORS["paper"])
        tags.pack(fill="x", pady=(0, self.px(12)))
        for text in ["✓ Formula visible", "✓ Runs offline", "✓ Saved on this device"]:
            tk.Label(
                tags,
                text=text,
                bg="#edf3ee",
                fg=COLORS["green_2"],
                padx=self.px(9),
                pady=self.px(5),
                font=("Segoe UI", 8),
            ).pack(side="left", padx=(0, self.px(7)))
        buttons = tk.Frame(card, bg=COLORS["paper"])
        buttons.pack(fill="x")
        self._primary_button(buttons, "Run handbook example", self.run_model).pack(side="left")
        self._secondary_button(buttons, "Show full reasoning", self.show_reasoning).pack(
            side="left", padx=self.px(9)
        )

        side = self._card(parent, COLORS["green"])
        side.grid(row=2, column=1, sticky="nsew", pady=(0, self.px(14)))
        side.configure(
            padx=self.px(24),
            pady=self.px(24),
            highlightbackground=COLORS["green"],
        )
        tk.Label(side, text="MODEL 1", bg=COLORS["green"], fg="#b9ccb9", font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(side, text="₹/q", bg=COLORS["green"], fg=COLORS["white"], font=("Georgia", 30)).pack(
            anchor="w", pady=(self.px(12), self.px(8))
        )
        tk.Label(side, text="Fair mandi price", bg=COLORS["green"], fg=COLORS["white"], font=("Segoe UI Semibold", 11)).pack(anchor="w")
        tk.Label(
            side,
            text="Uses yesterday’s price, today’s arrivals and a weather shock index. Verified against 15 local calibration rows.",
            bg=COLORS["green"],
            fg="#c5d4ca",
            justify="left",
            wraplength=self.px(240),
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(self.px(7), self.px(20)))
        bars = tk.Frame(side, bg=COLORS["green"])
        bars.pack(fill="x", pady=self.px(8))
        for index, height in enumerate([22, 48, 31, 18]):
            tk.Frame(
                bars,
                bg=COLORS["lime"] if index == 1 else "#607c69",
                width=self.px(48),
                height=self.px(height),
            ).pack(side="left", padx=(0, self.px(7)), anchor="s")
        tk.Label(side, text="NO NETWORK REQUIRED", bg=COLORS["green"], fg=COLORS["lime"], font=("Segoe UI Semibold", 8)).pack(side="bottom", anchor="w")

    def _metric(self, parent: tk.Frame, column: int, label: str, value: str) -> tk.Label:
        frame = tk.Frame(
            parent, bg="#f6f6f0", padx=self.px(16), pady=self.px(14)
        )
        frame.grid(row=0, column=column, sticky="nsew")
        if column:
            tk.Frame(frame, bg=COLORS["line"], width=self.px(1)).pack(
                side="left", fill="y", padx=(0, self.px(14))
            )
        content = tk.Frame(frame, bg="#f6f6f0")
        content.pack(side="left", fill="both", expand=True)
        tk.Label(content, text=label, bg="#f6f6f0", fg="#889189", font=("Segoe UI", 7)).pack(anchor="w")
        output = tk.Label(content, text=value, bg="#f6f6f0", fg=COLORS["ink"], font=("Segoe UI Semibold", 14))
        output.pack(anchor="w", pady=(self.px(6), 0))
        return output

    @staticmethod
    def _change_text(result: Prediction, previous: float) -> str:
        change = result.fair_price - previous
        return f"{change:+,.0f}/q"

    def _build_inputs(self, parent: tk.Frame) -> None:
        panel = tk.Frame(
            parent,
            bg=COLORS["green_soft"],
            padx=self.px(20),
            pady=self.px(16),
        )
        panel.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, self.px(14)),
        )
        tk.Label(
            panel,
            text="MODEL-1 INPUTS",
            bg=COLORS["green_soft"],
            fg=COLORS["green"],
            font=("Segoe UI Semibold", 8),
        ).grid(
            row=0,
            column=0,
            columnspan=5,
            sticky="w",
            pady=(0, self.px(9)),
        )
        for column in range(4):
            panel.grid_columnconfigure(column, weight=1)

        self.crop_var = tk.StringVar(value=self.preset.crop)
        self.market_var = tk.StringVar(value=self.preset.market)
        self.previous_var = tk.StringVar(value=f"{self.preset.previous_price:.0f}")
        self.arrivals_var = tk.StringVar(value=f"{self.preset.arrival_quantity:.0f}")
        self.weather_var = tk.StringVar(value=f"{self.preset.weather_index:.1f}")

        fields = [
            ("CROP", self.crop_var, "combo", ["Tomato"]),
            ("MARKET", self.market_var, "combo", ["Pune APMC"]),
            ("YESTERDAY’S PRICE (₹/Q)", self.previous_var, "entry", None),
            ("TODAY’S ARRIVALS (Q)", self.arrivals_var, "entry", None),
            ("WEATHER SHOCK INDEX", self.weather_var, "entry", None),
        ]
        for column, (label, variable, kind, values) in enumerate(fields):
            holder = tk.Frame(panel, bg=COLORS["green_soft"])
            holder.grid(
                row=1,
                column=column,
                sticky="ew",
                padx=(0, self.px(10)),
            )
            tk.Label(
                holder,
                text=label,
                bg=COLORS["green_soft"],
                fg=COLORS["muted"],
                font=("Segoe UI Semibold", 7),
            ).pack(anchor="w", pady=(0, self.px(5)))
            if kind == "combo":
                widget = ttk.Combobox(holder, textvariable=variable, values=values, state="readonly", style="Input.TCombobox")
            else:
                widget = ttk.Entry(holder, textvariable=variable, style="Input.TEntry")
            widget.pack(fill="x")
        panel.grid_columnconfigure(4, weight=1)
        self._primary_button(panel, "⌁  Run offline model", self.run_model).grid(
            row=1,
            column=5,
            sticky="sew",
            padx=(self.px(8), 0),
        )

    def _build_calculation_panel(self, parent: tk.Frame) -> None:
        panel = self._card(parent)
        panel.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, self.px(14)),
        )
        panel.configure(padx=self.px(24), pady=self.px(20))
        text = tk.Frame(panel, bg=COLORS["paper"])
        text.pack(anchor="w")
        tk.Label(text, text="TRANSPARENT CALCULATION", bg=COLORS["paper"], fg=COLORS["green_2"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(text, text="Every rupee in the baseline is visible", bg=COLORS["paper"], fg=COLORS["ink"], font=("Georgia", 17)).pack(anchor="w", pady=(self.px(4), 0))
        self.formula_value = tk.Label(
            panel,
            text="Pₜ = α₀ + α₁Pₜ₋₁ − γ ln(Aₜ) + βWₜ",
            bg=COLORS["paper"],
            fg=COLORS["green"],
            font=("Cambria Math", 17),
        )
        self.formula_value.pack(anchor="center", pady=(self.px(16), self.px(4)))
        self.term_frame = tk.Frame(panel, bg=COLORS["paper"])
        self.term_frame.pack(fill="x", pady=(self.px(12), self.px(4)))
        self._render_terms(self.latest_result)

    def _render_terms(self, result: Prediction) -> None:
        for child in self.term_frame.winfo_children():
            child.destroy()
        terms = [
            ("INTERCEPT", result.intercept_term),
            ("PRICE MEMORY", result.previous_price_term),
            ("ARRIVAL EFFECT", result.arrival_term),
            ("WEATHER EFFECT", result.weather_term),
            ("FAIR PRICE", result.fair_price),
        ]
        for column, (label, value) in enumerate(terms):
            self.term_frame.grid_columnconfigure(column, weight=1)
            block = tk.Frame(
                self.term_frame,
                bg="#f6f7f1",
                padx=self.px(13),
                pady=self.px(12),
            )
            block.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else self.px(5), 0),
            )
            tk.Label(block, text=label, bg="#f6f7f1", fg=COLORS["muted"], font=("Segoe UI", 7)).pack(anchor="w")
            prefix = "+" if value >= 0 and column not in (0, 4) else ""
            tk.Label(block, text=f"{prefix}{value:,.2f}", bg="#f6f7f1", fg=COLORS["green"] if column == 4 else COLORS["ink"], font=("Segoe UI Semibold", 11)).pack(anchor="w", pady=(self.px(5), 0))

    def _build_history(self, parent: tk.Frame) -> None:
        panel = self._card(parent)
        panel.grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, self.px(14)),
        )
        panel.configure(padx=self.px(22), pady=self.px(18))
        head = tk.Frame(panel, bg=COLORS["paper"])
        head.pack(fill="x", pady=(0, self.px(10)))
        tk.Label(head, text="RECENT LOCAL RUNS", bg=COLORS["paper"], fg=COLORS["green_2"], font=("Segoe UI Semibold", 8)).pack(side="left")
        self.run_count_label = tk.Label(head, text="Stored in SQLite", bg=COLORS["paper"], fg=COLORS["muted"], font=("Segoe UI", 8))
        self.run_count_label.pack(side="right")
        self.history_frame = tk.Frame(panel, bg=COLORS["paper"])
        self.history_frame.pack(fill="x")
        self._refresh_history()

    def _refresh_history(self) -> None:
        for child in self.history_frame.winfo_children():
            child.destroy()
        runs = recent_runs(4)
        self.run_count_label.configure(text=f"{len(runs)} most recent · Stored in SQLite")
        if not runs:
            tk.Label(
                self.history_frame,
                text="Run Model-1 to create the first local record.",
                bg=COLORS["paper"],
                fg=COLORS["muted"],
                font=("Segoe UI", 9),
            ).pack(anchor="w", pady=self.px(8))
            return
        for row in runs:
            line = tk.Frame(
                self.history_frame, bg=COLORS["paper"], pady=self.px(8)
            )
            line.pack(fill="x")
            tk.Label(line, text=f"#{row['id']:02d}", bg=COLORS["paper"], fg="#98a299", width=5, anchor="w", font=("Segoe UI", 8)).pack(side="left")
            tk.Label(line, text=row["crop"], bg=COLORS["paper"], fg=COLORS["ink"], width=15, anchor="w", font=("Segoe UI Semibold", 9)).pack(side="left")
            tk.Label(line, text=f"{row['arrival_quantity']:,.0f} q arrivals", bg=COLORS["paper"], fg=COLORS["muted"], width=20, anchor="w", font=("Segoe UI", 9)).pack(side="left")
            tk.Label(line, text=money(row["predicted_price"]) + "/q", bg=COLORS["paper"], fg=COLORS["green"], font=("Segoe UI Semibold", 10)).pack(side="left")
            tk.Label(line, text=row["created_at"].replace("T", "  "), bg=COLORS["paper"], fg="#98a299", font=("Segoe UI", 8)).pack(side="right")
            tk.Frame(self.history_frame, bg="#eceee7", height=self.px(1)).pack(
                fill="x"
            )

    def _build_access_cards(self, parent: tk.Frame) -> None:
        wrap = tk.Frame(parent, bg=COLORS["cream"])
        wrap.grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, self.px(14)),
        )
        for column in range(3):
            wrap.grid_columnconfigure(column, weight=1)
        cards = [
            ("△", "Model access", "Model-1 inputs, coefficients and term-by-term output are visible."),
            ("▱", "Database access", "Fifteen calibration records and every run stay in a local SQLite file."),
            ("▣", "Offline desktop", "The interface and calculation run entirely on this computer."),
        ]
        for column, (icon, title, description) in enumerate(cards):
            card = tk.Frame(
                wrap,
                bg=COLORS["green_soft"],
                padx=self.px(18),
                pady=self.px(16),
            )
            card.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else self.px(7), 0),
            )
            tk.Label(card, text=icon, bg=COLORS["green_soft"], fg=COLORS["green_2"], font=("Segoe UI", 17)).pack(anchor="w")
            tk.Label(card, text=title, bg=COLORS["green_soft"], fg=COLORS["ink"], font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(self.px(7), self.px(4)))
            tk.Label(card, text=description, bg=COLORS["green_soft"], fg=COLORS["muted"], wraplength=self.px(310), justify="left", font=("Segoe UI", 8)).pack(anchor="w")

    def run_model(self) -> None:
        try:
            values = ModelInput(
                crop=self.crop_var.get(),
                market=self.market_var.get(),
                previous_price=float(self.previous_var.get().replace(",", "")),
                arrival_quantity=float(self.arrivals_var.get().replace(",", "")),
                weather_index=float(self.weather_var.get()),
            )
            result = predict_fair_price(values, self.coefficients)
        except ValueError as exc:
            messagebox.showerror("Check the inputs", str(exc), parent=self)
            return
        self.latest_result = result
        self.price_value.configure(text=money(result.fair_price) + "/q")
        self.previous_value.configure(text=money(values.previous_price) + "/q")
        self.change_value.configure(text=self._change_text(result, values.previous_price))
        self._render_terms(result)
        save_run(values, result)
        self._refresh_history()
        messagebox.showinfo(
            "Model-1 completed",
            f"Predicted fair mandi price: {money(result.fair_price)} per quintal\n\nThe calculation was completed offline and saved to the local database.",
            parent=self,
        )

    def show_reasoning(self) -> None:
        result = self.latest_result
        coeff = self.coefficients
        messagebox.showinfo(
            "Model-1 calculation",
            (
                "Pₜ = α₀ + α₁Pₜ₋₁ − γ ln(Aₜ) + βWₜ\n\n"
                f"= {coeff.intercept:.0f} + ({coeff.autoregressive_weight:.2f} × {float(self.previous_var.get().replace(',', '')):,.0f}) "
                f"− ({coeff.arrival_elasticity:.0f} × {result.log_arrivals:.4f}) "
                f"+ ({coeff.weather_weight:.0f} × {float(self.weather_var.get()):.1f})\n\n"
                f"= {result.fair_price:,.2f}\n\n"
                f"Rounded fair price: {money(result.fair_price)} per quintal"
            ),
            parent=self,
        )

    def show_model_details(self) -> None:
        self._set_active_nav("Model lab")
        coeff = self.coefficients
        recovered = self.recovered_coefficients
        report = self.calibration_report
        messagebox.showinfo(
            "Model-1 details",
            (
                "Autoregressive Fair Mandi Price Predictor\n\n"
                "Pₜ = α₀ + α₁Pₜ₋₁ − γ ln(Aₜ) + βWₜ\n\n"
                f"α₀ = {coeff.intercept:.0f}\n"
                f"α₁ = {coeff.autoregressive_weight:.2f}\n"
                f"γ = {coeff.arrival_elasticity:.0f}\n"
                f"β = {coeff.weather_weight:.0f}\n\n"
                f"Calibration rows = {report.record_count}\n"
                f"Recovered α₀ = {recovered.intercept:.6f}\n"
                f"Recovered α₁ = {recovered.autoregressive_weight:.6f}\n"
                f"Recovered γ = {recovered.arrival_elasticity:.6f}\n"
                f"Recovered β = {recovered.weather_weight:.6f}\n"
                f"Formula-check RMSE = {report.root_mean_squared_error:.10f}\n"
                f"Formula-check R² = {report.r_squared:.10f}\n\n"
                "The 15 records are synthetic coefficient-recovery checks, not a field-accuracy claim.\n\n"
                "Only Model-1 is active in this prototype."
            ),
            parent=self,
        )
        self._set_active_nav("Decision desk")

    def show_data_console(self) -> None:
        self._set_active_nav("Data console")
        self._clear_content()
        page = tk.Frame(
            self.content,
            bg=COLORS["cream"],
            padx=self.px(42),
            pady=self.px(30),
        )
        page.pack(fill="both", expand=True)
        heading = tk.Frame(page, bg=COLORS["cream"])
        heading.pack(fill="x", pady=(0, self.px(20)))
        title = tk.Frame(heading, bg=COLORS["cream"])
        title.pack(side="left")
        tk.Label(title, text="PRIVATE · LOCAL · OFFLINE", bg=COLORS["cream"], fg=COLORS["green_2"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(title, text="Data console", bg=COLORS["cream"], fg=COLORS["ink"], font=("Georgia", 27)).pack(anchor="w", pady=(self.px(5), self.px(3)))
        tk.Label(
            title,
            text="data\\krishisetu.db · stored beside this application",
            bg=COLORS["cream"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="w")
        self._primary_button(heading, "Back to decision desk", self.show_decision_desk).pack(side="right", anchor="n")

        counts = database_counts()
        count_bar = tk.Frame(
            page,
            bg=COLORS["green_soft"],
            padx=self.px(17),
            pady=self.px(13),
        )
        count_bar.pack(fill="x", pady=(0, self.px(16)))
        for table, count in counts.items():
            tk.Label(count_bar, text=f"{table.replace('_', ' ').title()}  {count}", bg=COLORS["green_soft"], fg=COLORS["green"], font=("Segoe UI Semibold", 8)).pack(side="left", padx=(0, self.px(22)))

        work = tk.Frame(page, bg=COLORS["cream"])
        work.pack(fill="both", expand=True)
        table_list = self._card(work)
        table_list.pack(side="left", fill="y", padx=(0, self.px(12)))
        table_list.configure(
            width=self.px(220), padx=self.px(10), pady=self.px(10)
        )
        table_list.pack_propagate(False)
        table_names = ["model_parameters", "calibration_observations", "model_presets", "model_runs", "buyers", "supplies", "demands", "app_metadata"]
        data_panel = self._card(work)
        data_panel.pack(side="left", fill="both", expand=True)
        data_panel.configure(padx=self.px(15), pady=self.px(15))
        self.data_title = tk.Label(data_panel, text="", bg=COLORS["paper"], fg=COLORS["ink"], font=("Segoe UI Semibold", 13))
        self.data_title.pack(anchor="w", pady=(0, self.px(12)))
        tree_wrap = tk.Frame(data_panel, bg=COLORS["paper"])
        tree_wrap.pack(fill="both", expand=True)
        self.data_tree = ttk.Treeview(tree_wrap, style="Data.Treeview", show="headings")
        yscroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.data_tree.yview)
        xscroll = ttk.Scrollbar(tree_wrap, orient="horizontal", command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.data_tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        tree_wrap.grid_rowconfigure(0, weight=1)
        tree_wrap.grid_columnconfigure(0, weight=1)
        for name in table_names:
            tk.Button(
                table_list,
                text=name.replace("_", " ").title(),
                command=lambda selected=name: self._load_table(selected),
                anchor="w",
                bg=COLORS["paper"],
                fg=COLORS["ink"],
                activebackground=COLORS["green_soft"],
                bd=0,
                padx=self.px(12),
                pady=self.px(11),
                font=("Segoe UI", 9),
                cursor="hand2",
            ).pack(fill="x", pady=self.px(2))
        self._load_table("model_parameters")

    def _load_table(self, name: str) -> None:
        columns, rows = table_rows(name)
        self.data_title.configure(text=f"{name.replace('_', ' ').title()} · {len(rows)} rows")
        self.data_tree.delete(*self.data_tree.get_children())
        self.data_tree.configure(columns=columns)
        for column in columns:
            self.data_tree.heading(column, text=column.replace("_", " ").title())
            self.data_tree.column(
                column,
                width=self.px(max(110, min(240, len(column) * 12))),
                anchor="w",
            )
        for row in rows:
            self.data_tree.insert("", "end", values=row)

def main() -> None:
    app = KrishiSetuApp()
    app.mainloop()


if __name__ == "__main__":
    main()
