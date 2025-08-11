# Pixel Alchemy Studio

---

## Why this exists (Motivation)

Creative grading tools are either overkill or underpowered. You wanted something opinionated but tweakable: open a photo, pick a look, nudge a few big sliders, and *bam* — a stylized result that feels intentional. Pixel Alchemy Studio focuses on that sweet spot: tasteful defaults, fast feedback, and controls that make sense.

## Aim & Objectives

* **Aim:** Make high-quality stylistic grades accessible with a friendly, snappy desktop UI.
* **Objectives:**

  * Offer multiple **themes** (processing pipelines): Cyberpunk, Ghibli, Mughal Art, Hand Painting.
  * Make “good” results trivial via **presets** (JSON-configurable).
  * Keep controls **big** and **responsive**; include a **Before/After** slider and **Side-by-Side** modes.
  * Support **single**, **multi-select**, and **entire folder** batch processing.
  * Provide a **progress bar**, **dark mode**, **transform tools** (rotate/flip), and a **scrollable** tools panel.

---

## Features

* 🎨 **Themes:** Cyberpunk, Ghibli, Mughal Art, Hand Painting — each with tailored pipelines.
* ⚡ **Presets:** Apply curated looks; extend via `presets.json`.
* 🧪 **Randomizer:** Generate sane random params for quick exploration.
* 🖼️ **Preview Modes:** Side-by-Side or Before/After **slider overlay** (toggle anytime).
* 🗂️ **Browser:** Open a single image, pick multiple, or entire folders (optional batch).
* 🔧 **Transform:** Rotate ±90/180, Flip H/V.
* 🌗 **Light/Dark Mode:** Toggleable UI theme.
* 📏 **Responsive UI:** Scrollable controls; collapsible right panel when you need more canvas.
* 📊 **Progress Bar:** Single render spinner; determinate progress for batch runs.

---

## Quick Start

### 1) Clone

```bash
git clone <your-repo-url> pixel-alchemy-studio
cd pixel-alchemy-studio
```

### 2) Create & activate an environment (recommended)

#### Conda

```bash
conda create -n cyberpunk_env python=3.11 -y
conda activate cyberpunk_env
```

#### Or venv

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

If you don’t have a `requirements.txt`, install directly:

```bash
pip install opencv-python pillow numpy
```

> **Linux note:** If Tk isn’t present, install it (e.g., Ubuntu/Debian: `sudo apt-get install python3-tk`).
> **macOS (Homebrew) optional:** `brew install tcl-tk` (if you want a newer Tk).

### 4) Run

```bash
python main.py
```

---

## Project Structure

```
.
├─ app/
│  ├─ app.py               # Main application window & wiring
│  ├─ actions.py           # File/batch actions & handlers
│  └─ state.py             # App state (current image, theme, mode, etc.)
├─ processing/
│  ├─ pipeline.py          # Image ops + pipelines (Cyberpunk, Ghibli, Mughal, Hand Painting)
│  └─ themes.py            # Theme registry + get_pipeline()
├─ ui/
│  ├─ preview.py           # Side-by-side & before/after slider widgets
│  ├─ widgets.py           # LabeledSlider, shared UI helpers
│  ├─ theme.py             # Light/Dark ttk styling
│  └─ panels/
│     ├─ __init__.py
│     ├─ left_browser.py   # Thumbnails + mode (single/multi/folder)
│     ├─ preview_panel.py  # Preview selector + container
│     └─ right_controls.py # Scrollable tools, presets, progress bar, sliders, transforms
├─ utils/
│  ├─ image_io.py          # Robust image load/save, resizing, listing
│  └─ presets.py           # Load/get presets & random params
├─ presets.json            # Your presets (per theme)
├─ main.py                 # Entry point
└─ README.md
```

---

## Using the App

1. **Open images:**

   * Left panel → **Open Folder…** to see thumbnails
   * Or top-right → **Open Image…** for a single file
   * Modes: **Single**, **Multiple**, or **Folder**

2. **Choose a Theme:**
   Right panel → “Theme (choose processing style)”: **Cyberpunk / Ghibli / Mughal Art / Hand Painting**

3. **Pick a Preset:**
   Preset dropdown → **Apply Preset** (presets aren’t auto-applied).
   Use **Random** to explore.

4. **Transform (optional):**
   Rotate ±90/180, Flip H/V.

5. **Preview Modes:**
   Top center → **Side-by-Side** or **Before/After Slider**.
   Hide controls with **Hide Controls** to give the preview more space.

6. **Save:**
   Top-right → **Save Result**.

7. **Batch:**
   Choose **Multiple** or **Folder** mode, then **Process Batch…**.
   Watch progress in the bar just below **Transform**.

---

## Presets JSON Format

`presets.json` groups presets **by theme**. Each theme contains a dictionary of preset names → parameter dicts.

**Example:**

```json
{
  "Cyberpunk": {
    "Default": {
      "clahe_clip": 2.2, "contrast": 1.25, "saturation": 1.35, "vibr": 0.7,
      "tone_strength": 0.32, "glow": 0.85,
      "edge_strength": 0.35, "edge_low": 110, "edge_high": 220, "edge_soften": 1.5,
      "vignette_amt": 0.35, "scan_alpha": 0.05,
      "do_glitch": true, "glitch_n": 6, "glitch_shift": 14
    },
    "Punchy Neon": { /* same shape */ }
  },
  "Ghibli": {
    "Default": { /* ghibli-flavored params */ }
  },
  "Mughal Art": {
    "Default": { /* mughal-flavored params */ }
  },
  "Hand Painting": {
    "Default": { /* painterly params */ }
  }
}
```

**Notes**

* Theme names must match those in `processing/themes.py` (`THEME_NAMES`).
* If a theme has no presets, the UI shows just **Default**.
* Presets are applied only when you click **Apply Preset**.

---

## Adding a New Theme

1. Implement a new pipeline in `processing/pipeline.py`:

   ```python
   def my_new_pipeline(img_bgr, ..., **params):
       # do image magic
       return img_bgr
   ```
2. Register it in `processing/themes.py`:

   ```python
   from .pipeline import my_new_pipeline
   THEMES["My New Theme"] = my_new_pipeline
   ```
3. Add presets under a matching key in `presets.json`:

   ```json
   {
     "My New Theme": {
       "Default": { /* params */ }
     }
   }
   ```

---

## Tips & Troubleshooting

* **Thumbnails not showing in OS file picker?**
  Use the left **Open Folder…** browser — it renders thumbnails in-app.
* **Tk errors on Linux/macOS:**
  Ensure Tk is installed (`python3-tk` on Linux; optional `brew install tcl-tk` on macOS).
* **OpenCV missing features:**
  We fall back where possible. If you want everything, use `pip install opencv-contrib-python`.
* **Very wide images hide controls:**
  Use **Hide Controls** in the preview bar to maximize canvas; tools panel is scrollable.

---

## Requirements

* Python **3.9 – 3.12** (tested most on 3.11)
* Packages: `opencv-python`, `Pillow`, `numpy` (Tk/ttk ship with Python on most platforms)

`requirements.txt` (suggested):

```
opencv-python>=4.8
Pillow>=9.5
numpy>=1.24
```

> If you want OpenCV’s extra stylization filters:
> `opencv-contrib-python>=4.8` (replaces `opencv-python`)

---

## License

MIT — do whatever, just don’t remove the notice. Attribution appreciated if this helps your project. 🙌

---

## Credits

Designed with lots of user feedback (thanks!) and a shameless love for neon, watercolor skies, and old film grain.
