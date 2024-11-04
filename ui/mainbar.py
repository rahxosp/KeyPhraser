import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Tuple
from config.styles import Styles

class Mainbar(ttk.Frame):
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.on_save: Optional[Callable] = None
        self.on_delete: Optional[Callable] = None
        self.on_start: Optional[Callable] = None
        self.on_stop: Optional[Callable] = None
        self.setup_ui()

    def setup_ui(self):
        self.create_service_control()
        self.create_editor()
        self.configure_grid()

    def create_service_control(self):
        control_frame = ttk.LabelFrame(self, text="Service Control", padding=10)
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.service_status = ttk.Label(control_frame, text="Status: Stopped", font=Styles.FONTS['text'])
        self.service_status.pack(side="left", padx=5)
        self.start_button = ttk.Button(control_frame, text="Start Service", command=self._on_start_service, style="Accent.TButton")
        self.start_button.pack(side="left", padx=5)
        self.stop_button = ttk.Button(control_frame, text="Stop Service", command=self._on_stop_service, style="Accent.TButton")
        self.stop_button.pack(side="left", padx=5)
        self.stop_button.state(['disabled'])

    def create_editor(self):
        editor_frame = ttk.LabelFrame(self, text="Edit Shortcut", padding=10)
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        editor_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(editor_frame, text="Shortcut:", font=Styles.FONTS['text']).grid(row=0, column=0, sticky="w", pady=5)
        self.shortcut_entry = ttk.Entry(editor_frame, font=Styles.FONTS['text'])
        self.shortcut_entry.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(editor_frame, text="Content:", font=Styles.FONTS['text']).grid(row=1, column=0, sticky="w", pady=5)
        self.content_text = tk.Text(editor_frame, height=10, width=40, wrap="word", font=Styles.FONTS['text'])
        self.content_text.grid(row=1, column=1, sticky="nsew", pady=5)
        content_scroll = ttk.Scrollbar(editor_frame, orient="vertical", command=self.content_text.yview)
        content_scroll.grid(row=1, column=2, sticky="ns", pady=5)
        self.content_text.configure(yscrollcommand=content_scroll.set)

        button_frame = ttk.Frame(editor_frame)
        button_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete", command=self._on_delete_shortcut, style="Danger.TButton").pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save", command=self._on_save_shortcut, style="Accent.TButton").pack(side="right", padx=5)

    def configure_grid(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def bind_save(self, callback: Callable):
        self.on_save = callback

    def bind_delete(self, callback: Callable):
        self.on_delete = callback

    def bind_service_control(self, start_callback: Callable, stop_callback: Callable):
        self.on_start = start_callback
        self.on_stop = stop_callback

    def get_shortcut_data(self) -> Optional[Tuple[str, str]]:
        shortcut = self.shortcut_entry.get().strip()
        content = self.content_text.get('1.0', tk.END).strip()
        return (shortcut, content) if shortcut and content else None

    def set_shortcut_data(self, shortcut: str, content: str):
        self.clear_fields()
        self.shortcut_entry.insert(0, shortcut)
        self.content_text.insert('1.0', content)

    def clear_fields(self):
        self.shortcut_entry.delete(0, tk.END)
        self.content_text.delete('1.0', tk.END)

    def update_service_status(self, is_running: bool):
        status_text = "Running" if is_running else "Stopped"
        status_color = Styles.get_status_color('running' if is_running else 'stopped')
        self.service_status.config(text=f"Status: {status_text}", foreground=status_color)
        self.start_button.state(['disabled'] if is_running else ['!disabled'])
        self.stop_button.state(['!disabled'] if is_running else ['disabled'])

    def _on_save_shortcut(self):
        if self.on_save:
            self.on_save()

    def _on_delete_shortcut(self):
        if self.on_delete:
            self.on_delete()

    def _on_start_service(self):
        if self.on_start:
            self.on_start()

    def _on_stop_service(self):
        if self.on_stop:
            self.on_stop()
