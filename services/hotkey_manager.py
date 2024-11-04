import os
import subprocess
import keyboard
from typing import Dict
from utils.logger import Logger
from utils.helpers import show_error, show_info
class HotkeyManager:
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.hotkey_list = []  # Initialize the hotkey list
        self.registered_hotkeys = {}  # Initialize registered_hotkeys dictionary
        self.load_hotkeys()

    def load_hotkeys(self):
        try:
            self.hotkey_list = self.db_manager.get_all_hotkeys()
        except Exception as e:
            print(f"Failed to load hotkeys: {e}")
            self.hotkey_list = []

    def register_all_hotkeys(self):
        """Register all hotkeys from database"""
        try:
            self.unregister_all_hotkeys()
            hotkeys = self.db_manager.get_all_hotkeys()
            for key_combo, action_value, action_type in hotkeys:
                self.register_hotkey(key_combo, action_value, action_type)
            print(f"Registered {len(hotkeys)} hotkeys")
        except Exception as e:
            print(f"Failed to register hotkeys: {e}")
            raise

    def register_hotkey(self, key_combo: str, action_value: str, action_type: str):
        """Register a single hotkey with better error handling"""
        try:
            formatted_combo = self._format_key_combo(key_combo)
            try:
                if formatted_combo in self.registered_hotkeys:
                    keyboard.remove_hotkey(formatted_combo)
                    print(f"Removed existing hotkey: {formatted_combo}")
            except Exception as e:
                print(f"Failed to remove existing hotkey {formatted_combo}: {e}")
            
            self.registered_hotkeys[formatted_combo] = {
                'action_value': action_value,
                'action_type': action_type
            }
            keyboard.add_hotkey(
                formatted_combo,
                lambda: self._execute_hotkey(formatted_combo),
                suppress=True
            )
            print(f"Registered hotkey: {formatted_combo}")
        except Exception as e:
            print(f"Failed to register hotkey {key_combo}: {e}")
            self.registered_hotkeys.pop(formatted_combo, None)

    def _format_key_combo(self, key_combo: str) -> str:
        """Format key combination for keyboard library"""
        mapping = {
            'control_l': 'ctrl',
            'control_r': 'ctrl',
            'alt_l': 'alt',
            'alt_r': 'alt',
            'shift_l': 'shift',
            'shift_r': 'shift'
        }
        combo = key_combo.lower()
        for old, new in mapping.items():
            combo = combo.replace(old, new)
        return combo.replace(' ', '')

    def _execute_hotkey(self, key_combo: str):
        """Execute the action for a hotkey"""
        try:
            hotkey = self.registered_hotkeys.get(key_combo)
            if not hotkey:
                return
            action_value = hotkey['action_value']
            action_type = hotkey['action_type']
            if action_type == 'file':
                if os.path.exists(action_value):
                    os.startfile(action_value)
                else:
                    show_error("Error", f"File not found: {action_value}")
            elif action_type == 'application':
                try:
                    subprocess.Popen(action_value)
                except Exception as e:
                    show_error("Error", f"Failed to launch application: {str(e)}")
            print(f"Executed hotkey {key_combo}: {action_type} - {action_value}")
        except Exception as e:
            print(f"Failed to execute hotkey {key_combo}: {e}")
            show_error("Error", f"Failed to execute hotkey: {str(e)}")

    def unregister_all_hotkeys(self):
        """Unregister all hotkeys with better error handling"""
        try:
            for combo in list(self.registered_hotkeys.keys()):
                try:
                    keyboard.remove_hotkey(combo)
                    print(f"Unregistered hotkey: {combo}")
                except Exception as e:
                    print(f"Failed to unregister hotkey {combo}: {e}")
            self.registered_hotkeys.clear()
            print("Cleared all hotkey registrations")
        except Exception as e:
            print(f"Failed to unregister hotkeys: {e}")

from services.hotkey_manager import HotkeyManager