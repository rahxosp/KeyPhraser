# sidebar/credentials_tab.py
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, filedialog
from .base import SidebarBase, SidebarConfig
from utils.helpers import show_error

class CredentialsTab(ttk.Frame):
    """Component for managing credentials in the sidebar"""
    
    def __init__(self, parent: ttk.Frame, db_manager: Any, hotkey_manager: Any, main_window: Any, config: SidebarConfig = None):
        # Initialize ttk.Frame
        ttk.Frame.__init__(self, parent)
        
        # Store parameters
        self.db_manager = db_manager
        self.hotkey_manager = hotkey_manager
        self.main_window = main_window
        self.config = config or SidebarConfig()
        
        # Initialize protected variables
        self._service_var = tk.StringVar()
        self._service_combo = None
        self._credential_list = None
        self._cred_status = None
        self._current_service_id = None
        self.credential_context_menu = None
        
        # Setup UI
        self.setup_ui()

    # Properties
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
    
    def setup_ui(self) -> None:
        """Initialize all UI components"""
        # Create the main header frame
        header = ttk.Frame(self, style='Dark.TFrame')
        header.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        header.config(height=120)
        
        # Create service selection
        service_frame = self.create_service_frame(header)
        service_frame.place(relx=0, rely=0, relwidth=1, relheight=0.3)

        # Create action buttons
        button_frame = ttk.Frame(header)
        button_frame.place(relx=0, rely=0.4, relwidth=1, relheight=0.3)
        self.create_action_buttons(button_frame)
        
        # Status label
        self._cred_status = ttk.Label(header, text="No credentials loaded")
        self._cred_status.place(x=5, rely=0.8, relwidth=1, relheight=0.15)
        
        # Create credential list
        self.create_credential_list()
        self.create_context_menu()
        
        # Configure grid weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def create_service_frame(self, parent: ttk.Frame) -> None:
        """Create service selection frame"""
        service_frame = ttk.Frame(parent)
        service_frame.grid(row=0, column=0, sticky="ew")
        
        ttk.Label(service_frame, text="ACCCOUNTS", style='Header.TLabel').place(x=5, rely=0, relwidth=0.5, relheight=1)

        self._service_combo = ttk.Combobox(
            service_frame,
            textvariable=self._service_var,
            state="readonly"
        )
        self._service_combo.place(relx=0.5, rely=0, relwidth=0.45, relheight=1)
        
        # Bind service change event
        if self._service_combo:
            self._service_combo.bind('<<ComboboxSelected>>', self.on_service_change)
        
        return service_frame
    
    def create_action_buttons(self, parent: ttk.Frame) -> None:
        """Create action buttons for credential management"""
        buttons = [
            ("Load File", self._on_load_credentials, "Accent.TButton",  {"relx": 0.7, "rely": 0, "relwidth": 0.25, "relheight":1}),
            ("Reset", self._on_reset_credentials, None,        {"relx": 0.21, "rely": 0, "relwidth": 0.2, "relheight":1}),
            ("Delete", self._on_clear_credentials, "Danger.TButton", {"relx": 0.0, "rely": 0, "relwidth": 0.2, "relheight":1})
        ]
        for text, command, style, placement in buttons:
            btn_kwargs = {"text": text, "command": command}
            if style:
                btn_kwargs["style"] = style
            button = ttk.Button(parent, **btn_kwargs)
            button.place(**placement)

    def create_credential_list(self) -> None:
        """Create the treeview for displaying credentials"""
        list_frame = ttk.Frame(self)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configure grid weights
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # Create Treeview
        self._credential_list = ttk.Treeview(
            list_frame,
            columns=("Position", "Credentials"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure columns
        self.configure_credential_columns()
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self._credential_list.yview)
        self._credential_list.configure(yscrollcommand=scrollbar.set)
        
        # Grid components
        self._credential_list.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
    
    def update_credential_list(self) -> None:
        """Update the credential list through the main window"""
        if hasattr(self.winfo_toplevel(), 'update_credential_list'):
            self.winfo_toplevel().after(10, self.winfo_toplevel().update_credential_list)
    
    def on_service_change(self, event=None) -> None:
        """Handle service selection change"""
        try:
            service_name = self._service_var.get()
            services = self.db_manager.get_services()
            
            for service in services:
                if service['name'] == service_name:
                    self._current_service_id = service['id']
                    # Call the main window's update_credential_list directly
                    if hasattr(self.main_window, 'update_credential_list'):
                        self.main_window.update_credential_list()
                    break
                    
        except Exception as e:
            print(f"Error in service change: {e}")
    
    def configure_credential_columns(self) -> None:
        """Configure the columns for the credential list"""
        columns = [
            ("Position", self.config.position_column_width, False),
            ("Credentials", self.config.credentials_column_width, True),
        ]
        
        for col, width, stretch in columns:
            self._credential_list.heading(col, text=col, anchor="w")
            self._credential_list.column(col, width=width, stretch=stretch)
        
        # Configure tags for status indication
        self._credential_list.tag_configure('used', foreground='#808080')
        self._credential_list.tag_configure('pending', foreground='#00FF00')
    
    def create_context_menu(self) -> None:
        """Create the right-click context menu"""
        self.credential_context_menu = tk.Menu(self, tearoff=0)
        self.credential_context_menu.add_command(
            label="Delete",
            command=self._delete_selected_credential
        )
        
        self._credential_list.bind('<Button-3>', self._show_credential_context_menu)
    
    def load_services(self) -> None:
        """Load services into the combobox"""
        try:
            services = self.db_manager.get_services()
            service_names = [service['name'] for service in services]
            
            if self._service_combo:
                self._service_combo['values'] = service_names
                if service_names:
                    self._service_combo.set(service_names[0])
                    # Update the current service ID
                    self._current_service_id = services[0]['id']
                    # Explicitly call update after setting initial service
                    if hasattr(self.main_window, 'update_credential_list'):
                        self.main_window.update_credential_list()
                    
        except Exception as e:
            print(f"Failed to load services: {e}")
    
    def _update_credential_list(self) -> None:
        """Local update method that triggers the main window update"""
        if hasattr(self.main_window, 'update_credential_list'):
            self.main_window.update_credential_list()
    
    def _on_load_credentials(self) -> None:
        """Handle load credentials button click"""
        if not self.service_var.get():
            show_error("Error", "Please select a service first")
            return
        
        self._trigger_event('<<LoadCredentials>>')
    
    def _on_reset_credentials(self) -> None:
        """Handle reset credentials button click"""
        self._trigger_event('<<ResetCredentials>>')
    
    def _on_clear_credentials(self) -> None:
        """Handle clear credentials button click"""
        self._trigger_event('<<ClearCredentials>>')
    
    def _show_credential_context_menu(self, event) -> None:
        """Show the context menu on right-click"""
        item = self.credential_list.identify_row(event.y)
        if item:
            self.credential_list.selection_set(item)
            self.credential_context_menu.tk_popup(event.x_root, event.y_root)
    
    def _delete_selected_credential(self) -> None:
        """Delete the selected credential"""
        selection = self.credential_list.selection()
        if selection:
            credential_id = self.credential_list.item(selection[0])['values'][0]
            self._trigger_event('<<DeleteCredential>>', data=str(credential_id))
    
    def _trigger_event(self, event_name: str, data: str = None) -> None:
        """Safely trigger a custom event"""
        try:
            if data:
                self.winfo_toplevel().event_generate(event_name, data=data)
            else:
                self.winfo_toplevel().event_generate(event_name)
        except Exception as e:
            print(f"Error triggering event {event_name}: {str(e)}")
    
    def update_status(self, text: str) -> None:
        """Update the status label text"""
        if self.cred_status:
            self.cred_status.config(text=text)

    def update_credentials_status(self, total: int, used: int) -> None:
        """Update the credentials status text"""
        if self.cred_status:
            self.cred_status.configure(text=f"Loaded {total} credentials ({used} used)")

    @property
    def current_service_id(self) -> Optional[int]:
        """Get the current service ID"""
        return self._current_service_id

    @property
    def service_var(self) -> tk.StringVar:
        return self._service_var
    
    @service_var.setter
    def service_var(self, value: tk.StringVar):
        self._service_var = value
    
    @property
    def service_combo(self) -> ttk.Combobox:
        return self._service_combo
    
    @service_combo.setter
    def service_combo(self, value: ttk.Combobox):
        self._service_combo = value