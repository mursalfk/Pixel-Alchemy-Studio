import tkinter as tk
from tkinter import ttk

from ui.preview import SideBySidePreview, SliderPreview


class PreviewPanel(ttk.Frame):
    """
    Center preview area (no horizontal scrollbar).
    Content is centered and contained by the preview widgets themselves.
    """
    def __init__(self, master):
        super().__init__(master, padding=8)
        self.app = self.winfo_toplevel()  # real app/root
        self.mode = tk.StringVar(value="side")

        # Bar
        top = ttk.Frame(self)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Preview:").pack(side=tk.LEFT)
        ttk.Radiobutton(top, text="Side-by-Side", value="side", variable=self.mode,
                        command=self.app.refresh).pack(side=tk.LEFT, padx=8)
        ttk.Radiobutton(top, text="Before/After Slider", value="slider", variable=self.mode,
                        command=self.app.refresh).pack(side=tk.LEFT)
        self._ctrl_btn = ttk.Button(top, text="Hide Controls", command=self.app.toggle_right_panel)
        self._ctrl_btn.pack(side=tk.RIGHT)

        # Plain container; widgets inside handle centering/scaling
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        self.side = SideBySidePreview(self.container)
        self.slider = SliderPreview(self.container)
        self.side.pack(fill=tk.BOTH, expand=True)

    def set_controls_visible(self, visible: bool):
        self._ctrl_btn.configure(text=("Hide Controls" if visible else "Show Controls"))

    def show_side(self, orig, proc):
        self.slider.pack_forget()
        self.side.pack(fill=tk.BOTH, expand=True)
        self.side.update_images(orig, proc)

    def show_slider(self, orig, proc):
        self.side.pack_forget()
        self.slider.pack(fill=tk.BOTH, expand=True)
        self.slider.update_images(orig, proc)