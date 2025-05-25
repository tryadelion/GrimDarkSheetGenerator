import os
from io import BytesIO
from bs4 import BeautifulSoup
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader
import subprocess

def tint_svg(svg_path, color_hex):
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_data = f.read()

    soup = BeautifulSoup(svg_data, "xml")

    for tag in soup.find_all(["path", "circle", "rect", "polygon", "ellipse", "line", "polyline", "g"]):
        if "style" in tag.attrs:
            del tag["style"]
        if "fill" not in tag.attrs or tag["fill"] in ("none", "currentColor", "inherit", "", None):
            tag["fill"] = color_hex
        else:
            tag["fill"] = color_hex

    return str(soup)

def draw_svg_to_pdf(canvas, svg_string, x, y, width, height):
    svg_io = BytesIO(svg_string.encode("utf-8"))
    drawing = svg2rlg(svg_io)

    if drawing.width == 0 or drawing.height == 0:
        return  # Avoid division by zero

    scale = min(width / drawing.width, height / drawing.height)
    drawing.scale(scale, scale)

    renderPDF.draw(drawing, canvas, x, y)

def trigger_pdf_print_dialog(path):
    try:
        os.startfile(path, "print")  # Windows only
    except OSError as e:
        print(f"[WARN] os.startfile(print) failed: {e}")
        print("[INFO] Falling back to opening the PDF in default viewer.")
        try:
            subprocess.run(['cmd', '/c', 'start', '', path], check=True)
        except Exception as sub_e:
            print(f"[ERROR] Could not open PDF: {sub_e}")
