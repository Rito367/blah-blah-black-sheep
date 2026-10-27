"""
themes.py
Theme configuration with safe fallback for empty custom menu colors.
8 built-in themes + a fully customizable 'custom' theme.
"""

# All colour keys used across every theme
THEME_KEYS = [
    "bg_card", "bg_hdr", "bg_grid", "bg_today", "bg_hover",
    "border", "accent", "btn",
    "fg_main", "fg_dim", "fg_white", "fg_day_hdr",
    "menu_bg", "menu_fg", "menu_active_bg", "menu_active_fg",
    "bubble_bg", "bubble_out", "bubble_fg",
]

# Human-readable labels for the theme editor
THEME_KEY_LABELS = {
    "bg_card":        "Card / Window BG",
    "bg_hdr":         "Header BG",
    "bg_grid":        "Grid / Panel BG",
    "bg_today":       "Today Highlight",
    "bg_hover":       "Hover BG",
    "border":         "Border",
    "accent":         "Accent",
    "btn":            "Button BG",
    "fg_main":        "Main Text",
    "fg_dim":         "Dim Text",
    "fg_white":       "White Text",
    "fg_day_hdr":     "Day Header Text",
    "menu_bg":        "Menu BG",
    "menu_fg":        "Menu Text",
    "menu_active_bg": "Menu Hover BG",
    "menu_active_fg": "Menu Hover Text",
    "bubble_bg":      "Bubble BG",
    "bubble_out":     "Bubble Outline",
    "bubble_fg":      "Bubble Text",
}

THEMES = {
    "pink": {
        "bg_card": "#ffffff", "bg_hdr": "#ffb6c1", "bg_grid": "#fff0f5",
        "bg_today": "#ff69b4", "bg_hover": "#ffe4e1", "border": "#ffb6c1",
        "accent": "#e74c3c", "btn": "#f8bbd0",
        "fg_main": "#333333", "fg_dim": "#888888", "fg_white": "#ffffff", "fg_day_hdr": "#888888",
        "menu_bg": "#ffffff", "menu_fg": "#333333", "menu_active_bg": "#f8bbd0", "menu_active_fg": "#ffffff",
        "bubble_bg": "#ffffff", "bubble_out": "#ffb6c1", "bubble_fg": "#333333",
    },
    "dark": {
        "bg_card": "#20222e", "bg_hdr": "#151620", "bg_grid": "#181924",
        "bg_today": "#e74c3c", "bg_hover": "#2c2e3f", "border": "#181920",
        "accent": "#e74c3c", "btn": "#2c2e3f",
        "fg_main": "#ffffff", "fg_dim": "#888888", "fg_white": "#ffffff", "fg_day_hdr": "#aaaaaa",
        "menu_bg": "#20222e", "menu_fg": "#ffffff", "menu_active_bg": "#2c2e3f", "menu_active_fg": "#ffffff",
        "bubble_bg": "#20222e", "bubble_out": "#e74c3c", "bubble_fg": "#ffffff",
    },
    "lavender": {
        "bg_card": "#ffffff", "bg_hdr": "#b39ddb", "bg_grid": "#ede7f6",
        "bg_today": "#7e57c2", "bg_hover": "#d1c4e9", "border": "#b39ddb",
        "accent": "#5e35b1", "btn": "#d1c4e9",
        "fg_main": "#333333", "fg_dim": "#777777", "fg_white": "#ffffff", "fg_day_hdr": "#777777",
        "menu_bg": "#ffffff", "menu_fg": "#333333", "menu_active_bg": "#d1c4e9", "menu_active_fg": "#ffffff",
        "bubble_bg": "#ffffff", "bubble_out": "#b39ddb", "bubble_fg": "#333333",
    },
    "ocean": {
        "bg_card": "#e8f4f8", "bg_hdr": "#0077b6", "bg_grid": "#caf0f8",
        "bg_today": "#0096c7", "bg_hover": "#ade8f4", "border": "#90e0ef",
        "accent": "#0077b6", "btn": "#48cae4",
        "fg_main": "#03045e", "fg_dim": "#5d7f8f", "fg_white": "#ffffff", "fg_day_hdr": "#5d7f8f",
        "menu_bg": "#e8f4f8", "menu_fg": "#03045e", "menu_active_bg": "#48cae4", "menu_active_fg": "#ffffff",
        "bubble_bg": "#e8f4f8", "bubble_out": "#0077b6", "bubble_fg": "#03045e",
    },
    "forest": {
        "bg_card": "#f1f8e9", "bg_hdr": "#388e3c", "bg_grid": "#dcedc8",
        "bg_today": "#2e7d32", "bg_hover": "#c5e1a5", "border": "#a5d6a7",
        "accent": "#1b5e20", "btn": "#81c784",
        "fg_main": "#1b5e20", "fg_dim": "#558b2f", "fg_white": "#ffffff", "fg_day_hdr": "#558b2f",
        "menu_bg": "#f1f8e9", "menu_fg": "#1b5e20", "menu_active_bg": "#81c784", "menu_active_fg": "#ffffff",
        "bubble_bg": "#f1f8e9", "bubble_out": "#388e3c", "bubble_fg": "#1b5e20",
    },
    "sunset": {
        "bg_card": "#fff8f0", "bg_hdr": "#ff7043", "bg_grid": "#fff3e0",
        "bg_today": "#f4511e", "bg_hover": "#ffe0b2", "border": "#ffab91",
        "accent": "#e64a19", "btn": "#ffab91",
        "fg_main": "#4e342e", "fg_dim": "#8d6e63", "fg_white": "#ffffff", "fg_day_hdr": "#8d6e63",
        "menu_bg": "#fff8f0", "menu_fg": "#4e342e", "menu_active_bg": "#ffab91", "menu_active_fg": "#ffffff",
        "bubble_bg": "#fff8f0", "bubble_out": "#ff7043", "bubble_fg": "#4e342e",
    },
    "midnight": {
        "bg_card": "#0d0d1a", "bg_hdr": "#1a1a3e", "bg_grid": "#0d0d2b",
        "bg_today": "#7b2fff", "bg_hover": "#1e1e4a", "border": "#2e2e6e",
        "accent": "#7b2fff", "btn": "#2e2e6e",
        "fg_main": "#e0e0ff", "fg_dim": "#9090bb", "fg_white": "#ffffff", "fg_day_hdr": "#9090bb",
        "menu_bg": "#0d0d1a", "menu_fg": "#e0e0ff", "menu_active_bg": "#2e2e6e", "menu_active_fg": "#ffffff",
        "bubble_bg": "#0d0d1a", "bubble_out": "#7b2fff", "bubble_fg": "#e0e0ff",
    },
    "cherry": {
        "bg_card": "#fff5f7", "bg_hdr": "#c2185b", "bg_grid": "#fce4ec",
        "bg_today": "#ad1457", "bg_hover": "#f8bbd0", "border": "#f48fb1",
        "accent": "#880e4f", "btn": "#f48fb1",
        "fg_main": "#4a0028", "fg_dim": "#880e4f", "fg_white": "#ffffff", "fg_day_hdr": "#880e4f",
        "menu_bg": "#fff5f7", "menu_fg": "#4a0028", "menu_active_bg": "#f48fb1", "menu_active_fg": "#ffffff",
        "bubble_bg": "#fff5f7", "bubble_out": "#c2185b", "bubble_fg": "#4a0028",
    },
    # Fully customizable — loaded from pet_data.json on startup
    "custom": {
        "bg_card": "#ffffff", "bg_hdr": "#ffb6c1", "bg_grid": "#fff0f5",
        "bg_today": "#ff69b4", "bg_hover": "#ffe4e1", "border": "#ffb6c1",
        "accent": "#e74c3c", "btn": "#f8bbd0",
        "fg_main": "#333333", "fg_dim": "#888888", "fg_white": "#ffffff", "fg_day_hdr": "#888888",
        "menu_bg": "#ffffff", "menu_fg": "#333333", "menu_active_bg": "#f8bbd0", "menu_active_fg": "#ffffff",
        "bubble_bg": "#ffffff", "bubble_out": "#ffb6c1", "bubble_fg": "#333333",
    },
}

THEME_ORDER = [
    "pink", "dark", "lavender", "ocean", "forest",
    "sunset", "midnight", "cherry", "custom",
]
THEME_LABELS = {
    "pink":     "🌸 Sakura Pink",
    "dark":     "🌙 Midnight Dark",
    "lavender": "💜 Lavender Glow",
    "ocean":    "🌊 Ocean Breeze",
    "forest":   "🌿 Forest Green",
    "sunset":   "🌅 Sunset Orange",
    "midnight": "🔮 Midnight Purple",
    "cherry":   "🍒 Cherry Blossom",
    "custom":   "🎨 My Custom Theme",
}

_current_theme = "pink"
_custom_colors: dict[str, str] = {}


def set_theme(name: str):
    global _current_theme
    if name in THEMES:
        _current_theme = name


def set_custom_theme_data(theme_dict: dict):
    """Overwrite the mutable 'custom' theme entry with user-saved colours."""
    if isinstance(theme_dict, dict) and theme_dict:
        THEMES["custom"].update(theme_dict)


def set_custom_menu_colors(colors: dict):
    global _custom_colors
    if isinstance(colors, dict):
        _custom_colors = {k: v for k, v in colors.items() if v and isinstance(v, str) and v.strip()}
    else:
        _custom_colors = {}


def current_name() -> str:
    return _current_theme


def get() -> dict:
    theme_dict = dict(THEMES.get(_current_theme, THEMES["pink"]))
    if "bubble_fg" not in theme_dict:
        theme_dict["bubble_fg"] = theme_dict.get("fg_main", "#333333")
    theme_dict.update(_custom_colors)
    return theme_dict
