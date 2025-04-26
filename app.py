import customtkinter as ctk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageTk, ImageGrab, ImageOps, ImageEnhance
import os
import json

# Basic Config
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

APP_WIDTH = 1200
APP_HEIGHT = 800
GRID_ROWS = 22
GRID_COLS = 26
CELL_SIZE = 48

ICON_FOLDER = "icons"
FONT_FOLDER = "fonts"
SESSION_FOLDER = "sessions"
EXPORT_FOLDER = "exports"

class IconCell(ctk.CTkFrame):
    def __init__(self, master, row, col, *args, **kwargs):
        super().__init__(
            master,
            width=CELL_SIZE,
            height=CELL_SIZE,
            fg_color="#222222",  # Darker outer frame for \"border\" effect
            corner_radius=0,
            *args, **kwargs
        )
        self.grid_propagate(False)
        self.row = row
        self.col = col
        self.content = None
        self.color = "#FFFFFF"

        self.inner_frame = ctk.CTkFrame(self, fg_color="#333333", corner_radius=0)
        self.inner_frame.pack(expand=True, fill="both", padx=2, pady=2)

        self.label = ctk.CTkLabel(self.inner_frame, text="", width=CELL_SIZE-4, height=CELL_SIZE-4)
        self.label.pack(expand=True, fill="both")

    def set_icon(self, image):
        self.content = image
        self.label.configure(image=image, text="")

    def set_text(self, text, font):
        self.content = text
        self.label.configure(text=text, font=font)

    def clear(self):
        self.content = None
        self.label.configure(image=None, text="")

    def highlight(self, color="blue"):
        self.configure(fg_color=color)

    def unhighlight(self):
        self.configure(fg_color="#222222")


class IconGridApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Icon Grid Editor")
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")

        self.grid_frame = ctk.CTkFrame(self)
        self.grid_frame.pack(side="left", fill="both", expand=True)

        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.pack(side="right", fill="both", expand=True)

        self.cells = {}
        self.selected_cells = []

        self.create_grid()
        self.create_menu()

    def create_grid(self):
        for r in range(GRID_ROWS):
            self.grid_frame.rowconfigure(r, weight=1)
            for c in range(GRID_COLS):
                self.grid_frame.columnconfigure(c, weight=1)
                cell = IconCell(self.grid_frame, r, c)
                cell.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")
                cell.bind("<Button-1>", lambda e, r=r, c=c: self.select_cell(r, c))
                cell.label.bind("<Button-1>", lambda e, r=r, c=c: self.select_cell(r, c))
                self.cells[(r, c)] = cell

    def create_menu(self):
        self.menu_frame = ctk.CTkFrame(self.grid_frame, height=40)
        self.menu_frame.grid(row=GRID_ROWS, column=0, columnspan=GRID_COLS, sticky="ew")

        self.load_icon_button = ctk.CTkButton(self.menu_frame, text="Load Icon", command=self.load_icon)
        self.load_icon_button.pack(side="left", padx=5)

        self.paste_button = ctk.CTkButton(self.menu_frame, text="Paste Image", command=self.paste_image)
        self.paste_button.pack(side="left", padx=5)

        self.color_picker_button = ctk.CTkButton(self.menu_frame, text="Pick Color", command=self.pick_color)
        self.color_picker_button.pack(side="left", padx=5)

    def select_cell(self, row, col):
        for (r, c), cell in self.cells.items():
            cell.unhighlight()
        self.selected_cells = [(row, col)]
        self.cells[(row, col)].highlight()

    def load_icon(self):
        filepath = filedialog.askopenfilename(initialdir=ICON_FOLDER, filetypes=[("Image Files", "*.png;*.gif;*.svg")])
        if filepath:
            img = Image.open(filepath).convert("RGBA")
            img = img.resize((CELL_SIZE-4, CELL_SIZE-4), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, size=(CELL_SIZE-4, CELL_SIZE-4))
            for (r, c) in self.selected_cells:
                self.cells[(r, c)].set_icon(ctk_img)

    def paste_image(self):
        try:
            img = ImageGrab.grabclipboard()
            if img:
                img = img.convert("RGBA")
                img = img.resize((CELL_SIZE-4, CELL_SIZE-4), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, size=(CELL_SIZE-4, CELL_SIZE-4))
                for (r, c) in self.selected_cells:
                    self.cells[(r, c)].set_icon(ctk_img)
        except Exception as e:
            print(f"Paste failed: {e}")

    def pick_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            for (r, c) in self.selected_cells:
                self.cells[(r, c)].color = color
                # Apply color tint if image is present
                content = self.cells[(r, c)].content
                if isinstance(content, ctk.CTkImage):
                    # Re-tint would be implemented here in future versions
                    pass

if __name__ == "__main__":
    app = IconGridApp()
    app.mainloop()
