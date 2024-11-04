import tkinter as tk
from tkinter import ttk
from config import Styles, Config

class Footer(tk.Frame):
       
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=Styles.COLORS['footer'],
            **kwargs
        )
        self.parent = parent
        
        self.setup_ui()
        
    def setup_ui(self):
        self.create_version_label()
        self.create_author_label()
        
    def create_version_label(self):
        version_label = tk.Label(
            self,
            text=f"v{Config.VERSION}",
            font=Styles.FONTS['text'],
            fg=Styles.COLORS['text']['secondary'],
            bg=Styles.COLORS['footer']
        )
        version_label.pack(side="left", padx=10)
        
    def create_author_label(self):
        author_frame = tk.Frame(
            self,
            bg=Styles.COLORS['footer']
        )
        author_frame.pack(side="right", padx=10)
        
        tk.Label(
            author_frame,
            text="MADE WITH",
            font=Styles.FONTS['text'],
            fg=Styles.COLORS['text']['secondary'],
            bg=Styles.COLORS['footer']
        ).pack(side="left", padx=(0, 5))
        
        tk.Label(
            author_frame,
            text="\u2764",
            font=Styles.FONTS['icon'],
            fg=Styles.COLORS['text']['error'],
            bg=Styles.COLORS['footer']
        ).pack(side="left", padx=(0, 5))
        
        tk.Label(
            author_frame,
            text=f"BY {Config.AUTHOR}",
            font=Styles.FONTS['text'],
            fg=Styles.COLORS['text']['secondary'],
            bg=Styles.COLORS['footer']
        ).pack(side="left")
