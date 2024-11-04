import tkinter as tk
from tkinter import ttk, messagebox, filedialog  # Added filedialog import
from typing import Optional, Tuple, Dict, Any
from ui.sidebar.sidebar import Sidebar
from ui.mainbar import Mainbar
from ui.footer import Footer
from services.hotkey_manager import HotkeyManager
from config.styles import Styles
from config.settings import Config
from utils.helpers import show_error, show_info, show_confirmation


class MainWindow:
    def __init__(self, root: tk.Tk, text_replacer, db_manager, system_tray):
        self.root = root
        self.text_replacer = text_replacer
        self.db_manager = db_manager
        self.system_tray = system_tray
        self.hotkey_manager = HotkeyManager(db_manager)
        self.setup_window()
        # self.setup_menu() // will activate it later
        self.setup_ui()
        self.bind_credential_events()
        self.bind_events()
        self.load_initial_data()
    
    def bind_credential_events(self):
        """Bind credential-related events"""
        self.root.bind('<<ClearCredentials>>', lambda e: self.clear_credentials())
        self.root.bind('<<LoadCredentials>>', lambda e: self.load_credentials_file())
        self.root.bind('<<ResetCredentials>>', lambda e: self.reset_credentials())
        self.root.bind('<<DeleteCredential>>', self.delete_credential)
    
    def setup_window(self):
        self.root.title(Config.APP_NAME)
        self.root.geometry(Config.WINDOW_SIZE)
        self.root.minsize(Config.MIN_WIDTH, Config.MIN_HEIGHT)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_window)
        if hasattr(Config, 'ICON_PATH') and Config.ICON_PATH.exists():
            self.root.iconbitmap(Config.ICON_PATH)
    
    def clear_credentials(self):
        """Clear all credentials"""
        try:
            if not show_confirmation("Confirm Clear", 
                                "Are you sure you want to clear all credentials?"):
                return
                
            # Get current service_id
            if hasattr(self.sidebar, 'current_service_id'):
                service_id = self.sidebar.current_service_id
                self.db_manager.clear_all_credentials(service_id)  # Pass service_id
            else:
                self.db_manager.clear_all_credentials()
                
            if hasattr(self.sidebar, 'credential_list'):
                self.sidebar.credential_list.delete(*self.sidebar.credential_list.get_children())
            if hasattr(self.sidebar, 'cred_status'):
                self.sidebar.cred_status.configure(text="No credentials loaded")
                
            self.text_replacer.reload_replacements()
            show_info("Success", "All credentials have been cleared.")
        except Exception as e:
            show_error("Error", f"Failed to clear credentials: {str(e)}")
    
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load Credentials File", command=self.load_credentials_file)
        file_menu.add_command(label="Reset Credentials Sequence", command=self.reset_credentials)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close_window)
    
    def load_credentials_file(self):
        """Optimized method to load credentials from file with progress indication"""
        try:
            if not hasattr(self.sidebar, 'service_var'):
                show_error("Error", "Please select a service first")
                return
                    
            file_path = filedialog.askopenfilename(
                title="Select Credentials File",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )
            
            if not file_path:
                return

            # First count total lines for progress
            with open(file_path, 'r') as f:
                total_lines = sum(1 for line in f if line.strip())

            # Create progress dialog
            progress = tk.Toplevel(self.root)
            progress.title("Loading Credentials")
            progress.transient(self.root)
            progress.grab_set()
            
            # Center the dialog
            window_width = 300
            window_height = 150
            screen_width = progress.winfo_screenwidth()
            screen_height = progress.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            progress.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # Progress variables
            current = 0
            progress_var = tk.DoubleVar()
            cancel_var = tk.BooleanVar(value=False)

            # Progress UI
            ttk.Label(progress, text="Loading credentials...").pack(pady=5)
            progress_bar = ttk.Progressbar(
                progress, 
                length=280, 
                mode='determinate',
                variable=progress_var
            )
            progress_bar.pack(pady=5, padx=10)
            
            status_label = ttk.Label(progress, text="Checking existing credentials...")
            status_label.pack(pady=5)
            
            stats_label = ttk.Label(progress, text="")
            stats_label.pack(pady=5)
            
            cancel_button = ttk.Button(
                progress,
                text="Cancel",
                command=lambda: cancel_var.set(True)
            )
            cancel_button.pack(pady=5)
            
            try:
                # Get service ID efficiently
                service_name = self.sidebar.service_var.get()
                service_id = self.db_manager.get_service_id_by_name(service_name)
                
                if service_id is None:
                    progress.destroy()
                    show_error("Error", "Invalid service selected")
                    return
                
                # Get existing credentials efficiently
                status_label.config(text="Reading existing credentials...")
                progress.update()
                existing_contents = set(self.db_manager.get_credential_contents_by_service(service_id))
                
                # Initialize variables
                batch_size = 1000
                new_credentials = []
                duplicates = 0
                processed = 0
                
                status_label.config(text="Processing new credentials...")
                
                # Read and process file in chunks
                with open(file_path, 'r') as f:
                    position = len(existing_contents) + 1
                    
                    while True:
                        if cancel_var.get():
                            progress.destroy()
                            return
                            
                        lines = f.readlines(8192)  # Read 8KB at a time
                        if not lines:
                            break
                        
                        # Process the chunk
                        for line in lines:
                            content = line.strip()
                            if not content:
                                continue
                                
                            processed += 1
                            progress_var.set((processed / total_lines) * 100)
                            
                            if content in existing_contents:
                                duplicates += 1
                                stats_label.config(
                                    text=f"Added: {len(new_credentials)} | Duplicates: {duplicates}"
                                )
                                continue
                                
                            new_credentials.append({
                                'service_id': service_id,
                                'content': content,
                                'position': position
                            })
                            position += 1
                            
                            # Update statistics
                            stats_label.config(
                                text=f"Added: {len(new_credentials)} | Duplicates: {duplicates}"
                            )
                            progress.update()
                            
                            # If we have enough for a batch, insert them
                            if len(new_credentials) >= batch_size:
                                status_label.config(text="Saving batch to database...")
                                progress.update()
                                self.db_manager.batch_save_credentials(new_credentials)
                                new_credentials = []
                                status_label.config(text="Processing new credentials...")
                
                # Insert any remaining credentials
                if new_credentials:
                    status_label.config(text="Saving final batch...")
                    progress.update()
                    self.db_manager.batch_save_credentials(new_credentials)
                
                # Clean up
                progress.destroy()
                
                # Update UI
                self.text_replacer.reload_replacements()
                self.update_credential_list()
                
                show_info(
                    "Success",
                    f"Added {position - len(existing_contents) - 1} new credentials\n"
                    f"Skipped {duplicates} duplicates"
                )
                    
            except Exception as e:
                if 'progress' in locals():
                    progress.destroy()
                raise e
                
        except Exception as e:
            show_error("Error", f"Failed to load credentials: {str(e)}")

    def reset_credentials(self):
        """Reset the usage status of all credentials"""
        try:
            if not show_confirmation("Confirm Reset", 
                                "Reset all credentials usage status?"):
                return
                
            # Get current service_id
            if hasattr(self.sidebar, 'current_service_id'):
                service_id = self.sidebar.current_service_id
                self.db_manager.reset_credential_usage(service_id)  # Pass service_id
            else:
                self.db_manager.reset_credential_usage()
                
            self.update_credential_list()
            show_info("Success", "Credentials sequence reset successfully.")
        except Exception as e:
            show_error("Error", f"Failed to reset credentials: {str(e)}")
    
    def setup_ui(self):
        self.create_sidebar()
        self.create_mainbar()
        self.create_footer()
        self.configure_grid()
        self.create_context_menu()
    
    def create_sidebar(self):
        self.sidebar = Sidebar(self.root, self.db_manager, self.hotkey_manager, main_window=self)
        self.sidebar.place(relx=0, rely=0, relwidth=0.55, relheight=0.95)  # Sidebar takes 20% width, 90% height

    def create_mainbar(self):
        self.mainbar = Mainbar(self.root)
        self.mainbar.place(relx=0.55, rely=0, relwidth=0.45, relheight=0.95)  # Mainbar takes the remaining 80% width

    def create_footer(self):
        self.footer = Footer(self.root)
        self.footer.place(relx=0, rely=0.95, relwidth=1, relheight=0.05)  # Footer takes 10% height at the bottom


    def configure_grid(self):
        # Adjust row weights
        self.root.grid_rowconfigure(0, weight=1)  # Main content area
        self.root.grid_rowconfigure(1, weight=0)  # Footer area with minimal weight

        self.root.grid_columnconfigure(0, weight=2)
        self.root.grid_columnconfigure(1, weight=1) 
    
    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.on_edit_shortcut)
        self.context_menu.add_command(label="Delete", command=self.on_delete_shortcut)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy Shortcut", command=self.copy_shortcut)
        self.context_menu.add_command(label="Copy Content", command=self.copy_content)
    def bind_events(self):
        self.root.bind('<Control-s>', lambda e: self.on_save_shortcut())
        self.root.bind('<Control-n>', lambda e: self.mainbar.clear_fields())
        self.root.bind('<Control-q>', lambda e: self.on_close_window())
        self.root.bind('<F5>', lambda e: self.reload_shortcuts())
        self.root.bind('<<LoadCredentials>>', lambda e: self.load_credentials_file())
        self.root.bind('<<ResetCredentials>>', lambda e: self.reset_credentials())
        self.root.bind('<<ClearCredentials>>', lambda e: self.clear_credentials())
        self.root.bind('<<ClearCache>>', lambda e: self.clear_caches())
        if self.sidebar:
            self.sidebar.bind_shortcut_select(self.on_shortcut_select)
            self.sidebar.bind_context_menu(self.show_context_menu)
        if self.mainbar:
            self.mainbar.bind_save(self.on_save_shortcut)
            self.mainbar.bind_delete(self.on_delete_shortcut)
            self.mainbar.bind_service_control(
                self.on_start_service,
                self.on_stop_service
            )
    def clear_caches(self):
        try:
            if not self.text_replacer:
                return
            was_running = self.text_replacer.is_running
            if was_running:
                self.text_replacer.stop()
            with self.text_replacer.replacements_lock:
                self.text_replacer.typed_buffer.clear()
                self.text_replacer.clipboard_cache = None
                self.text_replacer.word_prefixes.clear()
                self.text_replacer.words_to_replace.clear()
                self.text_replacer.credential_keywords.clear()
                self.text_replacer.replacement_cache.clear()
            self.text_replacer.load_replacements()
            if was_running:
                self.text_replacer.start()
            self.reload_shortcuts()
            self.update_credential_list()
            show_info("Success", "All caches cleared and data reloaded!")
        except Exception as e:
            show_error("Error", f"Failed to clear caches: {str(e)}")
            if was_running and not self.text_replacer.is_running:
                self.text_replacer.start()
    def load_initial_data(self):
        try:
            self.reload_shortcuts()
            self.update_credential_list()
            self.text_replacer.reload_replacements()
        except Exception as e:
            show_error("Error", f"Failed to load initial data: {str(e)}")
    def reload_shortcuts(self):
        """Reload shortcuts into the sidebar"""
        try:
            shortcuts = self.db_manager.get_all_shortcuts()
            self.sidebar.load_shortcuts(shortcuts)
        except Exception as e:
            show_error("Error", f"Failed to load shortcuts: {str(e)}")
    def update_service_status(self, is_running: bool):
        self.mainbar.update_service_status(is_running)
    def get_current_shortcut(self) -> Optional[Tuple[str, str]]:
        return self.sidebar.get_selected_shortcut()
    def on_shortcut_select(self, shortcut_data: Optional[Tuple[str, str]]):
        if shortcut_data:
            self.mainbar.set_shortcut_data(*shortcut_data)
    def on_save_shortcut(self) -> bool:
        try:
            shortcut_data = self.mainbar.get_shortcut_data()
            if not shortcut_data:
                show_error("Error", "Please enter both shortcut and content")
                return False
            shortcut, content = shortcut_data
            self.db_manager.save_shortcut(shortcut, content)
            self.text_replacer.reload_replacements()
            self.reload_shortcuts()
            show_info("Success", "Shortcut saved successfully!")
            return True
        except Exception as e:
            show_error("Error", f"Failed to save shortcut: {str(e)}")
            return False
    
    def update_credential_list(self):
        """Update credential list with proper error handling"""
        try:
            if not hasattr(self, 'sidebar') or not self.sidebar:
                print("Debug: Sidebar not initialized")
                return
                
            service_name = self.sidebar.service_var.get() if self.sidebar.service_var else None
            if not service_name:
                print(f"Debug: No service selected. Current service var: {self.sidebar.service_var}")
                return
                
            print(f"Debug: Updating credentials for service: {service_name}")
            
            services = self.db_manager.get_services()
            service_id = next(
                (service['id'] for service in services if service['name'] == service_name),
                None
            )
            
            if service_id is None:
                print(f"Debug: No service_id found for service: {service_name}")
                return
            
            print(f"Debug: Found service_id: {service_id}")
            credentials = self.db_manager.get_credentials_by_service(service_id)
            
            # Count total and used credentials
            total_count = len(credentials)
            used_count = sum(1 for cred in credentials if cred['last_used'])

            print(f"Debug: Found {total_count} credentials ({used_count} used)")

            if self.sidebar.credential_list:
                self.sidebar.credential_list.delete(*self.sidebar.credential_list.get_children())

                for cred in credentials:
                    last_used = cred['last_used']
                    tag = 'used' if last_used else 'unused'
                    self.sidebar.credential_list.insert(
                        "",
                        "end",
                        values=(cred['position'], cred['content']),
                        tags=(tag,)
                    )
                    
                # Configure tags after inserting items
                self.sidebar.credential_list.tag_configure(
                    'used',
                    foreground=Styles.COLORS['status']['stopped'],
                    font=Styles.FONTS['text']
                )
                self.sidebar.credential_list.tag_configure(
                    'unused',
                    foreground=Styles.COLORS['status']['running'],
                    font=Styles.FONTS['text']
                )
                
            if self.sidebar.cred_status:
                self.sidebar.cred_status.configure(
                    text=f"Loaded {total_count} credentials ({used_count} used)"
                )
                
        except Exception as e:
            print(f"Error updating credential list: {str(e)}")
            import traceback
            traceback.print_exc()
            show_error("Error", f"Failed to update credentials list: {str(e)}")

    def delete_credential(self, event):
        """Handle credential deletion"""
        try:
            credential_id = event.data if hasattr(event, 'data') else None
            if not credential_id:
                return
                
            if not show_confirmation("Delete Credential", 
                                "Are you sure you want to delete this credential?"):
                return
                
            service_id = self.sidebar.current_service_id
            if service_id is None:
                show_error("Error", "No service selected")
                return
                
            self.db_manager.delete_credential(int(credential_id))
            self.text_replacer.reload_replacements()
            self.update_credential_list()
            show_info("Success", "Credential deleted successfully!")
        except Exception as e:
            show_error("Error", f"Failed to delete credential: {str(e)}")

    def on_delete_shortcut(self) -> bool:
        current_shortcut = self.get_current_shortcut()
        if not current_shortcut:
            show_error("Error", "Please select a shortcut to delete")
            return False
        if not show_confirmation("Confirm Delete", 
                               "Are you sure you want to delete this shortcut?"):
            return False
        try:
            self.db_manager.delete_shortcut(current_shortcut[0])
            self.text_replacer.reload_replacements()
            self.reload_shortcuts()
            self.mainbar.clear_fields()
            show_info("Success", "Shortcut deleted successfully!")
            return True
        except Exception as e:
            show_error("Error", f"Failed to delete shortcut: {str(e)}")
            return False
    def on_edit_shortcut(self):
        current_shortcut = self.get_current_shortcut()
        if current_shortcut:
            self.mainbar.set_shortcut_data(*current_shortcut)
    def on_start_service(self):
        try:
            self.text_replacer.start()
            self.hotkey_manager.register_all_hotkeys()
        except Exception as e:
            show_error("Error", f"Failed to start service: {str(e)}")
    def on_stop_service(self):
        try:
            self.text_replacer.stop()
            self.hotkey_manager.unregister_all_hotkeys()
            show_info("Success", "Text replacement service stopped!")
        except Exception as e:
            show_error("Error", f"Failed to stop service: {str(e)}")
    def on_close_window(self):
        self.root.withdraw()
        try:
            self.system_tray.start()
        except Exception as e:
            show_error("Error", f"Failed to show system tray: {str(e)}")
    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    def copy_shortcut(self):
        current_shortcut = self.get_current_shortcut()
        if current_shortcut:
            self.root.clipboard_clear()
            self.root.clipboard_append(current_shortcut[0])
    def copy_content(self):
        current_shortcut = self.get_current_shortcut()
        if current_shortcut:
            self.root.clipboard_clear()
            self.root.clipboard_append(current_shortcut[1])