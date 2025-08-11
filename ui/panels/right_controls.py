import tkinter as tk
from tkinter import ttk

from ui.widgets import LabeledSlider
from utils.presets import get_preset_names, get_preset, random_params
from processing.themes import THEME_NAMES


def _apply_values(slider, value):
    if slider is None:
        return
    slider.set(value)


class RightControls(ttk.Frame):
    """
    Fixed-width, scrollable right sidebar with theme/preset row,
    transform buttons, progress bar, and all processing sliders.
    """

    def __init__(self, master, on_open, on_save, on_batch, on_theme, on_params_changed):
        super().__init__(master, padding=0)
        self.on_params_changed = on_params_changed
        self.app = self.winfo_toplevel()  # access to .state, rotate/flip, .set_theme

        # Scrollable shell
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.vscroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas, padding=8)  # content goes here
        self.body_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")

        self.canvas.configure(yscrollcommand=self.vscroll.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.body_id, width=e.width))

        # Mouse-wheel support
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

        # Build controls
        self._build(on_open, on_save, on_batch, on_theme)

    # --- scroll wheel helpers ---
    def _on_mousewheel(self, event):
        if hasattr(event, "delta") and event.delta:
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        elif getattr(event, "num", None) in (4, 5):
            self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

    def _bind_mousewheel(self, _e):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _e):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    # ----- progress helpers (used by app/app.py & actions.py) -----
    def progress_start(self, text="Working..."):
        if hasattr(self, "status_var"):
            self.status_var.set(text)
        if hasattr(self, "prog"):
            self.prog.config(mode="indeterminate", value=0, maximum=100)
            self.prog.start(12)
        self.body.update_idletasks()

    def progress_stop(self, text=""):
        if hasattr(self, "prog"):
            try:
                self.prog.stop()
            except Exception:
                pass
            self.prog.config(mode="determinate", value=0)
        if hasattr(self, "status_var"):
            self.status_var.set(text)
        self.body.update_idletasks()

    def set_progress(self, current: int, total: int, text: str | None = None):
        total = max(1, int(total))
        current = min(max(0, int(current)), total)
        if hasattr(self, "prog"):
            self.prog.config(mode="determinate", maximum=total, value=current)
        if text is not None and hasattr(self, "status_var"):
            self.status_var.set(text)
        self.body.update_idletasks()

    # --- UI build ---
    def _build(self, on_open, on_save, on_batch, on_theme):
        # Top actions
        top = ttk.Frame(self.body)
        top.pack(fill=tk.X)
        ttk.Button(top, text="Open Image...", command=on_open).pack(side=tk.LEFT)
        ttk.Button(top, text="Save Result", command=on_save).pack(side=tk.LEFT, padx=6)
        ttk.Button(top, text="Process Batch...", command=on_batch).pack(side=tk.LEFT)
        self.dark_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Dark Mode", variable=self.dark_var, command=on_theme).pack(side=tk.RIGHT)

        # Theme selection
        theme_row = ttk.Frame(self.body)
        theme_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(theme_row, text="Theme (choose processing style):").grid(row=0, column=0, sticky="w")
        self.theme_var = tk.StringVar(value=self.app.state.current_theme)
        self.theme_box = ttk.Combobox(theme_row, textvariable=self.theme_var, state="readonly",
                                      values=THEME_NAMES, width=16)
        self.theme_box.grid(row=0, column=1, padx=6, sticky="w")
        self.theme_box.bind("<<ComboboxSelected>>", self._on_theme_change)
        theme_row.columnconfigure(2, weight=1)

        # Presets row (manual apply)
        self.preset_row = ttk.Frame(self.body)
        self.preset_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(self.preset_row, text="Preset (click Apply):").grid(row=0, column=0, sticky="w")
        self.preset_var = tk.StringVar(value="Default")
        self.preset_box = None
        self._make_preset_box()
        self.preset_box.bind("<FocusIn>", lambda e: self._refresh_preset_names())
        self.preset_box.bind("<Button-1>", lambda e: self._refresh_preset_names())

        ttk.Button(self.preset_row, text="Apply Preset", command=self.apply_selected_preset).grid(
            row=0, column=2, padx=(6, 0), sticky="w"
        )
        ttk.Button(self.preset_row, text="Random", command=self.apply_random_params).grid(
            row=0, column=3, padx=(6, 0), sticky="w"
        )
        self.preset_row.columnconfigure(1, weight=1)

        # Transform group
        xform = ttk.Labelframe(self.body, text="Transform", padding=8)
        xform.pack(fill=tk.X, pady=8)
        ttk.Button(xform, text="Rotate -90", command=self.app.rotate_left).grid(row=0, column=0, padx=4, pady=2, sticky="ew")
        ttk.Button(xform, text="Rotate +90", command=self.app.rotate_right).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ttk.Button(xform, text="Rotate 180", command=self.app.rotate_180).grid(row=0, column=2, padx=4, pady=2, sticky="ew")
        ttk.Button(xform, text="Flip H", command=self.app.flip_h).grid(row=1, column=0, padx=4, pady=2, sticky="ew")
        ttk.Button(xform, text="Flip V", command=self.app.flip_v).grid(row=1, column=1, padx=4, pady=2, sticky="ew")
        for c in (0, 1, 2):
            xform.columnconfigure(c, weight=1)

        # Progress bar (after Transform, before sliders)
        prog_row = ttk.Frame(self.body)
        prog_row.pack(fill=tk.X, pady=(2, 6))
        self.prog = ttk.Progressbar(prog_row, mode="determinate", maximum=100)
        self.prog.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_var = tk.StringVar(value="")
        ttk.Label(prog_row, textvariable=self.status_var, width=14, anchor="e").pack(side=tk.RIGHT, padx=(6, 0))

        # Slider groups
        def group(title: str):
            lf = ttk.Labelframe(self.body, text=title, padding=8)
            lf.pack(fill=tk.X, pady=8)
            return lf

        g1 = group("Color & Contrast")
        self.s_clahe = LabeledSlider(g1, "CLAHE Clip", 0.5, 4.0, 2.2, resolution=0.1, command=self.on_params_changed)
        self.s_contr = LabeledSlider(g1, "Contrast", 0.8, 1.8, 1.25, resolution=0.01, command=self.on_params_changed)
        self.s_sat = LabeledSlider(g1, "Saturation", 0.8, 2.0, 1.35, resolution=0.01, command=self.on_params_changed)
        self.s_vibr = LabeledSlider(g1, "Vibrance", 0.0, 1.5, 0.7, resolution=0.01, command=self.on_params_changed)
        for w in (self.s_clahe, self.s_contr, self.s_sat, self.s_vibr):
            w.pack(fill=tk.X, pady=4)

        g2 = group("Grade & Glow")
        self.s_tone = LabeledSlider(g2, "Tone Strength", 0.0, 0.8, 0.32, resolution=0.01, command=self.on_params_changed)
        self.s_glow = LabeledSlider(g2, "Glow", 0.0, 1.5, 0.85, resolution=0.01, command=self.on_params_changed)
        self.s_vign = LabeledSlider(g2, "Vignette", 0.0, 0.8, 0.35, resolution=0.01, command=self.on_params_changed)
        self.s_scan = LabeledSlider(g2, "Scanlines", 0.0, 0.2, 0.05, resolution=0.005, command=self.on_params_changed)
        for w in (self.s_tone, self.s_glow, self.s_vign, self.s_scan):
            w.pack(fill=tk.X, pady=4)

        g3 = group("Edges & Glitch")
        self.s_edgeS = LabeledSlider(g3, "Edge Strength", 0.0, 1.0, 0.35, resolution=0.01, command=self.on_params_changed)
        self.s_edgeL = LabeledSlider(g3, "Edge Low Th", 10, 200, 110, resolution=1, is_int=True, command=self.on_params_changed)
        self.s_edgeH = LabeledSlider(g3, "Edge High Th", 50, 300, 220, resolution=1, is_int=True, command=self.on_params_changed)
        self.s_soft = LabeledSlider(g3, "Edge Soften", 0.0, 3.0, 1.5, resolution=0.05, command=self.on_params_changed)
        for w in (self.s_edgeS, self.s_edgeL, self.s_edgeH, self.s_soft):
            w.pack(fill=tk.X, pady=4)

        self.g_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(g3, text="Tiny Glitch", variable=self.g_var, command=self.on_params_changed).pack(
            anchor="w", pady=(4, 0)
        )
        self.s_gn = LabeledSlider(g3, "Glitch Count", 0, 20, 6, resolution=1, is_int=True, command=self.on_params_changed)
        self.s_gs = LabeledSlider(g3, "Glitch Shift", 0, 40, 14, resolution=1, is_int=True, command=self.on_params_changed)
        self.s_gn.pack(fill=tk.X, pady=4)
        self.s_gs.pack(fill=tk.X, pady=4)

        # Reset row
        reset_row = ttk.Frame(self.body)
        reset_row.pack(fill=tk.X, pady=(6, 12))
        ttk.Button(reset_row, text="Reset Params", command=self.reset_params).pack(side=tk.LEFT)

    # --- preset combobox helpers ---
    def _make_preset_box(self):
        if getattr(self, "preset_box", None) is not None and self.preset_box.winfo_exists():
            self.preset_box.destroy()

        names = get_preset_names(self.app.state.current_theme)
        if not names:
            names = ["Default"]

        self.preset_box = ttk.Combobox(
            self.preset_row,
            textvariable=self.preset_var,
            state="readonly",
            values=names,
            width=20,
        )
        self.preset_box.grid(row=0, column=1, padx=6, sticky="ew")
        self.preset_row.columnconfigure(1, weight=1)

    def _refresh_preset_names(self):
        try:
            names = get_preset_names(self.app.state.current_theme)
            if not names:
                names = ["Default"]
            current = list(self.preset_box.cget("values"))
            if current != names:
                self.preset_box.configure(values=names)
                if self.preset_var.get() not in names:
                    self.preset_var.set("Default")
        except Exception:
            pass

    def _on_theme_change(self, _evt):
        theme = self.theme_var.get()
        self.app.set_theme(theme)

    # ----- presets / random / reset -----
    def reset_params(self):
        cfg = get_preset(self.app.state.current_theme, "Default")
        self._apply_preset_dict(cfg)
        self.on_params_changed()

    def apply_selected_preset(self):
        name = self.preset_var.get().strip()
        cfg = get_preset(self.app.state.current_theme, name)
        self._apply_preset_dict(cfg)
        self.on_params_changed()

    def apply_random_params(self):
        cfg = random_params(self.app.state.current_theme)
        self._apply_preset_dict(cfg)
        self.on_params_changed()

    def _apply_preset_dict(self, cfg: dict):
        _apply_values(self.s_clahe, cfg["clahe_clip"])
        _apply_values(self.s_contr, cfg["contrast"])
        _apply_values(self.s_sat, cfg["saturation"])
        _apply_values(self.s_vibr, cfg["vibr"])
        _apply_values(self.s_tone, cfg["tone_strength"])
        _apply_values(self.s_glow, cfg["glow"])
        _apply_values(self.s_edgeS, cfg["edge_strength"])
        _apply_values(self.s_edgeL, cfg["edge_low"])
        _apply_values(self.s_edgeH, cfg["edge_high"])
        _apply_values(self.s_soft, cfg["edge_soften"])
        _apply_values(self.s_vign, cfg["vignette_amt"])
        _apply_values(self.s_scan, cfg["scan_alpha"])
        self.g_var.set(bool(cfg["do_glitch"]))
        _apply_values(self.s_gn, cfg["glitch_n"])
        _apply_values(self.s_gs, cfg["glitch_shift"])

    def get_params(self):
        return dict(
            clahe_clip=self.s_clahe.get(),
            contrast=self.s_contr.get(),
            saturation=self.s_sat.get(),
            vibr=self.s_vibr.get(),
            tone_strength=self.s_tone.get(),
            glow=self.s_glow.get(),
            edge_strength=self.s_edgeS.get(),
            edge_low=int(self.s_edgeL.get()),
            edge_high=int(self.s_edgeH.get()),
            edge_soften=self.s_soft.get(),
            vignette_amt=self.s_vign.get(),
            scan_alpha=self.s_scan.get(),
            do_glitch=self.g_var.get(),
            glitch_n=int(self.s_gn.get()),
            glitch_shift=int(self.s_gs.get()),
        )

    # called by app when theme changes
    def reload_presets_for_theme(self):
        self.preset_var.set("Default")
        self._make_preset_box()
