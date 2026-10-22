"""
project_backup.py
Creates dated project snapshots and safely rolls back to previous working states.
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path
import shutil

try:
    import paths
    PROJECT_ROOT = paths.PROJECT_ROOT
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_ARCHIVE_DIR = PROJECT_ROOT / "project_snapshots"

INCLUDE_EXTENSIONS = {".py", ".json", ".png", ".jpg", ".jpeg", ".txt", ".md", ".bat"}
EXCLUDE_DIRS = {"__pycache__", ".backups", ".broken_backups", "project_snapshots", ".git", ".idea", ".vscode"}


def create_full_project_backup() -> Path:
    """Zips all project scripts, assets, and data files into a dated snapshot."""
    BACKUP_ARCHIVE_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_zip_path = BACKUP_ARCHIVE_DIR / f"full_project_backup_{timestamp}.zip"

    with zipfile.ZipFile(backup_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in INCLUDE_EXTENSIONS:
                    rel_path = file_path.relative_to(PROJECT_ROOT)
                    zipf.write(file_path, arcname=rel_path)

    # Keep the 15 newest backups
    all_snapshots = sorted(BACKUP_ARCHIVE_DIR.glob("full_project_backup_*.zip"))
    while len(all_snapshots) > 15:
        oldest = all_snapshots.pop(0)
        try:
            oldest.unlink()
        except OSError:
            pass

    return backup_zip_path


def restore_previous_project_backup() -> bool:
    """Restores the backup right before the current active session."""
    if not BACKUP_ARCHIVE_DIR.exists():
        return False

    all_snapshots = sorted(BACKUP_ARCHIVE_DIR.glob("full_project_backup_*.zip"))
    if not all_snapshots:
        return False

    # If multiple snapshots exist, pick the previous one (not the one created on current launch)
    target_snapshot = all_snapshots[-2] if len(all_snapshots) >= 2 else all_snapshots[-1]
    
    try:
        with zipfile.ZipFile(target_snapshot, "r") as zipf:
            for member in zipf.namelist():
                # Reject paths that escape the project directory
                resolved = (PROJECT_ROOT / member).resolve()
                if not resolved.is_relative_to(PROJECT_ROOT.resolve()):
                    print(f"Skipping unsafe path in zip: {member}")
                    continue
                zipf.extract(member, PROJECT_ROOT)
        return True
    except Exception as e:
        print(f"Restore failed: {e}")
        return False