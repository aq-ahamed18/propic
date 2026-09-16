import os
import math
from dataclasses import dataclass
from PIL import Image as PILImage, ImageOps

@dataclass
class PropertyImage:
    part: str
    path: str

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def remove(self):
        if self.exists():
            try:
                os.remove(self.path)
            except Exception:
                pass

    def get_info(self) -> dict:
        if not self.exists():
            return {"exists": False, "orientation": "unknown", "width": 0, "height": 0, "aspect_ratio": 1.0}
        try:
            with PILImage.open(self.path) as img:
                w, h = img.size
                orientation = "landscape" if w >= h else "portrait"
                return {
                    "exists": True,
                    "orientation": orientation,
                    "width": w,
                    "height": h,
                    "aspect_ratio": round(w / h, 2) if h > 0 else 1.0
                }
        except Exception:
            return {"exists": False, "orientation": "unknown", "width": 0, "height": 0, "aspect_ratio": 1.0}


def save_uploaded_image(uploaded_file, dest_path: str) -> bool:
    """
    Saves any uploaded image (jpg/png) as a proper JPEG file on disk.
    Converts PNG with alpha to RGB to ensure fpdf compatibility.
    Returns True on success.
    """
    try:
        uploaded_file.seek(0)
        img = PILImage.open(uploaded_file)
        
        # Apply EXIF rotation if available
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        if img.mode in ("RGBA", "P", "LA"):
            bg = PILImage.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
            
        img.save(dest_path, "JPEG", quality=95)
        return True
    except Exception:
        try:
            uploaded_file.seek(0)
            with open(dest_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return True
        except Exception:
            return False


def standardize_image_for_container(src_path: str, dest_path: str, target_w_mm: float, target_h_mm: float) -> str:
    """
    Center-crops and resizes the source image so that it fits EXACTLY into a 
    predefined physical container of (target_w_mm x target_h_mm) without stretching,
    distortion, or letterboxing.
    Returns the path of the processed image (dest_path).
    """
    if not os.path.exists(src_path):
        return src_path

    try:
        with PILImage.open(src_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode != "RGB":
                img = img.convert("RGB")

            src_w, src_h = img.size
            target_aspect = target_w_mm / target_h_mm
            src_aspect = src_w / src_h

            if abs(src_aspect - target_aspect) < 0.02:
                crop_box = (0, 0, src_w, src_h)
            elif src_aspect > target_aspect:
                # Source is wider than target container -> crop left/right
                new_src_w = int(src_h * target_aspect)
                offset = (src_w - new_src_w) // 2
                crop_box = (offset, 0, offset + new_src_w, src_h)
            else:
                # Source is taller than target container -> crop top/bottom
                new_src_h = int(src_w / target_aspect)
                offset = (src_h - new_src_h) // 2
                crop_box = (0, offset, src_w, offset + new_src_h)

            cropped = img.crop(crop_box)

            # High resolution target pixel size for crisp PDF printing (~300 dpi)
            px_w = int(target_w_mm * 11.81)
            px_h = int(target_h_mm * 11.81)

            resample_filter = getattr(PILImage, "Resampling", PILImage).LANCZOS
            final_img = cropped.resize((px_w, px_h), resample_filter)
            
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            final_img.save(dest_path, "JPEG", quality=95)
            return dest_path
    except Exception:
        return src_path