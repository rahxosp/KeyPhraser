import tkinter as tk
from tkinter import messagebox
import json
from typing import Optional, Any, Dict
from datetime import datetime
from pathlib import Path
from config import Config, Styles

def create_tooltip(widget: tk.Widget, text: str):
    """Create a tooltip for a widget"""
    
    tooltip: Optional[tk.Toplevel] = None
    
    def show_tooltip(event):
        nonlocal tooltip
        
        x, y, _, _ = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 20
        
        # Create tooltip window
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip content
        label = tk.Label(
            tooltip,
            text=text,
            justify='left',
            background=Styles.COLORS['background'],
            foreground=Styles.COLORS['text']['primary'],
            relief='solid',
            borderwidth=1,
            font=Styles.FONTS['small']
        )
        label.pack()

    def hide_tooltip(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None

    widget.bind('<Enter>', show_tooltip)
    widget.bind('<Leave>', hide_tooltip)

def show_error(title: str, message: str):
    """Show error message box"""
    return messagebox.showerror(title, message)

def show_info(title: str, message: str):
    """Show information message box"""
    return messagebox.showinfo(title, message)

def show_confirmation(title: str, message: str) -> bool:
    """Show confirmation dialog"""
    return messagebox.askyesno(title, message)

def save_json(data: Any, filename: str):
    """Save data to JSON file"""
    filepath = Config.DATA_DIR / filename
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        raise IOError(f"Failed to save JSON file: {str(e)}")

def load_json(filename: str) -> Any:
    """Load data from JSON file"""
    filepath = Config.DATA_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise IOError(f"Failed to load JSON file: {str(e)}")

def format_timestamp(timestamp: float) -> str:
    """Format timestamp to human-readable string"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def ensure_directory(path: Path):
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)

def get_file_size(filepath: Path) -> str:
    """Get human-readable file size"""
    size = filepath.stat().st_size
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def create_backup_filename(prefix: str) -> str:
    """Create backup filename with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_backup_{timestamp}.json"
