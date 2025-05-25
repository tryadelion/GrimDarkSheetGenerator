import tkinter as tk
from tkinter import ttk, filedialog, font, messagebox, RIGHT
import json
import os
import io
import subprocess
from PIL import Image, ImageTk, ImageFont, ImageDraw
import cairosvg
import tkcolorpicker
from collections import defaultdict
from icon_parsing import load_icon_entries
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from bs4 import BeautifulSoup
import tempfile
import random
from io import BytesIO
from globals import get_cached_icon, COLOR_BG, COLOR_FG, FONT_DEFAULT, TAG_COLOR_MAP
from font_picker_dialog import FontPickerDialog
from preview_window import open_preview_window
from icon_picker_dialog_v2 import IconPickerDialogV2

# --- Constants ---
APP_WIDTH = 1360
APP_HEIGHT = 860
GRID_COLUMNS = 10
GRID_ROWS = 5
CELL_SIZE = 60
SECTIONS = ["Left Shoulder", "Right Shoulder", "Gothic Numerals", "Imperial Numerals"]
COLOR_BG = "#1e1e1e"
COLOR_FG = "#ffffff"
ICON_DIR = "icons"
FONT_DEFAULT = "Arial"

# --- Global Icon Cache ---
ICON_CACHE = {}

# --- Helper Functions ---

def register_custom_font(font_name, ttf_path):
    if font_name not in pdfmetrics.getRegisteredFontNames():
        if os.path.exists(ttf_path):
            pdfmetrics.registerFont(TTFont(font_name, ttf_path))
        else:
            print(f"[WARNING] Font file not found: {ttf_path}")

# --- GUI Application ---
class IconGridApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self._maximized = False
        self.title("GrimDark Decal Sheet Creator")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.configure(bg=COLOR_BG)
        self.grid_cells = defaultdict(dict)
        self.grid_cells["Left Shoulder"] = {}
        self.grid_cells["Right Shoulder"] = {}
        self.grid_cells["Gothic Numerals"] = {}
        self.grid_cells["Imperial Numerals"] = {}
        self.icon_entries = load_icon_entries(ICON_DIR)

        for entry in self.icon_entries:
            if not hasattr(entry, "thumbnail"):
                entry.thumbnail = get_cached_icon(entry.file, size=(40, 40), color=COLOR_FG)

        self.create_titlebar()
        self.create_toolbar()
        self.create_widgets()
        self.prefill_numerals()
        self.bind_events()
        self.center_window()

    def create_titlebar(self):
        self.overrideredirect(True)

        self.titlebar = tk.Frame(self, bg="#121212", height=32)
        self.titlebar.pack(fill="x", side="top")
        self.titlebar.bind("<Button-1>", self.start_move)
        self.titlebar.bind("<B1-Motion>", self.do_move)

        title_label = tk.Label(self.titlebar, text="GrimDark Decal Sheet Creator",
                               bg="#111111", fg="white", font=(FONT_DEFAULT, 14, "bold"))
        title_label.pack(side="left", padx=10)
        title_label.bind("<Button-1>", self.start_move)
        title_label.bind("<B1-Motion>", self.do_move)

        btn_close = tk.Button(self.titlebar, text="✕", bg="#222", fg="white", command=self.quit,
                              relief="flat", bd=0, width=3, height=1)
        btn_close.pack(side="right", padx=2, pady=2)

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

    def center_window(self):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        size = (APP_WIDTH, APP_HEIGHT)
        x = max(0, (screen_w - size[0]) // 2)
        y = max(0, (screen_h - size[1]) // 2)
        self.geometry(f"{size[0]}x{size[1]}+{x}+{y}")

    def create_toolbar(self):
        self.toolbar = tk.Frame(self, bg="#111111", height=42)
        self.toolbar.pack(fill="x", side="top")

        self.file_button = tk.Button(
            self.toolbar, text="File", bg="#222222", fg="white",
            font=(FONT_DEFAULT, 12), relief="flat", bd=0,
            activebackground="#333333", activeforeground="white",
            command=self.toggle_file_menu
        )
        self.file_button.pack(side="left", padx=5, pady= 4)

        self.generate_button = tk.Button(
            self.toolbar, text="Generate Preview", bg="#222222", fg="white",
            font=(FONT_DEFAULT, 12), relief="flat", bd=0,
            activebackground="#333333", activeforeground="white",
            command=self.open_preview_window
        )
        self.generate_button.pack(side="left", padx=5, pady= 4)
        debug_btn = tk.Button(self.toolbar, text="Debug", bg="#555", fg="white", relief="flat", command=self.run_debug_randomize)
        debug_btn.pack(side=RIGHT, padx=(10, 5))
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
                            anchor="w", relief="flat", command=cmd, font=(FONT_DEFAULT, 12))
            btn.pack(fill="x", padx=5, pady=2)
            bind_hover(btn)
    
    def run_debug_randomize(self):
        print("[DEBUG] Running randomization...")

        # You must have a list of available icon entries and fonts in self.icon_entries and self.fonts
        icon_files = [entry for entry in self.icon_entries if entry.file]
        font_folder = os.path.join(os.getcwd(), "fonts")
        available_fonts = [
            (os.path.splitext(f)[0], 14)
            for f in os.listdir(font_folder)
            if f.lower().endswith(".ttf")
        ]

        def random_color():
            return "#{:06X}".format(random.randint(0, 0xFFFFFF))

        top_sections = SECTIONS[:2]
        bottom_sections = SECTIONS[2:]

        for section in top_sections:
            for row in range(GRID_ROWS):
                icon_entry = random.choice(icon_files)
                tint = random_color()
                img = get_cached_icon(icon_entry.file, size=(CELL_SIZE - 6, CELL_SIZE - 6), color=tint)
                for col in range(GRID_COLUMNS):
                    cell = self.grid_cells[section][(row, col)]
                    cell.set_icon(img, path=icon_entry.file, tint=tint)

        for section in bottom_sections:
            for row in range(GRID_ROWS):
                font = random.choice(available_fonts)
                tint = random_color()
                for col in range(GRID_COLUMNS):
                    cell = self.grid_cells[section][(row, col)]
                    if isinstance(cell.content, str):
                        cell.set_text(cell.content, font=font, color=tint)

        print("[DEBUG] Randomization complete.")

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
            section_label.grid(row=0, column=0, sticky="w", pady=(10, 0))

            for row in range(GRID_ROWS):
                control_frame = tk.Frame(section_frame, bg=COLOR_BG)
                control_frame.grid(row=row + 1, column=0, sticky="w", padx=5, pady=2)

                if section in ("Left Shoulder", "Right Shoulder"):
                    icon_btn = tk.Button(control_frame, text="🖼️", width=3, font=("Segoe UI Emoji", 10), bg="#333", fg="white", relief="flat")
                    icon_btn.config(command=lambda s=section, r=row, w=icon_btn: self.pick_icon_for_row(s, r, w))
                    icon_btn.grid(row=0, column=0, sticky="w", pady=1)
                    Tooltip(icon_btn, "Pick Icon")

                if section in ("Gothic Numerals", "Imperial Numerals"):
                    font_btn = tk.Button(control_frame, text="🖋️", width=3, font=("Segoe UI Emoji", 10), bg="#333", fg="white", relief="flat")
                    font_btn.config(command=lambda s=section, r=row, w=font_btn: self.pick_font_for_row(s, r, w))
                    font_btn.grid(row=1, column=0, sticky="w", pady=1)
                    Tooltip(font_btn, "Pick Font")

                color_btn = tk.Button(control_frame, text="🎨", width=3, font=("Segoe UI Emoji", 10), bg="#333", fg="white", relief="flat")
                color_btn.config(command=lambda s=section, r=row, w=color_btn: self.pick_color_for_row(s, r, w))
                color_btn.grid(row=2, column=0, sticky="w", pady=1)
                Tooltip(color_btn, "Pick Color")

                grid_frame = tk.Frame(control_frame, bg=COLOR_BG)
                grid_frame.grid(row=0, column=1, rowspan=3, sticky="w", padx=5)

                for col in range(GRID_COLUMNS):
                    cell = IconCell(grid_frame, row, col)
                    cell.grid(row=0, column=col, padx=1, pady=1)
                    self.grid_cells[section][(row, col)] = cell

    def pick_font_for_row(self, section, row, Widget=None):
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
            font_value = (FONT_DEFAULT, 10)

        apply_all = messagebox.askyesno("Apply to All?", "Apply this font to all rows in this section?")
        rows = range(GRID_ROWS) if apply_all else [row]

        for r in rows:
            for c in range(GRID_COLUMNS):
                cell = self.grid_cells[section][(r, c)]
                if isinstance(cell.content, str):
                    color = cell.tint or COLOR_FG
                    cell.set_text(cell.content, font=font_value, color=color)

    def get_row_color(self, section, row):
        # Returns the fill color of the first text cell in a row, or None.
        for c in range(GRID_COLUMNS):
            cell = self.grid_cells[section][(row, c)]
            if hasattr(cell, "tint"):
                return cell.tint
            elif isinstance(cell.content, str):
                items = cell.canvas.find_all()
                if items:
                    color = cell.canvas.itemcget(items[0], "fill")
                    if color:
                        return color
                break
        return None

    def pick_color_for_row(self, section, row, Widget=None):
        current_color = self.get_row_color(section, row) or COLOR_FG
        color = tkcolorpicker.askcolor(
            title="Pick a Color",
            color= current_color if current_color != None else COLOR_FG,
            alpha=False
        )[1]
        if not color:
            return

        apply_all = messagebox.askyesno("Apply to All?", "Apply this color to all rows in this section?")
        rows = range(GRID_ROWS) if apply_all else [row]

        for r in rows:
            for c in range(GRID_COLUMNS):
                cell = self.grid_cells[section][(r, c)]
                if isinstance(cell.content, str):
                    cell.set_text(cell.content, font=cell.font, color=color)
                elif cell.icon_path:
                    tinted_img = get_cached_icon(cell.icon_path, size=(CELL_SIZE - 6, CELL_SIZE - 6), color=color)
                    cell.set_icon(tinted_img, path=cell.icon_path, tint=color)

    def pick_icon_for_row(self, section, row, widget=None):
        dialog = IconPickerDialogV2(self, self.icon_entries)
        self.align_dialog(dialog, widget)
        self.wait_window(dialog)

        if not dialog.result or not hasattr(dialog, "result_mode"):
            return

        mode = getattr(dialog, "result_mode", "single")
        selected_icon = dialog.result
        rows = range(GRID_ROWS) if mode == "all" else [row]

        for r in rows:
            color = self.get_row_color(section, r) or COLOR_FG
            img = get_cached_icon(selected_icon.file, size=(CELL_SIZE - 6, CELL_SIZE - 6), color=color)
            for c in range(GRID_COLUMNS):
                cell = self.grid_cells[section][(r, c)]
                cell.set_icon(img, path=selected_icon.file, tint=color)

    def align_dialog(self, dialog, widget: None):
        if widget:
            widget.update_idletasks()
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height()
            dialog.update_idletasks()
            screen_w = dialog.winfo_screenwidth()
            screen_h = dialog.winfo_screenheight()
            win_w = dialog.winfo_width()
            win_h = dialog.winfo_height()
            x = min(max(0, x), screen_w - win_w)
            y = min(max(0, y), screen_h - win_h)
            dialog.geometry(f"+{x}+{y}")

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
                json.dump(layout, filepath, indent=2)

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

    def debug_icon_cell_data(self, grid_cells, sections):
        print("\n\033[95m" + "="*30 + " GRID CELLS DEBUG " + "="*30 + "\033[0m\n")
        for section in sections:
            print(f"\033[94m[SECTION] {section}\033[0m")
            cells = grid_cells.get(section, {})
            for (r, c), cell in cells.items():
                if hasattr(cell, "icon_path") and cell.icon_path:
                    print(f"  \033[96m[ICON CELL] ({r},{c})\033[0m")
                    print(f"      \033[93mPath:\033[0m {cell.icon_path}")
                    print(f"      \033[92mTint:\033[0m {getattr(cell, 'tint', 'None')}")
                    print(f"      \033[90mType:\033[0m {type(cell)}")
                    print(f"      \033[91mHas content:\033[0m {hasattr(cell, 'content')}, "
                        f"{'Text' if isinstance(getattr(cell, 'content', None), str) else 'Image' if cell.icon_path else 'None'}")
            print()
    print("\033[95m" + "="*80 + "\033[0m\n")
    
    def open_preview_window(self):
         open_preview_window(self)





    def bind_events(self):
        self.bind("<Control-s>", lambda e: self.save_layout())
        self.bind("<Control-o>", lambda e: self.load_layout())

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
                         font=(FONT_DEFAULT, 10, "normal"), padx=6, pady=3)
        label.pack(ipadx=6, ipady=3)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None


class IconCell(tk.Frame):
    def __init__(self, master, row, col):
        super().__init__(master, width=CELL_SIZE, height=CELL_SIZE, bg="#181818", highlightbackground="#2a2a2a", highlightthickness=1)
        self.grid_propagate(False)
        self.row = row
        self.col = col
        self.content = None
        self.icon_path = None
        self.font = (FONT_DEFAULT, 10, "bold")
        self.tint = COLOR_FG

        self.canvas = tk.Canvas(self, width=CELL_SIZE-6, height=CELL_SIZE-6,
                                highlightthickness=0, bg="#181818")
        self.canvas.place(x=3, y=3)

    def set_icon(self, image, path=None,  tint=COLOR_FG):
        self.content = image
        self.icon_path = path
        self.tint = tint  # ← store tint color
        self.canvas.delete("all")
        self.canvas.create_image(
            (CELL_SIZE - 6) // 2,
            (CELL_SIZE - 6) // 2,
            image=image,
            anchor="center"
        )
        self.canvas.image = image
        self.tint = tint

    def set_text(self, text, font=None, color=COLOR_FG):
        self.content = text
        if font:
            self.font = font
        self.tint = color
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
        self.configure(bg="#181818")
          
if __name__ == "__main__":
    app = IconGridApp()
    app.mainloop()
