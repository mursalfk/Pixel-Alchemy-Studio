# app/state.py
from dataclasses import dataclass, field
from typing import Optional, Set, Dict
import numpy as np

@dataclass
class AppState:
    original: Optional[np.ndarray] = None  # BGR
    processed: Optional[np.ndarray] = None # BGR

    current_path: Optional[str] = None
    current_folder: Optional[str] = None
    multiselect: Set[str] = field(default_factory=set)

    thumb_cache: Dict[str, object] = field(default_factory=dict)

    preview_mode: str = "side"        # 'side' or 'slider'
    pick_mode: str = "single"         # 'single' | 'multi' | 'folder'
    dark_mode: bool = False

    current_theme: str = "Cyberpunk"  # NEW: theme name
