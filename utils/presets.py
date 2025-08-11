# utils/presets.py
import json
import os
import random

# Path to presets.json (project root)
PRESET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "presets.json")

# Built-in fallback "Default"
FALLBACK_DEFAULT = {
    "clahe_clip": 2.2, "contrast": 1.25, "saturation": 1.35, "vibr": 0.7,
    "tone_strength": 0.32, "glow": 0.85,
    "edge_strength": 0.35, "edge_low": 110, "edge_high": 220, "edge_soften": 1.5,
    "vignette_amt": 0.35, "scan_alpha": 0.05,
    "do_glitch": True, "glitch_n": 6, "glitch_shift": 14,
}

# ---- helpers -------------------------------------------------

_PARAM_KEYS = {
    "clahe_clip", "contrast", "saturation", "vibr", "tone_strength", "glow",
    "edge_strength", "edge_low", "edge_high", "edge_soften",
    "vignette_amt", "scan_alpha", "do_glitch", "glitch_n", "glitch_shift",
}

def _load_raw():
    """Load JSON; tolerate UTF-8 BOM; return {} on any error."""
    try:
        with open(PRESET_PATH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _looks_like_params(d: dict) -> bool:
    """Does this mapping look like a single preset (has known parameter keys)?"""
    if not isinstance(d, dict):
        return False
    # require a few core keys so we don't misclassify theme sections
    must = {"contrast", "saturation", "glow"}
    return must.issubset(d.keys())

def _preset_map_for_theme(data: dict, theme: str) -> dict:
    """
    Return a mapping {preset_name: params_dict} for the requested theme.
    Handles:
      1) Themed layout: { "Cyberpunk": { "Default": {...}, ... }, "Neo Noir": {...} }
      2) Flat layout:   { "Default": {...}, "Punchy Neon": {...}, ... }
      3) Mixed layout:  top-level presets + some themed sections (your case)
    """
    # 1) The theme exists and is a mapping of presets
    section = data.get(theme)
    if isinstance(section, dict) and any(_looks_like_params(v) for v in section.values()):
        return section

    # 2) or FALLBACK: collect all top-level entries that look like presets
    flat = {k: v for k, v in data.items() if _looks_like_params(v)}
    if flat:
        return flat

    # 3) nothing matched
    return {}

# ---- public API ----------------------------------------------

def get_preset_names(theme: str):
    """List preset names for the given theme, reading from disk each time."""
    data = _load_raw()
    mapping = _preset_map_for_theme(data, theme)
    names = list(mapping.keys())
    return names if names else ["Default"]

def get_preset(theme: str, name: str):
    """Return the preset dict for a given (theme, name)."""
    data = _load_raw()
    mapping = _preset_map_for_theme(data, theme)

    if name in mapping and isinstance(mapping[name], dict):
        return mapping[name]

    if "Default" in mapping and isinstance(mapping["Default"], dict):
        return mapping["Default"]

    return dict(FALLBACK_DEFAULT)

def random_params(_theme: str):
    """Generate sensible random parameters (independent of theme)."""
    clahe_clip   = round(random.uniform(0.5, 4.0), 1)
    contrast     = round(random.uniform(0.85, 1.7), 2)
    saturation   = round(random.uniform(0.9, 1.9), 2)
    vibr         = round(random.uniform(0.0, 1.5), 2)
    tone_strength= round(random.uniform(0.0, 0.8), 2)
    glow         = round(random.uniform(0.0, 1.5), 2)
    edge_strength= round(random.uniform(0.05, 0.6), 2)
    low          = random.randint(10, 190)
    high_min     = max(50, low + 40)
    high         = random.randint(high_min, 300)
    edge_soften  = round(random.uniform(0.8, 2.2), 2)
    vignette_amt = round(random.uniform(0.2, 0.6), 2)
    scan_alpha   = round(random.uniform(0.0, 0.12), 3)
    do_glitch    = random.random() < 0.7
    glitch_n     = (0 if not do_glitch else random.randint(3, 12))
    glitch_shift = (0 if not do_glitch else random.randint(8, 24))
    return {
        "clahe_clip": clahe_clip, "contrast": contrast, "saturation": saturation, "vibr": vibr,
        "tone_strength": tone_strength, "glow": glow,
        "edge_strength": edge_strength, "edge_low": low, "edge_high": high, "edge_soften": edge_soften,
        "vignette_amt": vignette_amt, "scan_alpha": scan_alpha,
        "do_glitch": do_glitch, "glitch_n": glitch_n, "glitch_shift": glitch_shift,
    }
