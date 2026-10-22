"""
hotkey_manager.py
Manages global system hotkeys for DesktopPet:
- Supports built-in pet interactions and windows
- Supports custom user keybinds to launch any application, file, web URL, shell command, or custom speech phrase
- Thread-safe execution dispatched directly onto the Tkinter event loop
"""

from __future__ import annotations

import os
import shlex
import subprocess
import threading
import webbrowser
from typing import Any, Callable

try:
    import keyboard  # type: ignore[import-untyped]
except ImportError:
    keyboard = None


class HotkeyManager:
    """Central engine for registering, managing, and triggering global keyboard shortcuts."""

    def __init__(self, on_hide_toggle: Callable[[], None] | None = None,
                 on_summon: Callable[[], None] | None = None,
                 on_speech: Callable[[str], None] | None = None):
        self.on_hide_toggle = on_hide_toggle
        self.on_summon = on_summon
        self.on_speech = on_speech
        self.hide_hotkey = ""
        self.summon_hotkey = ""

        # Registered built-in actions: action_id -> {"name": str, "icon": str, "category": str, "callback": Callable}
        self._actions: dict[str, dict[str, Any]] = {}

        # Currently active custom keybinds list
        self._keybinds: list[dict[str, Any]] = []

        # Reference to Tkinter root for thread-safe UI dispatch
        self._tk_root: Any = None

        # Lock for hotkey unhook/hook operations
        self._lock = threading.Lock()

    # ── Action Registration ──────────────────────────────────────────────────
    def register_action(self, action_id: str, name: str, icon: str, category: str, callback: Callable[[], None]):
        """Registers a callable action that can be bound to any hotkey."""
        self._actions[action_id] = {
            "id": action_id,
            "name": name,
            "icon": icon,
            "category": category,
            "callback": callback,
        }

    def get_registered_actions(self) -> dict[str, dict[str, Any]]:
        """Returns all registered actions available for binding."""
        return dict(self._actions)

    # ── Legacy Compatibility ────────────────────────────────────────────────
    def apply_hotkeys(self, hide_combo: str, summon_combo: str, root: Any = None):
        """Backward-compatible method for hide and summon hotkeys."""
        if root is not None:
            self._tk_root = root
        self.hide_hotkey = (hide_combo or "").strip()
        self.summon_hotkey = (summon_combo or "").strip()

        # Update or add into _keybinds list
        existing_map = {kb.get("target"): kb for kb in self._keybinds if kb.get("type") == "builtin"}
        if "toggle_hide" in existing_map:
            existing_map["toggle_hide"]["key"] = self.hide_hotkey
        elif self.hide_hotkey:
            self._keybinds.append({
                "id": "kb_hide",
                "name": "Hide / Show Pet",
                "key": self.hide_hotkey,
                "enabled": True,
                "type": "builtin",
                "target": "toggle_hide",
            })

        if "summon" in existing_map:
            existing_map["summon"]["key"] = self.summon_hotkey
        elif self.summon_hotkey:
            self._keybinds.append({
                "id": "kb_summon",
                "name": "Summon Pet to Cursor",
                "key": self.summon_hotkey,
                "enabled": True,
                "type": "builtin",
                "target": "summon",
            })

        self._rebind_all()

    # ── Custom Keybinds Management ──────────────────────────────────────────
    def apply_keybinds(self, keybinds: list[dict[str, Any]], root: Any = None):
        """
        Applies a list of keybind configuration dictionaries and hooks them globally.
        Each item is expected to have:
            - id: unique string
            - name: display name
            - key: hotkey combination (e.g. 'ctrl+alt+z', 'f9', 'alt+w')
            - enabled: bool
            - type: 'builtin' | 'app' | 'url' | 'speech' | 'cmd'
            - target: action_id, file path, URL, speech text, or shell command
        """
        if root is not None:
            self._tk_root = root

        self._keybinds = [dict(kb) for kb in keybinds if isinstance(kb, dict)]
        self._rebind_all()

    def _rebind_all(self):
        """Unhooks all existing global hotkeys and re-registers enabled ones."""
        if keyboard is None:
            return

        with self._lock:
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass

            bound_combos: set[str] = set()
            for kb in self._keybinds:
                if not kb.get("enabled", True):
                    continue

                raw_key = kb.get("key", "")
                if not raw_key:
                    continue

                key_combo = self.normalize_key_combo(raw_key)
                if not key_combo or key_combo in bound_combos:
                    continue
                bound_combos.add(key_combo)

                try:
                    # Capture kb in closure
                    keyboard.add_hotkey(
                        key_combo,
                        lambda item=kb: self._handle_hotkey_press(item),
                        suppress=False
                    )
                except Exception as e:
                    print(f"[HotkeyManager] Failed to bind '{key_combo}' for '{kb.get('name')}': {e}")

    @staticmethod
    def normalize_key_combo(combo_str: str) -> str:
        """Cleans and standardizes hotkey strings like 'Ctrl + Alt + P' -> 'ctrl+alt+p'."""
        if not combo_str:
            return ""
        parts = [p.strip().lower() for p in combo_str.replace(" ", "").split("+") if p.strip()]
        return "+".join(parts)

    def _handle_hotkey_press(self, keybind: dict[str, Any]):
        """Called by keyboard background hook thread; dispatches safely to Tkinter event loop."""
        if self._tk_root:
            try:
                self._tk_root.after(0, lambda: self.execute_keybind(keybind))
                return
            except Exception:
                pass
        # Fallback direct execution if no tk_root
        self.execute_keybind(keybind)

    def execute_keybind(self, keybind: dict[str, Any]):
        """Executes the action associated with the given keybind dictionary."""
        ktype = keybind.get("type", "builtin")
        target = keybind.get("target", "")

        try:
            if ktype == "builtin":
                if target in self._actions:
                    cb = self._actions[target].get("callback")
                    if cb:
                        cb()
                elif target == "toggle_hide" and self.on_hide_toggle:
                    self.on_hide_toggle()
                elif target == "summon" and self.on_summon:
                    self.on_summon()

            elif ktype == "app":
                if target:
                    # Expand environment variables like %LocalAppData% or ~
                    expanded = os.path.expandvars(os.path.expanduser(str(target)))
                    if os.name == "nt":
                        try:
                            os.startfile(expanded)
                        except Exception:
                            subprocess.Popen(expanded, shell=True)
                    else:
                        subprocess.Popen(shlex.split(expanded))

            elif ktype == "url":
                if target:
                    url = target.strip()
                    if not (url.startswith("http://") or url.startswith("https://") or "://" in url):
                        url = "https://" + url
                    webbrowser.open(url)

            elif ktype == "speech":
                if target and self.on_speech:
                    self.on_speech(str(target))

            elif ktype == "cmd":
                if target:
                    subprocess.Popen(str(target), shell=True)

        except Exception as e:
            print(f"[HotkeyManager] Execution failed for keybind '{keybind.get('name', target)}': {e}")

    # ── Key Recording Helper ────────────────────────────────────────────────
    @staticmethod
    def record_hotkey_async(on_success: Callable[[str], None], on_error: Callable[[str], None] | None = None):
        """
        Listens for the next key combination pressed by the user in a background thread.
        Calls on_success(combo_string) on capture.
        """
        if keyboard is None:
            if on_error:
                on_error("Keyboard library is not available.")
            return

        def _worker():
            if keyboard is None:
                return
            try:
                combo = keyboard.read_hotkey(suppress=False)
                if combo:
                    on_success(combo.lower())
            except Exception as e:
                if on_error:
                    on_error(str(e))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def cleanup(self):
        """Unhooks all global hotkeys."""
        if keyboard is not None:
            with self._lock:
                try:
                    keyboard.unhook_all_hotkeys()
                except Exception:
                    pass