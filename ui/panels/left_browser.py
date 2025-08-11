import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from utils.image_io import list_images_in_folder


class LeftBrowserPanel(ttk.Frame):
    """Folder browser with thumbnail grid and modes (single/multi/folder)."""

    def __init__(self, master, on_choose_folder, on_mode_change, on_toggle_multi, on_click_thumb):
        super().__init__(master, padding=8)
        self.on_choose_folder = on_choose_folder
        self.on_mode_change = on_mode_change
        self.on_toggle_multi = on_toggle_multi
        self.on_click_thumb = on_click_thumb
        self._thumb_refs = {}  # keep PhotoImage refs alive
        self._build()

    def _build(self):
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Images").pack(side=tk.LEFT)
        ttk.Button(header, text="Open Folder...", command=self.on_choose_folder).pack(side=tk.RIGHT, padx=(8, 0))

        # Modes
        self.mode_var = tk.StringVar(value="single")
        modes = ttk.Labelframe(self, text="Mode", padding=6)
        modes.pack(fill=tk.X, pady=(8, 8))
        for text, val in (("Single", "single"), ("Multiple", "multi"), ("Folder", "folder")):
            ttk.Radiobutton(
                modes, text=text, value=val, variable=self.mode_var,
                command=lambda v=val: self.on_mode_change(v)
            ).pack(anchor="w")

        # Scrollable thumbnails
        self.canvas = tk.Canvas(self, width=300, height=690, highlightthickness=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.frame = ttk.Frame(self.canvas)
        self.win_id = self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.Y)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.win_id, width=e.width))

    def clear_multi_checks(self):
        for row in self.frame.winfo_children():
            for w in row.winfo_children():
                if isinstance(w, ttk.Checkbutton) and hasattr(w, "_var"):
                    w._var.set(False)

    def toggle_row_check(self, path: str):
        """Toggle the checkbox for a row matching the given file path."""
        base = os.path.basename(path)
        for row in self.frame.winfo_children():
            label_text = None
            var = None
            for w in row.winfo_children():
                if isinstance(w, ttk.Frame):
                    lbls = [c for c in w.winfo_children() if isinstance(c, ttk.Label)]
                    if lbls:
                        label_text = lbls[0].cget("text")
                if isinstance(w, ttk.Checkbutton) and hasattr(w, "_var"):
                    var = w._var
            if label_text == base and var is not None:
                var.set(not var.get())
                self.on_toggle_multi(path, var.get())
                return

    def populate_thumbs(self, folder):
        for w in self.frame.winfo_children():
            w.destroy()
        self._thumb_refs.clear()

        files = list_images_in_folder(folder)
        if not files:
            ttk.Label(self.frame, text="No images found").pack(anchor="w", padx=6, pady=6)
            return

        for path in files:
            try:
                pil = Image.open(path).convert("RGB")
                pil.thumbnail((240, 240))
                thumb = ImageTk.PhotoImage(pil)
                self._thumb_refs[path] = thumb

                row = ttk.Frame(self.frame, padding=4)
                row.pack(fill=tk.X, padx=2, pady=2)

                ttk.Button(row, image=thumb, command=lambda p=path: self.on_click_thumb(p)).pack(side=tk.LEFT)

                text_col = ttk.Frame(row)
                text_col.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)
                ttk.Label(text_col, text=os.path.basename(path)).pack(anchor="w")

                var = tk.BooleanVar(value=False)
                chk = ttk.Checkbutton(
                    row, text="Select", variable=var,
                    command=lambda p=path, v=var: self.on_toggle_multi(p, v.get())
                )
                chk._var = var  # keep a handle so we can reset later
                chk.pack(side=tk.RIGHT)
            except Exception:
                continue