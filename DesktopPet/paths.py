"""
paths.py
Central path resolution and environment bootstrap for DesktopPet.
Provides robust absolute paths for root directories, assets, data, and submodules.
"""
from pathlib import Path
import sys

# Base project directory is DesktopPet/
PROJECT_ROOT = Path(__file__).resolve().parent

# Core subdirectories
CORE_DIR = PROJECT_ROOT / "core"
WINDOWS_DIR = PROJECT_ROOT / "windows"
NPC_DIR = PROJECT_ROOT / "npc"
TOOLS_DIR = PROJECT_ROOT / "tools"
ASSETS_DIR = PROJECT_ROOT / "assets"
DOCS_DIR = PROJECT_ROOT / "docs"

# Data & backup locations
DATA_FILE = PROJECT_ROOT / "pet_data.json"
BACKUP_DIR = PROJECT_ROOT / ".backups"
SNAPSHOTS_DIR = PROJECT_ROOT / "project_snapshots"
MAIN_SCRIPT = PROJECT_ROOT / "main.py"

def setup_sys_path():
    """Ensure all submodules (core, windows, npc, tools, root) are in sys.path for clean imports."""
    search_dirs = [PROJECT_ROOT, CORE_DIR, WINDOWS_DIR, NPC_DIR, TOOLS_DIR]
    for folder in search_dirs:
        folder_str = str(folder.resolve())
        if folder_str not in sys.path:
            sys.path.insert(0, folder_str)

# Automatically bootstrap sys.path whenever paths is imported
setup_sys_path()
