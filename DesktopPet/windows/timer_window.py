"""
timer_window.py
Modern countdown timer with multi-mode duration views:
- Workdays Only (Excludes Weekends & Public Holidays)
- Calendar Time (Total standard days & time)
- Breakdown View (Shows workdays, weekends, and holidays separately)
- Interactive Date Picker (Month/Year calendar popup)
- 12-Hour Time Spinboxes (HH : MM) with AM/PM toggle button
"""

import calendar
import tkinter as tk
from datetime import date, datetime, timedelta
from typing import Callable
from pathlib import Path
import sys

try:
    import paths
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import paths

import themes

# 2026 Singapore Public Holidays (YYYY-MM-DD)
DEFAULT_HOLIDAYS = [
    "2026-01-01",  # New Year's Day
    "2026-02-17",  # Chinese New Year
    "2026-02-18",  # Chinese New Year Day 2
    "2026-03-20",  # Hari Raya Puasa
    "2026-04-03",  # Good Friday
    "2026-05-01",  # Labour Day
    "2026-05-27",  # Hari Raya Haji
    "2026-05-31",  # Vesak Day
    "2026-06-01",  # Vesak Day observed
    "2026-08-09",  # National Day
    "2026-08-10",  # National Day observed
    "2026-11-08",  # Deepavali
    "2026-11-09",  # Deepavali observed
    "2026-12-25",  # Christmas Day
]


class TimerWindow:
    def __init__(self, root: tk.Tk, get_data: Callable, save_data: Callable, on_alarm: Callable | None = None, on_menu: Callable | None = None):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.on_alarm = on_alarm
        self.on_menu  = on_menu   # signature: on_menu(close_win=None, hide_fn=None)
        self._visible = False
        self._drawer_open = False
        self._cal_popup = None

        self.win = tk.Toplevel(root)
        self.win.title("Countdown")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        self.win.withdraw()

        self._dx = self._dy = 0
        self.win.bind("<ButtonPress-1>", self._drag_start)
        self.win.bind("<B1-Motion>", self._drag_move)

        self._build()
        self._tick()

    def _drag_start(self, event):
        self._dx = event.x_root - self.win.winfo_x()
        self._dy = event.y_root - self.win.winfo_y()

    def _drag_move(self, event):
        self.win.geometry(f"+{event.x_root - self._dx}+{event.y_root - self._dy}")

    def _get_holidays(self) -> set:
        data = self.get_data()
        holiday_list = data.get("holidays", DEFAULT_HOLIDAYS)
        return {datetime.strptime(h, "%Y-%m-%d").date() for h in holiday_list}

    def _calc_day_breakdown(self, start_dt: datetime, end_dt: datetime) -> dict:
        holidays = self._get_holidays()
        curr_d = start_dt.date()
        end_d = end_dt.date()

        workdays = 0
        weekend_days = 0
        ph_days = 0

        while curr_d <= end_d:
            if curr_d.weekday() >= 5:
                weekend_days += 1
            elif curr_d in holidays:
                ph_days += 1
            else:
                workdays += 1
            curr_d += timedelta(days=1)

        return {
            "workdays": workdays,
            "weekend_days": weekend_days,
            "ph_days": ph_days
        }

    def _calc_workday_time_left(self, start_dt: datetime, end_dt: datetime) -> tuple[int, int, int, int]:
        if start_dt >= end_dt:
            return 0, 0, 0, 0

        holidays = self._get_holidays()

        if start_dt.date() == end_dt.date():
            d = start_dt.date()
            if d.weekday() < 5 and d not in holidays:
                diff = end_dt - start_dt
                hours, rem = divmod(diff.seconds, 3600)
                mins, secs = divmod(rem, 60)
                return 0, hours, mins, secs
            return 0, 0, 0, 0

        work_days = 0
        curr_d = start_dt.date() + timedelta(days=1)
        end_d = end_dt.date()

        while curr_d < end_d:
            if curr_d.weekday() < 5 and curr_d not in holidays:
                work_days += 1
            curr_d += timedelta(days=1)

        start_seconds = 0
        d_start = start_dt.date()
        if d_start.weekday() < 5 and d_start not in holidays:
            end_of_start_day = datetime.combine(d_start, datetime.max.time())
            start_seconds = int((end_of_start_day - start_dt).total_seconds())

        end_seconds = 0
        d_end = end_dt.date()
        if d_end.weekday() < 5 and d_end not in holidays:
            start_of_end_day = datetime.combine(d_end, datetime.min.time())
            end_seconds = int((end_dt - start_of_end_day).total_seconds())

        total_partial_secs = start_seconds + end_seconds
        extra_days, rem_secs = divmod(total_partial_secs, 86400)
        work_days += extra_days
        hours, rem = divmod(rem_secs, 3600)
        mins, secs = divmod(rem, 60)

        return work_days, hours, mins, secs

    def _build(self):
        for w in self.win.winfo_children():
            w.destroy()

        t = themes.get()
        self.win.configure(bg=t.get("border", "#181920"))

        self.outer = tk.Frame(self.win, bg=t.get("bg_card", "#20222e"), padx=8, pady=8)
        self.outer.pack(fill="both", expand=True)

        # ── Header Bar ──
        hdr = tk.Frame(self.outer, bg=t.get("bg_card", "#20222e"))
        hdr.pack(fill="x", pady=(0, 4))

        self.mode_tag_lbl = tk.Label(
            hdr, text="⏱ COUNTDOWN", bg=t.get("bg_card", "#20222e"),
            fg=t.get("accent", "#e74c3c"), font=("Segoe UI", 8, "bold")
        )
        self.mode_tag_lbl.pack(side="left")

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
            mb.bind("<Button-1>", lambda e: on_menu(None, self.hide))

        # ── Mode Switcher Bar ──
        mode_bar = tk.Frame(self.outer, bg=t.get("bg_grid", "#151620"), padx=2, pady=2)
        mode_bar.pack(fill="x", pady=(0, 6))

        self.mode_btns = {}
        for mode_key, mode_label in [("workdays", "Workdays"), ("calendar", "Calendar (All Days)")]:
            btn = tk.Button(
                mode_bar, text=mode_label, font=("Segoe UI", 7, "bold"),
                relief="flat", bd=0, padx=6, pady=2, cursor="hand2",
                command=lambda m=mode_key: self._set_mode(m)
            )
            btn.pack(side="left", expand=True, fill="x", padx=1)
            self.mode_btns[mode_key] = btn

        # ── Event Title & Switcher ──
        nav = tk.Frame(self.outer, bg=t.get("bg_card", "#20222e"))
        nav.pack(fill="x", pady=(0, 6))

        prev_btn = tk.Button(
            nav, text="‹", bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 11, "bold"), relief="flat", bd=0, width=2, cursor="hand2",
            command=self._prev_event
        )
        prev_btn.pack(side="left")

        self.title_lbl = tk.Label(
            nav, text="No Target Set", bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_white", "#ffffff"), font=("Segoe UI", 11, "bold")
        )
        self.title_lbl.pack(side="left", expand=True, padx=4)

        next_btn = tk.Button(
            nav, text="›", bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 11, "bold"), relief="flat", bd=0, width=2, cursor="hand2",
            command=self._next_event
        )
        next_btn.pack(side="right")

        # ── Digital Tiles Display ──
        tiles_frame = tk.Frame(self.outer, bg=t.get("bg_card", "#20222e"))
        tiles_frame.pack(fill="x", pady=(0, 4))

        self.tile_d = self._create_tile(tiles_frame, t, "00", "DAYS")
        self.tile_h = self._create_tile(tiles_frame, t, "00", "HRS")
        self.tile_m = self._create_tile(tiles_frame, t, "00", "MIN")
        self.tile_s = self._create_tile(tiles_frame, t, "00", "SEC")

        self.tile_d[0].pack(side="left", expand=True, padx=2)
        self.tile_h[0].pack(side="left", expand=True, padx=2)
        self.tile_m[0].pack(side="left", expand=True, padx=2)
        self.tile_s[0].pack(side="left", expand=True, padx=2)

        # ── Breakdown Banner ──
        self.breakdown_frame = tk.Frame(self.outer, bg=t.get("bg_grid", "#151620"), padx=4, pady=3)
        self.breakdown_frame.pack(fill="x", pady=(0, 4))

        self.breakdown_lbl = tk.Label(
            self.breakdown_frame, text="💼 -- Workdays  |  🌴 -- Wknds  |  🎉 -- PH",
            bg=t.get("bg_grid", "#151620"), fg=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 7)
        )
        self.breakdown_lbl.pack()

        # ── Progress Bar & Target Date ──
        self.prog_canvas = tk.Canvas(
            self.outer, height=4, bg=t.get("bg_grid", "#15161e"), highlightthickness=0
        )
        self.prog_canvas.pack(fill="x", padx=2, pady=(0, 4))

        self.target_date_lbl = tk.Label(
            self.outer, text="---- / -- / --  --:--:--", bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_dim", "#888888"), font=("Segoe UI", 7)
        )
        self.target_date_lbl.pack(pady=(0, 4))

        # ── Drawer Button ──
        self.toggle_drawer_btn = tk.Button(
            self.outer, text="⚙ Options & Edit Target ▼", font=("Segoe UI", 7, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, pady=2, command=self._toggle_drawer
        )
        self.toggle_drawer_btn.pack(fill="x", pady=(0, 2))

        # ── Drawer Frame ──
        self.drawer_frame = tk.Frame(self.outer, bg=t.get("bg_grid", "#181924"), padx=6, pady=6)

        # 1. Target Name
        tk.Label(self.drawer_frame, text="Name:", bg=t.get("bg_grid", "#181924"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 7, "bold")).grid(row=0, column=0, sticky="w", pady=3)
        self.name_entry = tk.Entry(self.drawer_frame, font=("Segoe UI", 8), bg=t.get("bg_card", "#20222e"), fg=t.get("fg_white", "#ffffff"), relief="flat")
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=3)

        # 2. Date Picker (Interactive Calendar Trigger)
        tk.Label(self.drawer_frame, text="Date:", bg=t.get("bg_grid", "#181924"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 7, "bold")).grid(row=1, column=0, sticky="w", pady=3)
        
        date_picker_frame = tk.Frame(self.drawer_frame, bg=t.get("bg_grid", "#181924"))
        date_picker_frame.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=3)

        self.selected_date_str = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_btn = tk.Button(
            date_picker_frame, textvariable=self.selected_date_str, font=("Segoe UI", 8, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"), relief="flat", bd=0,
            padx=6, pady=2, cursor="hand2", command=self._open_calendar_picker
        )
        self.date_btn.pack(side="left", fill="x", expand=True)

        cal_icon_btn = tk.Button(
            date_picker_frame, text="📅", font=("Segoe UI", 8),
            bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"), relief="flat", bd=0,
            padx=4, cursor="hand2", command=self._open_calendar_picker
        )
        cal_icon_btn.pack(side="left", padx=(3, 0))

        # 3. 12-Hour Clock & AM/PM Selector
        tk.Label(self.drawer_frame, text="Time:", bg=t.get("bg_grid", "#181924"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 7, "bold")).grid(row=2, column=0, sticky="w", pady=3)
        
        time_picker_frame = tk.Frame(self.drawer_frame, bg=t.get("bg_grid", "#181924"))
        time_picker_frame.grid(row=2, column=1, sticky="w", padx=(4, 0), pady=3)

        self.hour_spin = tk.Spinbox(
            time_picker_frame, from_=1, to=12, width=3, format="%02.0f", font=("Consolas", 8, "bold"),
            bg=t.get("bg_card", "#20222e"), fg=t.get("fg_white", "#ffffff"), relief="flat", bd=0, justify="center"
        )
        self.hour_spin.pack(side="left")

        tk.Label(time_picker_frame, text=":", bg=t.get("bg_grid", "#181924"), fg=t.get("fg_white", "#ffffff"), font=("Segoe UI", 8, "bold")).pack(side="left", padx=2)

        self.min_spin = tk.Spinbox(
            time_picker_frame, from_=0, to=59, width=3, format="%02.0f", font=("Consolas", 8, "bold"),
            bg=t.get("bg_card", "#20222e"), fg=t.get("fg_white", "#ffffff"), relief="flat", bd=0, justify="center"
        )
        self.min_spin.pack(side="left")

        self.ampm_var = tk.StringVar(value="PM")
        self.ampm_btn = tk.Button(
            time_picker_frame, textvariable=self.ampm_var, font=("Segoe UI", 8, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"), relief="flat", bd=0,
            padx=5, cursor="hand2", command=self._toggle_ampm
        )
        self.ampm_btn.pack(side="left", padx=(6, 0))

        self.drawer_frame.columnconfigure(1, weight=1)

        # Drawer Actions
        act_frame = tk.Frame(self.drawer_frame, bg=t.get("bg_grid", "#181924"))
        act_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 2))

        tk.Button(
            act_frame, text="✚ Save", font=("Segoe UI", 7, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, command=self._save_event
        ).pack(side="left", expand=True, fill="x", padx=(0, 2))

        tk.Button(
            act_frame, text="🗑 Delete", font=("Segoe UI", 7, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, command=self._delete_event
        ).pack(side="right", expand=True, fill="x", padx=(2, 0))

        self._update_mode_buttons()
        self._load_current_event_to_form()

    def _create_tile(self, parent, t, val: str, label: str):
        tile = tk.Frame(parent, bg=t.get("bg_grid", "#151620"), padx=4, pady=4, width=48)
        num_lbl = tk.Label(
            tile, text=val, bg=t.get("bg_grid", "#151620"),
            fg=t.get("fg_white", "#ffffff"), font=("Consolas", 14, "bold")
        )
        num_lbl.pack()

        unit_lbl = tk.Label(
            tile, text=label, bg=t.get("bg_grid", "#151620"),
            fg=t.get("accent", "#e74c3c"), font=("Segoe UI", 6, "bold")
        )
        unit_lbl.pack()
        return (tile, num_lbl, unit_lbl)

    def _toggle_ampm(self):
        curr = self.ampm_var.get()
        self.ampm_var.set("AM" if curr == "PM" else "PM")

    def _open_calendar_picker(self):
        if self._cal_popup and self._cal_popup.winfo_exists():
            self._cal_popup.lift()
            return

        try:
            curr_d = datetime.strptime(self.selected_date_str.get(), "%Y-%m-%d").date()
        except ValueError:
            curr_d = date.today()

        self.cal_year = curr_d.year
        self.cal_month = curr_d.month

        t = themes.get()
        self._cal_popup = tk.Toplevel(self.win)
        self._cal_popup.title("Select Date")
        self._cal_popup.overrideredirect(True)
        self._cal_popup.attributes("-topmost", True)
        self._cal_popup.configure(bg=t.get("border", "#181920"), padx=2, pady=2)

        x = self.win.winfo_x() + 20
        y = self.win.winfo_y() + 60
        self._cal_popup.geometry(f"+{x}+{y}")

        self._render_calendar_popup(t)

    def _render_calendar_popup(self, t):
        if self._cal_popup is None:
            return
        for w in self._cal_popup.winfo_children():
            w.destroy()

        outer = tk.Frame(self._cal_popup, bg=t.get("bg_card", "#20222e"), padx=8, pady=8)
        outer.pack(fill="both", expand=True)

        # Nav row
        nav_frame = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        nav_frame.pack(fill="x", pady=(0, 6))

        tk.Button(
            nav_frame, text="‹", bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0, width=2,
            command=self._prev_cal_month
        ).pack(side="left")

        month_title = f"{calendar.month_name[self.cal_month]} {self.cal_year}"
        tk.Label(
            nav_frame, text=month_title, bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_white", "#ffffff"), font=("Segoe UI", 9, "bold")
        ).pack(side="left", expand=True)

        tk.Button(
            nav_frame, text="›", bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0, width=2,
            command=self._next_cal_month
        ).pack(side="right")

        # Weekday headers
        days_frame = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        days_frame.pack(fill="x")

        for idx, day_str in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            fg_col = t.get("accent", "#e74c3c") if idx >= 5 else t.get("fg_dim", "#888888")
            tk.Label(
                days_frame, text=day_str, bg=t.get("bg_card", "#20222e"),
                fg=fg_col, font=("Segoe UI", 7, "bold"), width=3
            ).grid(row=0, column=idx, padx=1, pady=2)

        # Month calendar grid
        cal = calendar.monthcalendar(self.cal_year, self.cal_month)
        today = date.today()

        for r_idx, week in enumerate(cal):
            for c_idx, day_num in enumerate(week):
                if day_num == 0:
                    continue

                d_obj = date(self.cal_year, self.cal_month, day_num)
                is_selected = (d_obj.strftime("%Y-%m-%d") == self.selected_date_str.get())
                is_today = (d_obj == today)

                btn_bg = t.get("accent", "#e74c3c") if is_selected else (t.get("btn", "#2c2e3f") if is_today else t.get("bg_grid", "#151620"))
                btn_fg = t.get("fg_white", "#ffffff")

                btn = tk.Button(
                    days_frame, text=str(day_num), font=("Segoe UI", 7, "bold" if (is_selected or is_today) else "normal"),
                    bg=btn_bg, fg=btn_fg, relief="flat", bd=0, width=3, cursor="hand2",
                    command=lambda d=d_obj: self._select_date(d)
                )
                btn.grid(row=r_idx + 1, column=c_idx, padx=1, pady=1)

        # Cancel button
        tk.Button(
            outer, text="Cancel", font=("Segoe UI", 7, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, pady=2, command=lambda: self._cal_popup.destroy() if self._cal_popup else None
        ).pack(fill="x", pady=(6, 0))

    def _prev_cal_month(self):
        self.cal_month -= 1
        if self.cal_month < 1:
            self.cal_month = 12
            self.cal_year -= 1
        self._render_calendar_popup(themes.get())

    def _next_cal_month(self):
        self.cal_month += 1
        if self.cal_month > 12:
            self.cal_month = 1
            self.cal_year += 1
        self._render_calendar_popup(themes.get())

    def _select_date(self, d_obj: date):
        self.selected_date_str.set(d_obj.strftime("%Y-%m-%d"))
        if self._cal_popup and self._cal_popup.winfo_exists():
            self._cal_popup.destroy()

    def _set_mode(self, mode: str):
        data = self.get_data()
        data["countdown_mode"] = mode
        self.save_data(data)
        self._update_mode_buttons()
        self._update_display()

    def _update_mode_buttons(self):
        t = themes.get()
        data = self.get_data()
        current_mode = data.get("countdown_mode", "workdays")

        for k, btn in self.mode_btns.items():
            if k == current_mode:
                btn.config(bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"))
            else:
                btn.config(bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_dim", "#888888"))

    def _toggle_drawer(self):
        self._drawer_open = not self._drawer_open
        if self._drawer_open:
            self.drawer_frame.pack(fill="x", pady=(4, 0))
            self.toggle_drawer_btn.config(text="⚙ Close Drawer ▲")
        else:
            self.drawer_frame.pack_forget()
            self.toggle_drawer_btn.config(text="⚙ Options & Edit Target ▼")
            if self._cal_popup and self._cal_popup.winfo_exists():
                self._cal_popup.destroy()
        self.win.update_idletasks()

    def _get_active_event(self):
        data = self.get_data()
        events = data.get("countdown_events", [])
        idx = data.get("active_event_index", 0)
        if 0 <= idx < len(events):
            return events[idx], idx
        elif events:
            data["active_event_index"] = 0
            self.save_data(data)
            return events[0], 0
        return None, 0

    def _load_current_event_to_form(self):
        event, _ = self._get_active_event()
        if not hasattr(self, "name_entry"):
            return

        self.name_entry.delete(0, tk.END)

        if event:
            self.name_entry.insert(0, event.get("label", ""))
            dt_str = event.get("datetime", "")
            try:
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                self.selected_date_str.set(dt_obj.strftime("%Y-%m-%d"))
                hour_12 = dt_obj.strftime("%I").lstrip("0") or "12"
                self.hour_spin.delete(0, tk.END)
                self.hour_spin.insert(0, f"{int(hour_12):02d}")
                self.min_spin.delete(0, tk.END)
                self.min_spin.insert(0, dt_obj.strftime("%M"))
                self.ampm_var.set(dt_obj.strftime("%p"))
            except ValueError:
                self.selected_date_str.set(datetime.now().strftime("%Y-%m-%d"))
                self.hour_spin.delete(0, tk.END)
                self.hour_spin.insert(0, "06")
                self.min_spin.delete(0, tk.END)
                self.min_spin.insert(0, "00")
                self.ampm_var.set("PM")
        else:
            self.name_entry.insert(0, "New Goal")
            self.selected_date_str.set(datetime.now().strftime("%Y-%m-%d"))
            self.hour_spin.delete(0, tk.END)
            self.hour_spin.insert(0, "06")
            self.min_spin.delete(0, tk.END)
            self.min_spin.insert(0, "00")
            self.ampm_var.set("PM")

    def _prev_event(self):
        data = self.get_data()
        events = data.get("countdown_events", [])
        if events:
            idx = (data.get("active_event_index", 0) - 1) % len(events)
            data["active_event_index"] = idx
            self.save_data(data)
            self._load_current_event_to_form()
            self._update_display()

    def _next_event(self):
        data = self.get_data()
        events = data.get("countdown_events", [])
        if events:
            idx = (data.get("active_event_index", 0) + 1) % len(events)
            data["active_event_index"] = idx
            self.save_data(data)
            self._load_current_event_to_form()
            self._update_display()

    def _save_event(self):
        name = self.name_entry.get().strip() or "Untitled Event"
        d_str = self.selected_date_str.get().strip()
        
        try:
            h_val = int(self.hour_spin.get().strip())
            m_val = int(self.min_spin.get().strip())
        except ValueError:
            h_val, m_val = 6, 0

        ampm_val = self.ampm_var.get().strip()
        time_12_str = f"{h_val:02d}:{m_val:02d} {ampm_val}"

        try:
            parsed_time = datetime.strptime(time_12_str, "%I:%M %p").time()
            full_dt = f"{d_str} {parsed_time.strftime('%H:%M:%S')}"
            datetime.strptime(full_dt, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return

        data = self.get_data()
        events = data.get("countdown_events", [])
        idx = data.get("active_event_index", 0)

        new_obj = {"label": name, "datetime": full_dt}

        if 0 <= idx < len(events):
            events[idx] = new_obj
        else:
            events.append(new_obj)
            data["active_event_index"] = len(events) - 1

        data["countdown_events"] = events
        self.save_data(data)
        self._toggle_drawer()
        self._update_display()

    def _delete_event(self):
        data = self.get_data()
        events = data.get("countdown_events", [])
        idx = data.get("active_event_index", 0)

        if 0 <= idx < len(events):
            events.pop(idx)
            data["active_event_index"] = max(0, idx - 1)
            data["countdown_events"] = events
            self.save_data(data)
            self._load_current_event_to_form()
            self._toggle_drawer()
            self._update_display()

    def _update_display(self):
        event, _ = self._get_active_event()
        t = themes.get()
        data = self.get_data()
        mode = data.get("countdown_mode", "workdays")

        if mode == "workdays":
            self.mode_tag_lbl.config(text="💼 WORKDAYS (NO WKND/PH)")
            self.tile_d[2].config(text="WORK DAYS")
        else:
            self.mode_tag_lbl.config(text="📅 TOTAL CALENDAR DAYS")
            self.tile_d[2].config(text="DAYS")

        if not event:
            self.title_lbl.config(text="No Target Set")
            for t_tuple in (self.tile_d, self.tile_h, self.tile_m, self.tile_s):
                t_tuple[1].config(text="00")
            self.breakdown_lbl.config(text="💼 -- Workdays  |  🌴 -- Wknds  |  🎉 -- PH")
            self.target_date_lbl.config(text="Open Drawer to Add")
            self.prog_canvas.delete("all")
            return

        self.title_lbl.config(text=event.get("label", "Untitled"))
        dt_str = event.get("datetime", "")

        try:
            target_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return

        now = datetime.now()

        if target_dt <= now:
            for t_tuple in (self.tile_d, self.tile_h, self.tile_m, self.tile_s):
                t_tuple[1].config(text="--")
            self.target_date_lbl.config(text="✦ Target Reached! ✦")
            self.breakdown_lbl.config(text="🎉 Event Completed!")
            self._draw_progress(1.0, t.get("accent", "#e74c3c"))
            return

        self.target_date_lbl.config(text=target_dt.strftime("Target: %b %d, %Y at %I:%M %p"))

        breakdown = self._calc_day_breakdown(now, target_dt)
        self.breakdown_lbl.config(
            text=f"💼 {breakdown['workdays']} Workdays  |  🌴 {breakdown['weekend_days']} Wknd Days  |  🎉 {breakdown['ph_days']} PH"
        )

        if mode == "workdays":
            days, hours, minutes, seconds = self._calc_workday_time_left(now, target_dt)
        else:
            diff = target_dt - now
            days = diff.days
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

        self.tile_d[1].config(text=f"{days:02d}")
        self.tile_h[1].config(text=f"{hours:02d}")
        self.tile_m[1].config(text=f"{minutes:02d}")
        self.tile_s[1].config(text=f"{seconds:02d}")

        start_of_period = target_dt.replace(day=1, hour=0, minute=0, second=0)
        total_span = (target_dt - start_of_period).total_seconds()
        remaining_span = (target_dt - now).total_seconds()
        progress = max(0.0, min(1.0, 1.0 - (remaining_span / max(1.0, total_span))))
        self._draw_progress(progress, t.get("accent", "#e74c3c"))

    def _draw_progress(self, ratio: float, color: str):
        self.prog_canvas.delete("all")
        w = self.prog_canvas.winfo_width()
        if w <= 1:
            w = 210
        fill_w = int(w * ratio)
        self.prog_canvas.create_rectangle(0, 0, fill_w, 4, fill=color, outline="")

    def _check_alarms(self):
        if not hasattr(self, "_alerted_events"):
            self._alerted_events = set()
        data = self.get_data()
        events = data.get("countdown_events", [])
        now = datetime.now()
        for ev in events:
            label = ev.get("label", "Event")
            dt_str = ev.get("datetime", "")
            if not dt_str:
                continue
            try:
                target_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            event_id = f"{label}_{dt_str}"
            diff = (now - target_dt).total_seconds()
            if 0 <= diff <= 60 and event_id not in self._alerted_events:
                self._alerted_events.add(event_id)
                if self.on_alarm:
                    self.on_alarm(f"⏰ Countdown Reached!\n{label} 🎉")

    def _tick(self):
        self._check_alarms()
        if self._visible:
            self._update_display()
        self.root.after(1000, self._tick)

    def apply_theme(self):
        self._build()
        if self._visible:
            self._update_display()

    def show(self, near_x: int = 300, near_y: int = 400):
        self._build()
        self._visible = True
        self.win.deiconify()
        self.win.update_idletasks()

        w = self.win.winfo_width()
        h = self.win.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        x = min(near_x + 20, sw - w - 10)
        y = max(near_y - h // 2, 10)
        if y + h > sh - 10:
            y = sh - h - 10

        self.win.geometry(f"+{x}+{y}")
        self._update_display()

    def hide(self):
        self._visible = False
        if self._cal_popup and self._cal_popup.winfo_exists():
            self._cal_popup.destroy()
        self.win.withdraw()

    def toggle(self, near_x: int = 300, near_y: int = 400):
        if self._visible:
            self.hide()
        else:
            self.show(near_x, near_y)