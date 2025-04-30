import tkinter as tk
from icon_parsing import load_icon_entries
from tkinter import messagebox, ttk
from tkcolorpicker import askcolor
from PIL import Image, ImageTk, ImageFont
import tkinter.font as tkfont
import os, ctypes
import io
import cairosvg
import json

with open("tag_color_mapping.json", "r") as f:
    TAG_COLOR_MAP = json.load(f)

# Basic Config
APP_WIDTH = 1200
APP_HEIGHT = 930
CELL_SIZE = 48

ICON_FOLDER = "icons"
FONT_FOLDER = "fonts"
SESSION_FOLDER = "sessions"
EXPORT_FOLDER = "exports"

DEFAULT_HIGHLIGHT_COLOR = "#1f6aa5"
DARK_BG = "#222222"
MID_BG = "#333333"
LIGHT_TEXT = "#eeeeee"

GOTHIC_NUMERALS = [str(i) for i in range(1, 11)]
IMPERIAL_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

def load_svg_as_photoimage(svg_path, size=(60, 60), tint="#FFFFFF"):
    try:
        # Render the SVG to PNG bytes
        png_data = cairosvg.svg2png(url=svg_path, output_width=size[0], output_height=size[1])
        image = Image.open(io.BytesIO(png_data)).convert("RGBA")
        image.thumbnail(size, Image.LANCZOS)

        # Create solid fill image
        solid = Image.new("RGBA", image.size, tint)

        # Mask the non-transparent pixels
        alpha = image.getchannel("A")
        tinted = Image.composite(solid, Image.new("RGBA", image.size, (0, 0, 0, 0)), mask=alpha)

        return ImageTk.PhotoImage(tinted)
    except Exception as e:
        print(f"[ERROR] Failed to tint SVG {svg_path}: {e}")
        return None

class IconCell(tk.Frame):
    def __init__(self, master, row, col, *args, **kwargs):
        super().__init__(master, width=CELL_SIZE, height=CELL_SIZE, bg=DARK_BG, *args, **kwargs)
        self.grid_propagate(False)
        self.row = row
        self.col = col
        self.content = None
        self.icon_path = None
        self.font = ("Arial", 12, "bold")

        self.inner_frame = tk.Frame(self, bg=MID_BG)
        self.inner_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self.inner_frame, width=CELL_SIZE-6, height=CELL_SIZE-6,
                                highlightthickness=0, bg=MID_BG)
        self.canvas.place(x=3, y=3)

    def set_icon(self, image, path=None):
        self.content = image
        self.icon_path = path
        self.inner_frame.configure(bg=DARK_BG)
        self.canvas.configure(bg=DARK_BG)
        self.canvas.delete("all")
        img = image
        self.canvas.create_image(
                (CELL_SIZE - 6) // 2,
                (CELL_SIZE - 6) // 2,
                image=image,
                anchor="center"
            )
        self.canvas.image = img

    def set_text(self, text, font=None):
        self.content = text
        if font:
            self.font = font
        self.inner_frame.configure(bg=MID_BG)
        self.canvas.configure(bg=MID_BG)
        self.canvas.delete("all")

        temp_font = tkfont.Font(font=self.font)

        x = (CELL_SIZE - 6) // 2
        y = (CELL_SIZE - 6) // 2

        self.canvas.create_text(
            x,
            y,
            text=text,
            font=self.font,
            fill=LIGHT_TEXT,
            anchor="center"
        )

    def highlight(self, color=DEFAULT_HIGHLIGHT_COLOR):
        self.configure(bg=color)

    def unhighlight(self):
        self.configure(bg=DARK_BG)

class FontPickerDialog(tk.Toplevel):
    def __init__(self, master, section, row):
        super().__init__(master)
        self.title(f"Pick Font: {section} Row {row+1}")
        self.configure(bg=DARK_BG)
        self.section, self.row = section, row
        self.selected_index = None
        self.hover_index = None

        fonts = [f for f in os.listdir(FONT_FOLDER) if f.lower().endswith(('.ttf','.otf'))]
        self.fonts = fonts

        self.canvas = tk.Canvas(self, bg=DARK_BG, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_hover)

        self.draw_font_list()

        btnf = tk.Frame(self, bg=DARK_BG)
        btnf.pack(pady=5)
        tk.Button(btnf, text="Cancel", command=self.destroy,
                bg=MID_BG, fg=LIGHT_TEXT, relief="flat").pack(side="left", padx=5)
        tk.Button(btnf, text="Apply to All", command=self.apply_to_all,
                bg=MID_BG, fg=LIGHT_TEXT, relief="flat").pack(side="right", padx=5)
        tk.Button(btnf, text="Apply", command=self.apply,
                bg=MID_BG, fg=LIGHT_TEXT, relief="flat").pack(side="right", padx=5)


    def draw_font_list(self):
        self.canvas.delete("all")
        y = 20
        self.items = []

        for idx, fname in enumerate(self.fonts):
            display_name = os.path.splitext(fname)[0]
            path = os.path.join(FONT_FOLDER, fname)
            try:
                FR_PRIVATE = 0x10
                if os.name == 'nt':
                    ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0)
                pil_font = ImageFont.truetype(path, size=16)
                family = pil_font.getname()[0]
                font_obj = tkfont.Font(family=family, size=16)
            except Exception:
                font_obj = tkfont.Font(family="Arial", size=16)

            color = DEFAULT_HIGHLIGHT_COLOR if idx == self.selected_index else ("#555555" if idx == self.hover_index else LIGHT_TEXT)
            text_preview = f"{display_name} - IX 3"
            self.canvas.create_text(30, y, anchor='w', text=text_preview, font=font_obj, fill=color, tags=("font", f"font_{idx}"))
            self.items.append((y-10, y+20, idx))
            y += 50

        self.canvas.config(scrollregion=(0,0,500,y))

    def on_click(self, event):
        for top, bottom, idx in self.items:
            if top <= event.y <= bottom:
                self.selected_index = idx
                break
        self.draw_font_list()

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
        if self.selected_index is None:
            return

        fname = self.fonts[self.selected_index]
        path = os.path.join(FONT_FOLDER, fname)

        try:
            FR_PRIVATE = 0x10
            if os.name == 'nt':
                ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0)
            pil_font = ImageFont.truetype(path, size=12)
            family = pil_font.getname()[0]

            # Only bold Imperial numerals, normal for Gothic
            if self.section == "Imperial Numerals":
                new_font = (family, 12, 'bold')
            else:
                new_font = (family, 12)
        except Exception:
            new_font = ("Arial", 12)

        for c in range(10):
            key = (self.section, self.row, c)
            if key in self.master.cells:
                cell = self.master.cells[key]
                if isinstance(cell.content, str):
                    cell.set_text(cell.content, font=new_font)
        self.destroy()

    def apply_to_all(self):
        if self.selected_index is None:
            return

        fname = self.fonts[self.selected_index]
        path = os.path.join(FONT_FOLDER, fname)

        try:
            FR_PRIVATE = 0x10
            if os.name == 'nt':
                ctypes.windll.gdi32.AddFontResourceExW(path, FR_PRIVATE, 0)
            pil_font = ImageFont.truetype(path, size=12)
            family = pil_font.getname()[0]

            if self.section == "Imperial Numerals":
                new_font = (family, 12, "bold")
            else:
                new_font = (family, 12)
        except Exception:
            new_font = ("Arial", 12)

        for r in range(5):
            for c in range(10):
                key = (self.section, r, c)
                if key in self.master.cells:
                    cell = self.master.cells[key]
                    if isinstance(cell.content, str):
                        cell.set_text(cell.content, font=new_font)

        self.destroy()


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
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, bg="black", fg="white",
                         relief="solid", borderwidth=1,
                         font=("Arial", 10, "normal"))
        label.pack(ipadx=5, ipady=2)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

class IconGridApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Astartes Decal Customizator")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.configure(bg=DARK_BG)
        self.overrideredirect(True)  # Remove OS title bar

        # ── Title Bar ────────────────────────────
        self.titlebar = tk.Frame(self, bg="#121212", height=32)
        self.titlebar.pack(fill="x", side="top")

        self.titlebar.bind("<Button-1>", self.start_move)
        self.titlebar.bind("<B1-Motion>", self.do_move)

        title_label = tk.Label(self.titlebar, text="Astartes Decal Customizator",
                            bg="#111111", fg="white", font=("Arial", 14, "bold"))
        title_label.pack(side="left", padx=10)
        title_label.bind("<Button-1>", self.start_move)
        title_label.bind("<B1-Motion>", self.do_move)

        # Titlebar buttons
        btn_close = tk.Button(self.titlebar, text="✕", bg="#222", fg="white", command=self.quit,
                            relief="flat", bd=0, width=3, height=1)
        btn_close.pack(side="right", padx=2, pady=2)

        btn_max = tk.Button(self.titlebar, text="🗖", bg="#222", fg="white", command=self.toggle_maximize,
                            relief="flat", bd=0, width=3, height=1)
        btn_max.pack(side="right", padx=2, pady=2)

        btn_min = tk.Button(self.titlebar, text="━", bg="#222", fg="white", command=self.iconify,
                            relief="flat", bd=0, width=3, height=1)
        btn_min.pack(side="right", padx=2, pady=2)

        # ── Toolbar (Menu Bar) ────────────────────────────
        self.toolbar = tk.Frame(self, bg="#111111", height=30)
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

        # File Menu Dropdown
        self.create_file_menu()

        # Main UI below the toolbars
        self.cells = {}
        self.sel_cell = None
        self._maximized = False

        self.main_frame = tk.Frame(self, bg=DARK_BG)
        self.main_frame.pack(fill="both", expand=True)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.create_section(self.main_frame, "Left Shoulder Pad", 0, 0)
        self.create_section(self.main_frame, "Right Shoulder Pad", 0, 1)
        self.create_section(self.main_frame, "Gothic Numerals", 1, 0)
        self.create_section(self.main_frame, "Imperial Numerals", 1, 1)

        self.prefill_numerals()


    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        x = event.x_root - self.x
        y = event.y_root - self.y
        self.geometry(f"+{x}+{y}")

    def create_file_menu(self):
        def bind_hover(btn):
            btn.bind("<Enter>", self.on_menu_hover)
            btn.bind("<Leave>", self.on_menu_leave)

        btns = [
            ("Load Layout", self.load_layout),
            ("Save Layout", self.save_layout),
            ("Print", self.print_layout),
            ("Exit", self.quit),
            ("About", self.open_about)
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
            def show_menu():
                x = self.file_button.winfo_rootx() - self.winfo_rootx()
                y = self.titlebar.winfo_height() + self.toolbar.winfo_height()
                self.file_menu_frame.place(x=x, y=y)
                self.file_menu_frame.lift()
                self.file_menu_frame.focus_set()  # Make it focusable
                self.file_menu_frame.bind("<FocusOut>", lambda e: self.hide_file_menu())
                self.file_menu_frame.bind("<Escape>", lambda e: self.hide_file_menu())
                self.file_menu_visible = True

            self.after(10, show_menu)

    def on_menu_hover(self, event):
        event.widget.configure(bg="#333333")

    def on_menu_leave(self, event):
        event.widget.configure(bg="#222222")

    def hide_file_menu(self):
        self.file_menu_frame.place_forget()
        self.file_menu_visible = False

    def toggle_maximize(self):
        if self._maximized:
            self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
            self._maximized = False
        else:
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
            self._maximized = True

    def create_section(self, parent, title, r, c):
        f = tk.Frame(parent, bg=DARK_BG)
        f.grid(row=r, column=c, sticky='nsew', padx=5, pady=5)
        tk.Label(f,text=title,font=("Arial",18,"bold"),bg=DARK_BG,fg=LIGHT_TEXT).pack(pady=5)
        grid = tk.Frame(f, bg=DARK_BG)
        grid.pack(fill='both', expand=True)
        self.create_grid(grid, title)

    def create_grid(self, parent, section):
        for r in range(5):
            for c in range(11):
                if c == 0:
                    btn_frame = tk.Frame(parent, bg=DARK_BG)
                    btn_frame.grid(row=r, column=c, padx=1, pady=1)

                    if section in ("Gothic Numerals", "Imperial Numerals"):
                        font_btn = tk.Button(
                            btn_frame, text="𝙵𝙵", width=2, height=1,
                            command=lambda s=section, row=r: FontPickerDialog(self, s, row),
                            bg=MID_BG, fg="white", relief="solid", bd=1, highlightthickness=0,
                            anchor="center", justify="center",
                            font=("Arial", 14, "bold")
                        )
                        font_btn.pack(padx=1, pady=1, fill='both')
                        self.create_tooltip(font_btn, "Pick Font")

                        color_btn = tk.Button(
                            btn_frame, text="🎨", width=2, height=1,
                            command=lambda s=section, row=r: self.pick_color_action(s, row),
                            bg=MID_BG, fg="white", relief="solid", bd=1, highlightthickness=0,
                            anchor="center", justify="center",
                            font=("Arial", 14, "bold")
                        )
                        color_btn.pack(padx=1, pady=1, fill='both')
                        self.create_tooltip(color_btn, "Pick Color")

                    else:
                        img_btn = tk.Button(
                            btn_frame, text="     🖼️", width=2, height=1,
                            command=lambda s=section, row=r: IconPickerDialog(self, s, row),
                            bg=MID_BG, fg="white", relief="solid", bd=1, highlightthickness=0,
                            anchor="center", justify="center",
                            font=("Arial", 14, "bold")
                        )
                        img_btn.pack(padx=1, pady=1, fill='both')
                        self.create_tooltip(img_btn, "Pick Icon")

                        color_btn = tk.Button(
                            btn_frame, text="🎨", width=2, height=1,
                            command=lambda s=section, row=r: self.pick_color_action(s, row),
                            bg=MID_BG, fg="white", relief="solid", bd=1, highlightthickness=0,
                            anchor="center", justify="center",
                            font=("Arial", 14, "bold")
                        )
                        color_btn.pack(padx=1, pady=1, fill='both')
                        self.create_tooltip(color_btn, "Pick Color")
                else:
                    cell = IconCell(parent, r, c-1)
                    cell.grid(row=r, column=c, padx=1, pady=1)
                    cell.bind("<Button-1>", lambda e, s=section, row=r, col=c-1: self.select_cell(s, row, col))
                    cell.canvas.bind("<Button-1>", lambda e, s=section, row=r, col=c-1: self.select_cell(s, row, col))
                    self.cells[(section, r, c-1)] = cell

    def create_tooltip(self, widget, text):
        Tooltip(widget, text)

    def select_cell(self, section,row,col):
        if hasattr(self,'sel_cell') and self.sel_cell:
            self.sel_cell.unhighlight()
        key=(section,row,col)
        cell=self.cells.get(key)
        if cell: cell.highlight(); self.sel_cell=cell

    def prefill_numerals(self):
        for r in range(5):
            for c in range(10):
                gothic_key = ("Gothic Numerals", r, c)
                imperial_key = ("Imperial Numerals", r, c)
                if gothic_key in self.cells:
                    self.cells[gothic_key].set_text(GOTHIC_NUMERALS[c])
                if imperial_key in self.cells:
                    self.cells[imperial_key].set_text(IMPERIAL_NUMERALS[c])

    def get_current_color(self, section, row):
        # Returns the current fill color of the first text cell in a row, or None.
        for c in range(10):
            key = (section, row, c)
            if key in self.cells:
                cell = self.cells[key]
                if isinstance(cell.content, str):
                    items = cell.canvas.find_all()
                    if items:
                        color = cell.canvas.itemcget(items[0], "fill")
                        if color:
                            return color
                    break
        return None

    def pick_color_action(self, section, row):
        current_color = self.get_current_color(section, row)
        color = askcolor(
            title="Pick a Color",
            color= current_color if current_color != None else "#FFFFFF",
            alpha=False
        )
        # color is a tuple: ( (R,G,B), "#rrggbb" )
        if not color or not color[1] or not isinstance(color[1], str):
            return  # user cancelled or invalid

        hex_color = color[1]

        apply_all = messagebox.askyesno("Apply to All?", "Apply color to all rows in this section?")
        rows = range(5) if apply_all else [row]

        for r in rows:
            for c in range(10):
                key = (section, r, c)
                if key in self.cells:
                    cell = self.cells[key]
                    if isinstance(cell.content, str):
                         # This is a text cell
                        cell.canvas.delete("all")
                        x = (CELL_SIZE - 6) // 2
                        y = (CELL_SIZE - 6) // 2
                        cell.canvas.create_text(
                            x, y,
                            text=cell.content,
                            font=cell.font,
                            fill=hex_color,
                            anchor="center"
                        )
                    elif getattr(cell, "icon_path", None):
                        # This is an icon cell with a path
                        tinted_img = load_svg_as_photoimage(
                            cell.icon_path,
                            size=(CELL_SIZE - 6, CELL_SIZE - 6),
                            tint=hex_color
                        )
                        cell.set_icon(tinted_img, path=cell.icon_path)

    def reset_row_color(self, section, row):
        default_color = LIGHT_TEXT
        for c in range(10):
            key = (section, row, c)
            if key in self.cells:
                cell = self.cells[key]
                if isinstance(cell.content, str):
                    cell.canvas.delete("all")
                    x = (CELL_SIZE - 6) // 2
                    y = (CELL_SIZE - 6) // 2
                    cell.canvas.create_text(
                        x, y,
                        text=cell.content,
                        font=cell.font,
                        fill=default_color,
                        anchor="center"
                    )

    def save_layout(self):
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Save Layout As..."
        )
        if not filepath:
            return

        layout = {}
        for key, cell in self.cells.items():
            section, row, col = key
            if isinstance(cell.content, str):
                layout[str(key)] = {"type": "text", "text": cell.content, "font": cell.font}
            else:
                layout[str(key)] = {"type": "icon"}

        with open(filepath, "w") as f:
            json.dump(layout, f, indent=4)
        print(f"[INFO] Layout saved to {filepath}")

    def load_layout(self):
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Load Layout"
        )
        if not filepath:
            return

        with open(filepath, "r") as f:
            layout = json.load(f)

        for key_str, info in layout.items():
            key = eval(key_str)  # turn "(section, row, col)" string back into tuple
            if key in self.cells:
                cell = self.cells[key]
                if info["type"] == "text":
                    cell.set_text(info["text"], font=info.get("font", ("Arial", 12)))
                # if icons, you could later reload assigned images here

    def print_layout(self):
        print("[INFO] Print command clicked (printing to be implemented later)")

    def open_about(self):
        about_win = tk.Toplevel(self)
        about_win.title("About Astartes Decal Customizator")
        about_win.configure(bg="#222222")
        about_win.geometry("600x600")
        about_win.resizable(False, False)

        try:
            font_path = os.path.join(FONT_FOLDER, "CaslonAntique.ttf")
            import ctypes
            FR_PRIVATE = 0x10
            if os.name == 'nt':
                ctypes.windll.gdi32.AddFontResourceExW(font_path, FR_PRIVATE, 0)
            from PIL import ImageFont
            pil_font = ImageFont.truetype(font_path, size=14)
            family = pil_font.getname()[0]
            text_font = (family, 18)
        except Exception:
            text_font = ("Times New Roman", 12)

        try:
            from PIL import Image, ImageTk
            logo_path = os.path.join(ICON_FOLDER, "chapter_logo.png")
            raw_logo = Image.open(logo_path).convert("RGBA")
            raw_logo.thumbnail((100, 100))
            alpha = raw_logo.split()[3].point(lambda p: p * 0.2)
            raw_logo.putalpha(alpha)
            logo_img = ImageTk.PhotoImage(raw_logo)
            logo_label = tk.Label(about_win, image=logo_img, bg="#222222")
            logo_label.image = logo_img
            logo_label.pack(pady=(10, 0))
        except Exception as e:
            print(f"[WARN] Could not load logo: {e}")

        text = (
            "Astartes Decal Customizator\n\n"
            "This tool was developed by Eric Cugota (GitHub: tryadelion)\n"
            "with inspiration and resources from the Bolter and Chainsword community.\n\n"
            "Includes work from:\n"
            "- Caliban Angelus Font (creator unknown)\n"
            "- Caslon Antique Font (Berne Nadall, 1894)\n"
            "- Grimworld 40K's icon library by Bishop Greisyn and Abomination\n"
            "- And moral support from my cat Morgana 🐾\n\n"
            "Published under the MIT License.\n"
            "No ownership is claimed over included resources.\n"
            "No affiliation with Games Workshop.\n\n"
            "Repository link pending. Contributions and feedback welcome!"
        )

        label = tk.Label(about_win, text=text, bg="#222222", fg="white",
                        font=text_font, justify="left", wraplength=560, anchor="n")
        label.pack(padx=20, pady=20)

        close_btn = tk.Button(about_win, text="Close", command=about_win.destroy,
                            bg=MID_BG, fg="white", relief="flat")
        close_btn.pack(pady=10)

    def quit(self):
        self.destroy()

class IconPickerDialog(tk.Toplevel):
    def __init__(self, master, section, row):
        super().__init__(master)
        self.title("Pick an Icon")
        self.geometry("700x500")
        self.configure(bg=DARK_BG)

        self.section = section
        self.row = row
        self.selected_image = None
        self.selected_path = None
        self.selected_frame = None
        self.icon_images = []

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar", gripcount=0, background="#333", darkcolor="#222", lightcolor="#444",
                        troughcolor="#111", bordercolor="#222", arrowcolor="white")

        container = tk.Frame(self, bg=DARK_BG)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self.scroll_canvas = tk.Canvas(container, bg=DARK_BG, highlightthickness=0)
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.scroll_canvas.yview, style="Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        self.icon_frame = tk.Frame(self.scroll_canvas, bg=DARK_BG)
        self.scroll_window = self.scroll_canvas.create_window((0, 0), window=self.icon_frame, anchor="nw")
        def resize_canvas(event):
            canvas_width = event.width
            self.scroll_canvas.itemconfig(self.scroll_window, width=canvas_width)

        self.scroll_canvas.bind("<Configure>", resize_canvas)

        self.icon_frame.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))

        self.button_frame = tk.Frame(self, bg=DARK_BG)
        self.button_frame.pack(pady=10)

        self.cancel_button = tk.Button(self.button_frame, text="Cancel", command=self.destroy,
                                       bg=MID_BG, fg=LIGHT_TEXT, activebackground="#555555", relief="flat")
        self.cancel_button.pack(side="left", padx=10)

        self.set_button = tk.Button(self.button_frame, text="Set Icon", command=self.apply_icon,
                                    bg=MID_BG, fg=LIGHT_TEXT, activebackground="#555555", relief="flat")
        self.set_button.pack(side="right", padx=10)

        self.apply_all_button = tk.Button(self.button_frame, text="Apply to All", command=self.apply_icon_to_all,
                                          bg=MID_BG, fg=LIGHT_TEXT, activebackground="#555555", relief="flat")
        self.apply_all_button.pack(side="right", padx=5)

        self.entries = load_icon_entries(ICON_FOLDER)
        self.entries.sort(key=lambda e: (not e.tags, e.tags, e.name.lower()))
        self.draw_icons()
        self.bind_mousewheel(self.scroll_canvas)

    def bind_mousewheel(self, widget):
        # Windows and Linux
        widget.bind_all("<MouseWheel>", self._on_mousewheel)
        # macOS
        widget.bind_all("<Button-4>", self._on_mousewheel_mac)
        widget.bind_all("<Button-5>", self._on_mousewheel_mac)

    def _on_mousewheel(self, event):
        self.scroll_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_mousewheel_mac(self, event):
        if event.num == 4:
            self.scroll_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.scroll_canvas.yview_scroll(1, "units")

    def draw_icons(self):
        for idx, entry in enumerate(self.entries):
            img = load_svg_as_photoimage(entry.filepath, tint="#FFFFFF")
            if img:
                self.icon_images.append(img)

                frame = tk.Frame(self.icon_frame, bg=MID_BG, highlightbackground="#444", highlightthickness=1)
                frame.pack(fill="x", padx=4, pady=3)
                def bind_clicks_to_frame(f, path):
                    def click_handler(event):
                        self.select_icon(path, f)
                    f.bind("<Button-1>", click_handler)
                    for child in f.winfo_children():
                        child.bind("<Button-1>", click_handler)

                frame.bind("<Enter>", lambda e, f=frame: f.configure(bg="#444444"))
                frame.bind("<Leave>", lambda e, f=frame: self.update_card_bg(f))
                frame.grid_columnconfigure(1, weight=1)

                icon_label = tk.Label(frame, image=img, bg=MID_BG)
                icon_label.grid(row=0, column=0, rowspan=2, padx=5, pady=5)
                
                title_label = tk.Label(frame, text=entry.name, fg=LIGHT_TEXT, bg=MID_BG,
                                       font=("Arial", 10, "bold"), anchor="w", justify="left")
                title_label.grid(row=0, column=1, sticky="w")
        

                tag_frame = tk.Frame(frame, bg=MID_BG)
                tag_frame.grid(row=1, column=1, sticky="w")
                self.render_tag_pills(tag_frame, entry.tags)
                bind_clicks_to_frame(frame, entry.filepath)

    def render_tag_pills(self, parent, tags):
        for tag in tags:
            bg, fg = TAG_COLOR_MAP.get(tag, ("#444444", "#FFFFFF"))
            pill = tk.Label(
                parent,
                text=tag,
                bg=bg,
                fg=fg,
                font=("Arial", 9, "bold"),
                padx=6,
                pady=2,
                borderwidth=1,
                relief="solid"
            )
            pill.pack(side="left", padx=(0, 5), pady=2)

    def update_card_bg(self, frame):
        if frame != self.selected_frame:
            frame.configure(bg=MID_BG)

    def select_icon(self, path, frame):
        self.selected_path = path
        self.selected_image = load_svg_as_photoimage(path, size=(60, 60), tint="#FFFFFF")
        if self.selected_frame:
            self.selected_frame.configure(bg=MID_BG)
        self.selected_frame = frame
        frame.configure(bg=DEFAULT_HIGHLIGHT_COLOR)

    def apply_icon(self):
        if not self.selected_path:
            return

        for c in range(10):
            key = (self.section, self.row, c)
            if key in self.master.cells:
                cell = self.master.cells[key]
                tinted_img = load_svg_as_photoimage(
                    self.selected_path,
                    size=(CELL_SIZE - 6, CELL_SIZE - 6),
                    tint="#FFFFFF"
                )
                cell.set_icon(tinted_img, path=self.selected_path)
        self.destroy()

    def apply_icon_to_all(self):
        if not self.selected_path:
            return

        for r in range(5):
            for c in range(10):
                key = (self.section, r, c)
                if key in self.master.cells:
                    cell = self.master.cells[key]
                    tinted_img = load_svg_as_photoimage(
                        self.selected_path,
                        size=(CELL_SIZE - 6, CELL_SIZE - 6),
                        tint="#FFFFFF"
                    )
                    cell.set_icon(tinted_img, path=self.selected_path)
        self.destroy()


if __name__ == "__main__":
    app = IconGridApp()
    app.mainloop()
