# sidebar/shortcuts_tab.py
from typing import Optional, Callable, Tuple, List
import tkinter as tk
from tkinter import ttk
from .base import SidebarBase, SidebarConfig

class ShortcutsTab(ttk.Frame):
    """Component for managing shortcuts in the sidebar"""
    
    def __init__(self, parent: ttk.Frame, config: SidebarConfig):
        super().__init__(parent)
        self.config = config
        self.shortcut_list: Optional[ttk.Treeview] = None
        self.search_var: Optional[tk.StringVar] = None
        self.all_shortcuts: List[Tuple[str, str]] = []
        self.on_shortcut_select: Optional[Callable] = None
        self.on_context_menu: Optional[Callable] = None
        
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Initialize the UI components"""
        self.create_header()
        self.create_search_bar()
        self.create_shortcuts_list()
        
        # Configure grid weights
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def create_header(self) -> None:
        """Create the header section with buttons"""
        header_frame = ttk.Frame(self, style='Dark.TFrame')
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(header_frame, text="Shortcuts", style='Header.TLabel').pack(side="left", padx=5)
        
        self.clear_cache_btn = ttk.Button(
            header_frame,
            text="Clear Cache",
            command=self._on_clear_cache
        )
        self.clear_cache_btn.pack(side="right", padx=5)
    
    def create_search_bar(self) -> None:
        """Create the search bar with real-time filtering"""
        search_frame = ttk.Frame(self, style='Dark.TFrame')
        search_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        # Search container
        entry_frame = ttk.Frame(search_frame, style='Dark.TFrame')
        entry_frame.pack(fill="x")
                
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_changed)
        
        self.search_entry = ttk.Entry(
            entry_frame,
            textvariable=self.search_var,
            style='Search.TEntry'
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Clear button
        clear_btn = ttk.Label(
            entry_frame,
            text="✕",
            style='Header.TLabel',
            cursor="hand2"
        )
        clear_btn.pack(side="right", padx=5)
        clear_btn.bind('<Button-1>', self._clear_search)
    
    def create_shortcuts_list(self) -> None:
        """Create the treeview for displaying shortcuts"""
        list_frame = ttk.Frame(self, style='Dark.TFrame')
        list_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # Create Treeview
        self.shortcut_list = ttk.Treeview(
            list_frame,
            columns=("Shortcuts", "Content"),
            show="headings",
            selectmode="browse",
            style="Dark.Treeview"
        )
        
        # Configure columns
        self.shortcut_list.heading("Shortcuts", text="Shortcuts", anchor="w")
        self.shortcut_list.heading("Content", text="Content", anchor="w")
        
        self.shortcut_list.column(
            "Shortcuts",
            width=self.config.shortcut_column_width,
            minwidth=self.config.shortcut_column_width,
            stretch=True
        )
        self.shortcut_list.column(
            "Content",
            width=self.config.content_column_width,
            minwidth=200,
            stretch=True
        )
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.shortcut_list.yview)
        self.shortcut_list.configure(yscrollcommand=scrollbar.set)
        
        # Pack components
        self.shortcut_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind events
        self.shortcut_list.bind('<<TreeviewSelect>>', self._on_shortcut_select)
        self.shortcut_list.bind('<Button-3>', self._on_right_click)
    
    def load_shortcuts(self, shortcuts: List[Tuple[str, str]]) -> None:
        """Load shortcuts into the treeview"""
        self.all_shortcuts = shortcuts
        self._refresh_shortcuts_display()
    
    def _refresh_shortcuts_display(self, filter_text: str = "") -> None:
        """Refresh the shortcuts display with optional filtering"""
        self.shortcut_list.delete(*self.shortcut_list.get_children())
        
        for shortcut, content in self.all_shortcuts:
            if (not filter_text or
                filter_text in shortcut.lower() or
                filter_text in content.lower()):
                display_content = self._format_display_text(content)
                self.shortcut_list.insert("", "end", values=(shortcut, display_content))
    
    def _format_display_text(self, content: str) -> str:
        """Format the display text with maximum length"""
        display_text = ' '.join(content.split())
        if len(display_text) > self.config.max_display_length:
            return f"{display_text[:self.config.max_display_length]}..."
        return display_text
    
    def _on_search_changed(self, *args) -> None:
        """Handle search text changes"""
        search_text = self.search_var.get().lower()
        self._refresh_shortcuts_display(search_text)
    
    def _clear_search(self, event=None) -> None:
        """Clear the search entry"""
        self.search_var.set('')
        self.search_entry.focus()
    
    def _on_clear_cache(self) -> None:
        """Handle clear cache button click"""
        self._trigger_event('<<ClearCache>>')
    
    def _on_shortcut_select(self, event) -> None:
        """Handle shortcut selection"""
        if self.on_shortcut_select:
            selected = self.get_selected_shortcut()
            self.on_shortcut_select(selected)
    
    def _on_right_click(self, event) -> None:
        """Handle right-click on shortcuts"""
        item = self.shortcut_list.identify_row(event.y)
        if item:
            self.shortcut_list.selection_set(item)
            if self.on_context_menu:
                self.on_context_menu(event)
    
    def get_selected_shortcut(self) -> Optional[Tuple[str, str]]:
        """Get the currently selected shortcut"""
        selected = self.shortcut_list.selection()
        if selected:
            item = self.shortcut_list.item(selected[0])
            return tuple(item['values'])
        return None
    
    def clear_selection(self) -> None:
        """Clear the current selection"""
        self.shortcut_list.selection_remove(*self.shortcut_list.selection())
    
    def bind_shortcut_select(self, callback: Callable) -> None:
        """Bind callback for shortcut selection"""
        self.on_shortcut_select = callback
    
    def bind_context_menu(self, callback: Callable) -> None:
        """Bind callback for context menu"""
        self.on_context_menu = callback