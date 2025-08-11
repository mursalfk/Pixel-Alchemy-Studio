# processing/themes.py
from typing import Callable, Dict

from .pipeline import (
    cyberpunkify_pipeline,
    ghibli_pipeline,
    mughal_pipeline,
    hand_painting_pipeline,
)

# Public registry used by the UI
THEMES: Dict[str, Callable] = {
    "Cyberpunk":     cyberpunkify_pipeline,
    "Ghibli":        ghibli_pipeline,
    "Mughal Art":    mughal_pipeline,
    "Hand Painting": hand_painting_pipeline,
}

# Used to populate the Theme combobox
THEME_NAMES = list(THEMES.keys())


def get_pipeline(theme: str) -> Callable:
    """
    Return the processing pipeline function for a given theme name.
    Falls back to Cyberpunk if the name is missing or unrecognized.
    Supports a few simple aliases.
    """
    if not theme:
        return cyberpunkify_pipeline

    t = theme.strip().lower()

    # Exact name match (case-insensitive)
    for name, fn in THEMES.items():
        if t == name.lower():
            return fn

    # Friendly aliases
    aliases = {
        "cyber": "Cyberpunk",
        "mughal": "Mughal Art",
        "handpaint": "Hand Painting",
        "hand-painted": "Hand Painting",
        "hand painting": "Hand Painting",
    }
    if t in aliases:
        return THEMES[aliases[t]]

    # Default
    return cyberpunkify_pipeline
