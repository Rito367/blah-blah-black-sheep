"""
tray_manager.py
System tray manager using pystray with options for Pet and UI opacity.
"""

import threading
from PIL import Image, ImageDraw
import pystray
from pystray import Menu, MenuItem as item
from core import sound_manager


class TrayManager:
    def __init__(self, app):
        self.app = app
        self.icon = None
        self.is_muted = False
        self.current_pet_opacity = 1.0
        self.current_ui_opacity = 1.0

    def _create_icon_image(self):
        image = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 12, 56, 60), fill=(255, 182, 193), outline=(0, 0, 0), width=2)
        draw.polygon([(12, 18), (20, 4), (28, 16)], fill=(255, 182, 193), outline=(0, 0, 0))
        draw.polygon([(36, 16), (44, 4), (52, 18)], fill=(255, 182, 193), outline=(0, 0, 0))
        draw.ellipse((20, 30, 26, 36), fill=(0, 0, 0))
        draw.ellipse((38, 30, 44, 36), fill=(0, 0, 0))
        return image

    def toggle_visibility(self, icon, item):
        self.app.root.after(0, self.app.pet.toggle_hide)

    def toggle_mute(self, icon, item):
        self.is_muted = not self.is_muted
        sound_manager.set_muted(self.is_muted)

    def set_pet_opacity(self, alpha: float):
        def inner(icon, item):
            self.current_pet_opacity = alpha
            if hasattr(self.app.pet, "win") and self.app.pet.win.winfo_exists():
                self.app.root.after(0, lambda: self.app.pet.win.attributes("-alpha", alpha))
        return inner

    def set_ui_opacity(self, alpha: float):
        def inner(icon, item):
            self.current_ui_opacity = alpha
            self.app.root.after(0, lambda: self.app.set_all_ui_opacity(alpha))
        return inner

    def summon_pet(self, icon, item):
        def _summon():
            self.app.pet.ensure_visible()
            self.app.pet.summon_to_cursor()
        self.app.root.after(0, _summon)

    def request_exit(self, icon, item):
        self.app.root.after(0, self.app._quit)

    def build_menu(self):
        return Menu(
            item(
                "Show / Hide Pet",
                self.toggle_visibility,
                checked=lambda item: not getattr(self.app.pet, "_is_hidden", False)
            ),
            item("🎯 Find / Summon Pet", self.summon_pet),
            Menu.SEPARATOR,
            item(
                "Pet Opacity",
                Menu(
                    item("100%", self.set_pet_opacity(1.0), checked=lambda item: self.current_pet_opacity == 1.0),
                    item("80%", self.set_pet_opacity(0.8), checked=lambda item: self.current_pet_opacity == 0.8),
                    item("60%", self.set_pet_opacity(0.6), checked=lambda item: self.current_pet_opacity == 0.6),
                    item("40%", self.set_pet_opacity(0.4), checked=lambda item: self.current_pet_opacity == 0.4),
                )
            ),
            item(
                "UI Windows Opacity",
                Menu(
                    item("100%", self.set_ui_opacity(1.0), checked=lambda item: self.current_ui_opacity == 1.0),
                    item("85%", self.set_ui_opacity(0.85), checked=lambda item: self.current_ui_opacity == 0.85),
                    item("70%", self.set_ui_opacity(0.7), checked=lambda item: self.current_ui_opacity == 0.7),
                    item("50%", self.set_ui_opacity(0.5), checked=lambda item: self.current_ui_opacity == 0.5),
                )
            ),
            item(
                "Mute Sounds",
                self.toggle_mute,
                checked=lambda item: self.is_muted
            ),
            Menu.SEPARATOR,
            item("⌨️ Keybinds & Shortcuts", lambda icon, item: self.app.root.after(0, lambda: self.app._open_window_with_opacity(self.app.keybind_win))),
            item("Settings", lambda icon, item: self.app.root.after(0, lambda: self.app.settings_win.show(*self.app.pet.get_position()))),
            item("Exit Desktop Pet", self.request_exit),
        )

    def start(self):
        self.icon = pystray.Icon(
            name="DesktopPet",
            icon=self._create_icon_image(),
            title="Desktop Pet",
            menu=self.build_menu()
        )
        threading.Thread(target=self.icon.run, daemon=True).start()

    def stop(self):
        if self.icon:
            self.icon.stop()