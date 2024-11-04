# sidebar/hotkey_tab.py
import os
import subprocess
import keyboard
import sys
from typing import Optional, Set, Dict, Any
import tkinter as tk
from tkinter import ttk, filedialog
from dataclasses import dataclass
from utils.helpers import show_error, show_info, show_confirmation
from .base import SidebarConfig


@dataclass
class HotkeyDialogConfig:
    """Configuration for hotkey dialog"""
    width: int = 400
    height: int = 300
    padding: int = 10
    font_size: int = 10
    font_family: str = 'Segoe UI'

class HotkeyTab(ttk.Frame):
    
    KEY_DISPLAY_MAP = {
        'control_l': 'CTRL',
        'control_r': 'CTRL',
        'alt_l': 'ALT',
        'alt_r': 'ALT',
        'shift_l': 'SHIFT',
        'shift_r': 'SHIFT',
        'super_l': 'WIN',
        'super_r': 'WIN',
    }
    REVERSE_KEY_MAP = {
        'CTRL': 'control_l',
        'ALT': 'alt_l',
        'SHIFT': 'shift_l',
        'WIN': 'super_l'
    }

    def __init__(self, parent: ttk.Frame, db_manager: Any, hotkey_manager: Any, config: SidebarConfig):
        super().__init__(parent)
        self.db_manager = db_manager
        self.hotkey_manager = hotkey_manager
        self.config = config
        self.dialog_config = HotkeyDialogConfig()
        self.registered_hotkeys: Dict[str, bool] = {}

        # State variables
        self.recording: bool = False
        self.current_keys: Set[str] = set()
        
        # UI elements
        self.hotkey_list: Optional[ttk.Treeview] = None
        self.context_menu: Optional[tk.Menu] = None
        self.shortcut_var: Optional[tk.StringVar] = None
        self.action_type: Optional[tk.StringVar] = None
        self.path_var: Optional[tk.StringVar] = None
        self.record_button: Optional[ttk.Button] = None
        
        # Add these two dictionaries for format mapping
        self.internal_to_display: Dict[str, str] = {}
        self.display_to_internal: Dict[str, str] = {}
        
        self.setup_ui()
        self.load_hotkeys()
    
    def setup_ui(self) -> None:
        """Initialize the UI components"""
        # Configure grid weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create header
        self.create_header()
        
        # Create hotkey list
        self.create_hotkey_list()
        
        # Create context menu
        self.create_context_menu()
    
    def create_header(self) -> None:
        header = ttk.Frame(self, style='Dark.TFrame')
        header.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        header.config(height=30)  # Set a fixed height for the header

        ttk.Label(header, text="HOTKEYS", style='Header.TLabel').place(relx=0, rely=0, relwidth=0.5, relheight=1)
        ttk.Button(header, text="Add", command=self.show_add_dialog, style="Accent.TButton").place(relx=0.7, rely=0, relwidth=0.3, relheight=1)

    def format_key_combo(self, key_combo: str) -> str:
        """Format key combination for display"""
        if not key_combo:
            return ""
            
        parts = key_combo.lower().split('+')
        formatted_parts = []
        
        for part in parts:
            part = part.strip()  # Remove any whitespace
            # Check if part is in our mapping
            if part in self.KEY_DISPLAY_MAP:
                formatted_parts.append(self.KEY_DISPLAY_MAP[part])
            else:
                # Capitalize single letters/numbers, otherwise just capitalize first letter
                formatted_parts.append(part.upper() if len(part) == 1 else part.capitalize())
        
        formatted = ' + '.join(formatted_parts)
        # Store the mapping for later use
        self.internal_to_display[key_combo] = formatted
        self.display_to_internal[formatted] = key_combo
        return formatted

    def format_action_value(self, action_value: str, action_type: str) -> str:
        """Format action value for display"""
        if not action_value:
            return ""
                
        # Always show just the filename/program name regardless of type
        return os.path.basename(action_value)

    def create_hotkey_list(self) -> None:
        """Create the treeview for displaying hotkeys"""
        self.hotkey_list = ttk.Treeview(
            self,
            columns=("Shortcut", "Action", "Type"),
            show="headings",
            selectmode="browse",
            style="Dark.Treeview"
        )
        
        # Configure columns
        columns = [
            ("Shortcut", 120),  # Increased width for formatted shortcuts
            ("Action", 200),    # Adjusted for shorter action display
            ("Type", 80)        # Slightly wider for better readability
        ]
        
        for col, width in columns:
            self.hotkey_list.heading(col, text=col, anchor="w")
            self.hotkey_list.column(col, width=width, anchor="w")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.hotkey_list.yview)
        self.hotkey_list.configure(yscrollcommand=scrollbar.set)
        
        # Grid components
        self.hotkey_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
    
    def create_context_menu(self) -> None:
        """Create the right-click context menu"""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_hotkey)
        self.hotkey_list.bind('<Button-3>', self.show_context_menu)
        self.hotkey_list.bind('<Delete>', lambda e: self.delete_hotkey())
    
    def show_add_dialog(self) -> None:
        """Show dialog for adding a new hotkey"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Hotkey")
        dialog.geometry(f"{self.dialog_config.width}x{self.dialog_config.height}")
        dialog.transient(self)
        dialog.grab_set()
        
        self.create_record_frame(dialog)
        self.create_action_frame(dialog)
        self.create_dialog_buttons(dialog)
        
        # Bind key events
        dialog.bind('<KeyPress>', self.on_key_press)
        dialog.bind('<KeyRelease>', self.on_key_release)
    
    def create_record_frame(self, dialog: tk.Toplevel) -> None:
        """Create the frame for recording shortcuts"""
        record_frame = ttk.LabelFrame(
            dialog,
            text="Keyboard Shortcut",
            padding=self.dialog_config.padding
        )
        record_frame.pack(fill="x", padx=10, pady=5)
        
        self.shortcut_var = tk.StringVar(value="Click to record...")
        shortcut_label = ttk.Label(
            record_frame,
            textvariable=self.shortcut_var,
            font=(self.dialog_config.font_family, self.dialog_config.font_size)
        )
        shortcut_label.pack(fill="x", pady=5)
        
        self.record_button = ttk.Button(
            record_frame,
            text="Record Shortcut",
            command=self.toggle_recording
        )
        self.record_button.pack(pady=5)
    
    def create_action_frame(self, dialog: tk.Toplevel) -> None:
        """Create the frame for action selection"""
        action_frame = ttk.LabelFrame(
            dialog,
            text="Action",
            padding=self.dialog_config.padding
        )
        action_frame.pack(fill="x", padx=10, pady=5)
        
        # Action type selection
        self.action_type = tk.StringVar(value="application")
        action_types = [
            ("Launch Application", "application"),
            ("Open File", "file")
        ]
        
        for text, value in action_types:
            ttk.Radiobutton(
                action_frame,
                text=text,
                value=value,
                variable=self.action_type
            ).pack(anchor="w")
        
        # Path selection
        path_frame = ttk.Frame(action_frame)
        path_frame.pack(fill="x", pady=5)
        
        self.path_var = tk.StringVar()
        ttk.Entry(
            path_frame,
            textvariable=self.path_var
        ).pack(side="left", fill="x", expand=True)
        
        ttk.Button(
            path_frame,
            text="Browse",
            command=self.browse_path
        ).pack(side="right", padx=5)
    
    def create_dialog_buttons(self, dialog: tk.Toplevel) -> None:
        """Create the dialog action buttons"""
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side="right", padx=5)
        
        ttk.Button(
            button_frame,
            text="Save",
            style='Accent.TButton',
            command=lambda: self.save_hotkey(dialog)
        ).pack(side="right", padx=5)
    
    def toggle_recording(self) -> None:
        """Toggle the recording state"""
        self.recording = not self.recording
        if self.recording:
            self.record_button.configure(text="Stop Recording")
            self.shortcut_var.set("Press keys...")
            self.current_keys.clear()
        else:
            self.record_button.configure(text="Record Shortcut")
    
    def on_key_press(self, event) -> None:
        """Handle key press events during recording"""
        if self.recording:
            key = event.keysym.lower()
            self.current_keys.add(key)
            self.update_shortcut_display()
    
    def on_key_release(self, event) -> None:
        """Handle key release events during recording"""
        if self.recording:
            key = event.keysym.lower()
            if key in self.current_keys:
                self.current_keys.remove(key)
            self.update_shortcut_display()
    
    def update_shortcut_display(self) -> None:
        """Update the display of recorded keys"""
        if self.current_keys:
            combo = ' + '.join(sorted(self.current_keys))
            formatted_combo = self.format_key_combo(combo)
            self.shortcut_var.set(formatted_combo)
    
    def browse_path(self) -> None:
        """Open file browser for path selection"""
        if self.action_type.get() == "application":
            filetypes = [("Executable files", "*.exe"), ("All files", "*.*")]
            title = "Select Application"
        else:
            filetypes = [("All files", "*.*")]
            title = "Select File"
        
        path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if path:
            self.path_var.set(path)
    
    def save_hotkey(self, dialog: tk.Toplevel) -> None:
        """Save the new hotkey configuration"""
        key_combo = self.shortcut_var.get()
        action = self.path_var.get()
        action_type = self.action_type.get()
        
        if key_combo == "Click to record..." or not action:
            show_error("Error", "Please record a shortcut and specify an action.")
            return
        
        try:
            self.db_manager.save_hotkey(key_combo, action, action_type)
            self.load_hotkeys()
            dialog.destroy()
            show_info("Success", "Hotkey saved successfully!")
            self.hotkey_manager.register_all_hotkeys()
        except Exception as e:
            show_error("Error", f"Failed to save hotkey: {str(e)}")
    
    def load_hotkeys(self) -> None:
        """Load and display all hotkeys"""
        try:
            hotkeys = self.db_manager.get_all_hotkeys()
            self.hotkey_list.delete(*self.hotkey_list.get_children())
            self.internal_to_display.clear()
            self.display_to_internal.clear()
            
            for combo, action_value, action_type in hotkeys:
                formatted_combo = self.format_key_combo(combo)
                formatted_action = self.format_action_value(action_value, action_type)
                display_type = 'APP' if action_type.lower() == 'application' else 'FILE'
                
                self.hotkey_list.insert("", "end", values=(
                    formatted_combo,
                    formatted_action,
                    display_type
                ))
        except Exception as e:
            show_error("Error", f"Failed to load hotkeys: {str(e)}")
    
    def delete_hotkey(self) -> None:
        """Delete the selected hotkey"""
        selection = self.hotkey_list.selection()
        if not selection:
            show_error("Error", "Please select a hotkey to delete")
            return
            
        item = self.hotkey_list.item(selection[0])
        if not item or 'values' not in item or not item['values']:
            show_error("Error", "Invalid hotkey selection")
            return
            
        formatted_combo = item['values'][0]  # Get the formatted key combination
        
        # Convert the formatted combo back to internal format
        key_combo = self.reverse_format_key_combo(formatted_combo)
        
        if not show_confirmation("Delete Hotkey", 
                               f"Are you sure you want to delete the hotkey '{formatted_combo}'?"):
            return
            
        try:
            # Delete from database
            self.db_manager.delete_hotkey(key_combo)
            
            # Unregister the hotkey from the service
            self.unregister_hotkey(key_combo)
            
            # Remove from UI
            self.hotkey_list.delete(selection[0])
            
            # Clean up mappings
            if formatted_combo in self.display_to_internal:
                internal_combo = self.display_to_internal[formatted_combo]
                del self.display_to_internal[formatted_combo]
                if internal_combo in self.internal_to_display:
                    del self.internal_to_display[internal_combo]
            
            show_info("Success", f"Hotkey '{formatted_combo}' deleted successfully!")
            
        except Exception as e:
            show_error("Error", f"Failed to delete hotkey: {str(e)}")

    def unregister_hotkey(self, key_combo: str) -> None:
        """Unregister a single hotkey"""
        try:
            if key_combo in self.registered_hotkeys:
                keyboard.remove_hotkey(key_combo)
                del self.registered_hotkeys[key_combo]
                print(f"Unregistered hotkey: {key_combo}")
        except Exception as e:
            show_error("Error", f"Failed to unregister hotkey: {str(e)}")

    def register_hotkey(self, key_combo: str, action_value: str, action_type: str) -> None:
        """Register a single hotkey with its action"""
        try:
            if key_combo in self.registered_hotkeys:
                keyboard.remove_hotkey(key_combo)
            
            # Create callback that captures the action details
            def callback():
                try:
                    self.execute_action(action_value, action_type)
                except Exception as e:
                    show_error("Error", f"Failed to execute hotkey action: {str(e)}")
            
            keyboard.add_hotkey(key_combo, callback, suppress=True)
            self.registered_hotkeys[key_combo] = True
            print(f"Registered hotkey {key_combo}: {action_type} - {action_value}")
            
        except Exception as e:
            show_error("Error", f"Failed to register hotkey: {str(e)}")
            self.registered_hotkeys[key_combo] = False

    def execute_action(self, action_value: str, action_type: str) -> None:
        """Execute the action associated with a hotkey"""
        try:
            if not os.path.exists(action_value):
                raise FileNotFoundError(f"Path not found: {action_value}")

            # Use appropriate method based on OS and action type
            if sys.platform == 'win32':
                if action_type.upper() == 'APP':
                    try:
                        # First try with subprocess
                        subprocess.Popen([action_value], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    except Exception as e:
                        # Fallback to shell execute
                        os.startfile(action_value)
                else:  # FILE
                    try:
                        # Try using the default associated program
                        os.startfile(action_value)
                    except Exception as e:
                        # Fallback to shell execute
                        subprocess.run(['cmd', '/c', 'start', '', action_value], shell=True)
            else:
                # For non-Windows systems
                if sys.platform == 'darwin':  # macOS
                    opener = 'open'
                else:  # Linux and others
                    opener = 'xdg-open'
                subprocess.run([opener, action_value])

            print(f"Executed {action_type.lower()}: {action_value}")
                
        except Exception as e:
            error_msg = f"Failed to execute {action_type.lower()}: {str(e)}"
            print(error_msg)  # For debugging
            show_error("Error", error_msg)
            
            # Additional debug info
            print(f"Debug Info:")
            print(f"Action Type: {action_type}")
            print(f"Action Value: {action_value}")
            print(f"File exists: {os.path.exists(action_value)}")
            print(f"Is file: {os.path.isfile(action_value)}")
            print(f"Is directory: {os.path.isdir(action_value)}")
            print(f"Platform: {sys.platform}")

    def show_context_menu(self, event) -> None:
        """Show the context menu for hotkey operations"""
        item = self.hotkey_list.identify_row(event.y)
        if item:
            self.hotkey_list.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def reverse_format_key_combo(self, formatted_combo: str) -> str:
        """Convert display format back to internal format"""
        # First check if we have this stored in our mapping
        if formatted_combo in self.display_to_internal:
            return self.display_to_internal[formatted_combo]
            
        # If not found in mapping, do the conversion
        if not formatted_combo:
            return ""
            
        parts = formatted_combo.upper().split(' + ')
        original_parts = []
        
        for part in parts:
            # Check if part is in our reverse mapping
            if part in self.REVERSE_KEY_MAP:
                original_parts.append(self.REVERSE_KEY_MAP[part])
            else:
                # Convert back to lowercase for consistency
                original_parts.append(part.lower())
        
        return '+'.join(original_parts)  # Note: Using + without spaces

    def update_hotkey(self, key_combo: str, action: str, action_type: str) -> None:
        """Update an existing hotkey"""
        try:
            self.db_manager.update_hotkey(key_combo, action, action_type)
            self.load_hotkeys()
            show_info("Success", "Hotkey updated successfully!")
            self.hotkey_manager.register_all_hotkeys()
        except Exception as e:
            show_error("Error", f"Failed to update hotkey: {str(e)}")

    def register_all_hotkeys(self) -> None:
        """Register all hotkeys from the database"""
        try:
            # Clear existing hotkeys first
            self.unregister_all_hotkeys()
            
            # Get and register all hotkeys
            hotkeys = self.db_manager.get_all_hotkeys()
            for combo, action_value, action_type in hotkeys:
                self.register_hotkey(combo, action_value, action_type)
                
        except Exception as e:
            show_error("Error", f"Failed to register hotkeys: {str(e)}")

    def unregister_all_hotkeys(self) -> None:
        """Unregister all currently registered hotkeys"""
        try:
            for key_combo in list(self.registered_hotkeys.keys()):
                self.unregister_hotkey(key_combo)
        except Exception as e:
            show_error("Error", f"Failed to unregister hotkeys: {str(e)}")

    def is_registered(self, key_combo: str) -> bool:
        """Check if a hotkey is currently registered"""
        return key_combo in self.registered_hotkeys