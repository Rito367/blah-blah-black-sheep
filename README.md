# 🐾 Desktop Pet Companion (Hais Edition)

> An interactive, physics-enabled desktop pet companion for Windows built with Python and Tkinter. Includes productivity utilities, mini-games, dynamic NPC walkers, customizable soundboards, and automated local/cloud synchronization.

---

## 📂 Repository Structure

```text
blah-blah-black-sheep/
├── .vscode/                     # Workspace editor configurations
├── DesktopPet/                  # Main Application Package
│   ├── assets/                  # Sprites, animations, and sound effects
│   │   ├── haiya/               # Haiya character animation frames
│   │   ├── pet/                 # Default pet character frames
│   │   ├── npc/                 # NPC walker frames & custom heads/shirts
│   │   └── spritesheets/        # Raw spritesheet archives
│   ├── core/                    # Core application engine & physics
│   │   ├── pet.py               # Main pet physics loop & animation renderer
│   │   ├── data_store.py        # Settings & state persistence
│   │   ├── themes.py            # Color schemes & UI palettes
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
│   ├── paths.py                 # Centralized path resolution
│   ├── pet_data.json            # Active runtime state & preferences
│   ├── requirements.txt         # Python package dependencies
│   └── run_pet.bat              # 1-Click Windows launcher batch script
└── README.md                    # Project overview & documentation
```

---

## 🚀 Quick Start

### 1. Requirements
- **Python**: 3.10+ (tested on Python 3.13)
- **Windows**: Windows 10 or 11

### 2. Installation
Install the required Python libraries:
```bash
cd DesktopPet
pip install -r requirements.txt
```

### 3. Running the Pet
Launch directly via Python:
```bash
python DesktopPet/main.py
```
Or double-click `DesktopPet/run_pet.bat`.

---

## 🎮 Key Features
- **Physics-Enabled Companion**: Gravity, bounce physics, draggable pet, and idle animations.
- **Productivity Suite**: Pomodoro timers, event countdowns, daily report reminders, and full calendar.
- **Weather & World Time**: Live 200+ city weather and world clock dashboard.
- **Mini-Games**: Tic-Tac-Toe, Chopsticks, and interactive decision dice.
- **NPC Companion**: Wandering NPCs with custom heads/shirts and elastic leash mechanics.
- **Custom Sound Effects**: Procedural sound discovery for whip cracks, hits, and screams.
- **Auto Backup & Cloud Sync**: Automated timestamped zip snapshots and silent GitHub commits.