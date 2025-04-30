import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, simpledialog, font, messagebox
import json
import os
import io
from PIL import Image, ImageTk, ImageFont, ImageDraw
import cairosvg
from functools import partial
from collections import defaultdict

# --- Constants ---
APP_WIDTH = 1200
APP_HEIGHT = 700
GRID_COLUMNS = 10
GRID_ROWS = 5
CELL_SIZE = 60
SECTIONS = ["Left Shoulder", "Right Shoulder", "Gothic Numerals", "Imperial Numerals"]
COLOR_BG = "#1e1e1e"
COLOR_FG = "#ffffff"
ICON_DIR = "icons"

# --- Global Icon Cache ---
ICON_CACHE = {}

# --- Helper Functions ---
from icon_parsing import load_icon_entries  # replaces internal loader

def tint_image(image, color):
    image = image.convert("RGBA")
    overlay = Image.new("RGBA", image.size, color)
    return Image.alpha_composite(image, overlay)

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

# --- Font Picker Dialog ---
class FontPickerDialog(tk.Toplevel):
    def __init__(self, master, section, row):
        super().__init__(master)
        self.title(f"Pick Font: {section} Row {row+1}")
        self.configure(bg=COLOR_BG)
        self.section, self.row = section, row
        self.result = None
        self.selected_index = None
        self.hover_index = None

        self.fonts = [f for f in os.listdir("fonts") if f.lower().endswith(('.ttf','.otf'))]

        self.canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_hover)

        self.draw_font_list()

        btnf = tk.Frame(self, bg=COLOR_BG)
        btnf.pack(pady=5)
        tk.Button(btnf, text="Cancel", command=self.destroy, bg="#333", fg=COLOR_FG, relief="flat").pack(side="left", padx=5)
        tk.Button(btnf, text="Apply", command=self.apply, bg="#333", fg=COLOR_FG, relief="flat").pack(side="right", padx=5)

    def draw_font_list(self):
        self.canvas.delete("all")
        y = 20
        self.items = []

        for idx, fname in enumerate(self.fonts):
            name = os.path.splitext(fname)[0]
            path = os.path.join("fonts", fname)
            try:
                if os.name == 'nt':
                    import ctypes
                    ctypes.windll.gdi32.AddFontResourceExW(path, 0x10, 0)
                pil_font = ImageFont.truetype(path, size=16)
                family = pil_font.getname()[0]
                font_obj = font.Font(family=family, size=16)
            except Exception:
                font_obj = font.Font(family="Arial", size=16)

            color = COLOR_FG if idx != self.hover_index else "#66ccff"
            self.canvas.create_text(30, y, anchor='w', text=f"{name} - IX 3", font=font_obj, fill=color)
            self.items.append((y - 10, y + 20, idx))
            y += 40

        self.canvas.config(scrollregion=(0, 0, 500, y))

    def on_click(self, event):
        for top, bottom, idx in self.items:
            if top <= event.y <= bottom:
                self.selected_index = idx
                self.result = self.fonts[idx]
                self.destroy()
                break

    def on_hover(self, event):
        new_hover = None
        for top, bottom, idx in self.items:
            if top <= event.y <= bottom:
                new_hover = idx
                break
        if new_hover != self.hover_index:
            self.hover_index = new_hover
            self.draw_font_list()

    def apply(self):
        if self.selected_index is not None:
            self.result = self.fonts[self.selected_index]
        self.destroy()

# --- Icon Picker Dialog ---
class IconPickerDialog(tk.Toplevel):
    def __init__(self, parent, icon_entries):
        super().__init__(parent)
        self.title("Choose an Icon")
        self.icon_entries = icon_entries
        self.filtered_entries = icon_entries
        self.result = None
        self.selected_frame = None
        self.configure(bg=COLOR_BG)
        self.resizable(False, True)
    def __init__(self, parent, icon_entries):
        super().__init__(parent)
        self.title("Choose an Icon")
        self.icon_entries = icon_entries
        self.filtered_entries = icon_entries
        self.result = None
        self.configure(bg=COLOR_BG)
        self.resizable(False, True)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.apply_filter())

        search_entry = ttk.Entry(self, textvariable=self.search_var)
        search_entry.pack(fill="x", padx=5, pady=(5, 0))
        search_entry.focus()

        self.canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_BG)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.populate_icons()

    def render_tag_pills(self, parent, tags):
        for tag in tags:
            tag_label = tk.Label(parent, text=tag, bg="#444", fg="white",
                                 font=("Arial", 8, "bold"), padx=5, pady=1,
                                 relief="solid", borderwidth=1)
            tag_label.pack(side="left", padx=2, pady=2)

    def populate_icons(self):
        for entry in self.filtered_entries:
            img = get_cached_icon(entry['file'])

            frame = tk.Frame(self.scrollable_frame, bg="#333", highlightbackground="#555", highlightthickness=1)
            frame.pack(fill="x", padx=6, pady=4)

            def on_enter(e, f=frame):
                if f != self.selected_frame:
                    f.configure(bg="#444")

            def on_leave(e, f=frame):
                if f != self.selected_frame:
                    f.configure(bg="#333")

            frame.bind("<Enter>", on_enter)
            frame.bind("<Leave>", on_leave)

            icon_label = tk.Label(frame, image=img, bg="#333")
            icon_label.image = img
            icon_label.grid(row=0, column=0, rowspan=2, padx=5, pady=5)

            title_label = tk.Label(frame, text=entry['name'], fg="white", bg="#333",
                                   font=("Arial", 10, "bold"), anchor="w", justify="left")
            title_label.grid(row=0, column=1, sticky="w")

            tag_frame = tk.Frame(frame, bg="#333")
            tag_frame.grid(row=1, column=1, sticky="w")
            self.render_tag_pills(tag_frame, entry['tags'])

            def bind_click(e, ent=entry, fr=frame):
                self.select_icon(ent, fr)

            for widget in (frame, icon_label, title_label, tag_frame):
                widget.bind("<Button-1>", bind_click)
            icon_label.bind("<Button-1>", bind_click)
            title_label.bind("<Button-1>", bind_click)
            tag_frame.bind("<Button-1>", bind_click)

    def select_icon(self, icon_entry, frame):
        self.result = icon_entry
        if self.selected_frame:
            self.selected_frame.configure(bg="#333")
        self.selected_frame = frame
        frame.configure(bg="#1f6aa5")

# --- Icon Cell Widget ---
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, bg="#111", fg="white",
                         relief="solid", borderwidth=1,
                         font=("Arial", 10, "normal"), padx=6, pady=3)
        label.pack(ipadx=6, ipady=3)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None


class IconCell(tk.Frame):
    def __init__(self, master, row, col):
        super().__init__(master, width=CELL_SIZE, height=CELL_SIZE, bg=COLOR_BG)
        self.grid_propagate(False)
        self.row = row
        self.col = col
        self.content = None
        self.icon_path = None
        self.font = ("Arial", 10, "bold")
        self.text_color = COLOR_FG

        self.canvas = tk.Canvas(self, width=CELL_SIZE-6, height=CELL_SIZE-6,
                                highlightthickness=0, bg=COLOR_BG)
        self.canvas.place(x=3, y=3)

    def set_icon(self, image, path=None):
        self.content = image
        self.icon_path = path
        self.canvas.delete("all")
        self.canvas.create_image(
            (CELL_SIZE - 6) // 2,
            (CELL_SIZE - 6) // 2,
            image=image,
            anchor="center"
        )
        self.canvas.image = image
        self.text_color = None

    def set_text(self, text, font=None, color=COLOR_FG):
        self.content = text
        if font:
            self.font = font
        self.text_color = color
        self.canvas.delete("all")
        self.canvas.create_text(
            (CELL_SIZE - 6) // 2,
            (CELL_SIZE - 6) // 2,
            text=text,
            font=self.font,
            fill=color,
            anchor="center"
        )

    def highlight(self, color="#1f6aa5"):
        self.configure(bg=color)

    def unhighlight(self):
        self.configure(bg=COLOR_BG)
        self.configure(bg=COLOR_BG)


# --- GUI Application ---
class IconGridApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self._maximized = False
        self.title("Lienzo - WH40K Decal Editor")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.configure(bg=COLOR_BG)
        self.grid_cells = defaultdict(dict)
        self.icon_entries = load_icon_entries(ICON_DIR)

        self.create_titlebar()
        self.create_toolbar()
        self.create_widgets()
        self.prefill_numerals()
        self.bind_events()

    def create_titlebar(self):
        self.overrideredirect(True)

        self.titlebar = tk.Frame(self, bg="#121212", height=32)
        self.titlebar.pack(fill="x", side="top")
        self.titlebar.bind("<Button-1>", self.start_move)
        self.titlebar.bind("<B1-Motion>", self.do_move)

        title_label = tk.Label(self.titlebar, text="Astartes Decal Customizator",
                               bg="#111111", fg="white", font=("Arial", 14, "bold"))
        title_label.pack(side="left", padx=10)
        title_label.bind("<Button-1>", self.start_move)
        title_label.bind("<B1-Motion>", self.do_move)

        btn_close = tk.Button(self.titlebar, text="✕", bg="#222", fg="white", command=self.quit,
                              relief="flat", bd=0, width=3, height=1)
        btn_close.pack(side="right", padx=2, pady=2)

        btn_max = tk.Button(self.titlebar, text="🗖", bg="#222", fg="white", command=self.toggle_maximize,
                            relief="flat", bd=0, width=3, height=1)
        btn_max.pack(side="right", padx=2, pady=2)

        btn_min = tk.Button(self.titlebar, text="━", bg="#222", fg="white", command=self.iconify,
                            relief="flat", bd=0, width=3, height=1)
        btn_min.pack(side="right", padx=2, pady=2)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        x = event.x_root - self.x
        y = event.y_root - self.y
        self.geometry(f"+{x}+{y}")

    def toggle_maximize(self):
        if hasattr(self, '_maximized') and self._maximized:
            self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
            self._maximized = False
        else:
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            self._maximized = True

    def create_toolbar(self):
        self.toolbar = tk.Frame(self, bg="#111111", height=30)
        self.generate_button = tk.Button(
            self.toolbar, text="Generate Preview", bg="#111111", fg="white",
            font=("Arial", 12), relief="flat", bd=0,
            activebackground="#333333", activeforeground="white",
            command=self.open_preview_window
        )
        self.generate_button.pack(side="left", padx=5)
        self.toolbar.pack(fill="x", side="top")

        self.file_button = tk.Button(
            self.toolbar, text="File", bg="#111111", fg="white",
            font=("Arial", 12), relief="flat", bd=0,
            activebackground="#333333", activeforeground="white",
            command=self.toggle_file_menu
        )
        self.file_button.pack(side="left", padx=5)

        self.file_menu_frame = tk.Frame(self, bg="#222222", bd=1, relief="solid")
        self.file_menu_visible = False
        self.create_file_menu()

    def create_file_menu(self):
        def bind_hover(btn):
            btn.bind("<Enter>", lambda e: btn.configure(bg="#333333"))
            btn.bind("<Leave>", lambda e: btn.configure(bg="#222222"))

        btns = [
            ("Load Layout", self.load_layout),
            ("Save Layout", self.save_layout),
            ("About", self.open_about),
            ("Exit", self.quit)
        ]
        for text, cmd in btns:
            btn = tk.Button(self.file_menu_frame, text=text, bg="#222222", fg="white",
                            anchor="w", relief="flat", command=cmd, font=("Arial", 12))
            btn.pack(fill="x", padx=5, pady=2)
            bind_hover(btn)

    def toggle_file_menu(self):
        if self.file_menu_visible:
            self.file_menu_frame.place_forget()
            self.file_menu_visible = False
        else:
            x = self.file_button.winfo_rootx() - self.winfo_rootx()
            y = self.titlebar.winfo_height() + self.toolbar.winfo_height()
            self.file_menu_frame.place(x=x, y=y)
            self.file_menu_frame.lift()
            self.file_menu_frame.focus_set()
            self.file_menu_frame.bind("<FocusOut>", lambda e: self.toggle_file_menu())
            self.file_menu_frame.bind("<Escape>", lambda e: self.toggle_file_menu())
            self.file_menu_visible = True

    def prefill_numerals(self):
        gothic = [str(i + 1) for i in range(GRID_COLUMNS)]
        imperial = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
        for c in range(GRID_COLUMNS):
            for r in range(GRID_ROWS):
                if "Gothic Numerals" in self.grid_cells:
                    self.grid_cells["Gothic Numerals"][(r, c)].set_text(gothic[c])
                if "Imperial Numerals" in self.grid_cells:
                    self.grid_cells["Imperial Numerals"][(r, c)].set_text(imperial[c])

    def create_widgets(self):
        self.content_frame = tk.Frame(self, bg=COLOR_BG)
        self.content_frame.pack(fill="both", expand=True)

        self.canvas_frame = tk.Frame(self.content_frame, bg=COLOR_BG)
        self.canvas_frame.grid(row=0, column=0, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(1, weight=1)
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_rowconfigure(1, weight=1)

        positions = {
            "Left Shoulder": (0, 0),
            "Right Shoulder": (0, 1),
            "Gothic Numerals": (1, 0),
            "Imperial Numerals": (1, 1)
        }

        for section, (grid_r, grid_c) in positions.items():
            section_frame = tk.Frame(self.canvas_frame, bg=COLOR_BG)
            section_frame.grid(row=grid_r, column=grid_c, padx=10, pady=10, sticky="n")

            section_label = ttk.Label(section_frame, text=section, background=COLOR_BG, foreground=COLOR_FG)
            section_label.pack(anchor="w", pady=(10, 0))

            for row in range(GRID_ROWS):
                control_frame = tk.Frame(section_frame, bg=COLOR_BG)
                control_frame.grid(row=row, column=0, sticky="w", padx=5, pady=2)

                if section in ("Left Shoulder", "Right Shoulder"):
                    icon_btn = tk.Button(control_frame, text="🖼️", command=lambda s=section, r=row: self.pick_icon_for_row(s, r))
                    Tooltip(icon_btn, "Pick Icon")
                    icon_btn.grid(row=0, column=0, padx=2, pady=1, sticky="w")

                if section in ("Gothic Numerals", "Imperial Numerals"):
                    font_btn = tk.Button(control_frame, text="🖋️", command=lambda s=section, r=row: self.pick_font_for_row(s, r))
                    Tooltip(font_btn, "Pick Font")
                    font_btn.grid(row=0, column=1, padx=2, pady=1, sticky="w")

                color_btn = tk.Button(control_frame, text="🎨", command=lambda s=section, r=row: self.pick_color_for_row(s, r))
                Tooltip(color_btn, "Pick Color")
                color_btn.grid(row=0, column=2, padx=2, pady=1, sticky="w")

                grid_frame = tk.Frame(control_frame, bg=COLOR_BG)
                grid_frame.grid(row=0, column=3, sticky="w", padx=5)

                for col in range(GRID_COLUMNS):
                    cell = IconCell(grid_frame, row, col)
                    cell.grid(row=0, column=col, padx=1, pady=1)
                    self.grid_cells[section][(row, col)] = cell

    def pick_font_for_row(self, section, row):
        dialog = FontPickerDialog(self, section, row)
        self.wait_window(dialog)
        if not dialog.result:
            return

        font_path = os.path.join("fonts", dialog.result)
        try:
            if os.name == 'nt':
                import ctypes
                ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
            pil_font = ImageFont.truetype(font_path, size=12)
            family = pil_font.getname()[0]
            font_value = (family, 10, 'bold') if section == "Imperial Numerals" else (family, 10)
        except Exception:
            font_value = ("Arial", 10)

        apply_all = messagebox.askyesno("Apply to All?", "Apply this font to all rows in this section?")
        rows = range(GRID_ROWS) if apply_all else [row]

        for r in rows:
            for c in range(GRID_COLUMNS):
                cell = self.grid_cells[section][(r, c)]
                if isinstance(cell.content, str):
                    cell.set_text(cell.content, font=font_value)

    def pick_color_for_row(self, section, row):
        current_color = self.get_row_color(section, row)
        color = colorchooser.askcolor(title="Pick color", color=current_color)[1]
        if not color:
            return

        apply_all = messagebox.askyesno("Apply to All?", "Apply this color to all rows in this section?")
        rows = range(GRID_ROWS) if apply_all else [row]

        for r in rows:
            for c in range(GRID_COLUMNS):
                cell = self.grid_cells[section][(r, c)]
                if isinstance(cell.content, str):
                    cell.set_text(cell.content, color=color)
                elif cell.icon_path:
                    tinted_img = get_cached_icon(cell.icon_path, size=(CELL_SIZE - 6, CELL_SIZE - 6), color=color)
                    cell.set_icon(tinted_img, path=cell.icon_path)

    def pick_icon_for_row(self, section, row):
        dialog = IconPickerDialog(self, self.icon_entries)
        self.wait_window(dialog)
        if not dialog.result:
            return

        apply_all = messagebox.askyesno("Apply to All?", "Apply this icon to all rows in this section?")
        rows = range(GRID_ROWS) if apply_all else [row]

        for r in rows:
            for c in range(GRID_COLUMNS):
                img = get_cached_icon(dialog.result['file'], size=(CELL_SIZE - 6, CELL_SIZE - 6))
                cell = self.grid_cells[section][(r, c)]
                cell.set_icon(img, path=dialog.result['file'])

    def save_layout(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Save Layout As..."
        )
        if not filepath:
            return
        layout = {}
        for section, cells in self.grid_cells.items():
            layout[section] = {}
            for (row, col), cell in cells.items():
                data = {}
                if isinstance(cell.content, str):
                    data["text"] = cell.content
                    data["font"] = cell.font
                    data["color"] = cell.canvas.itemcget("all", "fill") or COLOR_FG
                elif cell.icon_path:
                    data["icon_file"] = cell.icon_path
                if data:
                    layout[section][f"{row},{col}"] = data
        with open(filepath, "w") as f:
            json.dump(layout, f, indent=2)

    def load_layout(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not filepath:
            return
        with open(filepath) as f:
            layout = json.load(f)
        for section, cells in layout.items():
            for coord, data in cells.items():
                row, col = map(int, coord.split(","))
                icon_data = {"file": data["icon_file"]} if data.get("icon_file") else None
                self.set_cell_content(
                    section, row, col,
                    icon=icon_data,
                    text=data.get("text"),
                    font_name=data.get("font"),
                    color=data.get("color")
                )

    def open_preview_window(self):
        preview_win = tk.Toplevel(self)
        preview_win.title("Printable A5 Preview")
        preview_win.configure(bg=COLOR_BG)
        preview_win.geometry("900x650")

        canvas = tk.Canvas(preview_win, bg="white", width=1748, height=2480)  # A5 at 300 DPI
        canvas.pack()

        sheet = Image.new("RGB", (1748, 2480), "white")
        draw = ImageDraw.Draw(sheet)

        x_offset, y_offset = 50, 50
        cell_px = 100
        pad = 10

        for section, cells in self.grid_cells.items():
            draw.text((x_offset, y_offset - 30), section, fill="black")
            for (row, col), cell in cells.items():
                x = x_offset + col * (cell_px + pad)
                y = y_offset + row * (cell_px + pad)

                if isinstance(cell.content, str):
                    draw.text((x + 20, y + 35), cell.content, fill=cell.text_color or "black")
                elif cell.icon_path:
                    try:
                        png_data = cairosvg.svg2png(url=cell.icon_path, output_width=cell_px, output_height=cell_px)
                        icon = Image.open(io.BytesIO(png_data)).convert("RGBA")
                        sheet.paste(icon, (x, y), icon)
                    except Exception as e:
                        print(f"[ERROR] Could not render icon: {e}")

        preview_img = ImageTk.PhotoImage(sheet.resize((900, 1277)))
        canvas.create_image(0, 0, anchor="nw", image=preview_img)
        canvas.image = preview_img


    def open_about(self):
        about_win = tk.Toplevel(self)
        about_win.title("About Astartes Decal Customizator")
        about_win.configure(bg=COLOR_BG)
        about_win.geometry("600x600")
        about_win.resizable(False, False)

        try:
            font_path = os.path.join("fonts", "CaslonAntique.ttf")
            if os.name == 'nt':
                import ctypes
                ctypes.windll.gdi32.AddFontResourceExW(font_path, 0x10, 0)
            pil_font = ImageFont.truetype(font_path, size=18)
            family = pil_font.getname()[0]
            text_font = (family, 18)
        except Exception:
            text_font = ("Times New Roman", 12)

        try:
            logo_path = os.path.join(ICON_DIR, "chapter_logo.png")
            raw_logo = Image.open(logo_path).convert("RGBA")
            raw_logo.thumbnail((100, 100))
            alpha = raw_logo.split()[3].point(lambda p: p * 0.2)
            raw_logo.putalpha(alpha)
            logo_img = ImageTk.PhotoImage(raw_logo)
            logo_label = tk.Label(about_win, image=logo_img, bg=COLOR_BG)
            logo_label.image = logo_img
            logo_label.pack(pady=(10, 0))
        except Exception as e:
            print(f"[WARN] Could not load logo: {e}")

        text = """Astartes Decal Customizator

This tool was developed by Eric Cugota (GitHub: tryadelion)
with inspiration and resources from the Bolter and Chainsword community.

Includes work from:
- Caliban Angelus Font (creator unknown)
- Caslon Antique Font (Berne Nadall, 1894)
- Grimworld 40K's icon library by Bishop Greisyn and Abomination
- And moral support from my cat Morgana 🐾

Published under the MIT License.
No ownership is claimed over included resources.
No affiliation with Games Workshop.

Repository link pending. Contributions and feedback welcome!"""
        

        label = tk.Label(about_win, text=text, bg=COLOR_BG, fg="white",
                         font=text_font, justify="left", wraplength=560, anchor="n")
        label.pack(padx=20, pady=20)

        close_btn = tk.Button(about_win, text="Close", command=about_win.destroy,
                              bg="#333", fg="white", relief="flat")
        close_btn.pack(pady=10)


    def bind_events(self):
        self.bind("<Control-s>", lambda e: self.save_layout())
        self.bind("<Control-o>", lambda e: self.load_layout())
    
    def set_cell_content(self, section, row, col, *, icon=None, text=None, font_name=None, color=None):
        cell = self.grid_cells[section][(row, col)]
        if icon:
            img = get_cached_icon(icon['file'], size=(CELL_SIZE - 6, CELL_SIZE - 6), color=color or COLOR_FG)
            cell.set_icon(img, path=icon['file'])
        elif text:
            font_tuple = (font_name, 10) if font_name else cell.font
            cell.set_text(text, font=font_tuple, color=color or COLOR_FG)
        if font_name:
            cell.font = (font_name, 10)
        if color:
            pass  # already applied via set_text or set_icon
            # btn.config(fg=color)  # color applied inside set_text or set_icon
        # You may want to update this depending on IconCell logic
            cell["color"] = color

if __name__ == "__main__":
    app = IconGridApp()
    app.mainloop()