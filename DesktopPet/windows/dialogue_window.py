"""
dialogue_window.py
GUI window to customize and manage pet speech lines for all actions.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Any, Callable

try:
    import paths
except ImportError:
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import paths

import themes

CATEGORIES = [
    ("idle_messages", "💬 Random Idle Lines"),
    ("pat_messages", "💖 Petting / Click Lines"),
    ("sleep_messages", "💤 Sleeping Lines"),
    ("eat_messages", "🍣 Eating Lines"),
    ("complain_messages", "😫 Tired / Walk Complaints"),
    ("whip_messages", "💥 Whip Reactions"),
    ("npc_walk_messages", "🚶 Owner Walking Lines"),
    ("npc_pull_messages", "🪢 Owner Leash Pull Lines"),
    ("npc_arrival_messages", "🎯 Owner Destination Arrival Lines"),
    ("pet_leash_walk_messages", "🐾 Pet Leash Walking Lines"),
    ("pet_leash_pull_messages", "🐕 Pet Leash Pull Complaints"),
]


class DialogueWindow:
    def __init__(
        self,
        root: tk.Tk,
        get_data: Callable[[], dict[str, Any]],
        save_data: Callable[[dict[str, Any]], None],
        on_update: Callable[[], None] | None = None,
        on_menu: Callable[..., Any] | None = None,
    ):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.on_update = on_update
        self.on_menu = on_menu
        self.win: tk.Toplevel | None = None
        self.active_category: str = "idle_messages"
        self.entry: tk.Entry | None = None
        self.listbox: tk.Listbox | None = None
        self.cat_var: tk.StringVar | None = None

    def hide(self) -> None:
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None

    def show(self, near_x: int = 100, near_y: int = 100) -> None:
        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        t = themes.get()
        self.win = tk.Toplevel(self.root)
        self.win.title("Customize Pet Speech")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 360, 480
        safe_x = max(10, min(near_x, sw - target_w - 10))
        safe_y = max(10, min(near_y, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("bg_card", "#ffffff"))
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        # ── header bar ────────────────────────────────────────────────────
        hdr = tk.Frame(self.win, bg=t.get("bg_hdr", "#ffb6c1"), pady=5, padx=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="💬 Pet Dialogue Editor", bg=t.get("bg_hdr", "#ffb6c1"),
                 fg=t.get("fg_white", "#ffffff"), font=("Georgia", 10, "bold")).pack(side="left")
        if self.on_menu is not None:
            on_m = self.on_menu
            menu_btn = tk.Label(hdr, text="☰", bg=t.get("bg_hdr", "#ffb6c1"),
                                fg=t.get("fg_white", "#ffffff"),
                                font=("Segoe UI", 9, "bold"), cursor="hand2")
            menu_btn.pack(side="right")
            menu_btn.bind("<Button-1>", lambda e: on_m(close_win=self.win, hide_fn=self.hide))

        container = tk.Frame(self.win, bg=t["bg_card"])
        container.pack(fill="both", expand=True, padx=15, pady=5)

        # 1. Category Switcher
        tk.Label(
            container, text="Select Category:", bg=t["bg_card"],
            fg=t["fg_main"], font=("Georgia", 8, "bold")
        ).pack(anchor="w", pady=(2, 2))

        self.cat_var = tk.StringVar(value=CATEGORIES[0][1])
        cat_menu = tk.OptionMenu(
            container, self.cat_var, *[c[1] for c in CATEGORIES], command=self._on_category_changed
        )
        cat_menu.config(bg=t["btn"], fg=t["fg_white"], font=("Georgia", 8, "bold"), relief="flat", bd=0)
        cat_menu.pack(fill="x", pady=(0, 6))

        # 2. Dialogue Listbox
        self.listbox = tk.Listbox(
            container, bg=t.get("bg_grid", "#f0f0f0"), fg=t["fg_main"],
            font=("Georgia", 8), selectbackground=t.get("accent", "#e74c3c"),
            selectforeground=t["fg_white"], height=10, relief="flat", bd=0
        )
        self.listbox.pack(fill="both", expand=True, pady=(0, 6))
        self.listbox.bind("<<ListboxSelect>>", self._on_select_phrase)

        # 3. Text Entry
        entry_row = tk.Frame(container, bg=t["bg_card"])
        entry_row.pack(fill="x", pady=(0, 6))

        self.entry = tk.Entry(entry_row, font=("Georgia", 9), relief="solid", bd=1)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

        tk.Button(
            entry_row, text="✚ Add", font=("Georgia", 8, "bold"),
            bg=t["btn"], fg=t["fg_white"], relief="flat", command=self._add_phrase
        ).pack(side="right")

        # 4. Action Row (Edit, Delete, Reset Defaults)
        btn_frame = tk.Frame(self.win, bg=t["bg_card"])
        btn_frame.pack(fill="x", padx=15, pady=(0, 12))

        tk.Button(
            btn_frame, text="✏️ Update", font=("Georgia", 8, "bold"),
            bg=t["btn"], fg=t["fg_white"], relief="flat", command=self._edit_phrase
        ).pack(side="left", expand=True, fill="x", padx=(0, 2))

        tk.Button(
            btn_frame, text="🗑 Delete", font=("Georgia", 8, "bold"),
            bg=t["btn"], fg=t["fg_white"], relief="flat", command=self._delete_phrase
        ).pack(side="left", expand=True, fill="x", padx=(2, 2))

        tk.Button(
            btn_frame, text="Done", font=("Georgia", 8, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t["fg_white"], relief="flat", command=self.win.destroy
        ).pack(side="right", expand=True, fill="x", padx=(2, 0))

        self._refresh_list()

    def _get_key_from_label(self, label):
        for key, text in CATEGORIES:
            if text == label:
                return key
        return "idle_messages"

    def _on_category_changed(self, selected_label: Any = None) -> None:
        lbl_str = str(selected_label.get() if hasattr(selected_label, "get") else selected_label)
        self.active_category = self._get_key_from_label(lbl_str)
        if self.entry is not None:
            self.entry.delete(0, tk.END)
        self._refresh_list()

    def _refresh_list(self) -> None:
        if self.listbox is None:
            return
        self.listbox.delete(0, tk.END)
        data = self.get_data()
        phrases = data.get(self.active_category, [])
        for p in phrases:
            self.listbox.insert(tk.END, f"• {p}")

    def _on_select_phrase(self, event: Any) -> None:
        if self.listbox is None or self.entry is None:
            return
        sel = self.listbox.curselection()
        if not sel:
            return
        data = self.get_data()
        phrases = data.get(self.active_category, [])
        if sel[0] < len(phrases):
            self.entry.delete(0, tk.END)
            self.entry.insert(0, phrases[sel[0]])

    def _add_phrase(self) -> None:
        if self.entry is None:
            return
        text = self.entry.get().strip()
        if not text:
            return

        data = self.get_data()
        phrases = list(data.get(self.active_category, []))
        phrases.append(text)
        data[self.active_category] = phrases
        self.save_data(data)

        self.entry.delete(0, tk.END)
        self._refresh_list()
        if self.on_update:
            self.on_update()

    def _edit_phrase(self) -> None:
        if self.listbox is None or self.entry is None:
            return
        sel = self.listbox.curselection()
        if not sel:
            parent_win: tk.Misc = self.win if self.win is not None else self.root
            messagebox.showinfo("Select Line", "Please select a line from the list to update.", parent=parent_win)
            return

        new_text = self.entry.get().strip()
        if not new_text:
            return

        data = self.get_data()
        phrases = list(data.get(self.active_category, []))
        idx = sel[0]
        if idx < len(phrases):
            phrases[idx] = new_text
            data[self.active_category] = phrases
            self.save_data(data)
            self._refresh_list()
            self.listbox.select_set(idx)
            if self.on_update:
                self.on_update()

    def _delete_phrase(self) -> None:
        if self.listbox is None or self.entry is None:
            return
        sel = self.listbox.curselection()
        if not sel:
            return

        data = self.get_data()
        phrases = list(data.get(self.active_category, []))
        idx = sel[0]
        if idx < len(phrases):
            phrases.pop(idx)
            data[self.active_category] = phrases
            self.save_data(data)
            self.entry.delete(0, tk.END)
            self._refresh_list()
            if self.on_update:
                self.on_update()