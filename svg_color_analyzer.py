import tkinter as tk
from tkinter import Canvas, Frame, Label, Button, colorchooser, Entry, Scrollbar
import xml.etree.ElementTree as ET
from PIL import Image, ImageTk
import cairosvg
import io
import re
import copy

SVG_FILE = "sample.svg"
COLOR_REGEX = re.compile(r'#(?:[0-9a-fA-F]{3}){1,2}\b|rgb\(.+?\)|rgba\(.+?\)')

original_svg_tree = None
path_color_map = {}
color_usage_map = {}
zoom_factor = 1.0
ZOOM_MIN = 0.5
ZOOM_MAX = 3.0
BG_COLOR = "#1e1e1e"
FG_COLOR = "#d0d0d0"
BTN_COLOR = "#333333"
TITLEBAR_BG = "#121212"
TITLEBAR_LABEL_BG = "#111111"
TITLEBAR_FG = "white"
BTN_BAR_BG = "#222"


def extract_colors_and_map(svg_content):
    global original_svg_tree, path_color_map, color_usage_map
    root = ET.fromstring(svg_content)
    original_svg_tree = copy.deepcopy(root)
    path_color_map.clear()
    color_usage_map.clear()
    colors = set()

    def search_colors(element):
        current_id = id(element)
        for attr in ('fill', 'stroke'):
            val = element.attrib.get(attr)
            if val and val != 'none':
                match = COLOR_REGEX.match(val.strip())
                if match:
                    color = match.group()
                    colors.add(color)
                    path_color_map.setdefault(current_id, {})[attr] = color
                    color_usage_map.setdefault(color, []).append((element, attr))
        for child in element:
            search_colors(child)

    search_colors(root)
    return root, sorted(colors)


def render_svg_tree_to_image(svg_tree, zoom=1.0):
    base_width, base_height = 256, 256
    width, height = int(base_width * zoom), int(base_height * zoom)
    svg_bytes = ET.tostring(svg_tree, encoding='utf-8', method='xml')
    png_data = cairosvg.svg2png(bytestring=svg_bytes, output_width=width, output_height=height)
    return Image.open(io.BytesIO(png_data)), width, height


def create_checkerboard(width, height, box_size=8):
    bg = Image.new('RGB', (width, height), 'white')
    for y in range(0, height, box_size):
        for x in range(0, width, box_size):
            if (x // box_size + y // box_size) % 2 == 0:
                for i in range(box_size):
                    for j in range(box_size):
                        if x + i < width and y + j < height:
                            bg.putpixel((x + i, y + j), (64, 64, 64))
    return bg


def main():
    global original_svg_tree, color_usage_map, zoom_factor

    root = tk.Tk()
    root.title("SVG Color Analyzer")
    root.configure(bg=BG_COLOR)
    root.overrideredirect(True)

    # Center the window on the screen
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = 350
    window_height = 600
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def start_move(event):
        root.x = event.x
        root.y = event.y

    def do_move(event):
        x = root.winfo_pointerx() - root.x
        y = root.winfo_pointery() - root.y
        root.geometry(f"+{x}+{y}")

    titlebar = tk.Frame(root, bg=TITLEBAR_BG, height=32)
    titlebar.pack(fill="x", side="top")
    titlebar.bind("<Button-1>", start_move)
    titlebar.bind("<B1-Motion>", do_move)

    btn_close = tk.Button(titlebar, text="✕", bg=BTN_BAR_BG, fg="white", command=root.quit, relief="flat", bd=0, width=3, height=1)
    btn_close.pack(side="right", padx=2, pady=2)

    btn_min = tk.Button(titlebar, text="━", bg=BTN_BAR_BG, fg="white", command=root.iconify, relief="flat", bd=0, width=3, height=1)
    btn_min.pack(side="right", padx=2, pady=2)

    title_label = tk.Label(titlebar, text="SVG Color Analyzer", bg=TITLEBAR_LABEL_BG, fg=TITLEBAR_FG, font=("Arial", 10, "bold"))
    title_label.pack(side="left", padx=10)
    title_label.bind("<Button-1>", start_move)
    title_label.bind("<B1-Motion>", do_move)

    frame = Frame(root, bg=BG_COLOR)
    frame.pack(padx=10, pady=10)

    canvas_frame = Frame(frame, bg=BG_COLOR)
    canvas_frame.grid(row=0, column=0, columnspan=3)

    canvas = Canvas(canvas_frame, width=256, height=256, bg='black', highlightthickness=0)
    canvas.grid(row=0, column=0)

    hbar = Scrollbar(canvas_frame, orient='horizontal', command=canvas.xview)
    hbar.grid(row=1, column=0, sticky='ew')
    vbar = Scrollbar(canvas_frame, orient='vertical', command=canvas.yview)
    vbar.grid(row=0, column=1, sticky='ns')
    canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set, scrollregion=(0, 0, 256, 256))

    zoom_controls = Frame(frame, bg=BG_COLOR)
    zoom_controls.grid(row=1, column=0, pady=5, sticky='w')
    Label(zoom_controls, text="Zoom %:", fg=FG_COLOR, bg=BG_COLOR).pack(side='left')
    zoom_entry = Entry(zoom_controls, width=5, bg=BTN_COLOR, fg=FG_COLOR, insertbackground=FG_COLOR)
    zoom_entry.insert(0, "100")
    zoom_entry.pack(side='left')

    def apply_zoom():
        nonlocal tk_img, svg_tree, canvas_img_id
        global zoom_factor
        try:
            new_zoom = float(zoom_entry.get()) / 100.0
            if ZOOM_MIN <= new_zoom <= ZOOM_MAX:
                zoom_factor = new_zoom
                update_preview()
        except ValueError:
            pass

    Button(zoom_controls, text="Apply", command=apply_zoom, bg=BTN_COLOR, fg=FG_COLOR).pack(side='left', padx=5)
    Button(zoom_controls, text="Reset", command=lambda: (zoom_entry.delete(0, tk.END), zoom_entry.insert(0, "100"), apply_zoom()), bg=BTN_COLOR, fg=FG_COLOR).pack(side='left')

    with open(SVG_FILE, 'r', encoding='utf-8') as f:
        svg_raw = f.read()

    svg_tree, colors = extract_colors_and_map(svg_raw)

    rendered, width, height = render_svg_tree_to_image(svg_tree, zoom_factor)
    checker = create_checkerboard(width, height)
    combined = checker.copy()
    combined.paste(rendered, (0, 0), rendered.convert('RGBA'))
    tk_img = ImageTk.PhotoImage(combined)
    canvas_img_id = canvas.create_image(0, 0, anchor='nw', image=tk_img)

    def update_preview(center_scroll=False):
        nonlocal svg_tree, tk_img, canvas_img_id
        global zoom_factor
        rendered, width, height = render_svg_tree_to_image(svg_tree, zoom_factor)
        checker = create_checkerboard(width, height)
        combined = checker.copy()
        combined.paste(rendered, (0, 0), rendered.convert('RGBA'))
        tk_img = ImageTk.PhotoImage(combined)
        canvas.config(scrollregion=(0, 0, width, height))
        canvas.delete("all")
        canvas_img_id = canvas.create_image(0, 0, anchor='nw', image=tk_img)
        if center_scroll:
            canvas.xview_moveto((width / 2 - 128) / width)
            canvas.yview_moveto((height / 2 - 128) / height)

    def pick_new_color(old_color):
        new_color = colorchooser.askcolor(title=f"Replace {old_color}", initialcolor=old_color)[1]
        if new_color:
            for element, attr in color_usage_map.get(old_color, []):
                element.set(attr, new_color)
            color_usage_map[new_color] = color_usage_map.pop(old_color)
            update_preview()
            refresh_color_list()

    def reset_colors():
        nonlocal svg_tree, tk_img
        svg_tree = copy.deepcopy(original_svg_tree)
        svg_tree, _ = extract_colors_and_map(ET.tostring(svg_tree, encoding='unicode'))
        update_preview(center_scroll=True)
        refresh_color_list()

    def on_mousewheel(event):
        global zoom_factor
        direction = 1 if event.delta > 0 else -1
        zoom_factor += direction * 0.1
        zoom_factor = max(ZOOM_MIN, min(ZOOM_MAX, zoom_factor))
        zoom_entry.delete(0, tk.END)
        zoom_entry.insert(0, f"{int(zoom_factor * 100)}")
        update_preview(center_scroll=True)

    canvas.bind_all("<MouseWheel>", on_mousewheel)

    color_list_frame = Frame(root, bg=BG_COLOR)
    color_list_frame.pack(pady=10)

    def refresh_color_list():
        for widget in color_list_frame.winfo_children():
            widget.destroy()
        Label(color_list_frame, text=f"Colors found: {len(color_usage_map)}", fg=FG_COLOR, bg=BG_COLOR).pack(anchor='w')
        for color in sorted(color_usage_map.keys()):
            row = Frame(color_list_frame, bg=BG_COLOR)
            row.pack(anchor='w', pady=2, padx=10)
            swatch = Canvas(row, width=24, height=24, bg=color, highlightthickness=1, highlightbackground='black')
            swatch.pack(side='left')
            Label(row, text=color, font=('Arial', 10), fg=FG_COLOR, bg=BG_COLOR).pack(side='left', padx=10)
            Button(row, text="Change", command=lambda c=color: pick_new_color(c), bg=BTN_COLOR, fg=FG_COLOR).pack(side='left')

    Button(root, text="Reset Colors", command=reset_colors, bg=BTN_COLOR, fg=FG_COLOR).pack(pady=5)

    refresh_color_list()
    root.mainloop()


if __name__ == '__main__':
    main()