# KeyPhraser

**KeyPhrase** is a powerful utility designed for text replacement, hotkey-based application control, and credential management. Built with Python, it provides a seamless experience for users who need to automate repetitive tasks, manage credentials securely, and use hotkeys for various actions.

## Features

- **Text Replacement**: Automatically replace specified keywords with pre-defined phrases or data from the clipboard.
- **Hotkey Management**: Set and manage custom hotkeys for launching applications or pasting text.
- **Credential Management**: Securely store, access, and cycle through credentials for different services.
- **System Tray Integration**: Control the application from the system tray with easy options to show, hide, and exit.
- **Database Management**: Use an SQLite database to store and manage replacement phrases, hotkeys, and credentials.
- **Cross-platform Compatibility**: Works on both Windows and Linux (some Windows-specific features may be limited on Linux).

## Getting Started

### Prerequisites

Ensure the following are installed:
- Python 3.7+
- [pystray](https://pypi.org/project/pystray/) for system tray functionality
- [keyboard](https://pypi.org/project/keyboard/) for hotkey detection and management
- [Pillow](https://pypi.org/project/Pillow/) for tray icon support
- Additional packages may be required depending on your OS (e.g., `win32clipboard` for Windows)

### Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/rahxosp/KeyPhrase.git
    cd KeyPhrase
    ```

2. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure Application**:
   Set up configuration in `config/settings.py` (e.g., database path, hotkey settings, etc.).

4. **Run the Application**:
    ```bash
    python main.py
    ```

## Usage

### Text Replacement
Define keywords and their replacements in the database. Whenever you type the keyword followed by a space or enter, **KeyPhrase** will automatically replace it with the defined phrase.

### Hotkey Management
Use the `hotkey_manager.py` to configure hotkeys for launching files, applications, or text actions. Registered hotkeys can be easily managed and executed.

### Credential Management
Store credentials in the `database.py` service. You can retrieve and cycle through stored credentials using specific keywords or hotkeys.

### System Tray Integration
**KeyPhrase** includes a system tray icon for quick access. From the tray, you can show/hide the application or exit it entirely.

## Project Structure
.
├── assets                      # Assets such as icons, images, etc.
├── config                      # Configuration files
│   ├── settings.py             # Application settings and constants
│   ├── styles.py               # UI styling settings
│   └── __init__.py
├── data                        # Data storage and logs
│   ├── logs                    # Log files for debugging and monitoring
│   └── replacements.db         # SQLite database for replacements and credentials
├── services                    # Core services of the application
│   ├── database.py             # Manages SQLite database operations
│   ├── hotkey_manager.py       # Manages hotkey registration and execution
│   ├── system_tray.py          # Handles system tray integration
│   ├── text_replacer.py        # Text replacement service for automatic substitutions
│   └── __init__.py
├── ui                          # User interface components
│   ├── main_window.py          # Main application window
│   ├── footer.py               # Footer component for the UI
│   ├── sidebar                 # Sidebar components for navigation
│   │   ├── base.py             # Base class for sidebar components
│   │   ├── credentials_tab.py  # Tab for managing credentials
│   │   ├── hotkey_tab.py       # Tab for hotkey settings
│   │   ├── shortcuts_tab.py    # Tab for managing shortcuts and replacements
│   │   ├── sidebar.py          # Main sidebar functionality
│   │   └── __init__.py
│   └── __init__.py
├── utils                       # Utility functions and helpers
│   ├── decorators.py           # Decorators for various functionalities
│   ├── helpers.py              # Helper functions for common tasks
│   ├── logger.py               # Logging utility for application events
│   ├── validators.py           # Input validation functions
│   └── __init__.py
├── main.py                     # Entry point for the application
├── requirements.txt            # Required dependencies for the project
└── README.md                   # Project documentation
