import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Tuple
from tkinter import filedialog
from utils.helpers import show_error, show_info, show_confirmation
from config.styles import Styles


class Sidebar(ttk.Frame):
    
    def __init__(self, parent, db_manager, hotkey_manager, main_window, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.db_manager = db_manager
        self.hotkey_manager = hotkey_manager
        self.main_window = main_window 
        self.on_shortcut_select: Optional[Callable] = None
        self.on_context_menu: Optional[Callable] = None
        self.shortcuts_list: Optional[ttk.Treeview] = None
        self.reload_btn: Optional[ttk.Label] = None
        self.credential_list: Optional[ttk.Treeview] = None
        self.current_service_id = None  # Add this line
        
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        self.shortcuts_tab = ttk.Frame(self.notebook)
        self.credentials_tab = ttk.Frame(self.notebook)
        self.hotkeys_tab = HotkeyTab(self.notebook, self.db_manager, self.hotkey_manager)
        self.notebook.add(self.shortcuts_tab, text="Shortcuts")
        self.notebook.add(self.credentials_tab, text="Credentials")
        self.notebook.add(self.hotkeys_tab, text="Hotkeys")
        self.create_shortcuts_tab()
        self.create_credentials_tab()
        self.configure_grid()

    def load_services(self):
        """Load services into combobox"""
        try:
            services = self.db_manager.get_services()
            service_names = [service['name'] for service in services]
            self.service_combo['values'] = service_names
            if service_names:
                self.service_combo.set(service_names[0])
                self.current_service_id = services[0]['id']
                main_window = self.winfo_toplevel()
                if hasattr(main_window, 'update_credential_list'):
                    self.parent.main_window.update_credential_list()
        except Exception as e:
            print(f"Failed to load services: {e}")

    def on_service_change(self, event=None):
        """Handle service selection change"""
        try:
            service_name = self.service_var.get()
            print(f"Service changed to: {service_name}")
            services = self.db_manager.get_services()

            for service in services:
                if service['name'] == service_name:
                    print(f"Found service ID: {service['id']}")
                    self.current_service_id = service['id']
                    
                    # Use `self.main_window.root.after` to schedule the update
                    if hasattr(self.main_window, 'update_credential_list'):
                        self.main_window.root.after(10, self.main_window.update_credential_list)
                    else:
                        print("Error: `main_window` does not have `update_credential_list`.")
                    break
        except Exception as e:
            print(f"Error in service change: {e}")

    def create_shortcuts_tab(self):
        header_frame = self.create_header(self.shortcuts_tab)
        header_frame.pack(fill="x", padx=5, pady=5)
        self.create_search_bar(self.shortcuts_tab)
        self.create_shortcuts_list()
    
    def create_credentials_tab(self):
        header = ttk.Frame(self.credentials_tab, style='Dark.TFrame')
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Add service selection
        service_frame = ttk.Frame(header)
        service_frame.grid(row=0, column=0, sticky="ew", pady=2)
        
        ttk.Label(service_frame, text="Service:").grid(row=0, column=0, padx=5)
        self.service_var = tk.StringVar()
        self.service_combo = ttk.Combobox(
            service_frame,
            textvariable=self.service_var,
            state="readonly"
        )
        self.service_combo.grid(row=0, column=1, sticky="ew", padx=5)
        self.load_services()
        
        # Button frame
        button_frame = ttk.Frame(header)
        button_frame.grid(row=1, column=0, sticky="ew", pady=2)
        
        ttk.Button(
            button_frame, 
            text="Load File",
            command=self._on_load_credentials,
            style="Accent.TButton"
        ).grid(row=0, column=0, padx=2)
        
        ttk.Button(
            button_frame,
            text="Reset Sequence",
            command=self._on_reset_credentials
        ).grid(row=0, column=1, padx=2)
        
        ttk.Button(
            button_frame,
            text="Clear All",
            command=self._on_clear_credentials,
            style="Danger.TButton"
        ).grid(row=0, column=2, padx=2)
        self.cred_status = ttk.Label(header, text="No credentials loaded")
        self.cred_status.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
        header.grid_columnconfigure(0, weight=1)
        self.service_combo.bind('<<ComboboxSelected>>', self.on_service_change)
        self.setup_credentials_list()


    def setup_credentials_list(self):
        list_frame = ttk.Frame(self.credentials_tab)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.credential_list = ttk.Treeview(
            list_frame,
            columns=("Position", "Credentials"),
            show="headings",
            selectmode="browse"
        )
        self.configure_credentials_columns()
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.credential_list.yview)
        self.credential_list.configure(yscrollcommand=scrollbar.set)
        
        self.credential_list.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.create_credential_context_menu()

    def configure_credentials_columns(self):
        columns = [
            ("Position", 50, False),
            ("Credentials", 300, True),  
        ]
        for col, width, stretch in columns:
            self.credential_list.heading(col, text=col, anchor="w")
            self.credential_list.column(col, width=width, stretch=stretch)
        
        self.credential_list.tag_configure('used', foreground='#808080')
        self.credential_list.tag_configure('pending', foreground='#00FF00')

    
    def create_credential_context_menu(self):
        self.credential_context_menu = tk.Menu(self, tearoff=0)
        self.credential_context_menu.add_command(label="Delete", command=self._delete_selected_credential)
        self.credential_list.bind('<Button-3>', self._show_credential_context_menu)
    
    def _on_clear_credentials(self):
        try:
            top = self.winfo_toplevel()
            if hasattr(top, 'event_generate'):
                top.event_generate('<<ClearCredentials>>')
        except Exception as e:
            print(f"Error in clear button handler: {str(e)}")
    
    def _show_credential_context_menu(self, event):
        item = self.credential_list.identify_row(event.y)
        if item:
            self.credential_list.selection_set(item)
            self.credential_context_menu.tk_popup(event.x_root, event.y_root)
    
    def _delete_selected_credential(self):
        selection = self.credential_list.selection()
        if selection:
            credential_id = self.credential_list.item(selection[0])['values'][0]
            self.winfo_toplevel().event_generate('<<DeleteCredential>>', data=str(credential_id))
    
    def _on_load_credentials(self):
        """Handle load credentials button click"""
        if not self.service_var.get():
            show_error("Error", "Please select a service first")
            return
        
        self.winfo_toplevel().event_generate('<<LoadCredentials>>')

    def _on_reset_credentials(self):
        self.winfo_toplevel().event_generate('<<ResetCredentials>>')
        
    def create_header(self, parent_frame):
        header_frame = ttk.Frame(parent_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        header_content = ttk.Frame(header_frame, style='Dark.TFrame')
        header_content.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        header_content.grid_columnconfigure(0, weight=1)
        ttk.Label(header_content, text="LIST", style='Header.TLabel').pack(side="left", padx=5)
        self.clear_cache_btn = ttk.Button(header_content, text="Clear Cache", command=self._on_clear_cache)
        self.clear_cache_btn.pack(side="right", padx=5)
        return header_frame
    
    def _on_clear_cache(self):
        """Handle clear cache button click"""
        try:
            self.winfo_toplevel().event_generate('<<ClearCache>>')
        except Exception as e:
            print(f"Error in clear cache button handler: {str(e)}")
    
    def create_shortcuts_list(self):
        list_frame = ttk.Frame(self.shortcuts_tab, style='Dark.TFrame')
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Changed from shortcuts_list to shortcut_list for consistency
        self.shortcut_list = ttk.Treeview(
            list_frame,
            columns=("Shortcuts", "Content"),
            show="headings",
            selectmode="browse",
            style="Dark.Treeview"
        )
        
        self.shortcut_list.heading("Shortcuts", text="Shortcuts", anchor="w")
        self.shortcut_list.heading("Content", text="Content", anchor="w")
        self.shortcut_list.column("Shortcuts", width=100, minwidth=100, stretch=True, anchor="w")
        self.shortcut_list.column("Content", width=300, minwidth=200, stretch=True, anchor="w")
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.shortcut_list.yview)
        self.shortcut_list.configure(yscrollcommand=scrollbar.set)
        
        self.shortcut_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Update bindings to use shortcut_list instead of shortcuts_list
        self.shortcut_list.bind('<<TreeviewSelect>>', self._on_shortcut_select)
        self.shortcut_list.bind('<Button-3>', self._on_right_click)
    
    def create_search_bar(self, parent_frame):
        """Create search bar with real-time filtering"""
        search_frame = ttk.Frame(parent_frame, style='Dark.TFrame')
        search_frame.pack(fill="x", padx=5, pady=(5, 0))
        entry_frame = ttk.Frame(search_frame, style='Dark.TFrame')
        entry_frame.pack(fill="x")
        search_icon = ttk.Label(
            entry_frame, 
            text="\u2315", 
            style='Header.TLabel'
        )
        search_icon.pack(side="left", padx=(5, 0))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search)
        self.search_entry = ttk.Entry(
            entry_frame,
            textvariable=self.search_var,
            style='Search.TEntry'
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.clear_btn = ttk.Label(
            entry_frame,
            text="\u2a2f",
            style='Header.TLabel',
            cursor="hand2"
        )
        self.clear_btn.pack(side="right", padx=5)
        self.clear_btn.bind('<Button-1>', self._clear_search)
        self.all_shortcuts = []
    
    def _on_search(self, *args):
        """Filter shortcuts based on search text"""
        search_text = self.search_var.get().lower()
        self.shortcuts_list.delete(*self.shortcuts_list.get_children())
        if not search_text:
            for shortcut, content in self.all_shortcuts:
                display_content = self.format_display_text(content)
                self.shortcuts_list.insert("", "end", values=(shortcut, display_content))
            return
        for shortcut, content in self.all_shortcuts:
            if (search_text in shortcut.lower() or 
                search_text in content.lower()):
                display_content = self.format_display_text(content)
                self.shortcuts_list.insert("", "end", values=(shortcut, display_content))
    
    def _clear_search(self, event=None):
        """Clear search entry and show all shortcuts"""
        self.search_var.set('')
        self.search_entry.focus()
    
    def load_shortcuts(self, shortcuts: List[Tuple[str, str]]):
        """Store shortcuts and display them"""
        self.all_shortcuts = shortcuts
        self.shortcut_list.delete(*self.shortcut_list.get_children())
        for shortcut, content in shortcuts:
            display_content = self.format_display_text(content)
            self.shortcut_list.insert("", "end", values=(shortcut, display_content))
    
    def configure_grid(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Allow vertical expansion
        self.grid_columnconfigure(0, weight=1)

    def bind_shortcut_select(self, callback: Callable):
        """Bind shortcut selection callback"""
        def on_select(event):
            selected = self.shortcut_list.selection()
            if selected:
                item = self.shortcut_list.item(selected[0])
                callback(item['values'])
        
        self.shortcut_list.bind('<<TreeviewSelect>>', on_select)

    def bind_context_menu(self, callback: Callable):
        """Bind context menu callback"""
        self.shortcut_list.bind('<Button-3>', callback)
    
    def get_selected_shortcut(self) -> Optional[Tuple[str, str]]:
        """Get the currently selected shortcut"""
        selected = self.shortcut_list.selection()
        if selected:
            item = self.shortcut_list.item(selected[0])
            return tuple(item['values'])
        return None
    
    def clear_selection(self):
        # Update to use shortcut_list instead of shortcuts_list
        self.shortcut_list.selection_remove(*self.shortcut_list.selection())
        
    def format_display_text(self, content: str) -> str:
        max_length = 50
        display_text = ' '.join(content.split())
        return display_text[:max_length] + "..." if len(display_text) > max_length else display_text
    
    def _on_shortcut_select(self, event):
        if self.on_shortcut_select:
            selected = self.get_selected_shortcut()
            self.on_shortcut_select(selected)
    
    def _on_right_click(self, event):
        item = self.shortcuts_list.identify_row(event.y)
        if item:
            self.shortcuts_list.selection_set(item)
            if self.on_context_menu:
                self.on_context_menu(event)
    
    def bind_reload(self, callback: Callable):
        if self.reload_btn:
            self.reload_btn.bind('<Button-1>', lambda e: callback())

class HotkeyTab(ttk.Frame):
    def __init__(self, parent, db_manager, hotkey_manager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.hotkey_manager = hotkey_manager
        self.service_var = None
        self.service_combo = None
        self.shortcut_list = None
        self.credential_list = None
        self.cred_status = None
        self.recording = False
        self.current_keys = set()
        self.setup_ui()
        self.load_hotkeys()
    
    def setup_ui(self):
        # Add hotkey_list initialization first
        self.hotkey_list = ttk.Treeview(
            self,
            columns=("Shortcut", "Action", "Type"),
            show="headings",
            selectmode="browse",
            style="Dark.Treeview"
        )
        
        # Configure grid weights
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ttk.Frame(self, style='Dark.TFrame')
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Label(header, text="Hotkeys", style='Header.TLabel').grid(row=0, column=0, sticky="w", padx=5)
        ttk.Button(header, text="Add", command=self.show_add_dialog, style="Accent.TButton").grid(row=0, column=1, padx=5)

        # Configure columns
        for col, width in [("Shortcut", 70), ("Action", 250), ("Type", 100)]:
            self.hotkey_list.heading(col, text=col, anchor="w")
            self.hotkey_list.column(col, width=width, anchor="w")

        # Place hotkey list
        self.hotkey_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.hotkey_list.yview)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=5)
        self.hotkey_list.configure(yscrollcommand=scrollbar.set)

        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_hotkey)
        self.hotkey_list.bind('<Button-3>', self.show_context_menu)

    def setup_service_selection(self):
        # Service Frame
        service_frame = ttk.LabelFrame(self, text="Service Selection")
        service_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        service_frame.grid_columnconfigure(0, weight=1)
        
        # Service Combobox
        self.service_var = tk.StringVar()
        self.service_combo = ttk.Combobox(
            service_frame,
            textvariable=self.service_var,
            state="readonly",
            style="TCombobox"
        )
        self.service_combo.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    
    def setup_shortcuts(self):
        # Shortcuts Frame
        shortcuts_frame = ttk.LabelFrame(self, text="Shortcuts")
        shortcuts_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        shortcuts_frame.grid_columnconfigure(0, weight=1)
        
        # Shortcuts List
        self.shortcut_list = ttk.Treeview(
            shortcuts_frame,
            columns=("Keyword", "Replacement"),
            show="headings",
            height=6
        )
        self.shortcut_list.grid(row=0, column=0, sticky="nsew")
        
        # Configure columns
        self.shortcut_list.heading("Keyword", text="Keyword")
        self.shortcut_list.heading("Replacement", text="Replacement")
        self.shortcut_list.column("Keyword", width=100)
        self.shortcut_list.column("Replacement", width=150)
        
        # Add scrollbar
        shortcut_scrollbar = ttk.Scrollbar(
            shortcuts_frame,
            orient="vertical",
            command=self.shortcut_list.yview
        )
        shortcut_scrollbar.grid(row=0, column=1, sticky="ns")
        self.shortcut_list.configure(yscrollcommand=shortcut_scrollbar.set)     

    def show_add_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Hotkey")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        record_frame = ttk.LabelFrame(dialog, text="Keyboard Shortcut", padding=10)
        record_frame.pack(fill="x", padx=10, pady=5)
        self.shortcut_var = tk.StringVar(value="Click to record...")
        shortcut_label = ttk.Label(
            record_frame, 
            textvariable=self.shortcut_var,
            font=('Segoe UI', 10)
        )
        shortcut_label.pack(fill="x", pady=5)
        self.record_button = ttk.Button(
            record_frame,
            text="Record Shortcut",
            command=self.toggle_recording
        )
        self.record_button.pack(pady=5)
        action_frame = ttk.LabelFrame(dialog, text="Action", padding=10)
        action_frame.pack(fill="x", padx=10, pady=5)
        self.action_type = tk.StringVar(value="application")
        ttk.Radiobutton(
            action_frame,
            text="Launch Application",
            value="application",
            variable=self.action_type
        ).pack(anchor="w")
        ttk.Radiobutton(
            action_frame,
            text="Open File",
            value="file",
            variable=self.action_type
        ).pack(anchor="w")
        path_frame = ttk.Frame(action_frame)
        path_frame.pack(fill="x", pady=5)
        self.path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.path_var).pack(side="left", fill="x", expand=True)
        ttk.Button(
            path_frame,
            text="Browse",
            command=self.browse_path
        ).pack(side="right", padx=5)
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(
            button_frame,
            text="Save",
            style='Accent.TButton',
            command=lambda: self.save_hotkey(dialog)
        ).pack(side="right", padx=5)
        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side="right", padx=5)
        dialog.bind('<KeyPress>', self.on_key_press)
        dialog.bind('<KeyRelease>', self.on_key_release)
    
    def _trigger_load_credentials(self):
        """Trigger load credentials event"""
        self.event_generate('<<LoadCredentials>>')
    
    def _trigger_reset_credentials(self):
        """Trigger reset credentials event"""
        self.event_generate('<<ResetCredentials>>')
    
    def _trigger_clear_credentials(self):
        """Trigger clear credentials event"""
        self.event_generate('<<ClearCredentials>>')
    
    def toggle_recording(self):
        self.recording = not self.recording
        if self.recording:
            self.record_button.configure(text="Stop Recording")
            self.shortcut_var.set("Press keys...")
            self.current_keys.clear()
        else:
            self.record_button.configure(text="Record Shortcut")
    
    def on_key_press(self, event):
        if self.recording:
            key = event.keysym.lower()
            self.current_keys.add(key)
            self.update_shortcut_display()
    
    def on_key_release(self, event):
        if self.recording:
            key = event.keysym.lower()
            if key in self.current_keys:
                self.current_keys.remove(key)
            self.update_shortcut_display()
    
    def update_shortcut_display(self):
        if self.current_keys:
            combo = ' + '.join(sorted(self.current_keys))
            self.shortcut_var.set(combo)
    
    def browse_path(self):
        if self.action_type.get() == "application":
            path = filedialog.askopenfilename(
                title="Select Application",
                filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
            )
        else:
            path = filedialog.askopenfilename(
                title="Select File",
                filetypes=[("All files", "*.*")]
            )
        if path:
            self.path_var.set(path)
    def save_hotkey(self, dialog):
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
    def load_hotkeys(self):
        try:
            hotkeys = self.db_manager.get_all_hotkeys()
            self.hotkey_list.delete(*self.hotkey_list.get_children())
            for combo, action_value, action_type in hotkeys:
                self.hotkey_list.insert("", "end", values=(combo, action_value, action_type))
        except Exception as e:
            show_error("Error", f"Failed to load hotkeys: {str(e)}")
    def delete_hotkey(self):
        selection = self.hotkey_list.selection()
        if not selection:
            return
        if not show_confirmation("Delete Hotkey", "Are you sure you want to delete this hotkey?"):
            return
        try:
            item = self.hotkey_list.item(selection[0])
            key_combo = item['values'][0]
            self.db_manager.delete_hotkey(key_combo)
            self.load_hotkeys()
            show_info("Success", "Hotkey deleted successfully!")
        except Exception as e:
            show_error("Error", f"Failed to delete hotkey: {str(e)}")
    def show_context_menu(self, event):
        item = self.hotkey_list.identify_row(event.y)
        if item:
            self.hotkey_list.selection_set(item)
            self.context_menu.tk_popup(event.x_root, event.y_root)