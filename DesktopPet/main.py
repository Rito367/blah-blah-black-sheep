"""
main.py
Entry point for Desktop Pet with Full Project Auto-Backup, Custom Dialogue,
Character Renaming, Auto-Creation, Rollback, Leash, Hotkeys, Menu UI Scaling,
Pet & UI Opacity Sliders, Decision Maker, and Custom Menu Color Support.
"""

import random
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from typing import Any

import paths

import data_store
import themes
import project_backup
import git_sync
import sound_manager
from tray_manager         import TrayManager
from decision_window      import DecisionWindow
from pet                  import PetWindow
from timer_window         import TimerWindow
from reminder_window      import ReminderWindow
from calendar_window      import CalendarWindow
from settings_window      import SettingsWindow
from speech_bubble        import SpeechBubble
from tictactoe_window     import TicTacToeWindow
from chopsticks_window    import ChopsticksWindow
from hotkey_manager       import HotkeyManager
from leash_overlay        import LeashOverlay
from sprite_cutter_window import SpriteCutterWindow
from rename_char_window   import RenameCharacterWindow
from dialogue_window      import DialogueWindow
from weather_window       import WeatherWindow
from startup_apps_window  import StartupAppsWindow, launch_target
from password_dialog      import PasswordUnlockDialog, PasswordManagerWindow
from npc_walker           import NPCWalkerWindow
from npc_leash            import NPCLeashOverlay
from npc_customizer_window import NPCCustomizerWindow
from bomb                 import BombManager

ASSETS_DIR = Path(__file__).parent / "assets"
ANIM_NAMES = {"idle", "walk", "jump", "sleep", "eat"}


def discover_characters() -> list[tuple[str, Path]]:
    chars = []
    if not ASSETS_DIR.exists():
        return [("cat", ASSETS_DIR / "pet")]

    for sub in sorted(ASSETS_DIR.iterdir()):
        if not sub.is_dir():
            continue
        anim_dirs = [d for d in sub.iterdir() if d.is_dir() and d.name in ANIM_NAMES]
        if not anim_dirs:
            continue
        display = "Cat" if sub.name == "pet" else sub.name.replace("_", " ").title()
        chars.append((display, sub))

    if not chars:
        chars.append(("Cat", ASSETS_DIR / "pet"))
    return chars


class App:
    def __init__(self):
        project_backup.create_full_project_backup()

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self._menu: tk.Menu | None = None

        self._data = data_store.load()
        themes.set_theme(self._data.get("theme", "pink"))
        themes.set_custom_menu_colors(self._data.get("custom_menu_colors", {}))
        themes.set_custom_theme_data(self._data.get("custom_theme", {}))

        self._characters = discover_characters()
        saved_char = self._data.get("character", "pet")
        self._active_char_dir = self._resolve_char_dir(saved_char)

        self.bubble = SpeechBubble(self.root, on_click=self._on_bubble_clicked)

        self.pet = PetWindow(
            self.root,
            on_double_click = self._on_double_click,
            on_bubble       = self._on_bubble,
            character_dir   = self._active_char_dir,
            scale           = self._data.get("scale", 1.0),
            gravity         = self._data.get("gravity", 1.2),
            bounciness      = self._data.get("bounciness", 0.6),
            chatter_chance  = self._data.get("chatter_chance", 0.20),
            get_data        = self._get_data,
        )

        # Apply saved pet opacity
        saved_pet_opacity = self._data.get("pet_opacity", self._data.get("opacity", 1.0))
        if hasattr(self.pet, "win") and self.pet.win.winfo_exists():
            self.pet.win.attributes("-alpha", saved_pet_opacity)

        self.timer_win = TimerWindow(
            self.root,
            get_data  = self._get_data,
            save_data = self._save_data,
            on_alarm  = self._on_alarm,
            on_menu   = self._show_main_menu,
        )

        self.reminder_win = ReminderWindow(
            self.root,
            get_data   = self._get_data,
            save_data  = self._save_data,
            on_trigger = self._on_bubble,
            on_menu    = self._show_main_menu,
        )

        self.cal_win = CalendarWindow(
            self.root,
            get_data  = self._get_data,
            save_data = self._save_data,
            on_menu   = self._show_main_menu,
        )

        self.password_unlock = PasswordUnlockDialog(
            self.root,
            get_data  = self._get_data,
            save_data = self._save_data,
        )
        self.password_manager = PasswordManagerWindow(
            self.root,
            get_data   = self._get_data,
            save_data  = self._save_data,
            on_updated = self._on_password_settings_updated,
        )

        self.settings_win = SettingsWindow(
            self.root,
            get_data  = self._get_data,
            save_data = self._save_data,
            on_apply  = self._on_settings_applied,
            on_menu   = self._show_main_menu,
            on_password_manager = self._open_password_settings,
        )

        self.cutter_win = SpriteCutterWindow(
            self.root,
            on_complete = self._on_sprites_cut
        )

        self.dialogue_win = DialogueWindow(
            self.root,
            get_data  = self._get_data,
            save_data = self._save_data,
            on_menu   = self._show_main_menu,
        )

        self.weather_win = WeatherWindow(
            self.root,
            get_data  = self._get_data,
            save_data = self._save_data,
            on_bubble = self._show_bubble,
            on_menu   = self._show_main_menu,
        )

        self.ttt_game = TicTacToeWindow(
            self.root,
            get_data     = self._get_data,
            save_data    = self._save_data,
            on_game_over = self._on_ttt_over,
            on_menu      = self._show_main_menu,
        )

        self.chopsticks_game = ChopsticksWindow(
            self.root,
            on_game_over = self._on_chopsticks_over,
            on_menu      = self._show_main_menu,
        )

        self.decision_win = DecisionWindow(
            self.root,
            get_data    = self._get_data,
            save_data   = self._save_data,
            on_decision = self._on_bubble,
            on_menu     = self._show_main_menu,
        )

        self.startup_apps_win = StartupAppsWindow(
            self.root,
            get_data       = self._get_data,
            save_data      = self._save_data,
            on_launch_apps = self._on_startup_apps_launched,
            on_menu        = self._show_main_menu,
            on_whip        = self._toggle_whip,
        )

        self.leash = LeashOverlay(
            self.root,
            on_hit=self._on_whip_hit,
            on_close=self._on_whip_closed,
            is_muted_fn=lambda: getattr(self.tray, "is_muted", False) if hasattr(self, "tray") else False,
            get_pet_rect_fn=lambda: (*self.pet.get_position(), *self.pet.get_current_size()),
        )

        self.npc_customizer = NPCCustomizerWindow(
            self.root,
            get_data_fn=self._get_data,
            save_data_fn=self._save_data,
            on_save_and_start=self._on_npc_save_and_start,
        )

        self.npc_walker = NPCWalkerWindow(
            self.root,
            get_data_fn=self._get_data,
            save_data_fn=self._save_data,
            on_bubble=self._show_bubble,
            on_open_customizer=self._open_npc_customizer,
            on_dismiss=self._on_npc_dismissed,
        )

        self.npc_leash = NPCLeashOverlay(
            self.root,
            get_hand_fn=lambda: self.npc_walker.get_hand_screen_position(),
            get_collar_fn=lambda: self.pet.get_collar_position(),
            pull_pet_fn=lambda sx, sy, fr: self.pet.leash_pull(sx, sy, fr),
            get_config_fn=lambda: self._data.get("npc_walker", {}),
            on_pull_dialogue_fn=self._on_leash_pull_dialogue,
        )

        self.bomb_manager = BombManager(
            self.root,
            on_explode=self._on_bomb_explode,
            get_fuse_fn=lambda: self._data.get("bomb_fuse_time", 3.0),
            set_fuse_fn=self._set_bomb_fuse,
            get_power_fn=lambda: self._data.get("bomb_blast_power", 35.0),
            set_power_fn=self._set_bomb_blast_power,
        )

        self.hotkeys = HotkeyManager(
            on_hide_toggle = lambda: self.root.after(0, self.pet.toggle_hide),
            on_summon      = lambda: self.root.after(0, self.pet.summon_to_cursor)
        )
        self.hotkeys.apply_hotkeys(
            self._data.get("hide_hotkey", "alt+x"),
            self._data.get("summon_hotkey", "alt+z")
        )

        self.tray = TrayManager(self)
        self.tray.start()

        saved_speed = self._data.get("walk_speed", 2)
        self.pet.set_speed(saved_speed)

        px, py = self._data.get("pet_position", [100, 600])
        self.pet.set_position(px, py)

        self._build_context_menu()
        self.pet.canvas.bind("<Button-3>", self._show_context_menu)

        self._save_position_loop()

        # Deferred auto-launch of configured startup apps on PC/Pet boot
        self.root.after(2500, self._check_autostart_apps)

        if self._data.get("npc_walker", {}).get("enabled", False):
            self.root.after(1000, self._enable_npc_walker)

        if self._data.get("weather_startup_alert", True):
            self.root.after(3500, self.weather_win.say_weather_in_bubble)

    def _resolve_char_dir(self, folder_name: str) -> Path:
        for _, path in self._characters:
            if path.name == folder_name:
                return path
        return self._characters[0][1]

    def _get_data(self) -> dict[str, Any]:
        return self._data

    def _save_data(self, data: dict[str, Any]):
        self._data = data
        data_store.save(data)

    def _show_main_menu(self, close_win=None, hide_fn=None):
        """Close/hide the calling window then open the main context menu at the cursor with password check."""
        if hide_fn is not None:
            try:
                hide_fn()
            except Exception:
                pass
        elif close_win is not None:
            try:
                if close_win.winfo_exists():
                    close_win.withdraw()
            except Exception:
                pass

        px = self.root.winfo_pointerx()
        py = self.root.winfo_pointery()
        self._request_menu_access(
            lambda: self._display_context_menu(px, py),
            near_x=px,
            near_y=py
        )

    def set_all_ui_opacity(self, alpha: float):
        windows = [
            getattr(self.settings_win, "win", None),
            getattr(self.reminder_win, "win", None),
            getattr(self.timer_win, "win", None),
            getattr(self.cal_win, "win", None),
            getattr(self.cutter_win, "win", None),
            getattr(self.dialogue_win, "win", None),
            getattr(self.ttt_game, "win", None),
            getattr(self.chopsticks_game, "win", None),
            getattr(self.decision_win, "win", None),
            getattr(self.weather_win, "win", None),
            getattr(self.startup_apps_win, "win", None),
        ]
        for w in windows:
            if w is not None and w.winfo_exists():
                w.attributes("-alpha", alpha)

    def _open_window_with_opacity(self, window_obj):
        pos = self.pet.get_position()
        if hasattr(window_obj, "toggle"):
            window_obj.toggle(*pos)
        elif hasattr(window_obj, "show"):
            window_obj.show(*pos)

        ui_alpha = self._data.get("ui_opacity", 1.0)
        win = getattr(window_obj, "win", None)
        if win and win.winfo_exists():
            win.attributes("-alpha", ui_alpha)

    def _on_settings_applied(self, **kwargs):
        if "scale" in kwargs:
            self._data["scale"] = kwargs["scale"]
            self.pet.set_scale(kwargs["scale"])
        if "menu_scale" in kwargs:
            self._data["menu_scale"] = kwargs["menu_scale"]
        if "pet_opacity" in kwargs:
            self._data["pet_opacity"] = kwargs["pet_opacity"]
            if hasattr(self.pet, "win") and self.pet.win.winfo_exists():
                self.pet.win.attributes("-alpha", kwargs["pet_opacity"])
        if "ui_opacity" in kwargs:
            self._data["ui_opacity"] = kwargs["ui_opacity"]
            self.set_all_ui_opacity(kwargs["ui_opacity"])
        if "custom_menu_colors" in kwargs:
            self._data["custom_menu_colors"] = kwargs["custom_menu_colors"]
            themes.set_custom_menu_colors(kwargs["custom_menu_colors"])
        if "custom_theme" in kwargs:
            self._data["custom_theme"] = kwargs["custom_theme"]
            themes.set_custom_theme_data(kwargs["custom_theme"])
        if "menu_scale" in kwargs or "custom_menu_colors" in kwargs:
            self._build_context_menu()
            self.pet.canvas.bind("<Button-3>", self._show_context_menu)
        if "walk_speed" in kwargs:
            self._data["walk_speed"] = kwargs["walk_speed"]
            self.pet.set_speed(kwargs["walk_speed"])
        if "gravity" in kwargs:
            self._data["gravity"] = kwargs["gravity"]
            self.pet.gravity = kwargs["gravity"]
        if "bounciness" in kwargs:
            self._data["bounciness"] = kwargs["bounciness"]
            self.pet.bounciness = kwargs["bounciness"]
        if "bomb_blast_power" in kwargs:
            self._data["bomb_blast_power"] = kwargs["bomb_blast_power"]
        if "chatter_chance" in kwargs:
            self._data["chatter_chance"] = kwargs["chatter_chance"]
            self.pet.chatter_chance = kwargs["chatter_chance"]
        if "theme" in kwargs:
            self._apply_theme(kwargs["theme"])
        if "hide_hotkey" in kwargs or "summon_hotkey" in kwargs:
            self.hotkeys.apply_hotkeys(
                self._data.get("hide_hotkey", "alt+x"),
                self._data.get("summon_hotkey", "alt+z")
            )

    def _on_sprites_cut(self, char_name: str, char_dir: Path, auto_equip: bool = True):
        self._characters = discover_characters()
        if auto_equip:
            self._apply_character(char_name, char_dir)
            self._show_bubble(f"🎉 Switched to {char_name.replace('_', ' ').title()}!")
        else:
            self._build_context_menu()
            self.pet.canvas.bind("<Button-3>", self._show_context_menu)
            self._show_bubble("✂️ New character ready in menu!")

    def _check_autostart_apps(self):
        if not self._data.get("autostart_apps_on_boot", True):
            return
        apps = self._data.get("startup_apps", [])
        launched = 0
        for app in apps:
            if app.get("enabled", True):
                if launch_target(app.get("path", "")):
                    launched += 1
        if launched > 0:
            self._show_bubble(f"🚀 Opened {launched} startup app(s)!")

    def _on_startup_apps_launched(self, count: int):
        self._show_bubble(f"🚀 Launched {count} app(s)!")

    def _open_rename_window(self):
        RenameCharacterWindow(
            self.root,
            current_char_dir=self._active_char_dir,
            on_renamed=self._on_character_renamed
        ).show(*self.pet.get_position())

    def _on_character_renamed(self, new_folder_name: str, new_path: Path):
        self._characters = discover_characters()
        self._apply_character(new_folder_name, new_path)
        self._show_bubble(f"✏️ Renamed to {new_folder_name.replace('_', ' ').title()}!")

    def _save_github(self):
        t = themes.get()
        last_name = self._data.get("last_github_save_name", "").strip()

        dialog = tk.Toplevel(self.root)
        dialog.title("Save to GitHub")
        dialog.attributes("-topmost", True)
        dialog.configure(bg=t.get("border", "#181920"), padx=2, pady=2)
        dialog.resizable(False, False)

        outer = tk.Frame(dialog, bg=t.get("bg_card", "#ffffff"), padx=12, pady=10)
        outer.pack(fill="both", expand=True)

        px, py = self.pet.get_position()
        h = 175 if last_name else 140
        dialog.geometry(f"340x{h}+{px}+{max(40, py - h)}")

        tk.Label(
            outer,
            text="💾 Name your GitHub save copy:",
            bg=t.get("bg_card", "#ffffff"),
            fg=t.get("fg_main", "#333333"),
            font=("Georgia", 9, "bold")
        ).pack(pady=(0, 4), anchor="w")

        default_name = last_name if last_name else f"Save - {datetime.now().strftime('%b %d, %H:%M')}"
        entry = tk.Entry(
            outer,
            font=("Segoe UI", 9),
            bg=t.get("bg_grid", "#f0f0f0"),
            fg=t.get("fg_main", "#000000"),
            insertbackground=t.get("fg_main", "#000000"),
            relief="solid",
            bd=1
        )
        entry.insert(0, default_name)
        entry.pack(fill="x", pady=4)
        entry.select_range(0, tk.END)
        entry.focus_set()

        # Show only the single latest save name if available
        if last_name:
            def _choose_last_name():
                entry.delete(0, tk.END)
                entry.insert(0, last_name)
                entry.focus_set()

            chip = tk.Frame(outer, bg=t.get("bg_grid", "#f0f0f0"), padx=6, pady=3, cursor="hand2")
            chip.pack(fill="x", pady=(2, 6))

            lbl_hint = tk.Label(
                chip,
                text=f"🕒 Last used: {last_name}  (Click to use)",
                bg=t.get("bg_grid", "#f0f0f0"),
                fg=t.get("accent", "#e74c3c"),
                font=("Segoe UI", 7, "bold"),
                anchor="w",
                cursor="hand2"
            )
            lbl_hint.pack(side="left", fill="x", expand=True)

            chip.bind("<Button-1>", lambda e: _choose_last_name())
            lbl_hint.bind("<Button-1>", lambda e: _choose_last_name())

        def _confirm(event=None):
            save_name = entry.get().strip()
            if not save_name:
                save_name = default_name

            # Remember only the latest save name
            self._data["last_github_save_name"] = save_name
            data_store.save(self._data)

            dialog.destroy()
            self._do_github_save(save_name)

        btn_row = tk.Frame(outer, bg=t.get("bg_card", "#ffffff"))
        btn_row.pack(fill="x", pady=(4, 0))

        tk.Button(
            btn_row,
            text="Cancel",
            font=("Georgia", 8, "bold"),
            bg=t.get("btn", "#cccccc"),
            fg=t.get("fg_white", "#ffffff"),
            relief="flat",
            command=dialog.destroy
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        tk.Button(
            btn_row,
            text="Save to GitHub",
            font=("Georgia", 8, "bold"),
            bg=t.get("accent", "#e74c3c"),
            fg=t.get("fg_white", "#ffffff"),
            relief="flat",
            command=_confirm
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

        dialog.bind("<Return>", _confirm)
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def _do_github_save(self, save_name: str):
        self._show_bubble(f"Saving '{save_name}'... ⏳")

        def _on_done(success: bool, msg: str):
            self.root.after(0, lambda: self._show_bubble(msg))

        git_sync.push_to_github_async(commit_msg=save_name, on_complete=_on_done)

    def _pull_github(self):
        self._show_bubble("Downloading from GitHub... ⏳")

        def _on_done(success: bool, msg: str):
            self.root.after(0, lambda: self._show_bubble(msg))
            if success:
                self.root.after(1200, self._restart)

        git_sync.pull_from_github_async(on_complete=_on_done)

    def _manual_backup(self):
        saved = project_backup.create_full_project_backup()
        self._show_bubble(f"💾 Backup saved!\n{saved.name}")

    def _manual_restore(self):
        success = project_backup.restore_previous_project_backup()
        if success:
            self._show_bubble("🔄 Restored! Restarting...")
            self.root.after(1000, self._restart)
        else:
            self._show_bubble("No backup snapshot found!")

    def _leash_loop(self):
        if self.leash.active and not getattr(self.pet, "_is_hidden", False):
            px, py = self.pet.get_position()
            pw, ph = self.pet.get_current_size()
            self.leash.update_pet_rect(px, py, pw, ph)
            self.root.after(60, self._leash_loop)
        else:
            self.root.after(300, self._leash_loop)

    def _on_double_click(self):
        self._show_game_menu()

    def _show_game_menu(self):
        px, py = self.pet.get_position()
        pw, ph = self.pet.get_current_size()
        self._request_menu_access(
            self._display_game_menu,
            near_x=px + pw // 2,
            near_y=py + ph // 2
        )

    def _display_game_menu(self):
        t = themes.get()
        menu_scale = self._data.get("menu_scale", 1.0)
        font_size = max(8, int(9 * menu_scale))

        bg_col = t.get("menu_bg") or t.get("bg_card") or "#ffffff"
        fg_col = t.get("menu_fg") or t.get("fg_main") or "#333333"
        act_bg = t.get("menu_active_bg") or t.get("btn") or "#f8bbd0"
        act_fg = t.get("menu_active_fg") or t.get("fg_white") or "#ffffff"

        game_menu = tk.Menu(
            self.root, tearoff=0,
            bg=bg_col,
            fg=fg_col,
            activebackground=act_bg,
            activeforeground=act_fg,
            font=("Segoe UI", font_size, "bold"), relief="flat", bd=0
        )
        game_menu.add_command(label="🥢 Chopsticks", command=self._start_chopsticks)
        game_menu.add_command(label="❌ Tic-Tac-Toe", command=self._start_ttt)
        game_menu.add_command(label="✊ Rock Paper Scissors", command=self._start_rps_game)
        game_menu.add_command(label="🎯 Decision Maker", command=lambda: self._open_window_with_opacity(self.decision_win))
        game_menu.add_command(label="💥 Whip", command=self._toggle_whip)
        game_menu.add_command(label="💣 Drop Bomb", command=self._spawn_bomb_at_cursor)

        self._show_bubble("Pick a tool or game! 🎮")

        try:
            game_menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            game_menu.grab_release()

    def _start_chopsticks(self):
        self._show_bubble("Chopsticks! 🥢\nLet's see who wins!")
        x, y = self.pet.get_position()
        pw = getattr(self.pet, "w", 60)
        self.chopsticks_game.show(near_x=x + pw + 10, near_y=y - 120)

    def _on_chopsticks_over(self, result: str):
        msg = "You beat me at Chopsticks! 🥢🎉" if result == "win" else "I won Chopsticks! 🥢😋"
        self._show_bubble(msg)

    def _start_ttt(self):
        self._show_bubble("Tic-Tac-Toe! Let's play! ❌⭕")
        x, y = self.pet.get_position()
        pw = getattr(self.pet, "w", 60)
        self.ttt_game.show(near_x=x + pw + 10, near_y=y - 100)

    def _on_ttt_over(self, result: str):
        if result == "win":
            msg = "You won Tic-Tac-Toe! 🎉\nNice moves!"
        elif result == "lose":
            msg = "I won Tic-Tac-Toe! 😋\nBetter luck next time!"
        else:
            msg = "Tic-Tac-Toe draw! 🤝\nWe are evenly matched!"
        self._show_bubble(msg)

    def _start_rps_game(self):
        self._show_bubble("Rock, Paper, Scissors!\nPick your move! 👇")

        t = themes.get()
        menu_scale = self._data.get("menu_scale", 1.0)
        font_size = max(8, int(9 * menu_scale))

        bg_col = t.get("menu_bg") or t.get("bg_card") or "#ffffff"
        fg_col = t.get("menu_fg") or t.get("fg_main") or "#333333"
        act_bg = t.get("menu_active_bg") or t.get("btn") or "#f8bbd0"
        act_fg = t.get("menu_active_fg") or t.get("fg_white") or "#ffffff"

        rps_menu = tk.Menu(
            self.root, tearoff=0,
            bg=bg_col,
            fg=fg_col,
            activebackground=act_bg,
            activeforeground=act_fg,
            font=("Segoe UI", font_size, "bold"), relief="flat", bd=0
        )
        rps_menu.add_command(label="✊ Rock", command=lambda: self._play_rps("Rock"))
        rps_menu.add_command(label="✋ Paper", command=lambda: self._play_rps("Paper"))
        rps_menu.add_command(label="✌️ Scissors", command=lambda: self._play_rps("Scissors"))

        try:
            rps_menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            rps_menu.grab_release()

    def _play_rps(self, user_choice: str):
        choices = ["Rock", "Paper", "Scissors"]
        emojis = {"Rock": "✊", "Paper": "✋", "Scissors": "✌️"}
        pet_choice = random.choice(choices)

        if user_choice == pet_choice:
            result = "It's a tie! 🤝"
        elif (
            (user_choice == "Rock" and pet_choice == "Scissors")
            or (user_choice == "Paper" and pet_choice == "Rock")
            or (user_choice == "Scissors" and pet_choice == "Paper")
        ):
            result = "You win! 🎉"
        else:
            result = "I win! 😋"

        msg = f"I chose {emojis[pet_choice]} {pet_choice}!\n{result}"
        self._show_bubble(msg)

    def _play_alert_sound(self):
        if hasattr(self, "tray") and not getattr(self.tray, "is_muted", False):
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

    def _on_bubble_clicked(self):
        """Brings the pet directly under the clicked speech bubble and plays a cheerful jump animation."""
        try:
            bx = self.bubble.win.winfo_x()
            bw = self.bubble.win.winfo_width()
            target_cx = bx + bw // 2
            self.pet.ensure_visible(force_x=target_cx)
            self.pet.is_jumping = True
            self.pet.set_anim("jump")
        except Exception:
            self.pet.ensure_visible()

    def _show_bubble(self, message: str, play_sound: bool = False):
        """Ensures the pet is unhidden, topmost, and on-screen before displaying a speech bubble."""
        self.pet.ensure_visible()
        x, y = self.pet.get_position()
        pw = getattr(self.pet, "w", 60)
        self.bubble.show(message=message, pet_x=x, pet_y=y, pet_w=pw)
        if play_sound:
            self._play_alert_sound()

    def _on_alarm(self, label: str):
        self._show_bubble(label, play_sound=True)

    def _on_bubble(self, message: str):
        self._show_bubble(message, play_sound=True)

    def _apply_character(self, folder_name: str, char_dir: Path):
        self._active_char_dir = char_dir
        self._data["character"] = folder_name
        data_store.save(self._data)
        self.pet.load_character(char_dir)
        self._build_context_menu()
        self.pet.canvas.bind("<Button-3>", self._show_context_menu)

    def _apply_theme(self, name: str):
        themes.set_theme(name)
        self._data["theme"] = name
        # Clear any per-colour overrides so the new theme colours show cleanly.
        # The user can re-customise individual colours via Settings afterwards.
        self._data["custom_menu_colors"] = {
            "menu_bg": "", "menu_fg": "", "menu_active_bg": "", "menu_active_fg": "",
            "bubble_bg": "", "bubble_out": "", "bubble_fg": "",
            "bubble_font_family": "", "bubble_font_size": "",
        }
        themes.set_custom_menu_colors({})
        data_store.save(self._data)
        self.timer_win.apply_theme()
        self.cal_win.apply_theme()
        self.weather_win.apply_theme()
        self._build_context_menu()
        self.pet.canvas.bind("<Button-3>", self._show_context_menu)

    def _toggle_whip(self):
        # Disengage any mouse-chase mode so the pet stays free
        if getattr(self.pet, "chase_mouse", False):
            self.pet.chase_mouse = False

        if self.leash.active:
            self.leash.disable()
        else:
            self.leash.enable()
        self._build_context_menu()
        self.pet.canvas.bind("<Button-3>", self._show_context_menu)

    def _on_whip_hit(self, crack_x: int, crack_y: int, origin_x: int | None = None, origin_y: int | None = None):
        self.pet.whip_hit(crack_x, crack_y, origin_x, origin_y)

    def _on_whip_closed(self):
        self._build_context_menu()
        self.pet.canvas.bind("<Button-3>", self._show_context_menu)

    def _on_bomb_explode(self, bomb_x: int, bomb_y: int, blast_power: float | None = None):
        sound_manager.play_explosion_sound()
        if blast_power is None:
            blast_power = float(self._data.get("bomb_blast_power", 35.0))
        self.pet.bomb_blast(bomb_x, bomb_y, blast_power=blast_power)
        sound_manager.play_pet_blast_sound()

    def _spawn_bomb_at_cursor(self):
        px = self.root.winfo_pointerx()
        py = self.root.winfo_pointery()
        self.bomb_manager.spawn_bomb(px, py)

    def _set_bomb_fuse(self, sec: float):
        sec = max(0.5, min(60.0, round(sec, 1)))
        self._data["bomb_fuse_time"] = sec
        self._save_data(self._data)
        self._build_context_menu()

    def _prompt_custom_bomb_fuse(self):
        from tkinter import simpledialog
        cur = self.bomb_manager.get_default_fuse()
        val = simpledialog.askfloat(
            "Custom Bomb Fuse Time",
            "Enter default fuse duration in seconds (0.5 to 60.0):",
            initialvalue=cur, minvalue=0.5, maxvalue=60.0, parent=self.root
        )
        if val is not None:
            self._set_bomb_fuse(val)

    def _set_bomb_blast_power(self, power: float):
        power = max(5.0, min(250.0, round(power, 1)))
        self._data["bomb_blast_power"] = power
        self._save_data(self._data)
        self._build_context_menu()

    def _prompt_custom_bomb_power(self):
        from tkinter import simpledialog
        cur = float(self._data.get("bomb_blast_power", 35.0))
        val = simpledialog.askfloat(
            "Custom Fling Force",
            "Enter default bomb fling force (5.0 to 250.0):\n(Gentle: 15, Normal: 35, Strong: 55, Extreme: 80+)",
            initialvalue=cur, minvalue=5.0, maxvalue=250.0, parent=self.root
        )
        if val is not None:
            self._set_bomb_blast_power(val)

    def _toggle_patrol(self):
        self.pet.toggle_continuous_patrol()
        self._build_context_menu()
        self.pet.canvas.bind("<Button-3>", self._show_context_menu)

    def _toggle_npc_walker(self):
        if getattr(self, "npc_walker", None) and self.npc_walker.active:
            self.npc_walker.disable()
            self.npc_leash.disable()
            self._data.setdefault("npc_walker", {})["enabled"] = False
            self._save_data(self._data)
            self._show_bubble("Owner took a break! 🐾")
        else:
            self._enable_npc_walker()
        self._build_context_menu()
        self.pet.canvas.bind("<Button-3>", self._show_context_menu)

    def _enable_npc_walker(self):
        px, py = self.pet.get_position()
        self.npc_walker.enable(start_x=px - 140, start_y=py - 20)
        self.npc_leash.enable()
        self._data.setdefault("npc_walker", {})["enabled"] = True
        self._save_data(self._data)
        self._show_bubble("Walkies time! 🐕 Leashed up!")

    def _open_npc_customizer(self):
        px, py = self.pet.get_position()
        self.npc_customizer.show(near_x=px, near_y=py)

    def _on_npc_save_and_start(self):
        try:
            self._enable_npc_walker()
            self._build_context_menu()
        except Exception as e:
            print(f"[ERROR] Failed to start NPC walker: {e}", file=sys.stderr)
            self._show_bubble("Couldn't start Dog Walker!")

    def _on_npc_dismissed(self):
        if getattr(self, "npc_leash", None):
            self.npc_leash.disable()
        self._data.setdefault("npc_walker", {})["enabled"] = False
        self._save_data(self._data)
        self._build_context_menu()

    def _on_leash_pull_dialogue(self):
        # Trigger pet complaint or owner urge
        if random.random() < 0.6:
            complaints = self._data.get("pet_leash_pull_messages", ["Slow down! My paws hurt! 😫"])
            if complaints:
                self._show_bubble(random.choice(complaints))
        else:
            urges = self._data.get("npc_pull_messages", ["Keep up, buddy!"])
            if urges and getattr(self, "npc_walker", None) and self.npc_walker.active:
                self.npc_walker.say(random.choice(urges))

    def _rollback_version(self):
        prev_data = data_store.rollback_previous_version()
        if prev_data:
            self._data = prev_data
            # Only pass keys that _on_settings_applied actually handles
            applicable_keys = {
                "scale", "menu_scale", "pet_opacity", "ui_opacity",
                "custom_menu_colors", "custom_theme", "walk_speed",
                "gravity", "bounciness", "chatter_chance", "theme",
                "hide_hotkey", "summon_hotkey", "bomb_blast_power",
            }
            filtered = {k: v for k, v in prev_data.items() if k in applicable_keys}
            self._on_settings_applied(**filtered)
            saved_char = self._data.get("character", "pet")
            self._active_char_dir = self._resolve_char_dir(saved_char)
            self.pet.load_character(self._active_char_dir)
            self._build_context_menu()
            self.pet.canvas.bind("<Button-3>", self._show_context_menu)

            self._show_bubble("⏪ Reverted settings to previous backup!")
        else:
            self._show_bubble("No previous backups found!")

    def _build_context_menu(self):
        t = themes.get()
        menu_scale = self._data.get("menu_scale", 1.0)
        font_size = max(8, int(9 * menu_scale))

        bg_col = t.get("menu_bg") or t.get("bg_card") or "#ffffff"
        fg_col = t.get("menu_fg") or t.get("fg_main") or "#333333"
        act_bg = t.get("menu_active_bg") or t.get("btn") or "#f8bbd0"
        act_fg = t.get("menu_active_fg") or t.get("fg_white") or "#ffffff"

        menu_kw: dict[str, Any] = {
            "tearoff": 0,
            "bg": bg_col,
            "fg": fg_col,
            "activebackground": act_bg,
            "activeforeground": act_fg,
            "font": ("Segoe UI", font_size),
            "relief": "flat",
            "bd": 0,
        }

        self._menu = tk.Menu(self.root, **menu_kw)

        # Pet Actions
        self._menu.add_command(label="🍖  Feed", command=lambda: self.pet.feed())
        self._menu.add_command(label="🔄  Turn Around", command=lambda: self.pet.flip_direction())
        whip_label = "💥  Whip Mode  ✓" if self.leash.active else "💥  Whip Mode"
        self._menu.add_command(
            label=whip_label,
            command=self._toggle_whip
        )

        mode_menu = tk.Menu(self._menu, **menu_kw)
        patrol_active = getattr(self.pet, "continuous_patrol", False)
        patrol_label = "Auto Patrol  ✓" if patrol_active else "Auto Patrol"
        mode_menu.add_command(
            label=patrol_label,
            command=self._toggle_patrol
        )
        self._menu.add_cascade(label="🐾  Pet Modes", menu=mode_menu)

        # Dog Walker NPC
        walker_menu = tk.Menu(self._menu, **menu_kw)
        npc_active = getattr(self, "npc_walker", None) and self.npc_walker.active
        walker_toggle_lbl = "Walk with Owner  ✓" if npc_active else "Walk with Owner"
        walker_menu.add_command(label=walker_toggle_lbl, command=self._toggle_npc_walker)
        walker_menu.add_command(label="🎨  Customize Wardrobe & Appearance", command=self._open_npc_customizer)
        if npc_active:
            walker_menu.add_command(label="📍  Set Destination (Click Screen)", command=self.npc_walker.start_click_destination_mode)
            patrol_npc_lbl = "🚶  Auto Patrol  ✓" if self.npc_walker.patrol_active else "🚶  Auto Patrol"
            walker_menu.add_command(label=patrol_npc_lbl, command=self.npc_walker.toggle_patrol)
            follow_npc_lbl = "🖱️  Follow Cursor  ✓" if self.npc_walker.follow_cursor else "🖱️  Follow Cursor"
            walker_menu.add_command(label=follow_npc_lbl, command=self.npc_walker.toggle_follow_cursor)
        self._menu.add_cascade(label="🐕  Dog Walker NPC", menu=walker_menu)
        self._menu.add_separator()

        # Minigames & Decision Tools
        games_menu = tk.Menu(self._menu, **menu_kw)
        games_menu.add_command(label="🥢  Chopsticks", command=self._start_chopsticks)
        games_menu.add_command(label="🎲  Tic-Tac-Toe", command=self._start_ttt)
        games_menu.add_command(label="✊  Rock Paper Scissors", command=self._start_rps_game)
        games_menu.add_command(label="🎯  Decision Maker", command=lambda: self._open_window_with_opacity(self.decision_win))
        self._menu.add_cascade(label="🎮  Minigames & Tools", menu=games_menu)

        # Bomb Tool
        bomb_menu = tk.Menu(self._menu, **menu_kw)
        bomb_menu.add_command(label="💣  Drop Bomb Here", command=self._spawn_bomb_at_cursor)

        fuse_sub = tk.Menu(bomb_menu, **menu_kw)
        cur_fuse = round(float(self._data.get("bomb_fuse_time", 3.0)), 1)
        for preset in [1.0, 2.0, 3.0, 5.0, 10.0]:
            lbl = f"{preset}s{'  ✓' if cur_fuse == preset else ''}"
            fuse_sub.add_command(label=lbl, command=lambda s=preset: self._set_bomb_fuse(s))
        fuse_sub.add_separator()
        fuse_sub.add_command(label="✏️  Custom Fuse...", command=self._prompt_custom_bomb_fuse)
        bomb_menu.add_cascade(label=f"⏱️  Default Fuse ({cur_fuse}s)", menu=fuse_sub)

        force_sub = tk.Menu(bomb_menu, **menu_kw)
        cur_power = round(float(self._data.get("bomb_blast_power", 35.0)), 1)
        presets = [
            ("Gentle", 15.0),
            ("Normal", 35.0),
            ("Strong", 55.0),
            ("Extreme / YEET", 80.0),
            ("Orbital Rocket", 120.0),
        ]
        for name, p in presets:
            lbl = f"{name} ({int(p)}){'  ✓' if cur_power == p else ''}"
            force_sub.add_command(label=lbl, command=lambda val=p: self._set_bomb_blast_power(val))
        force_sub.add_separator()
        force_sub.add_command(label="✏️  Custom Force...", command=self._prompt_custom_bomb_power)
        bomb_menu.add_cascade(label=f"🚀  Fling Force ({int(cur_power)})", menu=force_sub)

        active_bombs = len(self.bomb_manager.bombs)
        if active_bombs > 0:
            bomb_menu.add_separator()
            bomb_menu.add_command(label=f"💥  Detonate All ({active_bombs})", command=self.bomb_manager.detonate_all)
            bomb_menu.add_command(label=f"🧯  Defuse All ({active_bombs})", command=self.bomb_manager.defuse_all)

        self._menu.add_cascade(label="💣  Bomb Tool", menu=bomb_menu)

        self._menu.add_command(label="📅  Calendar", command=lambda: self._open_window_with_opacity(self.cal_win))

        weather_time_menu = tk.Menu(self._menu, **menu_kw)
        weather_time_menu.add_command(label="🌤️  Live Weather & Clock", command=lambda: self.weather_win.show_tab("weather", *self.pet.get_position()))
        weather_time_menu.add_command(label="🌐  World Clocks & Weather", command=lambda: self.weather_win.show_tab("world_clock", *self.pet.get_position()))
        weather_time_menu.add_separator()
        weather_time_menu.add_command(label="💬  Say Weather & Time", command=self.weather_win.say_weather_in_bubble)
        self._menu.add_cascade(label="🌤️  Weather & World Time", menu=weather_time_menu)

        self._menu.add_command(label="🔔  Reminders", command=lambda: self._open_window_with_opacity(self.reminder_win))
        self._menu.add_command(label="⏰  Countdown", command=lambda: self._open_window_with_opacity(self.timer_win))
        self._menu.add_command(label="🚀  Auto-Start & Apps", command=lambda: self._open_window_with_opacity(self.startup_apps_win))
        self._menu.add_separator()

        # Character & Customization
        char_menu = tk.Menu(self._menu, **menu_kw)
        active_name = self._active_char_dir.name
        for display, path in self._characters:
            is_active = (path.name == active_name)
            char_menu.add_command(
                label=f"{display}{'  ✓' if is_active else ''}",
                command=lambda p=path: self._apply_character(p.name, p),
            )
        char_menu.add_separator()
        char_menu.add_command(label="📝  Rename Pet", command=self._open_rename_window)
        char_menu.add_command(label="✨  Create New Character", command=lambda: self.cutter_win.show(*self.pet.get_position()))
        self._menu.add_cascade(label="👤  Character", menu=char_menu)

        theme_menu = tk.Menu(self._menu, **menu_kw)
        current_theme = themes.current_name()
        for tname in themes.THEME_ORDER:
            is_theme = (tname == current_theme)
            theme_menu.add_command(
                label=f"{themes.THEME_LABELS[tname]}{'  ✓' if is_theme else ''}",
                command=lambda n=tname: self._apply_theme(n),
            )
        self._menu.add_cascade(label="🎨  Theme", menu=theme_menu)
        self._menu.add_command(label="💬  Edit Dialogue", command=lambda: self.dialogue_win.show(*self.pet.get_position()))
        self._menu.add_separator()

        # System & Backup
        self._menu.add_command(label="⚙  Settings", command=lambda: self.settings_win.show(*self.pet.get_position()))
        self._menu.add_command(label="🔐  Menu Password", command=self._open_password_settings)

        backup_menu = tk.Menu(self._menu, **menu_kw)
        backup_menu.add_command(label="💾  Save to GitHub", command=self._save_github)
        backup_menu.add_command(label="📥  Update from GitHub", command=self._pull_github)
        backup_menu.add_command(label="📁  Backup Project", command=self._manual_backup)
        backup_menu.add_command(label="🔄  Restore Project", command=self._manual_restore)
        backup_menu.add_command(label="⏪  Rollback Settings", command=self._rollback_version)
        self._menu.add_cascade(label="📦  Backup & Restore", menu=backup_menu)
        self._menu.add_separator()

        self._menu.add_command(label="🔄  Restart", command=self._restart)
        self._menu.add_command(label="❌  Quit", command=self._quit)

    def _show_context_menu(self, event: Any) -> None:
        self._request_menu_access(
            lambda: self._display_context_menu(event.x_root, event.y_root),
            near_x=event.x_root,
            near_y=event.y_root
        )

    def _display_context_menu(self, x: int, y: int) -> None:
        self._build_context_menu()
        if self._menu is not None:
            try:
                self._menu.tk_popup(x, y)
            finally:
                self._menu.grab_release()

    def _request_menu_access(self, on_granted: Any, near_x: int | None = None, near_y: int | None = None) -> None:
        is_enabled = bool(self._data.get("menu_password_enabled", True))
        password = str(self._data.get("menu_password", "")).strip()

        if near_x is None:
            near_x = self.root.winfo_pointerx()
        if near_y is None:
            near_y = self.root.winfo_pointery()

        # If security disabled, grant access directly
        if not is_enabled:
            on_granted()
            return

        # If enabled but no password has been chosen yet, open setup dialog
        if not password:
            self._bubble_say("🔒 Set a password to protect your pet's menus!")

            def _after_first_set() -> None:
                if str(self._data.get("menu_password", "")).strip():
                    on_granted()

            def _on_first_pw_update() -> None:
                self._build_context_menu()
                _after_first_set()

            self.password_manager.on_updated = _on_first_pw_update
            self.password_manager.show(near_x=near_x, near_y=near_y)
            return

        # Password required: show unlock popup
        def _on_fail() -> None:
            phrases = [
                "Hey! Wrong password! 🤨",
                "Access Denied! 🚫",
                "Nope, that's not it! 🔒",
                "Who are you trying to hack? 😼",
                "Password required! 🙅‍♂️"
            ]
            self._bubble_say(random.choice(phrases))

        self.password_unlock.show(
            near_x=near_x,
            near_y=near_y,
            on_success=on_granted,
            on_fail=_on_fail
        )

    def _bubble_say(self, msg: str) -> None:
        self._show_bubble(msg, play_sound=False)

    def _open_password_settings(self) -> None:
        px, py = self.pet.get_position()
        self.password_manager.show(near_x=px, near_y=py)

    def _on_password_settings_updated(self) -> None:
        self._build_context_menu()
        self.pet.canvas.bind("<Button-3>", self._show_context_menu)
        if hasattr(self, "settings_win") and hasattr(self.settings_win, "update_password_status_ui"):
            self.settings_win.update_password_status_ui()

    def _save_position_loop(self):
        x, y = self.pet.get_position()
        old_pos = self._data.get("pet_position", [None, None])
        if [x, y] != old_pos:
            self._data["pet_position"] = [x, y]
            data_store.save(self._data)
        self.root.after(60_000, self._save_position_loop)

    def _restart(self):
        self.tray.stop()
        self.hotkeys.cleanup()
        if hasattr(self, "bomb_manager"):
            self.bomb_manager.cleanup()
        sound_manager.stop_all()
        x, y = self.pet.get_position()
        self._data["pet_position"] = [x, y]
        data_store.save(self._data)

        script_path = str(Path(__file__).resolve())
        executable = sys.executable
        kwargs = {}
        if sys.platform == "win32":
            pythonw = Path(executable).parent / "pythonw.exe"
            if pythonw.exists():
                executable = str(pythonw)
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        subprocess.Popen([executable, script_path], **kwargs)
        self.root.destroy()

    def _quit(self):
        self.tray.stop()
        self.hotkeys.cleanup()
        if hasattr(self, "bomb_manager"):
            self.bomb_manager.cleanup()
        sound_manager.stop_all()
        x, y = self.pet.get_position()
        self._data["pet_position"] = [x, y]
        data_store.save(self._data)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()