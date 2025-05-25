import tkinter as tk
from tkinter import ttk
import os
from PIL import ImageTk
from icon_parsing import load_icon_entries  # Ensure this is available
from globals import get_cached_icon, COLOR_BG, COLOR_FG, FONT_DEFAULT, TAG_COLOR_MAP

class IconPickerDialog(tk.Toplevel):
    def __init__(self, parent, icon_entries):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=COLOR_BG)

        self.icon_entries = icon_entries
        self.filtered_entries = icon_entries
        self.result = None
        self.selected_frame = None
        self.resizable(False, False)

        print("[DEBUG] IconPickerDialog opened. Icon entries:")
        for entry in self.icon_entries:
            if not hasattr(entry, "thumbnail") or entry.thumbnail is None:
                try:
                    entry.thumbnail = get_cached_icon(entry.file, size=(40, 40), color=COLOR_FG)
                    print(f"  - {entry.name} | file: {entry.file} | thumbnail GENERATED")
                except Exception as e:
                    print(f"  - {entry.name} | file: {entry.file} | FAILED to generate thumbnail: {e}")
                    entry.thumbnail = None
            else:
                print(f"  - {entry.name} | file: {entry.file} | thumbnail OK")

        # --- Titlebar ---
        self._build_titlebar()

        # --- Scrollable Area ---
        self.canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_BG)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        wrapper = tk.Frame(self, bg=COLOR_BG)
        wrapper.pack(fill="both", expand=True, padx=5, pady=5)
        self.canvas.pack(in_=wrapper, side="left", fill="both", expand=True)
        self.scrollbar.pack(in_=wrapper, side="right", fill="y")

        self.populate_icons()

        # --- Buttons ---
        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", pady=(0, 10))
        tk.Button(btn_frame, text="Cancel", command=self.destroy, bg="#333", fg="white", relief="flat").pack(side="left", padx=10)
        tk.Button(btn_frame, text="Apply to All", command=self.apply_icon_to_all, bg="#333", fg="white", relief="flat").pack(side="right", padx=5)
        tk.Button(btn_frame, text="Set Icon", command=self.apply_icon, bg="#333", fg="white", relief="flat").pack(side="right", padx=10)

    def _build_titlebar(self):
        titlebar = tk.Frame(self, bg="#121212", height=30)
        titlebar.pack(fill="x", side="top")
        titlebar.bind("<Button-1>", self.start_move)
        titlebar.bind("<B1-Motion>", self.do_move)
        tk.Label(titlebar, text="Choose an Icon", bg="#111", fg="white", font=(FONT_DEFAULT, 12, "bold")).pack(side="left", padx=10)
        tk.Button(titlebar, text="✕", bg="#222", fg="white", command=self.destroy,
                  relief="flat", bd=0, width=3, height=1).pack(side="right", padx=4, pady=2)

    def render_tag_pills(self, parent, tags):
        for tag in tags:
            bg, fg = TAG_COLOR_MAP.get(tag, ("#444", "white"))
            tk.Label(parent, text=tag, bg=bg, fg=fg, font=(FONT_DEFAULT, 8, "bold"),
                     padx=5, pady=1, relief="solid", borderwidth=1).pack(side="left", padx=2, pady=2)

    def populate_icons(self):
        for entry in self.filtered_entries:
            print(f"[DEBUG] Rendering: {entry.name} | has thumbnail: {bool(entry.thumbnail)}")
            img = entry.thumbnail
            frame = tk.Frame(self.scrollable_frame, bg="#333", highlightbackground="#555", highlightthickness=1)
            frame.pack(fill="x", padx=6, pady=4)

            frame.bind("<Enter>", lambda e, f=frame: f.configure(bg="#444") if f != self.selected_frame else None)
            frame.bind("<Leave>", lambda e, f=frame: f.configure(bg="#333") if f != self.selected_frame else None)

            icon_label = tk.Label(frame, image=img, bg="#333")
            icon_label.image = img
            icon_label.grid(row=0, column=0, rowspan=2, padx=5, pady=5)

            title_label = tk.Label(frame, text=entry.name, fg="white", bg="#333",
                                   font=(FONT_DEFAULT, 10, "bold"), anchor="w", justify="left")
            title_label.grid(row=0, column=1, sticky="w")

            tag_frame = tk.Frame(frame, bg="#333")
            tag_frame.grid(row=1, column=1, sticky="w")
            self.render_tag_pills(tag_frame, entry.tags)

            for widget in (frame, icon_label, title_label, tag_frame):
                widget.bind("<Button-1>", lambda e, ent=entry, fr=frame: self.select_icon(ent, fr))

    def select_icon(self, icon_entry, frame):
        self.result = icon_entry
        if self.selected_frame:
            self.selected_frame.configure(bg="#333")
        self.selected_frame = frame
        frame.configure(bg="#1f6aa5")

    def apply_icon(self):
        self.result_mode = "single"
        self.destroy()

    def apply_icon_to_all(self):
        self.result_mode = "all"
        self.destroy()

    def apply_filter(self):
        self.filtered_entries = self.icon_entries
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.populate_icons()

    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        x = event.x_root - self._x
        y = event.y_root - self._y
        self.geometry(f"+{x}+{y}")
