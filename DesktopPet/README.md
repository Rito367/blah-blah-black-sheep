# 🐾 Desktop Pet Companion (Hais Edition)

> Please refer to the main [Repository README](../README.md) for full project documentation, interactive physics guides, and screenshots.

---

## ⚡ Quick Start

### 1. Launch Instantly (No Terminal Needed!)
You can launch the pet anytime using any of the following methods:

* **1-Click Batch**: Double-click [`run_pet.bat`](run_pet.bat)
* **Windows Run**: Press <kbd>Win</kbd> + <kbd>R</kbd>, type `run_pet`, and hit <kbd>Enter</kbd> (after setup)
* **Desktop Shortcut**: Double-click the `run_pet` shortcut on your Desktop

> [!TIP]
> **Automatic Dependency Installation**: [`run_pet.bat`](run_pet.bat) automatically checks Python and installs all required packages (`Pillow`, `pystray`, `keyboard`, `numpy`, `scipy`, `pywin32`, `tzdata`) on first launch!

### 2. Manual Terminal Launch
```bash
# Install dependencies
pip install -r requirements.txt

# Run main application
python main.py
```

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
* **🛟 Safe Launcher & Auto-Recovery**: [`tools/safe_launcher.py`](tools/safe_launcher.py) backs up broken files into `.broken_backups/` and pulls clean versions from GitHub if a crash occurs.
* **📦 Local Zip Backup**: Instantly bundles full project snapshots inside `.backups/`.

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
