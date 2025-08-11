# ui/preview.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from utils.image_io import bgr_to_pil


def _fit_contain_no_upscale(box_w, box_h, img_w, img_h):
    """Scale to fit inside the box while preserving aspect; never upscale."""
    if img_w <= 0 or img_h <= 0 or box_w <= 0 or box_h <= 0:
        return 1.0, 1, 1
    r = min(box_w / img_w, box_h / img_h)
    r = min(1.0, r)  # <- no upscaling
    tw = max(1, int(round(img_w * r)))
    th = max(1, int(round(img_h * r)))
    return r, tw, th


# ---------------- Side-by-Side ----------------
class SideBySidePreview(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.orig_bgr = None
        self.proc_bgr = None
        self._orig_imgtk = None
        self._proc_imgtk = None

        self.left = ttk.Label(self)
        self.right = ttk.Label(self)
        self.left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        self.bind("<Configure>", lambda e: self._redraw())

    def update_images(self, orig_bgr, proc_bgr):
        self.orig_bgr = orig_bgr
        self.proc_bgr = proc_bgr
        self._redraw()

    def _redraw(self):
        if self.orig_bgr is None or self.proc_bgr is None:
            return

        W = max(1, self.winfo_width())
        H = max(1, self.winfo_height())
        if W < 4 or H < 4:
            self.after(16, self._redraw)
            return

        half_w = max(1, (W - 8) // 2)

        # ORIG
        pil_o = bgr_to_pil(self.orig_bgr)
        _, tw_o, th_o = _fit_contain_no_upscale(half_w, H, pil_o.width, pil_o.height)
        self._orig_imgtk = ImageTk.PhotoImage(pil_o.resize((tw_o, th_o), Image.LANCZOS))
        self.left.configure(image=self._orig_imgtk)

        # PROC
        pil_p = bgr_to_pil(self.proc_bgr)
        _, tw_p, th_p = _fit_contain_no_upscale(half_w, H, pil_p.width, pil_p.height)
        self._proc_imgtk = ImageTk.PhotoImage(pil_p.resize((tw_p, th_p), Image.LANCZOS))
        self.right.configure(image=self._proc_imgtk)


# ---------------- Before/After Slider ----------------
class SliderPreview(ttk.Frame):
    """Canvas with draggable divider. Centered; fits inside, never upscales."""
    def __init__(self, master):
        super().__init__(master)
        self.orig_bgr = None
        self.proc_bgr = None
        self._orig_pil = None
        self._proc_pil = None
        self._orig_imgtk = None
        self._proc_imgtk = None
        self._left_imgtk = None
        self.split_x = None  # divider position in canvas coords

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Configure>", lambda e: self._redraw())
        self.canvas.bind("<Button-1>", self._drag)
        self.canvas.bind("<B1-Motion>", self._drag)

    def update_images(self, orig_bgr, proc_bgr):
        self.orig_bgr = orig_bgr
        self.proc_bgr = proc_bgr
        self._orig_pil = bgr_to_pil(self.orig_bgr)
        self._proc_pil = bgr_to_pil(self.proc_bgr)
        self._redraw(initial=True)

    def _drag(self, event):
        self.split_x = max(0, min(self.canvas.winfo_width(), event.x))
        self._draw_layers()

    def _redraw(self, initial=False):
        if self._orig_pil is None or self._proc_pil is None:
            return

        W = max(1, self.canvas.winfo_width())
        H = max(1, self.canvas.winfo_height())
        if W < 4 or H < 4:
            self.after(16, lambda: self._redraw(initial))
            return

        # Single target size (contain, no upscale) so both layers align
        _, tw, th = _fit_contain_no_upscale(W, H, self._orig_pil.width, self._orig_pil.height)

        disp_o = self._orig_pil.resize((tw, th), Image.LANCZOS)
        disp_p = self._proc_pil.resize((tw, th), Image.LANCZOS)
        self._orig_imgtk = ImageTk.PhotoImage(disp_o)
        self._proc_imgtk = ImageTk.PhotoImage(disp_p)

        # Center inside canvas (no scrollbars, so we never exceed the box)
        self.img_offset_x = (W - tw) // 2
        self.img_offset_y = (H - th) // 2

        if initial or self.split_x is None:
            self.split_x = self.img_offset_x + tw // 2

        self._draw_layers()

    def _draw_layers(self):
        self.canvas.delete("all")
        if self._proc_imgtk is None or self._orig_imgtk is None:
            return

        # AFTER (full)
        self.canvas.create_image(self.img_offset_x, self.img_offset_y, anchor="nw", image=self._proc_imgtk)

        tw = self._proc_imgtk.width()
        th = self._proc_imgtk.height()

        # BEFORE visible width at divider
        left_visible = max(0, self.split_x - self.img_offset_x)
        left_visible = int(min(tw, left_visible))

        if left_visible > 0:
            crop = self._orig_pil.resize((tw, th), Image.LANCZOS).crop((0, 0, left_visible, th))
            self._left_imgtk = ImageTk.PhotoImage(crop)  # keep ref alive
            self.canvas.create_image(self.img_offset_x, self.img_offset_y, anchor="nw", image=self._left_imgtk)

        # Divider + handle (centered)
        x = self.split_x
        self.canvas.create_line(x, self.img_offset_y, x, self.img_offset_y + th, width=2)
        self.canvas.create_oval(x - 8, self.img_offset_y + th // 2 - 8, x + 8, self.img_offset_y + th // 2 + 8, width=1)
        self.canvas.create_text(x - 40, self.img_offset_y + th // 2 - 18, text="Before", anchor="e")
        self.canvas.create_text(x + 40, self.img_offset_y + th // 2 - 18, text="After", anchor="w")
