from tkinter import ttk

__all__ = ["apply_theme", "get_palette"]

LIGHT = {"BG": "#FFFFFF", "FG": "#111111", "SUB": "#F2F2F2", "TROUGH": "#D9D9D9"}
DARK  = {"BG": "#121212", "FG": "#E6E6E6", "SUB": "#1E1E1E", "TROUGH": "#2A2A2A"}

def get_palette(mode: str):
    return DARK if mode == "dark" else LIGHT


def apply_theme(root, mode: str = "light"):
    """Apply light or dark theme to ttk widgets."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    P = get_palette(mode)

    root.configure(bg=P["BG"])
    style.configure(".", background=P["BG"], foreground=P["FG"], fieldbackground=P["SUB"]) 
    style.configure("TFrame", background=P["BG"]) 
    style.configure("TLabelframe", background=P["BG"], foreground=P["FG"]) 
    style.configure("TLabelframe.Label", background=P["BG"], foreground=P["FG"]) 
    style.configure("TLabel", background=P["BG"], foreground=P["FG"]) 
    style.configure("TButton", background=P["SUB"], foreground=P["FG"], padding=6, relief="flat") 
    style.map("TButton", background=[("active", P["TROUGH"])]) 
    style.configure("TCheckbutton", background=P["BG"], foreground=P["FG"]) 
    style.configure("TRadiobutton", background=P["BG"], foreground=P["FG"]) 
    style.configure("TScale", background=P["BG"], troughcolor=P["TROUGH"]) 
    style.configure("TScrollbar", background=P["SUB"], troughcolor=P["TROUGH"]) 