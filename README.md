# 🐾 Desktop Pet Companion (Hais Edition)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows" />
  <img src="https://img.shields.io/badge/GUI-Tkinter-green?style=for-the-badge" alt="Tkinter" />
  <img src="https://img.shields.io/badge/License-MIT-orange?style=for-the-badge" alt="License" />
</p>

> **An always-on-screen, physics-enabled interactive desktop pet companion for Windows.**  
> Lives directly on your desktop with zero border and zero taskbar clutter. Packed with productivity suites (timers, calendar, reminders, weather), mini-games (Tic-Tac-Toe, Chopsticks), wandering NPC companions with elastic leash physics, customizable soundboards, and silent 1-click GitHub cloud synchronization.

---

## ⚡ Quick Start

### 1. Launch Instantly (No Terminal Needed!)
You can launch the pet anytime using any of the following methods:

* **1-Click Batch**: Double-click [`DesktopPet/run_pet.bat`](DesktopPet/run_pet.bat)
* **Windows Run**: Press <kbd>Win</kbd> + <kbd>R</kbd>, type `run_pet`, and hit <kbd>Enter</kbd> (after initial setup)
* **Desktop Shortcut**: Double-click the `run_pet` shortcut on your Desktop (created via setup)

> [!TIP]
> **Automatic Dependency Installation**: `run_pet.bat` automatically inspects your Python installation and installs all required packages (`Pillow`, `pystray`, `keyboard`, `numpy`, `scipy`, `pywin32`, `tzdata`) on first launch!

### 2. Manual / Terminal Launch
```bash
# Navigate to DesktopPet folder
cd DesktopPet

# Install dependencies
pip install -r requirements.txt

# Run main application
python main.py
```

---

## 🎮 Controls & Mouse Interactions

| Action | Result |
|---|---|
| **Hover** | Pet executes a cheerful jump/hop animation. |
| **Left Click (Idle)** | Pat your pet! Triggers a happy jump and floating heart bubbles (`♡ ♡ ♡`). |
| **Left Click (Sleeping)** | Wakes pet up with speech bubble response (`zzZZ 💤`). |
| **Left Click (Eating)** | Pet smiles with eating dialogue (`Yummy~ ♡` / `Nom nom ♡`). |
| **Left Click + Drag** | Pick up and throw the pet anywhere on screen — realistic gravity pulls it back down with a soft landing bounce. |
| **Double Click** | Quick toggle for the **Countdown Timer & Stopwatch** window. |
| **Right Click** | Opens the comprehensive Context Menu with all utilities and games. |

---

## 📋 Comprehensive Features

### 🍱 Pet Needs & Customization
* **🍣 Feed**: Plays an immediate eating animation and serves delicious treats.
* **🐾 Character Switching**: Switch on-the-fly between installed characters (e.g. `Cat`, `haiya`, or your own custom sprites).
* **✏️ Rename Character**: Give your pet a custom display name across speech bubbles and dialogs.
* **🎨 9 Dynamic Color Themes**: Choose from Pink, Blue, Green, Purple, Dark, Sunset, Cyberpunk, Forest, and Custom themes that instantly restyle all popup windows.
* **💬 Speech Phrases**: Built-in manager to edit random idle lines, petting reactions, feeding quotes, and walking complaints.
* **💥 Whip Mode**: Spawns an interactive whip held by your mouse cursor. Click to crack the whip with realistic wave animations, comic sparks, procedural whip crack sounds, and hilarious pet physics reactions!

### ⏱️ Productivity & Utilities
* **⏰ Timer & Stopwatch**: Multi-event countdown timer with presets and precision stopwatch.
* **📅 Interactive Calendar**: Monthly and yearly calendar view with daily event notes and schedules.
* **🔔 Smart Reminders**: Alarms supporting both 12-hour (AM/PM) and 24-hour time pickers that trigger animated pet speech alerts.
* **🌍 World Clock & Weather**: Live weather forecasts and timezone clocks for 200+ global cities with local sunrise/sunset indicators.
* **🎲 Decision Maker**: Quick coin flips, 6-sided dice rolling, and Magic 8-Ball answers for indecisive moments.
* **🚀 Startup Apps Launcher**: Configure quick-launch shortcuts for your favorite productivity apps.

### 🕹️ Built-in Mini-Games
* **❌ Tic-Tac-Toe**: Classic 3x3 grid board game featuring an intelligent AI opponent with difficulty settings.
* **🥢 Chopsticks**: Turn-based finger-counting tactical math mini-game against AI.

### 🚶 Dynamic NPC Companion & Physics Leash
* **Independent NPC Walker**: Wandering NPC companion that roams across your monitors.
* **🪢 Elastic Physics Leash**: Visual tether mechanism connecting the pet to the NPC or mouse cursor with real tension, pulling, and complaining dialogue lines!
* **👤 NPC Customizer**: Procedural sprite compositor to customize NPC head shapes, hairstyles, shirt colors, and accessories.
* **💣 Interactive Bomb**: Fun mini-game mechanics with synthesized sound effects.

### ☁️ Cloud Sync & Safe Backups
* **💾 Silent GitHub Cloud Save**: 
  - 100% windowless background sync without flashing command prompts.
  - Supports custom version tags (e.g., `Release V2.0`, `Stable Checkpoint`).
* **🛟 Safe Launcher & Auto-Recovery**: Isolates syntax or runtime errors, backs up broken files into `.broken_backups/`, and restores stable versions automatically.
* **📦 Local Project Snapshots**: Instantly bundles timestamped `.zip` archives inside `.backups/` for rollback safety.

---

## 🎨 Adding Custom Characters

You can easily add your own pixel art or animated pets:

1. Create a new directory under [`DesktopPet/assets/<your_character_name>/`](DesktopPet/assets/).
2. Add the 5 required animation subdirectories:
   ```text
   DesktopPet/assets/<your_character_name>/
   ├── idle/    # 01.png, 02.png, 03.png, 04.png ...
   ├── walk/    # 01.png, 02.png, 03.png, 04.png ...
   ├── jump/    # 01.png, 02.png, 03.png, 04.png ...
   ├── sleep/   # 01.png, 02.png, 03.png, 04.png ...
   └── eat/     # 01.png, 02.png, 03.png, 04.png ...
   ```
3. Ensure all frames are transparent PNGs.
4. **Need to extract from a sprite sheet?** Use [`DesktopPet/tools/sprite_extract.py`](DesktopPet/tools/sprite_extract.py):
   ```bash
   # Preview auto-detection bounding boxes
   python DesktopPet/tools/sprite_extract.py --preview

   # Extract all frames into assets automatically
   python DesktopPet/tools/sprite_extract.py
   ```
5. Select your new character anytime via **Right Click → 🐾 Character**!

---

## 📂 Repository Structure

```text
blah-blah-black-sheep/
├── .vscode/                     # Multi-root VS Code settings & extraPaths
├── DesktopPet/                  # Main Application Package
│   ├── assets/                  # Sprites, animations, and sound effects
│   │   ├── haiya/               # Haiya character animation frames
│   │   ├── pet/                 # Default cat frames (idle, walk, jump, sleep, eat)
│   │   ├── npc/                 # NPC walker frames & custom heads/shirts
│   │   └── spritesheets/        # Raw spritesheet archives
│   ├── core/                    # Core application engine & physics
│   │   ├── pet.py               # Main pet physics loop & animation renderer
│   │   ├── data_store.py        # Settings & state persistence (JSON)
│   │   ├── themes.py            # 9 Color schemes & UI palettes
│   │   ├── sound_manager.py     # Audio synthesis, sound effects & dynamic discovery
│   │   ├── hotkey_manager.py    # Global keyboard shortcuts
│   │   └── tray_manager.py      # System tray icon & context menus
│   ├── windows/                 # GUI Windows & Dialogs
│   │   ├── calendar_window.py   # Monthly & yearly calendar view
│   │   ├── chopsticks_window.py # Chopsticks mini-game
│   │   ├── decision_window.py   # Decision roulette & coin flipper
│   │   ├── dialogue_window.py   # Interactive pet dialogue & speech bubbles
│   │   ├── password_dialog.py   # PIN & master password management
│   │   ├── reminder_window.py   # Daily & recurring reminder system
│   │   ├── rename_char_window.py# Character folder rename dialog
│   │   ├── settings_window.py   # Full preferences & theme customizer
│   │   ├── speech_bubble.py     # Dynamic canvas speech bubbles
│   │   ├── sprite_cutter_window.py # Sprite extraction & cutting tool
│   │   ├── startup_apps_window.py  # Startup apps launcher
│   │   ├── tictactoe_window.py  # Tic-Tac-Toe mini-game
│   │   ├── timer_window.py      # Pomodoro, stopwatch & countdown timers
│   │   ├── weather_window.py    # Real-time weather & world time dashboard
│   │   └── world_locations.py   # Global timezone & city geocoding data
│   ├── npc/                     # NPC Walker & Interactions
│   │   ├── npc_walker.py        # Independent wandering NPC engine
│   │   ├── npc_leash.py         # Elastic physics leash mechanism
│   │   ├── npc_graphics.py      # Procedural sprite compositing
│   │   ├── npc_customizer_window.py # Custom NPC appearance editor
│   │   ├── leash_overlay.py     # Screen-wide leash visualizer
│   │   └── bomb.py              # Interactive mini-game mechanics
│   ├── tools/                   # Developer & Management Utilities
│   │   ├── git_sync.py          # Background GitHub cloud sync
│   │   ├── project_backup.py    # Timestamped project snapshots & rollback
│   │   ├── safe_launcher.py     # Fault-tolerant auto-recovery launcher
│   │   ├── setup_and_run.py     # Environment check & dependency installer
│   │   └── sprite_extract.py    # Spritesheet segmentation utility
│   ├── docs/                    # UI inspiration & documentation notes
│   ├── main.py                  # Primary application entry point
│   ├── paths.py                 # Centralized absolute/relative path resolution
│   ├── pet_data.json            # Active runtime state & preferences
│   ├── requirements.txt         # Python package dependencies
│   └── run_pet.bat              # 1-Click Windows launcher batch script
├── pyrightconfig.json           # Type checking configuration
└── README.md                    # Repository documentation (You are here!)
```

---

## 🛠️ Requirements & Tech Stack

* **Operating System**: Windows 10 or Windows 11
* **Python**: 3.10 or newer (tested on Python 3.13)
* **Libraries**:
  * `Pillow` — Image loading, resizing, and transparency handling
  * `pystray` — Windows system tray integration
  * `keyboard` — Global hotkeys
  * `numpy` & `scipy` — Physics calculations and sprite segmentation
  * `pywin32` — Windows window styles, transparency, and top-level positioning
  * `tzdata` — Real-time timezone and world clock computation

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). Feel free to customize, add your own pets, and share!