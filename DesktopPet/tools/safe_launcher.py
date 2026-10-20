"""
safe_launcher.py
Runs main.py in a protected environment.
If a crash occurs:
1. Keeps broken snapshots hidden in '.broken_backups/' so your root stays clean.
2. Downloads and restores clean working files from your GitHub repo.
3. Shows an error report popup.
"""

import os
import sys
import shutil
import runpy
import traceback
import urllib.request
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# ── GITHUB CONFIGURATION ──
GITHUB_USERNAME = "benong188-dot"
GITHUB_REPO = "desktop-pet-hais"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = os.environ.get("GITHUB_PAT", "")

# Hidden directory for crash copies (keeps root folder clean)
try:
    import paths
    PROJECT_DIR = paths.PROJECT_ROOT
except ImportError:
    PROJECT_DIR = Path(__file__).resolve().parent.parent
BROKEN_DIR = PROJECT_DIR / ".broken_backups"

TRACKED_FILES = [
    "main.py",
    "pet.py",
    "speech_bubble.py",
    "data_store.py",
    "themes.py",
    "git_sync.py",
    "project_backup.py",
    "hotkey_manager.py",
    "tray_manager.py",
    "leash_overlay.py",
    "timer_window.py",
    "reminder_window.py",
    "calendar_window.py",
    "settings_window.py",
    "decision_window.py",
    "dialogue_window.py",
    "weather_window.py",
    "rename_char_window.py",
    "tictactoe_window.py",
    "chopsticks_window.py",
    "sprite_cutter_window.py",
    "startup_apps_window.py",
    "password_dialog.py",
    "bomb.py",
    "sound_manager.py",
    "world_locations.py",
]


def backup_broken_files():
    """Stores crash copies neatly inside a hidden '.broken_backups' folder."""
    try:
        BROKEN_DIR.mkdir(exist_ok=True)
        for filename in TRACKED_FILES:
            src = PROJECT_DIR / filename
            if src.exists():
                shutil.copy2(src, BROKEN_DIR / f"{filename}.broken")
    except Exception:
        pass


def fetch_and_replace_from_github():
    """Downloads clean files from GitHub or rolls back to local snapshot if offline."""
    backup_broken_files()
    restored = []

    # Attempt GitHub restore if token is available
    if GITHUB_TOKEN:
        for filename in TRACKED_FILES:
            api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/DesktopPet/{filename}?ref={GITHUB_BRANCH}"
            try:
                headers = {
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3.raw",
                    "User-Agent": "SafeLauncher/1.0",
                }
                req = urllib.request.Request(api_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as response:
                    content = response.read().decode("utf-8")
                    with open(PROJECT_DIR / filename, "w", encoding="utf-8") as f:
                        f.write(content)
                    restored.append(filename)
            except Exception as err:
                print(f"[Warning] Failed to download {filename} from GitHub: {err}", file=sys.stderr)

    # If GitHub restore failed or wasn't configured, restore from local snapshot
    if not restored:
        try:
            import project_backup
            if project_backup.restore_previous_project_backup():
                restored.append("Local project snapshot (restored from .backups/)")
        except Exception as e:
            print(f"[Warning] Local restore failed: {e}", file=sys.stderr)

    return restored


def show_error_report(exc_type, exc_val, tb, restored_files):
    """Parses traceback, finds the error line, and displays an alert."""
    full_trace = "".join(traceback.format_exception(exc_type, exc_val, tb))

    tb_frames = traceback.extract_tb(tb)
    failing_file = "Unknown"
    line_no = "Unknown"
    for frame in reversed(tb_frames):
        basename = os.path.basename(frame.filename)
        if basename in TRACKED_FILES or basename.endswith(".py"):
            failing_file = basename
            line_no = frame.lineno
            break

    error_summary = (
        f"🚨 APPLICATION CRASH DETECTED\n"
        f"────────────────────────────────────────\n"
        f"Error Type:   {exc_type.__name__}\n"
        f"Problem:      {exc_val}\n"
        f"File:         {failing_file} (Line {line_no})\n"
        f"────────────────────────────────────────\n\n"
        f"↺ GITHUB RECOVERY COMPLETED:\n"
        f"Broken files archived in '.broken_backups/'.\n"
        f"Files restored from GitHub ({GITHUB_BRANCH}):\n"
        + "\n".join([f"  • {f}" for f in restored_files])
        + "\n\nFull Traceback:\n"
        + full_trace
    )

    print("\n" + "=" * 60, file=sys.stderr)
    print(error_summary, file=sys.stderr)
    print("=" * 60 + "\n", file=sys.stderr)

    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showerror(
            "Crash Detected - GitHub Rollback Done",
            f"An error occurred in {failing_file} at line {line_no}:\n\n"
            f"{exc_type.__name__}: {exc_val}\n\n"
            f"Clean copies have been restored from GitHub.\n"
            f"Broken copies are archived inside '.broken_backups/'.",
        )
        root.destroy()
    except Exception:
        pass


def run():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    sys.path.insert(0, current_dir)

    try:
        runpy.run_path("main.py", run_name="__main__")
    except Exception:
        exc_type, exc_val, tb = sys.exc_info()
        restored = fetch_and_replace_from_github()
        show_error_report(exc_type, exc_val, tb, restored)


if __name__ == "__main__":
    run()