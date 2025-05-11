import os
import re
from typing import List, Tuple
from PIL import Image, ImageTk
import cairosvg
import io
ICON_THUMBNAIL_CACHE = {}

class IconEntry:
    def __init__(self, name: str, tags: List[str], filepath: str):
        self.name = name
        self.tags = tags
        self.file = filepath
        self.thumbnail = None  # to be loaded lazily

    def __lt__(self, other):
        return (self.tags, self.name.lower()) < (other.tags, other.name.lower())

    def __repr__(self):
        return f"{self.name} – {', '.join(self.tags)}"

    def load_image(self, size=(60, 60)) -> ImageTk.PhotoImage:
        key = (self.file, size)
        if self.thumbnail:
            return self.thumbnail
        if key in ICON_THUMBNAIL_CACHE:
            return ICON_THUMBNAIL_CACHE[key]
        try:
            with open(self.file, 'rb') as f:
                svg_data = f.read()
            png_data = cairosvg.svg2png(bytestring=svg_data, output_width=size[0], output_height=size[1])
            image = Image.open(io.BytesIO(png_data))
            image.thumbnail(size, Image.LANCZOS)
            self.thumbnail = ImageTk.PhotoImage(image)
            ICON_THUMBNAIL_CACHE[key] = self.thumbnail
            return self.thumbnail
        except Exception as e:
            print(f"[ERROR] Failed to load icon {self.file}: {e}")
            return None

def parse_icon_filename(filename: str) -> Tuple[str, List[str]]:
    base = filename.rsplit('.', 1)[0]  # Remove extension
    match = re.match(r"^(.*?)\s*\[(.*?)\]$", base)
    if match:
        name = match.group(1).strip()
        tags = [t.strip() for t in match.group(2).split(',') if t.strip()]
    else:
        name = base
        tags = []
    return name, tags

def load_icon_entries(icon_folder: str) -> List[IconEntry]:
    entries = []
    for fname in os.listdir(icon_folder):
        if fname.lower().endswith(".svg"):
            name, tags = parse_icon_filename(fname)
            path = os.path.join(icon_folder, fname)
            entries.append(IconEntry(name, tags, path))
    entries.sort()
    return entries