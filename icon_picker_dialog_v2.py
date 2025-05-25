import tkinter as tk
from tkinter import ttk
from globals import COLOR_BG, COLOR_FG, FONT_DEFAULT, get_cached_icon, TAG_COLOR_MAP

class IconPickerDialogV2(tk.Toplevel):
    def __init__(self, parent, icon_entries):
        super().__init__(parent)
        self.title("Pick an Icon")
        self.configure(bg=COLOR_BG)
        self.icon_entries = icon_entries
        self.result = None
        self.selected_tag = None
        self.selected_row = None
        self.rendering_complete = True  # Controls click blocking
        self._active_scroll_target = None

        self.geometry("820x700")
        self.resizable(False, False)

        # Main layout
        main_frame = tk.Frame(self, bg=COLOR_BG)
        main_frame.pack(fill="both", expand=True, pady=(0, 20))

        # --- TAG PANEL ---
        tag_panel_container = tk.Frame(main_frame, bg="#1e1e1e", height=600)
        tag_panel_container.pack(side="left", fill="y")

        self.tag_canvas = tk.Canvas(tag_panel_container, bg="#1e1e1e", highlightthickness=0, width=200)
        tag_scrollbar = ttk.Scrollbar(tag_panel_container, orient="vertical", command=self.tag_canvas.yview)
        tag_scrollable_frame = tk.Frame(self.tag_canvas, bg="#1e1e1e")

        tag_frame_window = self.tag_canvas.create_window((0, 0), window=tag_scrollable_frame, anchor="nw")
        self.tag_canvas.configure(yscrollcommand=tag_scrollbar.set)

        def update_tag_scroll(_=None):
            self.tag_canvas.configure(scrollregion=self.tag_canvas.bbox("all"))

        def resize_tag_frame(event):
            self.tag_canvas.itemconfig(tag_frame_window, width=event.width)

        tag_scrollable_frame.bind("<Configure>", update_tag_scroll)
        self.tag_canvas.bind("<Configure>", resize_tag_frame)

        self.tag_canvas.pack(side="left", fill="both", expand=True)
        tag_scrollbar.pack(side="right", fill="y")

        tag_panel = tag_scrollable_frame
        tk.Label(tag_panel, text="Tags", bg="#1e1e1e", fg="white", font=(FONT_DEFAULT, 10, "bold")).pack(anchor="nw", padx=8, pady=5)

        all_tags = set()

        for entry in icon_entries:
            if entry.tags:
                all_tags.update(entry.tags[:2])
            else:
                all_tags.add("Unknown")

        all_tags = sorted(all_tags)

        for tag in all_tags:
            btn = tk.Button(tag_panel, text=tag, bg="#2e2e2e", fg="white", relief="flat",
                            font=(FONT_DEFAULT, 9), anchor="w")
            btn.pack(fill="x", padx=6, pady=1)
            btn.bind("<Button-1>", lambda e, t=tag, b=btn: self.toggle_tag_filter(t, b))

        # --- ICON LIST PANEL ---
        outer = tk.Frame(main_frame, bg=COLOR_BG)
        outer.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(outer, bg=COLOR_BG, highlightthickness=0)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLOR_BG)
        canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        def update_scrollregion(_=None):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.itemconfig(canvas_frame, width=self.canvas.winfo_width())

        self.scrollable_frame.bind("<Configure>", update_scrollregion)
        self.canvas.bind("<Configure>", update_scrollregion)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mousewheel routing
        self.canvas.bind("<Enter>", lambda e: self._set_active_scroll_target(self.canvas))
        self.canvas.bind("<Leave>", lambda e: self._clear_scroll_target())
        self.tag_canvas.bind("<Enter>", lambda e: self._set_active_scroll_target(self.tag_canvas))
        self.tag_canvas.bind("<Leave>", lambda e: self._clear_scroll_target())

        self.bind("<MouseWheel>", self._on_mouse_scroll)
        self.bind("<Button-4>", lambda e: self._on_mouse_scroll(e, delta=-1))
        self.bind("<Button-5>", lambda e: self._on_mouse_scroll(e, delta=1))

        self.entry_frames = []
        self.show_instruction_text()

        # Footer buttons
        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.pack(fill="x", pady=10, side="bottom")
        tk.Button(btn_frame, text="Cancel", command=self.destroy, bg="#444", fg="white", relief="flat").pack(side="left", padx=8)
        tk.Button(btn_frame, text="Apply to All", command=self.apply_icon_to_all, bg="#444", fg="white", relief="flat").pack(side="right", padx=(4, 8))
        tk.Button(btn_frame, text="Apply", command=self.apply_icon, bg="#444", fg="white", relief="flat").pack(side="right", padx=(8, 4))

    def _set_active_scroll_target(self, widget): self._active_scroll_target = widget
    def _clear_scroll_target(self): self._active_scroll_target = None

    def _on_mouse_scroll(self, event, delta=None):
        widget = self._active_scroll_target
        if not widget:
            return
        direction = delta if delta is not None else int(-1 * (event.delta / 120))
        top, bottom = widget.yview()
        if (direction < 0 and top <= 0) or (direction > 0 and bottom >= 1):
            return
        widget.yview_scroll(direction, "units")

    def show_instruction_text(self):
        for f in self.entry_frames:
            f.destroy()
        self.entry_frames.clear()

        msg = ("Pick a tag from the list of recognized tags, or add images to the icons folder\n"
               "following the pattern:\nicon name [tag1, tag2, tag3, tag4].svg")
        label = tk.Label(self.scrollable_frame, text=msg, bg=COLOR_BG, fg="#bbb", font=(FONT_DEFAULT, 10),
                         justify="left", wraplength=380)
        label.pack(pady=40, padx=20)
        self.entry_frames.append(label)

    def populate_icons(self):
        self.canvas.yview_moveto(0)
        self.rendering_complete = False

        self.loading_overlay = tk.Frame(self.canvas, bg="#111")
        self.loading_overlay.place(in_=self.canvas, relx=0, rely=0, relwidth=1, relheight=1)

        tk.Label(self.loading_overlay, text="Loading icons...", fg="white", bg="#111", font=(FONT_DEFAULT, 12, "bold")).pack(pady=20)
        progress = ttk.Progressbar(self.loading_overlay, mode="indeterminate")
        progress.pack(pady=10, fill="x", padx=20)
        progress.start(10)

        self.scrollable_frame.update_idletasks()
        self.after(50, lambda: self._populate_icons_lazy(progress))

    def _populate_icons_lazy(self, progress):
        for f in self.entry_frames:
            f.destroy()
        self.entry_frames.clear()

        filtered = [
            e for e in self.icon_entries
            if (not self.selected_tag)
            or (self.selected_tag == "Unknown" and not e.tags)
            or (self.selected_tag in e.tags)
        ]

        self._render_batch(filtered, 0, 30, progress)

    def _render_batch(self, entries, index, batch_size, progress):
        if index >= len(entries):
            progress.stop()
            self.loading_overlay.destroy()
            self.scrollable_frame.configure(bg=COLOR_BG)
            self.scrollable_frame.update_idletasks()
            self.rendering_complete = True
            return

        for i in range(index, min(index + batch_size, len(entries))):
            entry = entries[i]
            if not entry.thumbnail:
                entry.thumbnail = get_cached_icon(entry.file, size=(40, 40), color=COLOR_FG)
            if not entry.thumbnail:
                continue

            frame = tk.Frame(self.scrollable_frame, bg="#2a2a2a", padx=4, pady=4)
            frame.pack(fill="x", padx=6, pady=3)
            self.entry_frames.append(frame)

            icon_label = tk.Label(frame, image=entry.thumbnail, bg="#2a2a2a")
            icon_label.image = entry.thumbnail
            icon_label.grid(row=0, column=0, rowspan=2, padx=5, pady=5)

            name_label = tk.Label(frame, text=entry.name, fg="white", bg="#2a2a2a", font=(FONT_DEFAULT, 10))
            name_label.grid(row=0, column=1, sticky="w")

            tag_frame = tk.Frame(frame, bg="#2a2a2a")
            tag_frame.grid(row=1, column=1, sticky="w", pady=(2, 0))
            self.render_tag_pills(tag_frame, entry.tags, entry, frame)

            for widget in (frame, icon_label, name_label, tag_frame):
                widget.bind("<Button-1>", lambda e, ent=entry, fr=frame: self.select_icon(ent, fr))

        self.after(10, lambda: self._render_batch(entries, index + batch_size, batch_size, progress))

    def render_tag_pills(self, parent, tags, entry, frame):
        max_width = 400
        row = tk.Frame(parent, bg=parent['bg'])
        row.pack(anchor="w", fill="x")
        current_width = 0
        for tag in tags:
            bg, fg = TAG_COLOR_MAP.get(tag, ("#444", "white"))
            pill = tk.Label(row, text=tag, bg=bg, fg=fg, font=(FONT_DEFAULT, 8, "bold"),
                            padx=5, pady=1, relief="solid", borderwidth=1)
            pill.update_idletasks()
            pill_width = pill.winfo_reqwidth() + 10
            if current_width + pill_width > max_width:
                row = tk.Frame(parent, bg=parent['bg'])
                row.pack(anchor="w", fill="x")
                current_width = 0
            pill.pack(side="left", padx=2, pady=1)
            pill.bind("<Button-1>", lambda e, ent=entry, fr=frame: self.select_icon(ent, fr))
            current_width += pill_width

    def select_icon(self, entry, frame):
        if not self.rendering_complete:
            return
        self.result = entry
        if self.selected_row:
            try: self.selected_row.config(bg="#2a2a2a")
            except tk.TclError: pass
        self.selected_row = frame
        self.selected_row.config(bg="#444477")

    def toggle_tag_filter(self, tag, button):
        if self.selected_tag == tag:
            self.selected_tag = None
            button.config(bg="#2e2e2e")
        else:
            self.selected_tag = tag
            for child in button.master.winfo_children():
                if isinstance(child, tk.Button):
                    child.config(bg="#2e2e2e")
            button.config(bg="#445577")

        for f in self.entry_frames:
            f.destroy()
        self.entry_frames.clear()

        if self.selected_tag:
            self.after(50, self.populate_icons)
        else:
            self.show_instruction_text()

    def apply_icon(self):
        self.result_mode = "single"
        self.destroy()

    def apply_icon_to_all(self):
        self.result_mode = "all"
        self.destroy()
