import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
from globals import COLOR_BG, COLOR_FG, FONT_DEFAULT, get_cached_icon
from export_helpers import tint_svg, draw_svg_to_pdf, trigger_pdf_print_dialog
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5, A4, portrait, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from io import BytesIO
import os

GRID_ROWS = 5
GRID_COLUMNS = 10

def clamp_whites(hex_color, threshold="#FDFFF5"):
    def hex_to_rgb(hex_code):
        hex_code = hex_code.lstrip("#")
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(rgb):
        return "#%02x%02x%02x" % rgb

    r, g, b = hex_to_rgb(hex_color)
    tr, tg, tb = hex_to_rgb(threshold)

    if r >= tr and g >= tg and b >= tb:
        return threshold.upper()
    return hex_color.upper()

def open_preview_window(app):
    SECTIONS = ["Left Shoulder", "Right Shoulder", "Gothic Numerals", "Imperial Numerals"]
    grid_cells = app.grid_cells

    preview_win = tk.Toplevel(app)
    preview_win.title("Printable A5 Preview")
    preview_win.configure(bg=COLOR_BG)

    PREVIEW_W, PREVIEW_H = 900, 636
    preview_win.geometry(f"{PREVIEW_W}x{PREVIEW_H + 48}")

    toolbar = tk.Frame(preview_win, bg="#222")
    toolbar.pack(side="top", fill="x")

    tk.Button(
        toolbar,
        text="📄 Print A5 (PDF)",
        command=lambda: export_preview_to_a5_pdf(grid_cells),
        bg="#444",
        fg="white",
        relief="flat",
        padx=10,
        pady=5
    ).pack(side="left", padx=10, pady=5)
    tk.Button(
        toolbar,
        text="📄 Print A4 (half) (PDF)",
        command=lambda: export_preview_to_pdf(grid_cells),
        bg="#444", fg="white", relief="flat", padx=10, pady=5
    ).pack(side="left", padx=10, pady=5)
    tk.Button(
        toolbar,
        text="📄 Print A4 (full) (PDF)",
        command=lambda: export_half_a4_to_full_a4_pdf(grid_cells),
        bg="#444", fg="white", relief="flat", padx=10, pady=5
    ).pack(side="left", padx=10, pady=5)

    checker = Image.new("RGB", (PREVIEW_W, PREVIEW_H), "#222222")
    check_size = 10
    draw = ImageDraw.Draw(checker)

    for y in range(0, PREVIEW_H, check_size):
        for x in range(0, PREVIEW_W, check_size):
            if (x // check_size + y // check_size) % 2 == 0:
                draw.rectangle([x, y, x + check_size, y + check_size], fill="#333333")

    checker_tk = ImageTk.PhotoImage(checker)
    canvas_widget = tk.Canvas(preview_win, width=PREVIEW_W, height=PREVIEW_H, highlightthickness=0)
    canvas_widget.pack()
    canvas_widget.create_image(0, 0, anchor="nw", image=checker_tk)
    canvas_widget._bg_ref = checker_tk
    canvas_widget.pack()

    quadrant_w = PREVIEW_W // 2
    quadrant_h = PREVIEW_H // 2

    if not hasattr(canvas_widget, "_icon_refs"):
        canvas_widget._icon_refs = []

    for i, section in enumerate(SECTIONS):
        base_x = (i % 2) * quadrant_w
        base_y = (i // 2) * quadrant_h

        row_h = (quadrant_h - 10) // GRID_ROWS
        col_w = (quadrant_w - 20) // GRID_COLUMNS

        for (r, c), cell in grid_cells[section].items():
            x = base_x + c * (col_w + 2)
            y = base_y + r * (row_h + 2)

            if isinstance(cell.content, str):
                text_color = cell.tint or "#000000"
                font_tuple = (cell.font[0], 14) if isinstance(cell.font, tuple) else (FONT_DEFAULT, 16)
                canvas_widget.create_text(
                    x + col_w // 2,
                    y + row_h // 2,
                    text=cell.content,
                    fill=text_color,
                    font=font_tuple
                )

            elif cell.icon_path:
                try:
                    tint_color = cell.tint or "#E425B4FF"
                    icon_img = get_cached_icon(
                        cell.icon_path,
                        size=(col_w, row_h),
                        color=tint_color
                    )
                    PADDING = 8  # pixels (approx 2mm at 300 DPI → ≈ 7.5–8px)
                    canvas_widget.create_image(x + PADDING, y + PADDING, anchor="nw", image=icon_img)
                    canvas_widget._icon_refs.append(icon_img)
                except Exception as e:
                    print(f"[ERROR] Failed to render icon: {e}")

def export_preview_to_pdf(grid_cells, canvas_obj=None, offset_y=0):
    from reportlab.lib.pagesizes import A4

    pdf_w, pdf_h = A4
    margin = 5 * mm
    icon_diameter = 6 * mm
    icon_zigzag_offset = 10 * mm
    font_size_pt = int(3.7 * 2.835)

    usable_width = pdf_w - 2 * margin
    usable_height = (pdf_h / 2) - 2 * margin
    section_h = usable_height / 4
    cell_h = section_h / GRID_ROWS
    cell_w = usable_width / GRID_COLUMNS

    temp_pdf = None
    if canvas_obj is None:
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        c = canvas.Canvas(temp_pdf.name, pagesize=A4)
    else:
        c = canvas_obj

    SECTIONS = ["Left Shoulder", "Right Shoulder", "Gothic Numerals", "Imperial Numerals"]

    for i, section in enumerate(SECTIONS):
        section_y = offset_y + margin + (3 - i) * section_h
        is_icon_section = "Shoulder" in section

        for (r, col), cell in grid_cells[section].items():
            horizontal_offset = -icon_zigzag_offset if (is_icon_section and r % 2 == 1) else 0
            x = margin + horizontal_offset + col * cell_w
            y = section_y + (GRID_ROWS - 1 - r) * cell_h

            if isinstance(cell.content, str):
                font_name = cell.font[0] if isinstance(cell.font, tuple) else "Helvetica"
                safe_color = clamp_whites(cell.tint or "#000000")
                c.setFillColor(safe_color)
                try:
                    c.setFont(font_name, font_size_pt)
                except:
                    font_path = os.path.join("fonts", f"{font_name}.ttf")
                    if os.path.isfile(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont(font_name, font_path))
                            c.setFont(font_name, font_size_pt)
                        except Exception as e:
                            print(f"[WARN] Font fallback: {e}")
                            c.setFont("Helvetica", font_size_pt)
                    else:
                        c.setFont("Helvetica", font_size_pt)

                c.drawCentredString(x + cell_w / 2, y + cell_h / 2 - font_size_pt / 4, cell.content)

            elif cell.icon_path:
                try:
                    safe_color = clamp_whites(cell.tint or "#000000")
                    svg_str = tint_svg(cell.icon_path, safe_color)
                    icon_x = x + (cell_w - icon_diameter) / 2
                    icon_y = y + (cell_h - icon_diameter) / 2
                    draw_svg_to_pdf(c, svg_str, icon_x, icon_y, icon_diameter, icon_diameter)
                except Exception as e:
                    print(f"[ERROR] Could not embed icon in PDF: {e}")

    if canvas_obj is None:
        c.showPage()
        c.save()
        temp_pdf.close()
        trigger_pdf_print_dialog(temp_pdf.name)

def export_half_a4_to_full_a4_pdf(grid_cells):

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_pdf.name, pagesize=A4)

    # Render top half
    export_preview_to_pdf(grid_cells, canvas_obj=c, offset_y=0)

    # Duplicate top half onto bottom half
    export_preview_to_pdf(grid_cells, canvas_obj=c, offset_y=A4[1] / 2)

    c.showPage()
    c.save()
    temp_pdf.close()
    trigger_pdf_print_dialog(temp_pdf.name)

def export_preview_to_a5_pdf(grid_cells):

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_pdf.name, pagesize=landscape(A5))

    # Just reuse the top-half rendering logic directly
    export_preview_to_pdf(grid_cells, canvas_obj=c, offset_y=0)

    c.showPage()
    c.save()
    temp_pdf.close()
    trigger_pdf_print_dialog(temp_pdf.name)

