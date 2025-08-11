import os
import cv2
import numpy as np
from PIL import Image

IMG_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".webp")

def list_images_in_folder(folder):
    files = [os.path.join(folder, f) for f in os.listdir(folder)
             if os.path.splitext(f.lower())[1] in IMG_EXTS]
    files.sort()
    return files

# Robust loader (unicode paths on Windows)
def load_bgr(path):
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return img

def save_bgr(path, img_bgr):
    Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)).save(path)

def bgr_to_pil(img_bgr):
    return Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))

def resize_max(img_bgr, max_w=700, max_h=700):
    h, w = img_bgr.shape[:2]
    scale = min(max_w / w, max_h / h, 1.0)
    nh, nw = int(h * scale), int(w * scale)
    return cv2.resize(img_bgr, (nw, nh), interpolation=cv2.INTER_AREA)

def resize_to_box(img_bgr, box_w, box_h):
    h, w = img_bgr.shape[:2]
    scale = min(box_w / w, box_h / h)
    nh = max(1, int(h * scale))
    nw = max(1, int(w * scale))
    return cv2.resize(img_bgr, (nw, nh), interpolation=cv2.INTER_AREA)