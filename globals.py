import io
import json
import os
from PIL import Image, ImageTk
import cairosvg

# Shared colors and defaults
COLOR_BG = "#1e1e1e"
COLOR_FG = "#ffffff"
FONT_DEFAULT = "Arial"

# Icon cache to avoid duplicate loads
ICON_CACHE = {}

def get_cached_icon(path, size=(40, 40), color=None):
    key = (path, size, color)
    if key in ICON_CACHE:
        return ICON_CACHE[key]

    png_data = cairosvg.svg2png(url=path, output_width=size[0], output_height=size[1])
    image = Image.open(io.BytesIO(png_data)).convert("RGBA")

    if color:
        image = tint_image(image, color)

    photo = ImageTk.PhotoImage(image)
    ICON_CACHE[key] = photo
    return photo

def tint_image(image, color):
    image = image.convert("RGBA")
    solid = Image.new("RGBA", image.size, color)
    alpha = image.getchannel("A")
    return Image.composite(solid, Image.new("RGBA", image.size, (0, 0, 0, 0)), mask=alpha)

with open("tag_color_mapping.json", "r") as f:
    TAG_COLOR_MAP = json.load(f)
