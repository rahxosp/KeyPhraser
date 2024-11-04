class Styles:
    
    FONTS = {
        'heading': ("Helvetica", 16, "bold"),
        'subheading': ("Helvetica", 14, "bold"),
        'text': ("Helvetica", 12),
        'small': ("Helvetica", 10),
        'icon': ("Segoe UI Emoji", 14),
        'monospace': ("Consolas", 12)
    }
    
    COLORS = {
        'background': "#292929",
        'foreground': "#ffffff",
        'footer': "#151515",
        'text': {
            'primary': "#ffffff",
            'secondary': "#a0a0a0",
            'disabled': "#666666",
            'error': "#ff4444",
            'success': "#44ff44",
            'warning': "#ffaa44"
        },
        'button': {
            'primary': "#007acc",
            'primary_hover': "#0098ff",
            'danger': "#cc0000",
            'danger_hover': "#ff0000"
        },
        'status': {
            'running': "#44ff44",
            'stopped': "#ff4444",
            'warning': "#ffaa44"
        }
    }
    DARK_THEME = {
        'window': {
            'background': "#292929",
            'header': "#1c1c1c"
        },
        'sidebar': {
            'background': "#1e1e1e",
            'item_hover': "#383838",
            'item_selected': "#383838"
        },
        'mainbar': {
            'background': "#252525",
            'frame_bg': "#2d2d2d"
        },
        'footer': {
            'background': "#151515",
            'text': "#ffffff"
        }
    }
    
    TREEVIEW_STYLE = {
            'configure': {
                'background': "#292929",
                'foreground': "white",
                'fieldbackground': "#292929",
                'borderwidth': 0,
                'rowheight': 30,
                'padding': 5,
                'font': FONTS['text']
            },
            'map': {
                'background': [('selected', '#383838')],
                'foreground': [('selected', 'white')]
            }
        }
    
    ENTRY_STYLE = {
        'padding': 5,
        'font': FONTS['text']
    }
    
    TEXT_STYLE = {
        'padding': 5,
        'font': FONTS['text'],
        'wrap': 'word',
        'relief': 'flat',
        'borderwidth': 1
    }
    
    BUTTON_STYLE = {
        'padding': (10, 5),
        'font': FONTS['text']
    }
    
    @classmethod
    def get_theme(cls, is_dark=True):
        return cls.DARK_THEME
    
    @classmethod
    def get_status_color(cls, status: str) -> str:
        return cls.COLORS['status'].get(status, cls.COLORS['text']['primary'])
    
    @classmethod
    def configure_treeview_style(cls, style):
        style.configure(
            "Treeview",
            **cls.TREEVIEW_STYLE['configure']
        )
        style.map(
            "Treeview",
            **cls.TREEVIEW_STYLE['map']
        )
        style.configure(
            "Treeview.Heading",
            background=cls.DARK_THEME['window']['header'],
            foreground=cls.COLORS['text']['primary'],
            padding=5
        )
    
    @classmethod
    def configure_all_styles(cls, style):
        style.configure(
            "Dark.TFrame",
            background="#1e1e1e"
        )
        style.configure(
            "Header.TLabel",
            background="#1e1e1e",
            foreground="white",
            font=cls.FONTS['heading']
        )
        style.configure(
            "Dark.Treeview",
            background="#1e1e1e",
            foreground="white",
            fieldbackground="#1e1e1e",
            borderwidth=0,
            rowheight=30,
            font=cls.FONTS['text']
        )
        style.configure(
            "Dark.Treeview.Heading",
            background="#1e1e1e",
            foreground="#888888",
            borderwidth=0,
            font=cls.FONTS['text']
        )
        style.map(
            "Dark.Treeview",
            background=[('selected', '#333333')],
            foreground=[('selected', '#00a8e8')]
        )
        style.configure(
            "TScrollbar",
            background="#1e1e1e",
            troughcolor="#1e1e1e",
            borderwidth=0,
            arrowsize=12
        )
        style.configure(
            'Search.TEntry',
            fieldbackground=Styles.COLORS['background'],
            foreground=Styles.COLORS['text']['primary'],
            borderwidth=1,
            relief="solid"
        )
        style.configure(
            "TCombobox",
            fieldbackground=Styles.COLORS['background'],
            foreground=Styles.COLORS['text']['primary'],
            font=("Helvetica", 16, "bold")
        )

        style.configure("Accent.TButton", background=Styles.COLORS['button']['primary'], foreground="white")
        style.map("Accent.TButton", background=[("active", Styles.COLORS['button']['primary_hover'])])
        style.configure("Danger.TButton", background=Styles.COLORS['button']['danger'], foreground="white")
        style.map("Danger.TButton", background=[("active", Styles.COLORS['button']['danger_hover'])])