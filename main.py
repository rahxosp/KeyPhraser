import os
import sys
import tkinter as tk
from typing import Optional
import sv_ttk
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
from ui.main_window import MainWindow
from config.settings import Config
from config.styles import Styles
from services.database import DatabaseManager
from services.text_replacer import TextReplacer
from services.system_tray import SystemTrayService
from utils.logger import Logger
from utils.helpers import show_error, show_info, show_confirmation
class Application:
    def __init__(self):
        self.logger = Logger("TextChanger", Logger.get_current_log_file())
        self.logger.info("Initializing application...")
        self.root: Optional[tk.Tk] = None
        self.db_manager: Optional[DatabaseManager] = None
        self.text_replacer: Optional[TextReplacer] = None
        self.system_tray: Optional[SystemTrayService] = None
        self.main_window: Optional[MainWindow] = None
        try:
            self.initialize_application()
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {str(e)}")
            show_error("Initialization Error", 
                      f"Failed to initialize application: {str(e)}")
            sys.exit(1)
    def initialize_application(self):
        if hasattr(Config, 'initialize'):
            Config.initialize()
        self.db_manager = DatabaseManager()
        self.text_replacer = TextReplacer()
        self.system_tray = SystemTrayService()
        self.root = tk.Tk()
        self.setup_window()
        self.setup_theme()
        self.main_window = MainWindow(
            self.root,
            self.text_replacer,
            self.db_manager,
            self.system_tray
        )
        self.setup_callbacks()
    def setup_window(self):
        self.root.title(Config.APP_NAME)
        self.root.geometry(Config.WINDOW_SIZE)
        self.root.minsize(Config.MIN_WIDTH, Config.MIN_HEIGHT)
        if hasattr(Config, 'ICON_PATH') and os.path.exists(Config.ICON_PATH):
            self.root.iconbitmap(Config.ICON_PATH)
        self.root.protocol('WM_DELETE_WINDOW', self.on_window_close)
    def setup_theme(self):
        sv_ttk.set_theme("dark")
        style = tk.ttk.Style()
        Styles.configure_all_styles(style)
        if sys.platform == 'win32':
            self.setup_windows_theme()
    def setup_windows_theme(self):
        try:
            import pywinstyles
            version = sys.getwindowsversion()
            if version.major == 10 and version.build >= 22000:
                pywinstyles.change_header_color(
                    self.root,
                    Styles.get_theme(True)['window']['header']
                )
            elif version.major == 10:
                pywinstyles.apply_style(self.root, "dark")
                self.root.after(10, lambda: self.root.wm_attributes("-alpha", 0.99))
                self.root.after(20, lambda: self.root.wm_attributes("-alpha", 1.0))
        except Exception as e:
            self.logger.warning(f"Failed to apply Windows theme: {str(e)}")
    def setup_callbacks(self):
        self.text_replacer.on_status_change = self.main_window.update_service_status
        self.system_tray.on_show = self.show_window
        self.system_tray.on_hide = self.hide_window
        self.system_tray.on_exit = self.quit_application
    def show_window(self):
        self.root.after(0, self.root.deiconify)
        self.root.lift()
        self.root.focus_force()
    def hide_window(self):
        self.root.withdraw()
    def on_window_close(self):
        if self.text_replacer and self.text_replacer.is_running:
            response = show_confirmation(
                "Exit Application",
                "Text replacement service is still running. Stop it and exit?"
            )
            if not response:
                return
            try:
                self.text_replacer.stop()
            except Exception as e:
                self.logger.error(f"Failed to stop text replacer: {str(e)}")
        self.hide_window()
    def quit_application(self):
        try:
            if self.text_replacer and self.text_replacer.is_running:
                self.text_replacer.stop()
            if self.system_tray:
                self.system_tray.stop()
            if self.root:
                self.root.quit()
                self.root.destroy()
            self.logger.info("Application shut down successfully")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}")
            show_error("Shutdown Error", 
                    f"Error during shutdown: {str(e)}")
        finally:
            os._exit(0) 
    def run(self):
        try:
            self.system_tray.start()
            self.logger.info("Starting application main loop")
            self.root.mainloop()
        except Exception as e:
            self.logger.critical(f"Application crashed: {str(e)}")
            show_error("Fatal Error", 
                      f"Application crashed: {str(e)}\n\nPlease check the logs.")
            sys.exit(1)
def main():
    try:
        app = Application()
        app.run()
    except Exception as e:
        show_error("Fatal Error", 
                  f"Unhandled error: {str(e)}\n\nThe application will now exit.")
        sys.exit(1)
if __name__ == "__main__":
    main()