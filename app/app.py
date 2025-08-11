# app/app.py
import tkinter as tk
from tkinter import ttk, messagebox
import cv2

from app.state import AppState
from app.actions import do_open_image, do_choose_folder, do_save_image, do_process_batch
from ui.theme import apply_theme
from ui.panels import LeftBrowserPanel, PreviewPanel, RightControls
from processing.themes import get_pipeline
from utils.image_io import load_bgr

RIGHT_PANEL_WIDTH = 440
RIGHT_PANEL_MINSIZE = 360  # keep controls visible

class CyberpunkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pixel Alchemy Studio")
        self.geometry("1480x880")
        apply_theme(self, mode="light")

        self.state = AppState()
        self.controls_visible = True  # sidebar visibility

        # LEFT: folder browser (keeps its own width)
        self.left = LeftBrowserPanel(
            self,
            on_choose_folder=lambda: do_choose_folder(self),
            on_mode_change=self.set_pick_mode,
            on_toggle_multi=self.toggle_multi,
            on_click_thumb=self.on_thumb_clicked,
        )
        self.left.pack(side=tk.LEFT, fill=tk.Y)

        # CENTER+RIGHT: use classic tk.PanedWindow so we can set minsize reliably
        self.center = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief="flat")
        self.center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # CENTER: preview
        self.preview = PreviewPanel(self.center)
        self.center.add(self.preview)  # preview stretches with the window

        # RIGHT: fixed-width shell -> holds scrollable RightControls
        self.right_shell = ttk.Frame(self.center)
        self.right_shell.config(width=RIGHT_PANEL_WIDTH)
        self.right_shell.pack_propagate(False)  # keep fixed width

        self.right = RightControls(
            self.right_shell,
            on_open=lambda: do_open_image(self),
            on_save=lambda: do_save_image(self),
            on_batch=lambda: do_process_batch(self),
            on_theme=self.toggle_theme_mode,
            on_params_changed=self.refresh,
        )
        self.right.pack(fill=tk.BOTH, expand=True)

        # Add right pane and lock a minimum size so it can't be squeezed away
        self.center.add(self.right_shell)
        self.center.paneconfigure(self.right_shell, minsize=RIGHT_PANEL_MINSIZE)

        # Place the sash so the right pane starts near RIGHT_PANEL_WIDTH
        self.after(120, self._set_initial_sash)

        # Ensure presets reflect current theme on launch
        self.right.reload_presets_for_theme()

    # ----- initial sash placement -----
    def _set_initial_sash(self):
        try:
            total = self.center.winfo_width()
            if total < RIGHT_PANEL_WIDTH + 300:
                self.after(120, self._set_initial_sash)
                return
            # position sash 0 so right pane ≈ RIGHT_PANEL_WIDTH
            self.center.sashpos(0, max(200, total - RIGHT_PANEL_WIDTH))
            self.center.paneconfigure(self.right_shell, minsize=RIGHT_PANEL_MINSIZE)
        except Exception:
            self.after(120, self._set_initial_sash)

    # ----- UI chrome -----
    def toggle_right_panel(self):
        if self.controls_visible:
            # remove the right pane (not destroyed)
            self.center.forget(self.right_shell)
            self.controls_visible = False
        else:
            # re-add and reapply minsize + sash position
            self.center.add(self.right_shell)
            self.center.paneconfigure(self.right_shell, minsize=RIGHT_PANEL_MINSIZE)
            self.after(50, self._set_initial_sash)
            self.controls_visible = True
        self.preview.set_controls_visible(self.controls_visible)

    def toggle_theme_mode(self):
        self.state.dark_mode = not self.state.dark_mode
        apply_theme(self, mode=("dark" if self.state.dark_mode else "light"))

    def set_theme(self, theme: str):
        self.state.current_theme = theme
        self.right.reload_presets_for_theme()
        self.right.reset_params()
        self.refresh()

    # ----- Selection / Files -----
    def set_pick_mode(self, mode: str):
        if mode not in ("single", "multi", "folder"):
            return
        if self.state.pick_mode == "multi" and mode != "multi":
            self.state.multiselect.clear()
            self.left.clear_multi_checks()
        self.state.pick_mode = mode

    def toggle_multi(self, path: str, selected: bool):
        if selected:
            self.state.multiselect.add(path)
        else:
            self.state.multiselect.discard(path)

    def on_thumb_clicked(self, path: str):
        if self.state.pick_mode in ("single", "folder"):
            self.load_image(path)
        else:
            self.left.toggle_row_check(path)

    def load_image(self, path: str):
        try:
            img = load_bgr(path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")
            return
        self.state.current_path = path
        self.state.original = img
        self.refresh()

    # ----- Transform tools -----
    def _ensure_img(self):
        return self.state.original is not None

    def rotate_left(self):
        if not self._ensure_img(): return
        self.state.original = cv2.rotate(self.state.original, cv2.ROTATE_90_COUNTERCLOCKWISE)
        self.refresh()

    def rotate_right(self):
        if not self._ensure_img(): return
        self.state.original = cv2.rotate(self.state.original, cv2.ROTATE_90_CLOCKWISE)
        self.refresh()

    def rotate_180(self):
        if not self._ensure_img(): return
        self.state.original = cv2.rotate(self.state.original, cv2.ROTATE_180)
        self.refresh()

    def flip_h(self):
        if not self._ensure_img(): return
        self.state.original = cv2.flip(self.state.original, 1)
        self.refresh()

    def flip_v(self):
        if not self._ensure_img(): return
        self.state.original = cv2.flip(self.state.original, 0)
        self.refresh()

    # ----- Processing -----
    def params(self):
        return self.right.get_params()

    def refresh(self, *_):
        if self.state.original is None:
            return
        # start spinner for single render
        if hasattr(self, "right"):
            self.right.progress_start("Processing...")
        try:
            pipeline = get_pipeline(self.state.current_theme)
            self.state.processed = pipeline(self.state.original, **self.params())
        finally:
            if hasattr(self, "right"):
                self.right.progress_stop("Ready")

        if hasattr(self.preview, "mode") and self.preview.mode.get() == "side":
            self.preview.show_side(self.state.original, self.state.processed)
        else:
            self.preview.show_slider(self.state.original, self.state.processed)
