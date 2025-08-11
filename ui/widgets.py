import tkinter as tk
from tkinter import ttk
import numpy as np

__all__ = ["LabeledSlider", "get_theme_colors"]


def get_theme_colors(root=None):
    """
    Read colors from the current ttk style, with sensible fallbacks.
    Returns (BG, FG, TROUGH).
    """
    style = ttk.Style(root) if root is not None else ttk.Style()
    bg = style.lookup("TFrame", "background") or "#FFFFFF"
    fg = style.lookup("TLabel", "foreground") or "#111111"
    trough = style.lookup("TScale", "troughcolor") or "#D9D9D9"
    return bg, fg, trough


class LabeledSlider(ttk.Frame):
    """
    Big, easy slider with +/- buttons and an entry for precise values.
    - Works with ttk themes (no parent["background"] lookups).
    - Mouse wheel support (Windows/macOS: <MouseWheel>, Linux: <Button-4/5>).
    - is_int=True -> integer stepping; otherwise floating (resolution).
    - 'command' is called on any change.
    """

    def __init__(
        self,
        master,
        label: str,
        from_: float,
        to: float,
        init: float,
        resolution: float = 0.01,
        is_int: bool = False,
        command=None,
        length: int = 260,
    ):
        super().__init__(master)
        self.command = command
        self.from_ = from_
        self.to = to
        self.resolution = max(resolution, 1 if is_int else resolution)
        self.is_int = is_int
        self.length = length

        BG, FG, TROUGH = get_theme_colors(self)

        ttk.Label(self, text=label).grid(row=0, column=0, sticky="w", padx=(0, 6))

        # tk.Scale for chunky handle; colors from current theme
        self.scale = tk.Scale(
            self,
            from_=from_,
            to=to,
            orient="horizontal",
            resolution=(1 if is_int else resolution),
            showvalue=0,
            length=self.length,
            highlightthickness=0,
            troughcolor=TROUGH,
            bg=BG,
            sliderlength=22,
            relief="flat",
            borderwidth=0,
        )
        self.scale.set(init)
        self.scale.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(2, 2))

        self.entry = ttk.Entry(self, width=7)
        self.entry.grid(row=1, column=3, padx=6)

        self.btn_minus = ttk.Button(self, text="-", width=2, command=lambda: self.bump(-1))
        self.btn_plus = ttk.Button(self, text="+", width=2, command=lambda: self.bump(+1))
        self.btn_minus.grid(row=1, column=4, padx=(0, 2))
        self.btn_plus.grid(row=1, column=5)

        self.entry.insert(0, self._fmt(init))

        self.scale.configure(command=self._on_scale)
        self.entry.bind("<Return>", self._on_entry)
        self.entry.bind("<FocusOut>", self._on_entry)

        self.scale.bind("<MouseWheel>", self._on_wheel)  # Windows/macOS
        self.scale.bind("<Button-4>", self._on_wheel)    # Linux up
        self.scale.bind("<Button-5>", self._on_wheel)    # Linux down

        self.columnconfigure(0, weight=1)

    def get(self):
        v = self.scale.get()
        return int(round(v)) if self.is_int else float(v)

    def set(self, value):
        value = self._clamp(value)
        self.scale.set(value)
        self._write_entry(value)

    def enable(self):
        self._set_state("normal")

    def disable(self):
        self._set_state("disabled")

    def _set_state(self, state):
        self.scale.configure(state=state)
        self.entry.configure(state=state)
        self.btn_minus.configure(state=state)
        self.btn_plus.configure(state=state)

    def bump(self, steps):
        step = (1 if self.is_int else self.resolution)
        self.set(self.get() + steps * step)
        if self.command:
            self.command(None)

    def _on_scale(self, _):
        val = self.get()
        self._write_entry(val)
        if self.command:
            self.command(None)

    def _on_entry(self, _):
        try:
            v = float(self.entry.get())
        except Exception:
            v = self.get()
        if self.is_int:
            v = int(round(v))
        self.set(v)
        if self.command:
            self.command(None)

    def _on_wheel(self, event):
        if hasattr(event, "delta") and event.delta != 0:
            delta = 1 if event.delta > 0 else -1
        else:
            delta = 1 if getattr(event, "num", 0) == 4 else -1
        self.bump(delta)

    def _clamp(self, v):
        v = max(self.from_, min(self.to, v))
        return int(round(v)) if self.is_int else float(v)

    def _fmt(self, v):
        return f"{int(round(v))}" if self.is_int else f"{round(float(v), 3)}"

    def _write_entry(self, v):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self._fmt(v))