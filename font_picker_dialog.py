import os
import tkinter as tk
from tkinter import font
from PIL import ImageFont

COLOR_BG = "#1e1e1e"
COLOR_FG = "#ffffff"
FONT_DEFAULT = "Arial"

class FontPickerDialog(tk.Toplevel):
    def __init__(self, master, section, row):
        super().__init__(master)
        self.title(f"Pick Font: {section} Row {row+1}")
        self.configure(bg=COLOR_BG)
        self.section, self.row = section, row
        self.result = None
        self.selected_index = None
        self.hover_index = None

        self.fonts = [f for f in os.listdir("fonts") if f.lower().endswith(('.ttf', '.otf'))]

        self.canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_hover)

        self.draw_font_list()

        btnf = tk.Frame(self, bg=COLOR_BG)
        btnf.pack(side="bottom", fill="x", pady=5)
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
                font_obj = font.Font(family=FONT_DEFAULT, size=16)

            color = COLOR_FG if idx != self.hover_index else "#66ccff"
            self.canvas.create_text(30, y, anchor='w', text=f"{name} - Abc IX 3", font=font_obj, fill=color)
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