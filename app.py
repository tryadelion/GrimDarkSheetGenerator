import tkinter as tk
from tkinter import filedialog, colorchooser
import os
import json

# Basic Config
APP_WIDTH = 1200
APP_HEIGHT = 800
CELL_SIZE = 48

ICON_FOLDER = "icons"
FONT_FOLDER = "fonts"
SESSION_FOLDER = "sessions"
EXPORT_FOLDER = "exports"

DEFAULT_HIGHLIGHT_COLOR = "#1f6aa5"
DARK_BG = "#222222"
MID_BG = "#333333"
LIGHT_TEXT = "#eeeeee"

class IconCell(tk.Frame):
    def __init__(self, master, row, col, *args, **kwargs):
        super().__init__(master, width=CELL_SIZE, height=CELL_SIZE, bg=DARK_BG, *args, **kwargs)
        self.grid_propagate(False)
        self.row = row
        self.col = col
        self.content = None
        self.color = LIGHT_TEXT

        self.inner_frame = tk.Frame(self, bg=MID_BG)
        self.inner_frame.pack(expand=True, fill="both", padx=3, pady=3)
        self.inner_frame.grid_propagate(False)

        self.canvas = tk.Canvas(self.inner_frame, width=CELL_SIZE-6, height=CELL_SIZE-6, highlightthickness=0, bg=MID_BG)
        self.canvas.pack(expand=True, fill="both")

    def set_icon(self, image):
        self.content = image
        self.canvas.delete("all")
        self.canvas.create_image((CELL_SIZE-6)//2, (CELL_SIZE-6)//2, anchor="center", image=image)
        self.canvas.image = image

    def set_text(self, text, font):
        self.content = text
        self.canvas.delete("all")
        self.canvas.create_text((CELL_SIZE-6)//2, (CELL_SIZE-6)//2, text=text, font=font, fill=LIGHT_TEXT)

    def clear(self):
        self.content = None
        self.canvas.delete("all")

    def highlight(self, color=DEFAULT_HIGHLIGHT_COLOR):
        self.configure(bg=color)

    def unhighlight(self):
        self.configure(bg=DARK_BG)

class IconGridApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Icon Grid Editor")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.configure(bg=DARK_BG)

        self.selected_cell = None
        self.cells = {}

        self.main_frame = tk.Frame(self, bg=DARK_BG)
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.grid_rowconfigure((0, 1), weight=1)
        self.main_frame.grid_columnconfigure((0, 1), weight=1)

        self.top_left_frame = self.create_section("Left Shoulder Pad", 0, 0)
        self.top_right_frame = self.create_section("Right Shoulder Pad", 0, 1)
        self.bottom_left_frame = self.create_section("Gothic Numerals", 1, 0)
        self.bottom_right_frame = self.create_section("Imperial Numerals", 1, 1)

    def create_section(self, title, row, column):
        frame = tk.Frame(self.main_frame, bg=DARK_BG)
        frame.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        header = tk.Label(frame, text=title, font=("Arial", 18, "bold"), bg=DARK_BG, fg=LIGHT_TEXT)
        header.grid(row=0, column=0, pady=5)

        grid_container = tk.Frame(frame, bg=DARK_BG)
        grid_container.grid(row=1, column=0, sticky="nsew")
        self.create_grid(grid_container, title)

        return frame

    def create_grid(self, parent, section_title):
        for r in range(5):
            parent.grid_rowconfigure(r, weight=1)
            for c in range(11):
                parent.grid_columnconfigure(c, weight=1)
                if c == 0:
                    btn = tk.Button(parent, text="Set", width=4, command=lambda s=section_title, r=r: self.set_row_action(s, r),
                                    bg=MID_BG, fg=LIGHT_TEXT, activebackground="#555555", relief="flat", highlightbackground=DARK_BG)
                    btn.grid(row=r, column=c, padx=1, pady=1)
                else:
                    cell = IconCell(parent, r, c-1)
                    cell.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")
                    cell.bind("<Button-1>", lambda e, s=section_title, r=r, c=c-1: self.select_cell(s, r, c))
                    cell.canvas.bind("<Button-1>", lambda e, s=section_title, r=r, c=c-1: self.select_cell(s, r, c))
                    self.cells[(section_title, r, c-1)] = cell

    def select_cell(self, section, row, col):
        if self.selected_cell:
            self.selected_cell.unhighlight()
        key = (section, row, col)
        if key in self.cells:
            self.selected_cell = self.cells[key]
            self.selected_cell.highlight()

    def set_row_action(self, section, row):
        IconPickerDialog(self, section, row)

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

        self.load_icons()

    def load_icons(self):
        for filename in os.listdir(ICON_FOLDER):
            print(f"[LOG] Found file: {filename}")
            if filename.lower().endswith((".png", ".gif")):
                path = os.path.join(ICON_FOLDER, filename)
                try:
                    tk_img = tk.PhotoImage(file=path)
                    self.icon_images.append(tk_img)
                    btn = tk.Button(self.icon_frame, image=tk_img, text="", command=lambda p=path: self.select_icon(p),
                                    bg=DARK_BG, bd=0, relief="flat", highlightthickness=0)
                    btn.pack(padx=5, pady=5)
                    print(f"[LOG] Displaying icon button for: {filename}")
                except Exception as e:
                    print(f"[ERROR] Failed to load {filename}: {e}")
        self.scroll_canvas.update_idletasks()

    def select_icon(self, path):
        self.selected_path = path
        tk_img = tk.PhotoImage(file=path)
        self.selected_image = tk_img
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

if __name__ == "__main__":
    app = IconGridApp()
    app.mainloop()
