# sidebar/sidebar.py
from typing import Optional
import tkinter as tk
from tkinter import ttk
from .base import SidebarBase, SidebarConfig
from .shortcuts_tab import ShortcutsTab
from .credentials_tab import CredentialsTab
from .hotkey_tab import HotkeyTab

class Sidebar(SidebarBase):
    """Main sidebar component that integrates all tab components"""
    
    def __init__(self, parent, db_manager, hotkey_manager, main_window):
        # Initialize base class with just parent first
        ttk.Frame.__init__(self, parent)
        
        # Store config
        self.config = SidebarConfig()
        
        # Initialize base class variables
        self.db_manager = db_manager
        self.hotkey_manager = hotkey_manager
        self.main_window = main_window
        
        # Configure grid layout for parent to make sidebar vertically responsive
        parent.grid_rowconfigure(0, weight=1)  # Ensure parent allows vertical expansion
        parent.grid_columnconfigure(0, weight=1)  # Ensure parent allows horizontal expansion

        # Create notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)  # Added padding to prevent edge overflow

        # Set a minimum size for the notebook to prevent overflow issues
        self.notebook.update_idletasks()  # Ensure the widget sizes are calculated correctly
        self.notebook.grid_propagate(False)  # Prevent the notebook from expanding uncontrollably

        # Create and initialize tabs
        self.create_tabs()
        self.initialize_tabs()
        self.configure_grid()
    
    def initialize_tabs(self) -> None:
        """Initialize functionality for each tab"""
        # Initialize shortcuts tab
        self.shortcuts_tab.bind_shortcut_select(self._on_shortcut_select)
        self.shortcuts_tab.bind_context_menu(self._on_context_menu)
        
        # Initialize credentials tab
        if hasattr(self.credentials_tab, 'load_services'):
            self.credentials_tab.load_services()
        
        # Initialize hotkeys tab
        if hasattr(self.hotkeys_tab, 'load_hotkeys'):
            self.hotkeys_tab.load_hotkeys()

    def create_tabs(self):
        """Create and setup all tabs"""
        # Create tab instances
        self.shortcuts_tab = ShortcutsTab(self.notebook, self.config)
        self.credentials_tab = CredentialsTab(
            self.notebook,
            self.db_manager,
            self.hotkey_manager,
            self.main_window,
            self.config
        )
        self.hotkeys_tab = HotkeyTab(
            self.notebook,
            self.db_manager,
            self.hotkey_manager,
            self.config
        )
        
        # Add tabs to notebook
        self.notebook.add(self.shortcuts_tab, text="Shortcuts")
        self.notebook.add(self.credentials_tab, text="Accounts")
        self.notebook.add(self.hotkeys_tab, text="Hotkeys")

    def configure_grid(self):
        # Configure the grid for the Sidebar frame
        self.grid_rowconfigure(0, weight=1)  # Allow the Notebook to expand vertically
        self.grid_columnconfigure(0, weight=1)  # Allow the Notebook to expand horizontally

    def load_shortcuts(self, shortcuts):
        """Load shortcuts into the shortcuts tab"""
        self.shortcuts_tab.load_shortcuts(shortcuts)
    
    def get_selected_shortcut(self):
        """Get the currently selected shortcut"""
        return self.shortcuts_tab.get_selected_shortcut()
    
    def clear_selection(self):
        """Clear the current selection in shortcuts tab"""
        self.shortcuts_tab.clear_selection()
    
    def _on_shortcut_select(self, selected):
        """Handle shortcut selection"""
        if hasattr(self.main_window, 'on_shortcut_select'):
            self.main_window.on_shortcut_select(selected)
    
    def _on_context_menu(self, event):
        """Handle context menu event"""
        if hasattr(self.main_window, 'on_context_menu'):
            self.main_window.on_context_menu(event)
    
    @property
    def current_service_id(self):
        """Get the current service ID from credentials tab"""
        return self.credentials_tab.current_service_id

    def update_credential_list(self) -> None:
        """Update the credential list display"""
        self.credentials_tab.update_credential_list()

    def load_services(self) -> None:
        """Load services into the credentials tab"""
        self.credentials_tab.load_services()

    @property
    def service_var(self) -> Optional[tk.StringVar]:
        return self.credentials_tab.service_var if self.credentials_tab else None
    
    @property
    def credential_list(self) -> Optional[ttk.Treeview]:
        return self.credentials_tab.credential_list if self.credentials_tab else None
    
    @property
    def cred_status(self) -> Optional[ttk.Label]:
        return self.credentials_tab.cred_status if self.credentials_tab else None
    
    @property
    def current_service_id(self) -> Optional[int]:
        return self.credentials_tab.current_service_id if self.credentials_tab else None