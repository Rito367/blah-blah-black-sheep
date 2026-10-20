"""
reminder_window.py
Redesigned reminders popup with a 12-hour clock picker (AM/PM) and clean UI styling.
"""

import re
import tkinter as tk
from datetime import datetime
from pathlib import Path
import sys

try:
    import paths
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import paths

import themes


def parse_to_hour_minute_24(t_str: str) -> tuple[int, int] | None:
    """Parses any time format ('14:30', '14:02 PM', '02:30 PM', '2 PM', '14') into (hour_24, minute)."""
    raw = (t_str or "").strip().upper()
    if not raw:
        return None

    # Strip malformed AM/PM if 24h hour >= 13 was combined with suffix
    match_24_suffix = re.match(r"^(\d{1,2}):(\d{2})\s*(AM|PM)?$", raw)
    if match_24_suffix:
        h = int(match_24_suffix.group(1))
        m = int(match_24_suffix.group(2))
        suffix = match_24_suffix.group(3)
        if h >= 13:
            return h, m
        if suffix == "PM" and h < 12:
            return h + 12, m
        if suffix == "AM" and h == 12:
            return 0, m
        return h, m

    formats_to_try = [
        "%H:%M",
        "%H:%M:%S",
        "%I:%M %p",
        "%I %p",
        "%I:%M%p",
        "%I%p",
        "%H",
    ]
    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.hour, dt.minute
        except ValueError:
            continue
    return None


class ReminderWindow:
    def __init__(self, root, get_data, save_data, on_trigger=None, on_menu=None):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.on_trigger = on_trigger
        self.on_menu = on_menu
        self.win = None
        self._last_triggered = {}

        self._check_reminders_loop()

    def _check_reminders_loop(self):
        now = datetime.now()
        cur_h = now.hour
        cur_m = now.minute
        today_str = now.strftime("%Y-%m-%d")

        reminders = self.get_data().get("reminders", [])
        for idx, r in enumerate(reminders):
            if isinstance(r, dict):
                if not r.get("enabled", True):
                    continue

                r_time = r.get("time", "").strip()
                r_text = r.get("text", "").strip()

                parsed = parse_to_hour_minute_24(r_time)
                if parsed is not None:
                    target_h, target_m = parsed
                    if target_h == cur_h and target_m == cur_m:
                        key = (idx, target_h, target_m, today_str)
                        if self._last_triggered.get(key) != today_str:
                            self._last_triggered[key] = today_str
                            if self.on_trigger:
                                self.on_trigger(r_text)

        self.root.after(3000, self._check_reminders_loop)

    def _toggle_ampm(self):
        curr = self.ampm_var.get()
        self.ampm_var.set("AM" if curr == "PM" else "PM")

    def hide(self):
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None

    def toggle(self, near_x=100, near_y=100):
        if self.win and self.win.winfo_exists():
            self.hide()
        else:
            self.show(near_x, near_y)

    def show(self, near_x=100, near_y=100):
        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        t = themes.get()
        self.win = tk.Toplevel(self.root)
        self.win.title("Reminders")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 320, 420
        safe_x = max(10, min(near_x, sw - target_w - 10))
        safe_y = max(10, min(near_y, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("border", "#181920"), padx=2, pady=2)
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        outer = tk.Frame(self.win, bg=t.get("bg_card", "#20222e"), padx=12, pady=10)
        outer.pack(fill="both", expand=True)

        # Header Bar
        hdr = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        hdr.pack(fill="x", pady=(0, 8))

        tk.Label(
            hdr, text="🔔 DAILY REMINDERS", bg=t.get("bg_card", "#20222e"),
            fg=t.get("accent", "#e74c3c"), font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        close_btn = tk.Label(
            hdr, text="✕", bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.hide())

        if self.on_menu:
            on_menu = self.on_menu
            mb = tk.Label(hdr, text="☰", bg=t.get("bg_card", "#20222e"),
                          fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 9, "bold"), cursor="hand2")
            mb.pack(side="right", padx=(0, 6))
            mb.bind("<Button-1>", lambda e: on_menu(close_win=self.win, hide_fn=self.hide))

        # Listbox for Reminders
        self.listbox = tk.Listbox(
            outer, bg=t.get("bg_grid", "#151620"), fg=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 8), selectbackground=t.get("accent", "#e74c3c"),
            selectforeground=t.get("fg_white", "#ffffff"), height=7, relief="flat", bd=0,
            highlightthickness=0
        )
        self.listbox.pack(fill="both", expand=True, pady=(0, 8))
        self.listbox.bind("<<ListboxSelect>>", self._on_select_reminder)
        self.listbox.bind("<Double-Button-1>", lambda event: self._toggle_reminder())

        # Input Card Area
        input_box = tk.Frame(outer, bg=t.get("bg_grid", "#181924"), padx=8, pady=8)
        input_box.pack(fill="x", pady=(0, 8))

        # Row 1: Time Pickers (12-Hour Clock + AM/PM Toggle)
        time_row = tk.Frame(input_box, bg=t.get("bg_grid", "#181924"))
        time_row.pack(fill="x", pady=(0, 6))

        tk.Label(
            time_row, text="Time:", bg=t.get("bg_grid", "#181924"),
            fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8, "bold")
        ).pack(side="left", padx=(0, 6))

        now = datetime.now()
        hour_12 = int(now.strftime("%I"))

        self.hour_spin = tk.Spinbox(
            time_row, from_=1, to=12, width=3, format="%02.0f", font=("Consolas", 10, "bold"),
            bg=t.get("bg_card", "#20222e"), fg=t.get("fg_white", "#ffffff"), relief="flat", bd=0,
            justify="center", highlightthickness=0
        )
        self.hour_spin.delete(0, tk.END)
        self.hour_spin.insert(0, f"{hour_12:02d}")
        self.hour_spin.pack(side="left")

        tk.Label(
            time_row, text=":", bg=t.get("bg_grid", "#181924"),
            fg=t.get("fg_white", "#ffffff"), font=("Consolas", 10, "bold")
        ).pack(side="left", padx=3)

        self.min_spin = tk.Spinbox(
            time_row, from_=0, to=59, width=3, format="%02.0f", font=("Consolas", 10, "bold"),
            bg=t.get("bg_card", "#20222e"), fg=t.get("fg_white", "#ffffff"), relief="flat", bd=0,
            justify="center", highlightthickness=0
        )
        self.min_spin.delete(0, tk.END)
        self.min_spin.insert(0, f"{now.minute:02d}")
        self.min_spin.pack(side="left")

        self.ampm_var = tk.StringVar(value=now.strftime("%p"))
        self.ampm_btn = tk.Button(
            time_row, textvariable=self.ampm_var, font=("Segoe UI", 8, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"), relief="flat", bd=0,
            padx=6, cursor="hand2", command=self._toggle_ampm
        )
        self.ampm_btn.pack(side="left", padx=(6, 0))

        # Row 2: Message Entry
        self.entry = tk.Entry(
            input_box, font=("Segoe UI", 8), bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_white", "#ffffff"), insertbackground=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0
        )
        self.entry.pack(fill="x", pady=(0, 6), ipady=3)

        # Row 3: Add Button
        tk.Button(
            input_box, text="✚ Add Reminder", font=("Segoe UI", 8, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, pady=3, cursor="hand2", command=self._add_reminder
        ).pack(fill="x")

        # Bottom Action Bar
        btn_frame = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        btn_frame.pack(fill="x")

        tk.Button(
            btn_frame, text="🔔 On / Off", font=("Segoe UI", 8, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, pady=3, cursor="hand2", command=self._toggle_reminder
        ).pack(side="left", expand=True, fill="x", padx=(0, 2))

        tk.Button(
            btn_frame, text="🗑 Delete", font=("Segoe UI", 8, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, pady=3, cursor="hand2", command=self._delete_reminder
        ).pack(side="left", expand=True, fill="x", padx=(2, 2))

        tk.Button(
            btn_frame, text="💬 Say Now", font=("Segoe UI", 8, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, pady=3, cursor="hand2", command=self._trigger_reminder
        ).pack(side="right", expand=True, fill="x", padx=(2, 0))

        self._refresh_list()

    def _on_select_reminder(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        index = sel[0]
        reminders = self.get_data().get("reminders", [])
        if index < len(reminders):
            r = reminders[index]
            if isinstance(r, dict):
                saved_time = r.get("time", "")
                parsed = parse_to_hour_minute_24(saved_time)
                if parsed:
                    h_24, m = parsed
                    ampm = "PM" if h_24 >= 12 else "AM"
                    h_12 = h_24 % 12
                    if h_12 == 0:
                        h_12 = 12

                    self.hour_spin.delete(0, tk.END)
                    self.hour_spin.insert(0, f"{h_12:02d}")
                    self.min_spin.delete(0, tk.END)
                    self.min_spin.insert(0, f"{m:02d}")
                    self.ampm_var.set(ampm)

                self.entry.delete(0, tk.END)
                self.entry.insert(0, r.get("text", ""))

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for r in self.get_data().get("reminders", []):
            if isinstance(r, dict):
                status = "🔔" if r.get("enabled", True) else "🔕"
                t_str = r.get("time", "")
                parsed = parse_to_hour_minute_24(t_str)
                if parsed:
                    h_24, m = parsed
                    ampm = "PM" if h_24 >= 12 else "AM"
                    h_12 = h_24 % 12
                    if h_12 == 0:
                        h_12 = 12
                    display_time = f"[{h_12:02d}:{m:02d} {ampm}] "
                else:
                    display_time = f"[{t_str}] "

                self.listbox.insert(tk.END, f" {status}  {display_time}{r.get('text', '')}")
            else:
                self.listbox.insert(tk.END, f" 🔔  {str(r)}")

    def _add_reminder(self):
        text = self.entry.get().strip()
        if not text:
            return

        try:
            h_12 = int(self.hour_spin.get().strip())
            m = int(self.min_spin.get().strip())
            h_12 = max(1, min(12, h_12))
            m = max(0, min(59, m))
        except ValueError:
            now = datetime.now()
            h_12 = int(now.strftime("%I"))
            m = now.minute

        ampm = self.ampm_var.get().strip().upper()
        if ampm == "PM" and h_12 < 12:
            h_24 = h_12 + 12
        elif ampm == "AM" and h_12 == 12:
            h_24 = 0
        else:
            h_24 = h_12

        time_val = f"{h_24:02d}:{m:02d}"

        data = self.get_data()
        reminders = data.get("reminders", [])
        reminders.append({"time": time_val, "text": text, "enabled": True})
        data["reminders"] = reminders
        self.save_data(data)

        self.entry.delete(0, tk.END)
        self._refresh_list()

    def _toggle_reminder(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        index = sel[0]
        data = self.get_data()
        reminders = data.get("reminders", [])
        if index < len(reminders):
            r = reminders[index]
            if isinstance(r, dict):
                r["enabled"] = not r.get("enabled", True)
            else:
                # Bug #26 fix: convert legacy string to dict keeping it ENABLED so it still works
                reminders[index] = {"time": "", "text": str(r), "enabled": True}
            data["reminders"] = reminders
            self.save_data(data)
            self._refresh_list()
            self.listbox.select_set(index)

    def _delete_reminder(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        data = self.get_data()
        reminders = data.get("reminders", [])
        reminders.pop(sel[0])
        data["reminders"] = reminders
        self.save_data(data)
        self.entry.delete(0, tk.END)
        self._refresh_list()

    def _trigger_reminder(self):
        sel = self.listbox.curselection()
        reminders = self.get_data().get("reminders", [])
        if sel:
            r = reminders[sel[0]]
        elif reminders:
            r = reminders[0]
        else:
            msg = "No reminders set!"
            if self.on_trigger:
                self.on_trigger(msg)
            return

        if isinstance(r, dict):
            msg = r.get("text", "")
        else:
            msg = str(r)

        if self.on_trigger:
            self.on_trigger(msg)