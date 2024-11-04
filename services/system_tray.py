import threading
from PIL import Image
import pystray
from pystray import MenuItem as item
from typing import Optional, Callable, Any
from config import Config

class SystemTrayService:
    
    def __init__(self):
        self.icon: Any = None
        self.icon_thread: Optional[threading.Thread] = None
        self.on_show: Optional[Callable[[], None]] = None
        self.on_hide: Optional[Callable[[], None]] = None
        self.on_exit: Optional[Callable[[], None]] = None
        self.icon_image = Image.open(Config.ICON_PATH) 
        self.create_icon()

    def create_icon(self) -> None:
        try:
            menu = (
                item('Show', self.show_window, default=True),
                item('Hide', self.hide_window),
                pystray.Menu.SEPARATOR,
                item('Exit', self.exit_application)
            )
            self.icon = pystray.Icon(
                name=Config.APP_NAME,
                icon=self.icon_image,
                title=Config.APP_NAME,
                menu=menu
            )
        except Exception as e:
            raise SystemTrayError(f"Failed to create system tray icon: {str(e)}")

    def show_window(self, icon: Any = None) -> None:
        if self.on_show:
            self.on_show()

    def hide_window(self, icon: Any = None) -> None:
        if self.on_hide:
            self.on_hide()

    def start(self) -> None:
        if not self.icon_thread and self.icon:
            try:
                self.icon_thread = threading.Thread(
                    target=self.icon.run,
                    daemon=True
                )
                self.icon_thread.start()
            except Exception as e:
                raise SystemTrayError(f"Failed to start system tray: {str(e)}")

    def stop(self) -> None:
        try:
            if self.icon:
                self.icon.visible = False
                self.icon.stop()
            self.icon_thread = None
        except Exception as e:
            raise SystemTrayError(f"Failed to stop system tray: {str(e)}")

    def exit_application(self, icon: Any = None) -> None:
        try:
            if self.on_exit:
                self.on_exit()
            self.stop()  # Use stop to avoid redundant icon stopping
        except Exception as e:
            raise SystemTrayError(f"Failed to exit application: {str(e)}")

    def show_icon(self) -> None:
        if not self.is_running:
            self.start()

    def hide_icon(self) -> None:
        if self.is_running:
            self.stop()

    @property
    def is_running(self) -> bool:
        return bool(self.icon_thread and self.icon_thread.is_alive())

class SystemTrayError(Exception):
    pass
