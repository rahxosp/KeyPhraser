# sidebar/base.py
from typing import Optional, Callable, List, Tuple, Any  # Added Any import
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from utils.helpers import show_error

@dataclass
class SidebarConfig:
    """Configuration class for Sidebar settings"""
    shortcut_column_width: int = 100
    content_column_width: int = 300
    max_display_length: int = 50
    search_delay_ms: int = 300
    position_column_width: int = 50
    credentials_column_width: int = 300

class SidebarBase(ttk.Frame):
    """Base class for sidebar components with common functionality"""
    
    def __init__(self, parent: ttk.Frame, db_manager: Any, hotkey_manager: Any, 
                 main_window: Any, config: SidebarConfig = None):
        # Initialize frame
        ttk.Frame.__init__(self, parent)
        
        # Initialize protected variables first
        self._service_var = tk.StringVar()
        self._service_combo = None
        self._credential_list = None
        self._cred_status = None
        self._current_service_id = None
        
        # Store references
        self.parent = parent
        self.db_manager = db_manager
        self.hotkey_manager = hotkey_manager
        self.main_window = main_window
        self.config = config or SidebarConfig()
        
        # Initialize other variables
        self.search_var = None
        self.search_after_id = None
        self.all_shortcuts = []
        self.on_shortcut_select = None
        self.on_context_menu = None
        
        # Configure grid
        self.configure_grid()

    def _initialize_variables(self):
        """Initialize all instance variables"""
        # Search-related variables
        self.search_var: Optional[tk.StringVar] = None
        self.search_after_id: Optional[str] = None
        self.all_shortcuts: List[Tuple[str, str]] = []
        self.on_shortcut_select: Optional[Callable] = None
        self.on_context_menu: Optional[Callable] = None
        
        # Credential-related variables
        self._service_var: Optional[tk.StringVar] = tk.StringVar()
        self._service_combo: Optional[ttk.Combobox] = None
        self._credential_list: Optional[ttk.Treeview] = None
        self._cred_status: Optional[ttk.Label] = None
        self._current_service_id: Optional[int] = None
        
        # Tab-related variables
        self.notebook: Optional[ttk.Notebook] = None
        self.shortcuts_tab: Optional[ttk.Frame] = None
        self.credentials_tab: Optional[ttk.Frame] = None
        self.hotkeys_tab: Optional[ttk.Frame] = None
    
    def create_header(self, parent_frame: ttk.Frame, title: str = "LIST") -> ttk.Frame:
        """Create a standardized header with title and optional buttons"""
        header_frame = ttk.Frame(parent_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        header_content = ttk.Frame(header_frame, style='Dark.TFrame')
        header_content.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        header_content.grid_columnconfigure(0, weight=1)
        
        ttk.Label(header_content, text=title, style='Header.TLabel').pack(side="left", padx=5)
        
        return header_content
    
    def create_scrollable_frame(self, parent: ttk.Frame) -> tuple[ttk.Frame, ttk.Scrollbar]:
        """Create a frame with scrollbar"""
        container = ttk.Frame(parent)
        scrollbar = ttk.Scrollbar(container, orient="vertical")
        frame = ttk.Frame(container)
        
        scrollbar.pack(side="right", fill="y")
        frame.pack(side="left", fill="both", expand=True)
        
        return frame, scrollbar
    
    def format_display_text(self, content: str) -> str:
        """Format text for display with maximum length"""
        display_text = ' '.join(content.split())
        return (f"{display_text[:self.config.max_display_length]}..." 
                if len(display_text) > self.config.max_display_length 
                else display_text)
    
    def _trigger_event(self, event_name: str, data: str = None) -> None:
        """Safely trigger a custom event"""
        try:
            if data:
                self.winfo_toplevel().event_generate(event_name, data=data)
            else:
                self.winfo_toplevel().event_generate(event_name)
        except Exception as e:
            print(f"Error triggering event {event_name}: {str(e)}")
    
    def _delayed_search(self, *args) -> None:
        """Implement delayed search to improve performance"""
        if self.search_after_id:
            self.after_cancel(self.search_after_id)
        self.search_after_id = self.after(
            self.config.search_delay_ms,
            self._perform_search
        )
    
    def _perform_search(self) -> None:
        """Template method for search functionality"""
        raise NotImplementedError("Subclasses must implement _perform_search")
    
    def bind_shortcut_select(self, callback: Callable) -> None:
        """Bind callback for shortcut selection"""
        self.on_shortcut_select = callback
    
    def bind_context_menu(self, callback: Callable) -> None:
        """Bind callback for context menu"""
        self.on_context_menu = callback
    
    def get_selected_shortcut(self) -> Optional[Tuple[str, str]]:
        """Template method for getting selected shortcut"""
        raise NotImplementedError("Subclasses must implement get_selected_shortcut")
    
    def clear_selection(self) -> None:
        """Template method for clearing selection"""
        raise NotImplementedError("Subclasses must implement clear_selection")
    
    def load_shortcuts(self, shortcuts: List[Tuple[str, str]]) -> None:
        """Template method for loading shortcuts"""
        raise NotImplementedError("Subclasses must implement load_shortcuts")
    
    def load_services(self) -> None:
        """Template method for loading services"""
        raise NotImplementedError("Subclasses must implement load_services")
    
    def create_service_selection(self) -> ttk.Frame:
        """Create service selection frame"""
        service_frame = ttk.Frame(self)
        service_frame.grid(row=0, column=0, sticky="ew", pady=2)
        
        ttk.Label(service_frame, text="Service:").grid(row=0, column=0, padx=5)
        
        self._service_var = tk.StringVar()  # Create the protected variable
        self._service_combo = ttk.Combobox(  # Create the protected combo
            service_frame,
            textvariable=self._service_var,
            state="readonly"
        )
        self._service_combo.grid(row=0, column=1, sticky="ew", padx=5)
        
        return service_frame

    def bind_reload(self, callback: Callable) -> None:
        """Bind reload callback for sidebar operations"""
        if hasattr(self, 'reload_btn'):
            self.reload_btn.bind('<Button-1>', lambda e: callback())

    def setup_credentials_list(self) -> None:
        """Template method for setting up credentials list"""
        raise NotImplementedError("Subclasses must implement setup_credentials_list")
    
    def update_credential_list(self) -> None:
        """Template method for updating credentials list"""
        raise NotImplementedError("Subclasses must implement update_credential_list")
    
    def handle_credential_deletion(self, event) -> None:
        """Template method for handling credential deletion"""
        raise NotImplementedError("Subclasses must implement handle_credential_deletion")
    
    def handle_credentials_clear(self) -> None:
        """Template method for handling credentials clear"""
        raise NotImplementedError("Subclasses must implement handle_credentials_clear")
    
    def handle_credentials_reset(self) -> None:
        """Template method for handling credentials reset"""
        raise NotImplementedError("Subclasses must implement handle_credentials_reset")

    @property
    def service_var(self) -> tk.StringVar:
        return self._service_var

    @service_var.setter
    def service_var(self, value: tk.StringVar):
        self._service_var = value

    @property
    def service_combo(self) -> Optional[ttk.Combobox]:
        return self._service_combo

    @service_combo.setter
    def service_combo(self, value: Optional[ttk.Combobox]):
        self._service_combo = value

    @property
    def credential_list(self) -> Optional[ttk.Treeview]:
        return self._credential_list

    @credential_list.setter
    def credential_list(self, value: Optional[ttk.Treeview]):
        self._credential_list = value

    @property
    def cred_status(self) -> Optional[ttk.Label]:
        return self._cred_status

    @cred_status.setter
    def cred_status(self, value: Optional[ttk.Label]):
        self._cred_status = value

    @property
    def current_service_id(self) -> Optional[int]:
        return self._current_service_id

    @current_service_id.setter
    def current_service_id(self, value: Optional[int]):
        self._current_service_id = value

    @property
    def service_var(self) -> Optional[tk.StringVar]:
        return self._service_var
    
    def configure_grid(self) -> None:
        """Configure grid weights for responsive layout"""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)