"""
data_store.py
Persists settings locally to pet_data.json with rolling local backups.
"""

import os
import json
import shutil
import time
from pathlib import Path

from datetime import datetime

DATA_FILE = Path(__file__).parent / "pet_data.json"
BACKUP_DIR = Path(__file__).parent / ".backups"

_defaults = {
    "custom_theme": {},
    "world_clock_cities": ["Singapore", "London", "New York", "Tokyo", "Sydney"],
    "countdown_events": [],
    "calendar_bookmarks": {},
    "last_github_save_name": "",
    "active_event_index": 0,
    "pet_position": [100, 600],
    "menu_scale": 1.0,
    "theme": "pink",
    "character": "pet",
    "walk_speed": 2,
    "scale": 1.0,
    "pet_opacity": 1.0,
    "ui_opacity": 1.0,
    "custom_menu_colors": {
        "menu_bg": "",
        "menu_fg": "",
        "menu_active_bg": "",
        "menu_active_fg": "",
        "bubble_bg": "",
        "bubble_out": "",
        "bubble_fg": "",
        "bubble_font_family": "",
        "bubble_font_size": "",
    },
    "coin_heads": "Yes / Go for it!",
    "coin_tails": "No / Take a break!",
    "d6_labels": [
        "1: Study / Code",
        "2: Workout / Stretch",
        "3: Read Book",
        "4: Play Game",
        "5: Tidy Room",
        "6: Free Choice"
    ],
    "d20_target_dc": 10,
    "d20_pass_text": "Success! Proceed with task.",
    "d20_fail_text": "Failed! Postpone or try alternate.",
    "custom_decisions": ["Chicken Rice", "Laksa", "Subway", "Ban Mian", "Western"],
    "gravity": 1.2,
    "bounciness": 0.6,
    "chatter_chance": 0.20,
    "hide_hotkey": "alt+x",
    "summon_hotkey": "alt+z",
    "countdown_mode": "workdays",
    "ttt_stats": {
        "wins": 0,
        "losses": 0,
        "draws": 0
    },
    "reminders": [
        {"time": "", "text": "Drink water! ♡",     "enabled": True},
        {"time": "", "text": "Stretch your legs!",  "enabled": True},
        {"time": "", "text": "Posture check!",      "enabled": True},
    ],
    "idle_messages": [
        "Keep going, you're learning.",
        "One step at a time.",
        "Progress over perfection.",
        "Learn, grow, improve.",
        "You've got this.",
        "Keep showing up.",
        "Small steps still count.",
        "Grow through the experience.",
        "Do your best, learn the rest.",
        "Every day is progress.",
        "Jiayou! 加油！",
        "Don't be stressed. ♡"
    ],
    "pat_messages": ["♡ ♡ ♡", "~(≧▽≦)/", "( ˘ ³˘)♥"],
    "sleep_messages": ["z z z . . .", "zzZZ 💤", "z z z ♡"],
    "eat_messages": ["Yummy~ ♡", "Yumz!", "Nom nom ♡", "So tasty~"],
    "complain_messages": [
        "I'm tired...",
        "Too much walking!",
        "My legs hurt!",
        "Can we stop?",
        "Slow down!"
    ],
    "whip_messages": [
        "OUCH! Why are you whipping me?! 😭",
        "OWWW! I'm working, I'm working! 🏃💨",
        "Mercy!! Please have mercy!! 🥺💔",
        "Hyaaaa! *runs for dear life* ⚡",
        "Call 911! Animal cruelty! 📢💀",
        "I'LL DO ANYTHING! JUST STOP! 😭🙌",
        "CRACK! That stings so bad! 🔥😿",
        "Faster! Faster! Sprinting now! 🏃‍♂️💨",
        "Aaaaargh! Not the whip! 😱"
    ],
    "autostart_pet_on_boot": True,
    "autostart_apps_on_boot": True,
    "startup_apps": [],
    "menu_password_enabled": True,
    "menu_password": "",
    "menu_password_hint": "",
    "whip_sound_durations": {},
    "bomb_fuse_time": 3.0,
    "bomb_blast_power": 35.0,
    "bomb_messages": [
        "BOOOOOOM?! 💥💀",
        "HOLY SHIT! WHAT WAS THAT?! 💣🔥",
        "I'M BLASTING OFF AGAINNNN! 🚀💫",
        "MY BUTT IS ON FIRE! 🚒💨",
        "WHO GAVE YOU A BOMB?! 😭💣",
        "AIRBORNE! ☁️🌪️",
        "MY EARS ARE RINGING! 🔔💥",
        "WHY DO YOU HAVE EXPLOSIVES?! 🙀💣"
    ],
    "weather_city": "auto",
    "weather_unit": "celsius",
    "weather_startup_alert": True
}


def load() -> dict:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in _defaults.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(_defaults)


def save(data: dict) -> None:
    if DATA_FILE.exists():
        BACKUP_DIR.mkdir(exist_ok=True)
        backups = sorted(BACKUP_DIR.glob("pet_data_*.json"))
        while len(backups) > 15:
            try:
                backups.pop(0).unlink()
            except OSError:
                break

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        try:
            shutil.copy(DATA_FILE, BACKUP_DIR / f"pet_data_{ts}.json")
        except Exception:
            pass

    # Atomic write pattern to avoid file corruption/truncation
    tmp_file = DATA_FILE.with_suffix(".tmp")
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, DATA_FILE)
    except Exception:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        if tmp_file.exists():
            try:
                tmp_file.unlink()
            except Exception:
                pass


def rollback_previous_version() -> dict | None:
    """Restores the latest snapshot backup."""
    if not BACKUP_DIR.exists():
        return None

    backups = sorted(BACKUP_DIR.glob("pet_data_*.json"))
    if not backups:
        return None

    latest_backup = backups.pop()
    try:
        with open(latest_backup, "r", encoding="utf-8") as f:
            restored_data = json.load(f)

        # Bug #21 fix: merge current defaults so new keys aren't missing after rollback
        for k, v in _defaults.items():
            restored_data.setdefault(k, v)

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(restored_data, f, indent=2, ensure_ascii=False)

        latest_backup.unlink()
        return restored_data
    except Exception as e:
        print(f"Rollback failed: {e}")
        return None