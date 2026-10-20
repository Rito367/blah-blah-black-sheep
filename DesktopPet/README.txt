╔══════════════════════════════════════════════════════════════════╗
║                      DesktopPet_Version1                            ║
║              Your pet always-on-screen companion             ║
╚══════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  QUICK START
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Requirements:
    - Python 3.10 or newer (Miniconda, Anaconda, or Python.org)
    - All packages are automatically installed on first run!

  Quickest Run (1-Click):
    • Double-click "run_pet.bat" in this folder.
      It will automatically find your Python, install any missing
      dependencies (Pillow, pystray, keyboard, numpy, scipy, pywin32, tzdata),
      and start the pet companion!

  Manual / Python Run:
    1. Open a terminal or PowerShell in this folder
    2. Run: python setup_and_run.py
       (or: python setup_and_run.py --shortcut  to add a Desktop icon!)

  The cat will appear at the bottom of your screen.
  No window border, no taskbar icon — it just lives on your desktop.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MOUSE INTERACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Hover over cat       →  Jump animation  (the cat hops)

  Left-click (single)
    • While IDLE       →  Pat!  Jump + hearts bubble  ♡ ♡ ♡
    • While SLEEPING   →  Wakes the cat up + speech bubble  zzZZ 💤
    • While EATING     →  Speech bubble  Yummy~ ♡ / Nom nom ♡

  Left-click (double)  →  Opens / closes the Countdown Timer window

  Left-click + drag    →  Pick up and move the cat anywhere
                          Release → gravity pulls it back down
                          It bounces softly when it lands

  Right-click          →  Opens context menu (see below)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RIGHT-CLICK MENU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  🍣 Feed
      Immediately plays the eat animation for a few seconds.

  🐾 Character  ►
      Switch between different sprite characters. 
      The active character is marked with ✓.
      To add a new character, see "Adding Characters" below.

  🎨 Theme  ►
      Change the colour theme of all pop-up windows.
      Five built-in options:
        🌸 Pink   (default)
        🫐 Blue
        🌿 Green
        🔮 Purple
        🌙 Dark
      Your choice is saved and restored on next launch.

  ✦ Countdown Timer
      Opens the countdown timer window (same as double-click).

  ✕ Quit
      Saves position and closes the app.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  COUNTDOWN TIMER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Open:   Double-click the cat  OR  right-click → ✦ Countdown Timer
  Close:  Click ✕ on the timer window  OR  double-click the cat again

  Adding an event:
    1. Type a name in the "Name" field   (e.g.  Project Deadline)
    2. Type the date in  YYYY-MM-DD      (e.g.  2026-12-31)
    3. Type the time in  HH:MM:SS        (e.g.  09:00:00)
    4. Click  ✦ Save


  When the timer hits zero:
    A speech bubble pops above the cat showing the event name.

  Multiple events:
    You can save as many as you like and scroll between them.
    Each one counts down independently when selected.

  The window can be dragged anywhere on screen.



━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PET BEHAVIOUR  (autonomous)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  The cat has a mind of its own:

  IDLE      Default state. The cat sits quietly most of the time.
            Every ~60 seconds there is a 20% chance it shows a
            random motivational message bubble

  WALK      Every 5–10 minutes the cat picks a random spot on
            the screen and walks there, then returns to idle.

  SLEEP     Every 15–30 minutes the cat falls asleep for 5 minutes.
            Single-click it to wake it up early.
            A  zzZZ 💤  bubble appears when you click it awake.

  EAT       Every 10 minutes the cat eats for 3 minutes.
            Right-click → 🍣 Feed to trigger eating immediately.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ADDING CHARACTERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Each character is a folder inside  assets/  containing the five
  animation subfolders.  Example structure:

    assets/
    ├── pet/            ← the default cat
    │   ├── idle/       01.png  02.png  03.png  04.png
    │   ├── walk/       01.png  02.png  03.png  04.png
    │   ├── jump/       01.png  02.png  03.png  04.png
    │   ├── sleep/      01.png  02.png  03.png  04.png
    │   └── eat/        01.png  02.png  03.png  04.png
    └── dog/            ← a new character called "Dog"
        ├── idle/
        ├── walk/
        ├── jump/
        ├── sleep/
        └── eat/

  Rules:
    • Frames must be PNG with transparent background
    • Name them  01.png  02.png  ...  (sorted alphabetically)
    • Any number of frames per animation is fine (min 1)
    • Folder name becomes the display name in the menu
      (underscores become spaces, title-cased)
      Exception: folder "pet" always displays as "Cat"

  After adding a character folder, restart the app and it will
  appear automatically in  right-click → 🐾 Character.

  You can use  sprite_extract.py  to slice a sprite sheet into
  the correct folder structure automatically.  Run:
    python sprite_extract.py --preview   (check detection)
    python sprite_extract.py             (extract frames)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  • All pop-up windows are draggable — click and drag their header.
  • The cat remembers its last position between sessions.
  • Theme and character choices are also remembered.
  • To reset everything, delete  pet_data.json  and restart.
  • The app has no taskbar icon by design — quit via right-click menu.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
