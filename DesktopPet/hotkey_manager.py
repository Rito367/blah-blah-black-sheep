"""
hotkey_manager.py
Manages global system hotkeys for pet summon and pet hide/stealth toggles.
"""

import keyboard


class HotkeyManager:
    def __init__(self, on_hide_toggle, on_summon):
        self.on_hide_toggle = on_hide_toggle
        self.on_summon = on_summon
        self.hide_hotkey = ""
        self.summon_hotkey = ""

    def apply_hotkeys(self, hide_combo: str, summon_combo: str):
        # Clear existing hotkeys
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

        self.hide_hotkey = hide_combo.strip()
        self.summon_hotkey = summon_combo.strip()

        # Register hide toggle hotkey
        if self.hide_hotkey:
            try:
                keyboard.add_hotkey(self.hide_hotkey, self.on_hide_toggle)
            except Exception as e:
                print(f"Failed to register hide hotkey '{self.hide_hotkey}': {e}")

        # Register summon to cursor hotkey
        if self.summon_hotkey:
            try:
                keyboard.add_hotkey(self.summon_hotkey, self.on_summon)
            except Exception as e:
                print(f"Failed to register summon hotkey '{self.summon_hotkey}': {e}")

    def cleanup(self):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass