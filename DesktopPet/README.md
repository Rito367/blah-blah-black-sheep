# 🐾 Desktop Pet Companion (Hais Edition)

> An always-on-screen, physics-enabled interactive desktop pet companion for Windows. Complete with productivity tools (timers, calendar, reminders), minigames (Tic-Tac-Toe, Chopsticks), sprite utilities, and silent 1-click GitHub cloud save.

---

## ⚡ Quick Start

### 1. Launch Instantly (No Terminal Needed!)
You can launch the pet anytime in 3 convenient ways:

* **Windows Start Search**: Press `Win`, type **`run_pet`**, and press `Enter`.
* **Windows Run**: Press `Win + R`, type **`run_pet`**, and press `Enter`.
* **Desktop Shortcut**: Double-click the **`run_pet`** icon on your Desktop.
* **1-Click Batch**: Double-click [`run_pet.bat`](file:///c:/Users/Ben%20Ong/OneDrive/Pictures/Documents/PET/desktop-pet-hais-f8b3a7562868f8ffe17ce41d990fe1cb8fb73d4f/DesktopPet/run_pet.bat).

> Missing dependencies? [`run_pet.bat`](file:///c:/Users/Ben%20Ong/OneDrive/Pictures/Documents/PET/desktop-pet-hais-f8b3a7562868f8ffe17ce41d990fe1cb8fb73d4f/DesktopPet/run_pet.bat) automatically checks Python and installs all required packages (`Pillow`, `pystray`, `keyboard`, `numpy`, `scipy`, `pywin32`, `tzdata`) on first run.

---

## 🎮 Controls & Interactions

| Action | Result |
|---|---|
| **Hover** | Pet does a playful hop animation. |
| **Left Click (Idle)** | Pat the pet! Pet jumps and displays heart bubbles (`♡ ♡ ♡`). |
| **Left Click (Sleeping)** | Wakes pet up with speech bubble (`zzZZ 💤`). |
| **Left Click (Eating)** | Pet smiles and displays eating quotes (`Yummy~ ♡`). |
| **Left Click + Drag** | Pick up and throw the pet anywhere on screen — gravity pulls it back down with a soft landing bounce. |
| **Double Click** | Quick toggle for the **Countdown Timer & Stopwatch** window. |
| **Right Click** | Opens the context menu with all utilities, minigames, and cloud save. |

---

## 📋 Features & Context Menu

### 🍱 Pet Needs & Customization
* **🍣 Feed**: Triggers eating animation and treats immediately.
* **🐾 Character**: Switch between installed characters (e.g. `Cat`, `haiya`, or custom characters).
* **✏️ Rename Character**: Give your pet a custom display name.
* **🎨 Theme**: Choose from 9 tailored color themes (Pink, Blue, Green, Purple, Dark, Sunset, Cyberpunk, Forest, Custom) that dynamically restyle all popup windows.
* **💬 Speech Phrases**: Customize random speech bubble lines and motivational messages.
* **💥 Whip Mode**: Spawns an interactive whip held by your cursor. Click to crack the whip with realistic wave snap animation, sound effect, comic sparks, and launch the pet with hilarious reactions.

### ⏱️ Productivity & Tools
* **⏰ Timer & Stopwatch**: Multi-event countdown timer and precision stopwatch.
* **📅 Calendar**: Interactive monthly calendar with daily event notes and schedules.
* **🔔 Reminder**: Alarms with 12h/24h picker that trigger pet speech alerts.
* **🌍 World Clock**: Real-time clocks across world timezones with daylight indicators.
* **🎲 Decision Maker**: Quick coin flips, 6-sided dice rolls, and Magic 8-Ball decisions.
* **✂️ Sprite Cutter**: Visual utility to slice custom sprite sheets into pet animation frames.
* **⚙️ Settings**: Control pet scale factor, animation speed, window transparency, and gravity.

### 🕹️ Minigames
* **❌ Tic-Tac-Toe**: Interactive grid board game against AI.
* **🥢 Chopsticks**: Turn-based finger-counting tactical game with AI opponent.

### ☁️ Cloud Sync & Backups
* **💾 Save project to GitHub**: 
  - Allows custom version naming (e.g. `Release V2.0`, `Stable checkpoint`).
  - Automatically records commit checkpoints even without code changes.
  - **100% Windowless & Silent**: Runs without flashing console or terminal popups.
* **🛟 Safe Launcher & Auto-Recovery**: [`safe_launcher.py`](file:///c:/Users/Ben%20Ong/OneDrive/Pictures/Documents/PET/desktop-pet-hais-f8b3a7562868f8ffe17ce41d990fe1cb8fb73d4f/DesktopPet/safe_launcher.py) backs up broken files into `.broken_backups/` and pulls clean versions from GitHub if a crash occurs.
* **📦 Local Zip Backup**: Instantly bundles full project snapshots inside `.backups/`.

---

## 📁 Project Architecture

```
DesktopPet/
├── main.py                     # Main application entry point & GUI loop
├── pet.py                      # Pet sprite engine, state machine & physics
├── speech_bubble.py            # Comic speech bubble rendering
├── data_store.py               # Persistent JSON configuration store
├── themes.py                   # 9 Color palettes & dynamic widget theming
├── git_sync.py                 # Silent background GitHub cloud sync
├── safe_launcher.py            # Crash isolation & automatic GitHub restore
├── setup_and_run.py            # Auto-installer & shortcut bootstrapper
├── run_pet.bat                 # 1-click batch launcher (silent pythonw)
│
├── calendar_window.py          # Calendar & daily event scheduler
├── timer_window.py             # Countdown timer & stopwatch
├── reminder_window.py          # Scheduled alarms & reminders
├── settings_window.py          # Settings, theme picker & sliders
├── decision_window.py          # Coin flip, dice roll & Magic 8-ball
├── dialogue_window.py          # Speech bubble phrases manager
├── weather_window.py           # Live weather forecasts & world time clocks
├── rename_char_window.py       # Character rename dialog
│
├── tictactoe_window.py         # Tic-Tac-Toe minigame
├── chopsticks_window.py        # Chopsticks finger math minigame
├── sprite_cutter_window.py     # Interactive sprite sheet cutter
├── leash_overlay.py            # Physics leash tether overlay
├── hotkey_manager.py           # System-wide keyboard shortcut hooks
├── tray_manager.py             # System tray icon & context menu
│
├── assets/                     # Character animation frames
│   ├── pet/                    # Default cat frames (idle, walk, jump, sleep, eat)
│   └── haiya/                  # Custom sprite character frames
└── requirements.txt            # Python dependencies
```

---

## 🎨 Adding Custom Characters

To add your own custom pet or character:
1. Create a new folder inside `assets/<your_character_name>/`.
2. Add the 5 required animation subfolders:
   - `idle/` (frames: `01.png`, `02.png`, ...)
   - `walk/` (frames: `01.png`, `02.png`, ...)
   - `jump/` (frames: `01.png`, `02.png`, ...)
   - `sleep/` (frames: `01.png`, `02.png`, ...)
   - `eat/` (frames: `01.png`, `02.png`, ...)
3. Ensure frames are PNGs with transparent backgrounds.
4. Restart the app or select your new character under **Right Click → 🐾 Character**.
