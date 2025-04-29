import tkinter as tk
from tkinter import filedialog, messagebox
from tkcolorpicker import askcolor
from PIL import Image, ImageTk, ImageFont
import tkinter.font as tkfont
import os, ctypes
import json

# Basic Config
APP_WIDTH = 1200
APP_HEIGHT = 900
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

class IconCell(tk.Frame):
    def __init__(self, master, row, col, *args, **kwargs):
        super().__init__(master, width=CELL_SIZE, height=CELL_SIZE, bg=DARK_BG, *args, **kwargs)
        self.grid_propagate(False)
        self.row = row
        self.col = col
        self.content = None
        self.font = ("Arial", 12, "bold")

        self.inner_frame = tk.Frame(self, bg=MID_BG)
        self.inner_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self.inner_frame, width=CELL_SIZE-6, height=CELL_SIZE-6,
                                highlightthickness=0, bg=MID_BG)
        self.canvas.place(x=3, y=3)

    def set_icon(self, image):
        self.content = image
        self.inner_frame.configure(bg=DARK_BG)
        self.canvas.configure(bg=DARK_BG)
        self.canvas.delete("all")
        img = image
        if image.width() > CELL_SIZE-6 or image.height() > CELL_SIZE-6:
            factor = max(image.width()/(CELL_SIZE-6), image.height()/(CELL_SIZE-6))
            img = image._PhotoImage__photo.subsample(int(factor))
        self.canvas.create_image((CELL_SIZE-6)//2, (CELL_SIZE-6)//2,
                                 image=img, anchor="center")
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
        self.title("Icon Grid Editor")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.configure(bg=DARK_BG)

        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)

        file_menu.add_command(label="Load Layout", command=self.load_layout)
        file_menu.add_command(label="Save Layout", command=self.save_layout)
        file_menu.add_separator()
        file_menu.add_command(label="Print", command=self.print_layout)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        self.cells = {}
        mf = tk.Frame(self, bg=DARK_BG)
        mf.pack(fill='both', expand=True)
        mf.grid_rowconfigure(0,weight=1); mf.grid_rowconfigure(1,weight=1)
        mf.grid_columnconfigure(0,weight=1); mf.grid_columnconfigure(1,weight=1)
        self.create_section(mf, "Left Shoulder Pad",0,0)
        self.create_section(mf, "Right Shoulder Pad",0,1)
        self.create_section(mf, "Gothic Numerals",1,0)
        self.create_section(mf, "Imperial Numerals",1,1)
        self.prefill_numerals()

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

    def pick_color_action(self, section, row):
        color = askcolor(title="Pick a Color")
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
        self.icon_images = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        container = tk.Frame(self, bg=DARK_BG)
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.scroll_canvas = tk.Canvas(container, bg=DARK_BG, highlightthickness=0)
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.scroll_canvas.yview)
        scrollbar.pack(side="right", fill="y")

        self.icon_frame = tk.Frame(self.scroll_canvas, bg=DARK_BG)
        self.scroll_canvas.create_window((0, 0), window=self.icon_frame, anchor="nw")
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        self.icon_frame.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))

        self.preview_frame = tk.Frame(self, bg=MID_BG)
        self.preview_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.preview_label = tk.Label(self.preview_frame, text="No Icon Selected", bg=MID_BG, fg=LIGHT_TEXT)
        self.preview_label.pack(expand=True, fill="both")

        self.button_frame = tk.Frame(self, bg=DARK_BG)
        self.button_frame.grid(row=1, column=0, columnspan=2, pady=10)

        self.cancel_button = tk.Button(self.button_frame, text="Cancel", command=self.destroy,
                                       bg=MID_BG, fg=LIGHT_TEXT, activebackground="#555555", relief="flat", highlightbackground=DARK_BG)
        self.cancel_button.pack(side="left", padx=10)

        self.set_button = tk.Button(self.button_frame, text="Set Icon", command=self.apply_icon,
                                    bg=MID_BG, fg=LIGHT_TEXT, activebackground="#555555", relief="flat", highlightbackground=DARK_BG)
        self.set_button.pack(side="right", padx=10)

        self.apply_all_button = tk.Button(self.button_frame, text="Apply to All", command=self.apply_icon_to_all,
                                  bg=MID_BG, fg=LIGHT_TEXT, relief="flat")
        self.apply_all_button.pack(side="right", padx=5)

        self.load_icons()

    def load_icons(self):
        files = [f for f in os.listdir(ICON_FOLDER) if f.lower().endswith((".png", ".gif"))]
        for idx, filename in enumerate(files):
            path = os.path.join(ICON_FOLDER, filename)
            try:
                img = Image.open(path)
                img.thumbnail((60, 60))
                tk_img = ImageTk.PhotoImage(img)
                self.icon_images.append(tk_img)
                row, col = divmod(idx, 5)
                btn = tk.Button(self.icon_frame, image=tk_img, text="", command=lambda p=path: self.select_icon(p),
                                bg=DARK_BG, bd=0, relief="flat", highlightthickness=0)
                btn.grid(row=row, column=col, padx=5, pady=5)
            except Exception as e:
                print(f"[ERROR] Failed to load {filename}: {e}")
        self.scroll_canvas.update_idletasks()

    def select_icon(self, path):
        self.selected_path = path
        img = Image.open(path)

        preview_width = self.preview_frame.winfo_width() or 300
        preview_height = self.preview_frame.winfo_height() or 400

        img.thumbnail((preview_width, preview_height))
        self.selected_image = ImageTk.PhotoImage(img)

        self.preview_label.configure(image=self.selected_image, text="")
        self.preview_label.image = self.selected_image

    def apply_icon(self):
        if not self.selected_image:
            return
        for c in range(10):
            key = (self.section, self.row, c)
            if key in self.master.cells:
                self.master.cells[key].set_icon(self.selected_image)
        self.destroy()
    
    def apply_icon_to_all(self):
        if not self.selected_image:
            return

        for r in range(5):
            for c in range(10):
                key = (self.section, r, c)
                if key in self.master.cells:
                    self.master.cells[key].set_icon(self.selected_image)
        self.destroy()

if __name__ == "__main__":
    app = IconGridApp()
    app.mainloop()
