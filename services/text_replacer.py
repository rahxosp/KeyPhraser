import threading
from collections import deque
import keyboard
import time
from typing import Dict, Optional, Callable, Set, List
from concurrent.futures import ThreadPoolExecutor
import queue
from config import Config
from utils.logger import Logger
import ctypes
from ctypes import wintypes
import win32clipboard
import win32con

KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1

# Windows API Structures
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("padding", ctypes.c_byte * 32)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION)
    ]

class ReplacementCache:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, str] = {}
        self.access_count: Dict[str, int] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            if key in self.cache:
                self.access_count[key] += 1
                return self.cache[key]
            return None

    def set(self, key: str, value: str) -> None:
        with self._lock:
            if len(self.cache) >= self.max_size:
                lfu_key = min(self.access_count.items(), key=lambda x: x[1])[0]
                del self.cache[lfu_key]
                del self.access_count[lfu_key]
            self.cache[key] = value
            self.access_count[key] = 1

    def clear(self) -> None:
        with self._lock:
            self.cache.clear()
            self.access_count.clear()

class TextReplacer:
    def __init__(self):
        # Basic setup
        self.typed_buffer = deque(maxlen=Config.MAX_BUFFER_SIZE)
        self.replacements_lock = threading.RLock()
        self.clipboard_lock = threading.Lock()
        self.words_to_replace: Dict[str, str] = {}
        self.word_prefixes: Set[str] = set()
        self.is_running = False
        self.is_replacing = False
        self.logger = Logger(__name__)

        # Callbacks
        self.on_status_change: Optional[Callable[[bool], None]] = None
        self.on_replacement: Optional[Callable[[str, str], None]] = None

        # Caches
        self.credential_keywords: Set[str] = set()
        self.replacements_cache = ReplacementCache(max_size=1000)
        self.credentials_cache = ReplacementCache(max_size=100)
        self.clipboard_cache = None

        # Threading
        self.replacement_queue = queue.Queue()
        self.replacement_thread = None
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Timing and delays
        self.last_key_time = 0
        self.key_interval_threshold = 0.01
        self.replacement_delay = 0.05
        self.backspace_delay = 0.001
        self.paste_delay = 0.05
        self.last_replacement_time = 0
        self.min_replacement_interval = 0.1

        # Add clipboard-specific settings
        self.clipboard_retry_count = 5
        self.clipboard_base_delay = 0.05
        self.clipboard_timeout = 1.0  # 1 second total timeout

        # Recovery and health
        self.max_retries = 3
        self.service_healthy = True
        self.health_check_interval = 60
        self.health_check_thread = None
        self.max_consecutive_errors = 3
        self.error_recovery_delay = 1.0
        self.last_successful_replacement = time.time()

        # Resource management
        self.max_queue_size = 1000
        self.max_buffer_size = 100
        self.max_replacement_length = 10000
        self.max_shortcut_length = 50
        self.resource_check_interval = 60
        self.last_resource_check = time.time()
        self.memory_usage = 0
        self.queue_usage = 0

        # Input validation
        self.valid_chars = set(
            'abcdefghijklmnopqrstuvwxyz'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            '0123456789'
            '!@#$%^&*()_+-=[]{}|;:,.<>?/~` '
            '"\'\\' # Add quotes and backslash
        )
        self.blocked_chars = set('\x00\x01\x02\x03\x04')

        # Windows API
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        
        # Initialize
        self.attach_thread_input()
        self.vk_map = self.initialize_vk_map()
        self.load_replacements()

    def initialize_vk_map(self) -> Dict[str, int]:
        vk_map = {}
        for i in range(26):
            vk_map[chr(65 + i).lower()] = ord('A') + i
        for i in range(10):
            vk_map[str(i)] = ord('0') + i
        navigation_keys = {
            'left': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT,
            'up': win32con.VK_UP,
            'down': win32con.VK_DOWN,
            'home': win32con.VK_HOME,
            'end': win32con.VK_END,
            'page_up': win32con.VK_PRIOR,
            'page_down': win32con.VK_NEXT
        }
        control_keys = {
            'backspace': win32con.VK_BACK,
            'tab': win32con.VK_TAB,
            'return': win32con.VK_RETURN,
            'enter': win32con.VK_RETURN,
            'shift': win32con.VK_SHIFT,
            'ctrl': win32con.VK_CONTROL,
            'alt': win32con.VK_MENU,
            'pause': win32con.VK_PAUSE,
            'caps_lock': win32con.VK_CAPITAL,
            'escape': win32con.VK_ESCAPE,
            'space': win32con.VK_SPACE,
            'delete': win32con.VK_DELETE,
            'insert': win32con.VK_INSERT
        }
        for i in range(1, 13):
            control_keys[f'f{i}'] = getattr(win32con, f'VK_F{i}')
        vk_map.update(navigation_keys)
        vk_map.update(control_keys)
        return vk_map

    def validate_input(self, text: str, is_shortcut: bool = False) -> bool:
        try:
            if not text:
                return False
            max_len = self.max_shortcut_length if is_shortcut else self.max_replacement_length
            if len(text) > max_len:
                self.logger.warning(f"Text too long: {len(text)} chars (max {max_len})")
                return False
            if is_shortcut:
                if not all(char in self.valid_chars for char in text):
                    self.logger.warning("Shortcut contains invalid characters")
                    return False
                if text.isspace():
                    self.logger.warning("Shortcut cannot be only whitespace")
                    return False
                if text[0].isspace() or text[-1].isspace():
                    self.logger.warning("Shortcut cannot start/end with space")
                    return False
            else:
                if any(char in self.blocked_chars for char in text):
                    self.logger.warning("Text contains blocked characters")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Input validation error: {e}")
            return False


    def on_key_event(self, event) -> None:
        if not self.is_running:
            return
        try:
            if event.event_type == 'down':
                if self.is_replacing:
                    return
                if event.name in ('space', 'enter'):
                    current_word = ''.join(self.typed_buffer)
                    if current_word in self.words_to_replace:
                        self.replacement_queue.put_nowait(current_word)
                    else:
                        print(f"No match found for: '{current_word}'")
                    self.typed_buffer.clear()
                    
                elif event.name == 'backspace' and self.typed_buffer:
                    self.typed_buffer.pop()
                elif len(event.name) == 1 and event.name.isprintable():
                    if len(self.typed_buffer) < self.max_buffer_size:
                        self.typed_buffer.append(event.name)
        except Exception as e:
            self.logger.error(f"Key event error: {e}")
            self.typed_buffer.clear()

    def attach_thread_input(self) -> None:
        try:
            foreground_window = self.user32.GetForegroundWindow()
            if foreground_window:
                target_thread = self.user32.GetWindowThreadProcessId(foreground_window, None)
                current_thread = self.kernel32.GetCurrentThreadId()
                self.user32.AttachThreadInput(current_thread, target_thread, True)
        except Exception as e:
            self.logger.error(f"Failed to attach thread input: {e}")

    def send_virtual_input(self, inputs: List[INPUT]) -> None:
        if not inputs:
            return
        num_inputs = len(inputs)
        input_array = (INPUT * num_inputs)(*inputs)
        result = self.user32.SendInput(num_inputs, input_array, ctypes.sizeof(INPUT))
        if result != num_inputs:
            error = ctypes.get_last_error()
            raise TextReplacerError(f"SendInput failed with error: {error}")

    def create_input_structure(self, vk: int, flags: int = 0) -> INPUT:
        input_struct = INPUT()
        input_struct.type = INPUT_KEYBOARD
        input_struct.union.ki.wVk = vk
        input_struct.union.ki.dwFlags = flags
        input_struct.union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
        return input_struct

    def check_resources(self) -> bool:
        try:
            current_time = time.time()
            if current_time - self.last_resource_check < self.resource_check_interval:
                return True
            self.last_resource_check = current_time
            self.queue_usage = self.replacement_queue.qsize()
            if self.queue_usage > self.max_queue_size:
                self.logger.warning(f"Queue size exceeded: {self.queue_usage}")
                self.clear_queue()
                return False
            if len(self.typed_buffer) > self.max_buffer_size:
                self.logger.warning(f"Buffer size exceeded: {len(self.typed_buffer)}")
                self.typed_buffer.clear()
                return False
            cache_size = (
                len(self.replacements_cache.cache) + 
                len(self.credentials_cache.cache)
            )
            if cache_size > self.max_queue_size:
                self.logger.warning(f"Cache size exceeded: {cache_size}")
                self.clear_caches()
                return False
            return True

        except Exception as e:
            self.logger.error(f"Resource check error: {e}")
            return False

    def start_health_monitoring(self) -> None:
        self.health_check_thread = threading.Thread(
            target=self._monitor_health,
            daemon=True
        )
        self.health_check_thread.start()

    def _monitor_health(self) -> None:
        while self.is_running:
            try:
                time.sleep(self.health_check_interval)
                if not self.service_healthy:
                    self.logger.warning("Service marked as unhealthy")
                    self.attempt_service_recovery()
                    continue
                current_time = time.time()
                time_since_last_replacement = current_time - self.last_successful_replacement
                if time_since_last_replacement > self.health_check_interval * 2:
                    self.logger.warning(f"No successful replacements for {time_since_last_replacement:.1f} seconds")
                    self.attempt_service_recovery() 
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")

    def attempt_service_recovery(self) -> None:
        try:
            self.logger.info("Starting service recovery")
            self.typed_buffer.clear()
            self.clipboard_cache = None
            self.clear_queue()
            self.load_replacements()
            self.attach_thread_input()
            self.logger.info("Service recovery completed")
            self.service_healthy = True
        except Exception as e:
            self.logger.error(f"Service recovery failed: {e}")
            self.restart_service()

    def restart_service(self) -> None:
        try:
            self.stop()
            time.sleep(1)
            self.start()
            self.logger.info("Service restarted successfully")
        except Exception as e:
            self.logger.error(f"Service restart failed: {e}")
            self.is_running = False
            if self.on_status_change:
                self.on_status_change(False)

    def clear_queue(self) -> None:
        try:
            while not self.replacement_queue.empty():
                try:
                    self.replacement_queue.get_nowait()
                except queue.Empty:
                    break
            self.logger.info("Replacement queue cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear queue: {e}")

    def clear_caches(self) -> None:
        try:
            self.replacements_cache.clear()
            self.credentials_cache.clear()
            self.clipboard_cache = None
            self.logger.info("All caches cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear caches: {e}")

    def process_replacement_queue(self) -> None:
        consecutive_errors = 0
        while self.is_running:
            try:
                if not self.check_resources():
                    self.logger.warning("Resource check failed, waiting before continuing")
                    time.sleep(1)
                    continue
                typed_word = self.replacement_queue.get(timeout=0.1)
                if typed_word == "STOP":
                    break
                if not self.validate_input(typed_word, is_shortcut=True):
                    self.logger.warning(f"Invalid shortcut rejected: {typed_word}")
                    continue
                replacement = None
                with self.replacements_lock:
                    if typed_word in self.credential_keywords:
                        replacement = self.credentials_cache.get(typed_word)
                        if replacement is None:
                            replacement = self.get_next_credential(typed_word)
                    else:
                        replacement = self.replacements_cache.get(typed_word)
                        if replacement is None:
                            replacement = self.words_to_replace.get(typed_word)
                            if replacement:
                                self.replacements_cache.set(typed_word, replacement)
                if replacement:
                    if not self.validate_input(replacement):
                        self.logger.warning(f"Invalid replacement rejected for {typed_word}")
                        continue
                    self.perform_replacement(typed_word, replacement)
                    consecutive_errors = 0
                    self.last_successful_replacement = time.time()
                    self.service_healthy = True
            except queue.Empty:
                continue
            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"Error in replacement queue (attempt {consecutive_errors}): {e}")
                if consecutive_errors >= self.max_consecutive_errors:
                    self.logger.critical("Too many consecutive errors, attempting service recovery")
                    self.service_healthy = False
                    self.attempt_service_recovery()
                    consecutive_errors = 0
                time.sleep(self.error_recovery_delay)

    def get_next_credential(self, keyword: str) -> Optional[str]:
        try:
            from services.database import DatabaseManager
            db = DatabaseManager()
            return db.get_next_credential(keyword)
        except Exception as e:
            self.logger.error(f"Failed to get next credential: {str(e)}")
            return None
        
    def get_clipboard_text(self) -> str:
        max_attempts = 5
        base_delay = 0.05
        for attempt in range(max_attempts):
            try:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
                if attempt > 0:
                    time.sleep(base_delay * (2 ** attempt))
                win32clipboard.OpenClipboard(None)
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                    win32clipboard.CloseClipboard()
                    return text
                win32clipboard.CloseClipboard()
                return ""
            except Exception as e:
                self.logger.warning(f"Clipboard read attempt {attempt + 1} failed: {e}")
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
                if attempt == max_attempts - 1:
                    raise TextReplacerError(f"Failed to access clipboard after {max_attempts} attempts")
        return ""

    def set_clipboard_text(self, text: str) -> None:
        max_attempts = 5
        base_delay = 0.05
        for attempt in range(max_attempts):
            try:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
                if attempt > 0:
                    time.sleep(base_delay * (2 ** attempt))
                win32clipboard.OpenClipboard(None)
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                verify_text = self.get_clipboard_text()
                if verify_text == text:
                    return
                self.logger.warning(f"Clipboard verification failed on attempt {attempt + 1}")
            except Exception as e:
                self.logger.warning(f"Clipboard write attempt {attempt + 1} failed: {e}")
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass
                if attempt == max_attempts - 1:
                    raise TextReplacerError(f"Failed to set clipboard after {max_attempts} attempts")
        raise TextReplacerError("Failed to verify clipboard content")

    def perform_replacement(self, typed_word: str, replacement: str) -> None:
        try:
            self.is_replacing = True
            current_time = time.time()
            if current_time - self.last_replacement_time < self.min_replacement_interval:
                self.logger.debug("Skipping replacement - too soon after last replacement")
                return
            try:
                with self.clipboard_lock:
                    original_clipboard = None
                    clipboard_restored = False
                    try:
                        try:
                            win32clipboard.CloseClipboard()
                        except:
                            pass
                        max_attempts = self.clipboard_retry_count
                        base_delay = self.clipboard_base_delay
                        for attempt in range(max_attempts):
                            try:
                                if attempt > 0:
                                    time.sleep(base_delay * (2 ** attempt))
                                win32clipboard.OpenClipboard(None)
                                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                                    original_clipboard = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                                win32clipboard.CloseClipboard()
                                break
                            except Exception as e:
                                self.logger.warning(f"Clipboard read attempt {attempt + 1} failed: {e}")
                                try:
                                    win32clipboard.CloseClipboard()
                                except:
                                    pass
                                if attempt == max_attempts - 1:
                                    raise TextReplacerError("Failed to access clipboard")
                        for attempt in range(max_attempts):
                            try:
                                if attempt > 0:
                                    time.sleep(base_delay * (2 ** attempt))
                                win32clipboard.OpenClipboard(None)
                                win32clipboard.EmptyClipboard()
                                win32clipboard.SetClipboardText(replacement, win32con.CF_UNICODETEXT)
                                win32clipboard.CloseClipboard()
                                verify_text = self.get_clipboard_text()
                                if verify_text == replacement:
                                    break
                                self.logger.warning(f"Clipboard verification failed on attempt {attempt + 1}")
                            except Exception as e:
                                self.logger.warning(f"Clipboard write attempt {attempt + 1} failed: {e}")
                                try:
                                    win32clipboard.CloseClipboard()
                                except:
                                    pass
                                if attempt == max_attempts - 1:
                                    raise TextReplacerError("Failed to set clipboard content")
                        time.sleep(self.replacement_delay)
                        word_length = len(typed_word) + 1
                        backspace_inputs = []
                        for _ in range(word_length):
                            backspace_inputs.extend([
                                self.create_input_structure(self.vk_map['backspace']),
                                self.create_input_structure(self.vk_map['backspace'], KEYEVENTF_KEYUP)
                            ])
                        self.send_virtual_input(backspace_inputs)
                        time.sleep(self.backspace_delay)
                        paste_inputs = [
                            self.create_input_structure(self.vk_map['ctrl']),
                            self.create_input_structure(self.vk_map['v']),
                            self.create_input_structure(self.vk_map['v'], KEYEVENTF_KEYUP),
                            self.create_input_structure(self.vk_map['ctrl'], KEYEVENTF_KEYUP)
                        ]
                        time.sleep(self.paste_delay)
                        self.send_virtual_input(paste_inputs)
                        time.sleep(self.paste_delay)
                        self.last_replacement_time = time.time()
                        self.last_successful_replacement = time.time()
                        self.service_healthy = True
                    finally:
                        if original_clipboard is not None and not clipboard_restored:
                            for attempt in range(max_attempts):
                                try:
                                    if attempt > 0:
                                        time.sleep(base_delay * (2 ** attempt))
                                    win32clipboard.OpenClipboard(None)
                                    win32clipboard.EmptyClipboard()
                                    win32clipboard.SetClipboardText(original_clipboard, win32con.CF_UNICODETEXT)
                                    win32clipboard.CloseClipboard()
                                    clipboard_restored = True
                                    break
                                except Exception as e:
                                    self.logger.warning(f"Clipboard restore attempt {attempt + 1} failed: {e}")
                                    try:
                                        win32clipboard.CloseClipboard()
                                    except:
                                        pass
                                    if attempt == max_attempts - 1:
                                        self.logger.error("Failed to restore clipboard")
                    self.logger.info(f"Replaced '{typed_word}'")
                    if self.on_replacement:
                        self.executor.submit(self.on_replacement, typed_word, replacement)
            except Exception as e:
                self.logger.error(f"Replacement failed: {e}")
                raise TextReplacerError(f"Replacement failed: {str(e)}")
        finally:
            self.is_replacing = False
            self.typed_buffer.clear()

    def load_replacements(self):
        try:
            from services.database import DatabaseManager
            db = DatabaseManager()
            with self.replacements_lock:
                self.replacements_cache.clear()
                self.credentials_cache.clear()
                self.words_to_replace = db.get_shortcuts_dict()
                self.word_prefixes = set()
                for keyword in self.words_to_replace:
                    if self.validate_input(keyword, is_shortcut=True):
                        current_word = []
                        for char in keyword:
                            current_word.append(char)
                            self.word_prefixes.add(''.join(current_word))
                for keyword, replacement in self.words_to_replace.items():
                    if self.validate_input(replacement):
                        self.replacements_cache.set(keyword, replacement)
                self.credential_keywords = {k for k in self.words_to_replace if k.startswith("@")}
                self.logger.info(f"Loaded {len(self.words_to_replace)} shortcuts")
                self.logger.debug(f"Cached {len(self.replacements_cache.cache)} replacements")
        except Exception as e:
            self.logger.error(f"Failed to load replacements: {str(e)}")
            raise TextReplacerError(f"Failed to load replacements: {str(e)}")


    def reload_replacements(self):
        was_running = self.is_running
        if was_running:
            self.stop()
        self.replacements_cache.clear()
        self.credentials_cache.clear()
        self.load_replacements()
        if was_running:
            self.start()

    def start(self) -> None:
        if not self.is_running:
            try:
                self.load_replacements()
                if not self.words_to_replace:
                    raise TextReplacerError("No replacements loaded")
                self.is_running = True
                self.service_healthy = True
                self.start_health_monitoring()
                self.replacement_thread = threading.Thread(
                    target=self.process_replacement_queue,
                    daemon=True
                )
                self.replacement_thread.start()
                keyboard.hook(self.on_key_event)
                self.logger.info("Text replacement service started successfully")
                if self.on_status_change:
                    self.on_status_change(True)
            except Exception as e:
                self.is_running = False
                self.logger.error(f"Failed to start service: {e}")
                raise TextReplacerError(f"Failed to start service: {str(e)}")

    def stop(self) -> None:
        if self.is_running:
            try:
                self.is_running = False
                self.service_healthy = False
                if self.health_check_thread and self.health_check_thread.is_alive():
                    try:
                        self.health_check_thread.join(timeout=1.0)
                    except Exception as e:
                        self.logger.error(f"Error stopping health monitor: {e}")
                self.replacements_cache.clear()
                self.credentials_cache.clear()
                if self.executor:
                    try:
                        for future in self.get_pending_futures():
                            future.cancel()
                        self.executor.shutdown(wait=True, cancel_futures=True)
                    except Exception as e:
                        self.logger.error(f"Error shutting down executor: {e}")
                if self.replacement_thread and self.replacement_thread.is_alive():
                    try:
                        self.replacement_queue.put("STOP")
                        self.replacement_thread.join(timeout=1.0)
                    except Exception as e:
                        self.logger.error(f"Error stopping replacement thread: {e}")
                keyboard.unhook_all()
                try:
                    foreground_window = self.user32.GetForegroundWindow()
                    if foreground_window:
                        target_thread = self.user32.GetWindowThreadProcessId(foreground_window, None)
                        current_thread = self.kernel32.GetCurrentThreadId()
                        self.user32.AttachThreadInput(current_thread, target_thread, False)
                except Exception as e:
                    self.logger.error(f"Failed to detach thread input: {e}")
                self.typed_buffer.clear()
                self.clipboard_cache = None
                self.logger.info("Text replacement service stopped successfully")
                if self.on_status_change:
                    self.on_status_change(False)
            except Exception as e:
                self.logger.error(f"Failed to stop service: {e}")
                raise TextReplacerError(f"Failed to stop service: {str(e)}")

    def get_pending_futures(self):
        try:
            if hasattr(self.executor, '_work_queue'):
                return list(self.executor._work_queue)
            return []
        except Exception:
            return []

class TextReplacerError(Exception):
    pass