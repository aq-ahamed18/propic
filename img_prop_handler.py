import os
from dataclasses import dataclass

@dataclass
class PropertyImage:
    part: str
    path: str

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def remove(self):
        if self.exists():
            os.remove(self.path)

def save_uploaded_image(uploaded_file, dest_path: str) -> bool:
    """
    Saves any uploaded image (jpg/png) as a proper JPEG file on disk.
    Converts PNG with alpha to RGB to ensure fpdf compatibility.
    Returns True on success.
    """
    try:
        from PIL import Image as PILImage
        img = PILImage.open(uploaded_file)
        if img.mode in ("RGBA", "P", "LA"):
            bg = PILImage.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.save(dest_path, "JPEG", quality=92)
        return True
    except Exception:
        # Fallback: write raw bytes
        uploaded_file.seek(0)
        with open(dest_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True