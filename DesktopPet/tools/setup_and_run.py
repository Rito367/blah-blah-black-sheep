"""
setup_and_run.py
Automated environment validator, dependency installer, and launcher for Desktop Pet.
Checks for missing packages (from requirements.txt), automatically installs them via pip,
verifies project assets, configures Windows shortcuts, and launches the pet companion.
"""

from __future__ import annotations

import sys
import os
import re
import subprocess
import importlib.util
from pathlib import Path

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            getattr(sys.stderr, "reconfigure")(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import paths
    PROJECT_ROOT = paths.PROJECT_ROOT
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"

# Known mapping between PyPI package names and their importable Python module names
PACKAGE_MODULE_MAP = {
    "pillow": "PIL",
    "pywin32": "win32com",
    "pystray": "pystray",
    "keyboard": "keyboard",
    "numpy": "numpy",
    "scipy": "scipy",
    "tzdata": "tzdata",
}

# Fallback package list if requirements.txt is missing
DEFAULT_PACKAGES = [
    ("Pillow>=10.0.0", "PIL"),
    ("pystray>=0.19.0", "pystray"),
    ("keyboard>=0.13.5", "keyboard"),
    ("numpy>=1.24.0", "numpy"),
    ("scipy>=1.10.0", "scipy"),
    ("pywin32>=306", "win32com"),
    ("tzdata>=2024.1", "tzdata"),
]


def print_banner():
    banner = """
================================================================
                    DESKTOP PET SETUP & LAUNCHER
          Auto-checking & installing required packages
================================================================
"""
    print(banner)


def check_module(module_name: str) -> bool:
    """Checks if a Python module is currently available without throwing errors."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


def evaluate_marker(marker_str: str) -> bool:
    """Evaluates PEP 508 environment markers (e.g. sys_platform == 'win32')."""
    try:
        from packaging.markers import Marker
        return Marker(marker_str).evaluate()
    except Exception:
        # Lightweight fallback
        if "sys_platform" in marker_str:
            if "'win32'" in marker_str or '"win32"' in marker_str:
                return sys.platform == "win32"
        return True


def load_required_packages() -> list[tuple[str, str]]:
    """
    Loads packages from requirements.txt, or falls back to DEFAULT_PACKAGES.
    Returns list of tuples: (package_spec, import_module_name)
    """
    if not REQUIREMENTS_FILE.exists():
        return list(DEFAULT_PACKAGES)

    packages: list[tuple[str, str]] = []
    try:
        content = REQUIREMENTS_FILE.read_text(encoding="utf-8")
        for raw_line in content.splitlines():
            line = raw_line.split("#")[0].strip()
            if not line:
                continue

            # Check environment marker
            spec = line
            if ";" in line:
                pkg_part, marker_part = line.split(";", 1)
                spec = pkg_part.strip()
                if not evaluate_marker(marker_part.strip()):
                    continue

            # Extract base package name to find module
            m = re.match(r"^([A-Za-z0-9_.\-]+)", spec)
            if not m:
                continue
            pkg_name = m.group(1)
            mod_name = PACKAGE_MODULE_MAP.get(
                pkg_name.lower(),
                pkg_name.lower().replace("-", "_")
            )
            packages.append((spec, mod_name))

        if packages:
            return packages
    except Exception as e:
        print(f"[!] Warning reading requirements.txt: {e}. Using defaults.")

    return list(DEFAULT_PACKAGES)


def ensure_pip() -> bool:
    """Ensures pip is installed and working."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return True
    except Exception:
        print("[!] pip is not detected. Attempting to bootstrap pip via ensurepip...")
        try:
            subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], check=True)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to initialize pip: {e}")
            return False


def install_package(package_spec: str) -> bool:
    """Runs python -m pip install for a single given package specifier."""
    print(f"[*] Installing {package_spec} via pip...")
    try:
        cmd = [sys.executable, "-m", "pip", "install", package_spec]
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print(f"    [SUCCESS] {package_spec} installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    [ERROR] Failed to install {package_spec}:")
        print(e.stdout)
        return False
    except Exception as e:
        print(f"    [ERROR] Unexpected error installing {package_spec}: {e}")
        return False


def install_packages_batch(package_specs: list[str]) -> bool:
    """Installs multiple packages in a single pip run, with individual fallback."""
    if not package_specs:
        return True

    if len(package_specs) == 1:
        return install_package(package_specs[0])

    print(f"[*] Installing {len(package_specs)} packages via pip: {', '.join(package_specs)}...")
    try:
        cmd = [sys.executable, "-m", "pip", "install", *package_specs]
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        print("    [SUCCESS] All packages installed successfully.")
        return True
    except subprocess.CalledProcessError:
        print("    [!] Batch installation encountered an issue, trying individual installs...")
        all_ok = True
        for pkg in package_specs:
            if not install_package(pkg):
                all_ok = False
        return all_ok
    except Exception as e:
        print(f"    [ERROR] Unexpected error: {e}")
        return False


def check_and_install_dependencies(force_reinstall: bool = False) -> bool:
    """Checks all required packages and installs any missing ones."""
    print("[1/3] Checking Python dependencies...")
    if not ensure_pip():
        return False

    required = load_required_packages()
    missing_packages = []

    for pkg_spec, mod_name in required:
        if not force_reinstall and check_module(mod_name):
            print(f"    [OK] {mod_name:<12} is already installed.")
        else:
            status = "Reinstalling" if force_reinstall else "Missing"
            print(f"    [{status.upper()}] {mod_name:<12} -> adding '{pkg_spec}' to install queue.")
            missing_packages.append(pkg_spec)

    if not missing_packages:
        print(">>> All required Python packages are already installed!\n")
        return True

    print(f"\n>>> Downloading and installing {len(missing_packages)} package(s)...")
    success = install_packages_batch(missing_packages)

    if success:
        print(">>> Missing packages installed successfully!\n")
    else:
        print("[!] Warning: Some packages failed to install. Please review errors above.\n")

    return success


def verify_assets() -> bool:
    """Verifies that the Desktop Pet assets directory and character animations exist."""
    print("[2/3] Checking project assets...")
    assets_dir = PROJECT_ROOT / "assets"
    if not assets_dir.exists():
        print(f"    [FAIL] Assets directory missing at: {assets_dir}")
        return False

    # Check for character folders
    characters = [d for d in assets_dir.iterdir() if d.is_dir()]
    if not characters:
        print(f"    [FAIL] No character directories found in {assets_dir}")
        return False

    print(f"    [OK] Found {len(characters)} character(s): {', '.join([c.name for c in characters])}")

    # Check default pet animations
    default_pet = assets_dir / "pet"
    if default_pet.exists():
        anims = [a.name for a in default_pet.iterdir() if a.is_dir()]
        print(f"    [OK] Default character animations: {', '.join(anims)}")

    print(">>> Asset verification complete.\n")
    return True


def get_desktop_dir() -> Path:
    """Finds the user's Desktop path, accounting for OneDrive folder redirection."""
    user_profile = Path(os.environ.get("USERPROFILE", os.path.expanduser("~")))
    candidates = [
        user_profile / "OneDrive" / "Desktop",
        user_profile / "Desktop",
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    return user_profile / "Desktop"


def get_start_menu_dir() -> Path | None:
    """Finds the user's Start Menu Programs folder for Windows Search indexing."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        p = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        if p.exists():
            return p
    return None


def register_system_shortcuts() -> bool:
    """Creates shortcuts specifically named 'run_pet' in Start Menu (Windows Search), Desktop, and Win+R."""
    bat_launcher = PROJECT_ROOT / "run_pet.bat"
    if not bat_launcher.exists():
        return False

    desktop = get_desktop_dir()
    start_menu = get_start_menu_dir()

    shortcut_targets = []
    # 1. Start Menu (Indexed by Windows Search when user types 'run_pet')
    if start_menu and start_menu.exists():
        shortcut_targets.append(start_menu / "run_pet.lnk")

    # 2. Desktop Shortcut
    if desktop.exists():
        shortcut_targets.append(desktop / "run_pet.lnk")

    shortcut_vbs = PROJECT_ROOT / ".create_shortcut.vbs"
    try:
        vbs_lines = ['Set oWS = WScript.CreateObject("WScript.Shell")']
        for target in shortcut_targets:
            vbs_lines.extend([
                f'Set oLink = oWS.CreateShortcut("{target}")',
                f'oLink.TargetPath = "{bat_launcher}"',
                f'oLink.WorkingDirectory = "{PROJECT_ROOT}"',
                'oLink.Description = "Run Desktop Pet (main.py)"',
                'oLink.Save',
            ])
        with open(shortcut_vbs, "w", encoding="utf-8") as f:
            f.write("\n".join(vbs_lines))

        subprocess.run(["cscript", "//nologo", str(shortcut_vbs)], check=True)
        if shortcut_vbs.exists():
            shortcut_vbs.unlink()
        print("    [OK] 'run_pet' shortcut registered for Windows Search & Desktop.")
    except Exception as e:
        print(f"    [!] Note: Could not create shortcut: {e}")

    # 3. Register 'run_pet' in WindowsApps for Win+R and Search
    try:
        windows_apps = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WindowsApps"
        if windows_apps.exists():
            cmd_path = windows_apps / "run_pet.cmd"
            with open(cmd_path, "w", encoding="utf-8") as f:
                f.write(f'@start "" "{bat_launcher}"\n')
            print("    [OK] 'run_pet' command registered for Windows Run (Win + R).")
    except Exception as e:
        print(f"    [!] Note: Could not register WindowsApps alias: {e}")

    return True


def get_running_pet_pids() -> list[int]:
    """Finds PIDs of any already-running desktop pet process."""
    pids = []
    current_pid = os.getpid()
    if sys.platform != "win32":
        return pids

    try:
        ps_cmd = (
            f"Get-CimInstance Win32_Process | "
            f"Where-Object {{ ($_.Name -like 'python*' -or $_.Name -like 'pythonw*') -and "
            f"$_.CommandLine -like '*main.py*' -and $_.ProcessId -ne {current_pid} }} | "
            f"Select-Object -ExpandProperty ProcessId"
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=3,
        )
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.isdigit():
                pids.append(int(line))
    except Exception:
        pass
    return pids


def stop_running_pets(pids: list[int]) -> None:
    """Terminates existing desktop pet processes."""
    for pid in pids:
        try:
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"    [OK] Stopped existing Desktop Pet process (PID {pid}).")
        except Exception:
            pass


def launch_pet(console_mode: bool = False, restart: bool = False):
    """Launches main.py directly."""
    print("[3/3] Launching main.py...")
    main_py = PROJECT_ROOT / "main.py"
    if not main_py.exists():
        print(f"[ERROR] Cannot find main.py in {PROJECT_ROOT}")
        sys.exit(1)

    running_pids = get_running_pet_pids()
    if running_pids:
        if restart:
            print(f"[*] Stopping existing pet instance(s): {running_pids}...")
            stop_running_pets(running_pids)
        else:
            print(f"    [i] Note: Desktop Pet is already running (PID: {', '.join(map(str, running_pids))}).")
            print("        Launching an additional pet instance.\n")

    print("[+] Starting main.py...\n")
    executable = sys.executable
    kwargs = {}
    if sys.platform == "win32" and not console_mode:
        pythonw = Path(executable).parent / "pythonw.exe"
        if pythonw.exists():
            executable = str(pythonw)
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    subprocess.Popen([executable, str(main_py)], cwd=str(PROJECT_ROOT), **kwargs)
    print(">>> Desktop Pet companion is running! Enjoy! 🐾\n")


def print_help():
    help_text = """
Usage: python setup_and_run.py [OPTIONS]

Options:
  --no-launch, --install-only  Install dependencies & shortcuts without launching
  --launch-only                Directly launch main.py (skip dependency check)
  --shortcut, --shortcut-only  Create/register desktop and Start Menu shortcuts only
  --check-only                 Verify dependencies & assets without installing
  --force-install              Force reinstallation of dependencies from requirements.txt
  --restart                    Restart pet (closes any running pet first)
  --console, --debug           Launch with visible console terminal for debugging
  -h, --help                   Show this help message
"""
    print(help_text)


def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print_banner()
        print_help()
        return

    # Flags
    install_only = "--install-only" in sys.argv or "--no-launch" in sys.argv
    shortcut_only = "--shortcut-only" in sys.argv or "--shortcut" in sys.argv
    launch_only = "--launch-only" in sys.argv
    check_only = "--check-only" in sys.argv
    force_install = "--force-install" in sys.argv
    restart = "--restart" in sys.argv
    console_mode = "--console" in sys.argv or "--debug" in sys.argv

    print_banner()

    # Shortcut-only fast path
    if shortcut_only:
        print("[*] Registering system shortcuts...")
        register_system_shortcuts()
        print("[OK] Shortcuts registered successfully.")
        return

    # Launch-only fast path
    if launch_only:
        launch_pet(console_mode=console_mode, restart=restart)
        return

    # Check and install python dependencies
    deps_ok = check_and_install_dependencies(force_reinstall=force_install)
    if not deps_ok and not check_only:
        print("[!] Proceeding, but some dependencies may be missing.")

    # Check project assets
    verify_assets()

    # Register shortcuts in Windows Search & Run
    register_system_shortcuts()

    if check_only:
        print("[OK] Environment checks complete.")
        return

    if install_only:
        print("[OK] Installation and environment checks finished successfully.")
        return

    launch_pet(console_mode=console_mode, restart=restart)


if __name__ == "__main__":
    main()
