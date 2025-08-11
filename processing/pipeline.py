# processing/pipeline.py
import cv2
import numpy as np

# ============================================================
# Core helpers (kept compatible with your existing UI)
# ============================================================

def unsharp_mask(img_bgr, amount=0.6, radius=1.5):
    blur = cv2.GaussianBlur(img_bgr, (0, 0), radius)
    return cv2.addWeighted(img_bgr, 1 + amount, blur, -amount, 0)

def clahe_contrast(img_bgr, clip=2.0):
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=max(0.1, clip), tileGridSize=(8, 8))
    L2 = clahe.apply(L)
    lab2 = cv2.merge([L2, A, B])
    return cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)

def adjust_contrast_saturation(img_bgr, contrast=1.2, sat=1.3):
    img = img_bgr.astype(np.float32) / 255.0
    img = np.clip((img - 0.5) * float(contrast) + 0.5, 0, 1)
    hsv = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * float(sat), 0, 255)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    return out

def vibrance(img_bgr, vib=0.6):
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    s = hsv[:, :, 1] / 255.0
    v = hsv[:, :, 2] / 255.0
    boost = float(vib) * (1.0 - s) * (0.6 + 0.4 * v)
    s2 = np.clip((s + boost), 0, 1)
    hsv[:, :, 1] = s2 * 255.0
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

def split_tone(img_bgr, shadow_tint=(180, 255, 255), highlight_tint=(255, 80, 220), strength=0.3):
    img = img_bgr.astype(np.float32) / 255.0
    lum = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    lum = cv2.GaussianBlur(lum, (0, 0), 1.2)
    st = np.array(shadow_tint, np.float32) / 255.0
    ht = np.array(highlight_tint, np.float32) / 255.0
    lum_3 = np.repeat(lum[:, :, None], 3, axis=2)
    tint = ht * lum_3 + st * (1 - lum_3)
    out = np.clip(img * (1 - float(strength)) + tint * float(strength), 0, 1)
    return (out * 255).astype(np.uint8)

def neon_bloom(img_bgr, strength=0.8):
    img = img_bgr.astype(np.float32) / 255.0
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    mask = np.clip((gray - 0.5) * 3.0, 0, 1)
    mask = cv2.GaussianBlur(mask, (0, 0), 2.0)
    bright = img * mask[:, :, None]
    glow = cv2.GaussianBlur(bright, (0, 0), 6.0)
    out = np.clip(img + glow * float(strength), 0, 1)
    return (out * 255).astype(np.uint8)

def thin_neon_edges(img_bgr, strength=0.4, low_th=110, high_th=220, soften=1.5):
    base = img_bgr.copy()
    blur = cv2.GaussianBlur(img_bgr, (0, 0), 0.8)
    edges = cv2.Canny(blur, int(low_th), int(high_th))
    if soften and soften > 0:
        edges = cv2.GaussianBlur(edges, (0, 0), float(soften))
    neon = np.zeros_like(img_bgr, dtype=np.float32)
    neon[:, :, 0] = 180  # B
    neon[:, :, 1] = 60   # G
    neon[:, :, 2] = 255  # R
    mask = (edges.astype(np.float32) / 255.0)[:, :, None]
    mix = np.clip(base.astype(np.float32) + neon * mask * float(strength), 0, 255)
    return mix.astype(np.uint8)

def vignette(img_bgr, strength=0.35):
    h, w = img_bgr.shape[:2]
    y, x = np.ogrid[:h, :w]
    yc, xc = (h - 1) / 2.0, (w - 1) / 2.0
    dist = np.sqrt((x - xc) ** 2 + (y - yc) ** 2)
    dist /= (dist.max() + 1e-6)
    mask = 1 - (dist ** 1.5) * float(strength)
    mask = mask.astype(np.float32)
    return (img_bgr.astype(np.float32) * mask[:, :, None]).astype(np.uint8)

def add_scanlines(img_bgr, alpha=0.05):
    if alpha <= 0:
        return img_bgr
    out = img_bgr.copy().astype(np.float32)
    out[::2, :, :] *= (1 - float(alpha))
    return np.clip(out, 0, 255).astype(np.uint8)

def tiny_glitch(img_bgr, n=6, max_shift=14):
    if n <= 0:
        return img_bgr
    h, w = img_bgr.shape[:2]
    out = img_bgr.copy()
    rng = np.random.default_rng()
    for _ in range(int(n)):
        y = int(rng.integers(0, h))
        band_h = int(rng.integers(2, max(3, h // 45)))
        x_shift = int(rng.integers(-int(max_shift), int(max_shift) + 1))
        y2 = min(h, y + band_h)
        band = out[y:y2].copy()
        M = np.float32([[1, 0, x_shift], [0, 1, 0]])
        band = cv2.warpAffine(band, M, (w, band.shape[0]), borderMode=cv2.BORDER_REFLECT)
        out[y:y2] = band
    return out

# Extra helpers for painterly themes
def _edges_mask(img_bgr, low, high, sigma=1.0):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    if sigma and sigma > 0:
        gray = cv2.GaussianBlur(gray, (0, 0), float(sigma))
    return cv2.Canny(gray, int(low), int(high))

def _overlay_edges_color(img_bgr, edges, color_bgr=(255, 255, 255), alpha=0.4, thick_px=1):
    """
    Overlay colored edges onto a BGR image.
    - edges: uint8 single-channel (0 or 255) from Canny.
    - color_bgr: tuple of 3 ints (B, G, R).
    - alpha: blend strength along edges [0..1].
    - thick_px: optional dilation size (>=1).
    """
    # Ensure edges is single-channel uint8
    e = edges
    if e is None:
        return img_bgr
    if e.ndim == 3:
        e = cv2.cvtColor(e, cv2.COLOR_BGR2GRAY)

    # Optional thickness
    if thick_px and thick_px > 1:
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (int(thick_px), int(thick_px)))
        e = cv2.dilate(e, k, 1)

    # Build a 3-channel mask in [0,1]
    m = (e > 0).astype(np.float32)[:, :, None]  # H×W×1
    a = float(max(0.0, min(1.0, alpha)))        # clamp alpha
    color = np.array(color_bgr, dtype=np.float32).reshape(1, 1, 3)

    # Blend only where mask==1: out = img*(1-a*m) + color*(a*m)
    out = img_bgr.astype(np.float32)
    out = out * (1.0 - a * m) + color * (a * m)
    return np.clip(out, 0, 255).astype(np.uint8)


def _kmeans_quantize(img_bgr, k=12, attempts=1):
    Z = img_bgr.reshape((-1, 3)).astype(np.float32)
    K = max(2, int(k))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _compactness, labels, centers = cv2.kmeans(Z, K, None, criteria, int(attempts), cv2.KMEANS_PP_CENTERS)
    centers = centers.astype(np.uint8)
    q = centers[labels.flatten()].reshape(img_bgr.shape)
    return q

# ============================================================
# Cyberpunk (your existing look)
# ============================================================

def cyberpunkify_pipeline(
    img_bgr,
    clahe_clip=2.2,
    contrast=1.25,
    saturation=1.35,
    vibr=0.7,
    tone_strength=0.32,
    glow=0.85,
    edge_strength=0.35,
    edge_low=110,
    edge_high=220,
    edge_soften=1.5,
    vignette_amt=0.35,
    scan_alpha=0.05,
    do_glitch=True,
    glitch_n=6,
    glitch_shift=14,
):
    img = unsharp_mask(img_bgr, amount=0.55, radius=1.3)
    img = clahe_contrast(img, clip=clahe_clip)
    img = adjust_contrast_saturation(img, contrast=contrast, sat=saturation)
    img = vibrance(img, vib=vibr)
    img = split_tone(img, shadow_tint=(180, 255, 255), highlight_tint=(255, 80, 220), strength=tone_strength)
    img = neon_bloom(img, strength=glow)
    img = thin_neon_edges(img, strength=edge_strength, low_th=edge_low, high_th=edge_high, soften=edge_soften)
    img = vignette(img, strength=vignette_amt)
    img = add_scanlines(img, alpha=scan_alpha)
    if do_glitch:
        img = tiny_glitch(img, n=glitch_n, max_shift=glitch_shift)
    return img

# ============================================================
# New themes
# ============================================================

def ghibli_pipeline(
    img_bgr,
    clahe_clip=2.0,
    contrast=1.10,
    saturation=1.15,
    vibr=0.6,
    tone_strength=0.20,  # warm tilt
    glow=0.80,           # softness/brush size
    edge_strength=0.25,
    edge_low=80,
    edge_high=180,
    edge_soften=1.2,
    vignette_amt=0.20,
    scan_alpha=0.0,
    do_glitch=False,
    glitch_n=0,
    glitch_shift=0,
):
    """
    Soft watercolor/cartoon vibe: edge-preserving smoothing + gentle posterization and warm tint.
    """
    img = img_bgr.copy()
    img = clahe_contrast(img, clip=clahe_clip)
    img = adjust_contrast_saturation(img, contrast=contrast, sat=saturation)
    img = vibrance(img, vib=vibr)

    # Edge-preserving watercolor feel (fallback to bilateral if not available)
    try:
        img = cv2.edgePreservingFilter(img, flags=1, sigma_s=int(50 * float(glow) + 10), sigma_r=0.35)
    except Exception:
        img = cv2.bilateralFilter(img, d=7, sigmaColor=40 + int(30 * float(glow)), sigmaSpace=7)

    # Gentle posterization
    img = _kmeans_quantize(img, k=12)

    # Warm tint based on tone_strength
    warm = np.array([0, 12, 24], np.float32) * float(tone_strength)  # BGR
    img = np.clip(img.astype(np.float32) + warm, 0, 255).astype(np.uint8)

    # Thin, soft, dark edges
    edges = _edges_mask(img_bgr, edge_low, edge_high, sigma=edge_soften)
    img = _overlay_edges_color(img, edges, color_bgr=(20, 20, 20), alpha=edge_strength, thick_px=1)

    img = vignette(img, strength=vignette_amt)
    return img

def mughal_pipeline(
    img_bgr,
    clahe_clip=2.0,
    contrast=1.20,
    saturation=1.10,
    vibr=0.4,
    tone_strength=0.25,  # parchment warmth
    glow=0.50,           # smoothing
    edge_strength=0.35,
    edge_low=70,
    edge_high=160,
    edge_soften=1.0,
    vignette_amt=0.28,
    scan_alpha=0.0,
    do_glitch=False,
    glitch_n=0,
    glitch_shift=0,
):
    """
    Miniature painting vibe: earthy palette (quantized), warm parchment tint, clear outlines.
    """
    img = img_bgr.copy()
    img = clahe_contrast(img, clip=clahe_clip)
    img = adjust_contrast_saturation(img, contrast=contrast, sat=saturation)
    img = vibrance(img, vib=vibr)

    # Palette reduction for painted look
    img = _kmeans_quantize(img, k=9)

    # Gentle smoothing
    img = cv2.bilateralFilter(img, d=7, sigmaColor=40 + int(30 * float(glow)), sigmaSpace=7)

    # Warm parchment tint
    tint = np.array([20, 30, 60], np.float32) * float(tone_strength)  # BGR
    img = np.clip(img.astype(np.float32) + tint, 0, 255).astype(np.uint8)

    # Stronger dark outlines
    edges = _edges_mask(img_bgr, edge_low, edge_high, sigma=edge_soften)
    img = _overlay_edges_color(img, edges, color_bgr=(10, 25, 35), alpha=edge_strength, thick_px=2)

    img = vignette(img, strength=vignette_amt)
    return img

def hand_painting_pipeline(
    img_bgr,
    clahe_clip=2.0,
    contrast=1.15,
    saturation=1.10,
    vibr=0.5,
    tone_strength=0.10,  # canvas warmth
    glow=0.70,           # brushy smoothing
    edge_strength=0.20,
    edge_low=90,
    edge_high=180,
    edge_soften=1.2,
    vignette_amt=0.22,
    scan_alpha=0.0,
    do_glitch=False,
    glitch_n=0,
    glitch_shift=0,
):
    """
    Painterly/illustrative: OpenCV stylization + gentle outlines + slight warmth.
    """
    img = img_bgr.copy()
    img = clahe_contrast(img, clip=clahe_clip)
    img = adjust_contrast_saturation(img, contrast=contrast, sat=saturation)
    img = vibrance(img, vib=vibr)

    # Watercolor/oil hybrid (fallback if stylization not present)
    try:
        sigma_s = int(60 + float(glow) * 80)            # 10..200
        sigma_r = float(min(1.0, max(0.05, 0.25 + 0.25 * float(glow))))  # 0..1
        img = cv2.stylization(img, sigma_s=max(10, sigma_s), sigma_r=sigma_r)
    except Exception:
        img = cv2.edgePreservingFilter(img, flags=1, sigma_s=80, sigma_r=0.35)

    # Gentle outlines to keep structure
    edges = _edges_mask(img_bgr, edge_low, edge_high, sigma=edge_soften)
    img = _overlay_edges_color(img, edges, color_bgr=(30, 30, 30), alpha=edge_strength, thick_px=1)

    # Slight warm canvas bias
    warm = np.array([5, 10, 18], np.float32) * float(tone_strength)
    img = np.clip(img.astype(np.float32) + warm, 0, 255).astype(np.uint8)

    img = vignette(img, strength=vignette_amt)
    return img
