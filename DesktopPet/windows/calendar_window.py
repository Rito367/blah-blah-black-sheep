"""
calendar_window.py
Redesigned interactive calendar with bookmarks and custom notes/important data storage.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import calendar
import datetime
import uuid
from typing import Callable
from pathlib import Path
import sys

try:
    import paths
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import paths

import themes

DAYS_HEADER = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]
TAG_ICONS = ["🔖", "⭐", "📌", "💼", "🎂", "💡", "🔑", "🎯"]


class CalendarWindow:
    def __init__(self, root: tk.Tk, get_data: Callable, save_data: Callable, on_menu: Callable | None = None):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.on_menu = on_menu

        now = datetime.date.today()
        self._year = now.year
        self._month = now.month
        self._today = now
        self._selected_date = now
        self._visible = False
        self._active_tab = "calendar"  # "calendar" or "bookmarks"
        self._search_query = ""

        self._dx = self._dy = 0
        self.win: tk.Toplevel | None = None
        self._ensure_window()
        self._build()

    def _ensure_window(self):
        """Ensures the Toplevel window exists and is configured properly."""
        if not hasattr(self, "win") or self.win is None or not self.win.winfo_exists():
            self.win = tk.Toplevel(self.root)
            self.win.title("Calendar & Bookmarks")
            self.win.overrideredirect(True)
            self.win.attributes("-topmost", True)
            self.win.resizable(False, False)
            self.win.withdraw()
            self.win.protocol("WM_DELETE_WINDOW", self.hide)

    # ── build ────────────────────────────────────────────────────────────
    def _build(self):
        self._ensure_window()
        assert self.win is not None
        for w in self.win.winfo_children():
            w.destroy()

        t = themes.get()
        self.win.configure(bg=t.get("border", "#181920"))

        self.outer = tk.Frame(self.win, bg=t.get("bg_card", "#20222e"), padx=10, pady=10)
        self.outer.pack(fill="both", expand=True, padx=2, pady=2)

        # ── Window Header (Draggable) ──
        hdr = tk.Frame(self.outer, bg=t.get("bg_card", "#20222e"))
        hdr.pack(fill="x", pady=(0, 6))
        hdr.bind("<ButtonPress-1>", self._drag_start)
        hdr.bind("<B1-Motion>", self._drag_move)

        title_lbl = tk.Label(
            hdr,
            text="📅 CALENDAR & BOOKMARKS",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("accent", "#e74c3c"),
            font=("Segoe UI", 9, "bold"),
            cursor="fleur"
        )
        title_lbl.pack(side="left")
        title_lbl.bind("<ButtonPress-1>", self._drag_start)
        title_lbl.bind("<B1-Motion>", self._drag_move)

        close_btn = tk.Label(
            hdr,
            text="✕",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"),
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=4,
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.hide())

        if self.on_menu:
            on_menu_fn = self.on_menu
            mb = tk.Label(
                hdr,
                text="☰",
                bg=t.get("bg_card", "#20222e"),
                fg=t.get("fg_main", "#ffffff"),
                font=("Segoe UI", 9, "bold"),
                cursor="hand2",
                padx=4,
            )
            mb.pack(side="right", padx=(0, 4))
            mb.bind("<Button-1>", lambda e: on_menu_fn(None, self.hide))

        # ── Tab Navigation ──
        tab_nav = tk.Frame(self.outer, bg=t.get("bg_card", "#20222e"))
        tab_nav.pack(fill="x", pady=(0, 8))

        self.btn_tab_cal = tk.Button(
            tab_nav,
            text="📅 Calendar",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            bd=0,
            pady=3,
            cursor="hand2",
            command=lambda: self._switch_tab("calendar"),
        )
        self.btn_tab_cal.pack(side="left", expand=True, fill="x", padx=(0, 2))

        self.btn_tab_bkm = tk.Button(
            tab_nav,
            text="🔖 All Bookmarks",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            bd=0,
            pady=3,
            cursor="hand2",
            command=lambda: self._switch_tab("bookmarks"),
        )
        self.btn_tab_bkm.pack(side="left", expand=True, fill="x", padx=(2, 0))

        # ── Main Content Container ──
        self.content_frame = tk.Frame(self.outer, bg=t.get("bg_card", "#20222e"))
        self.content_frame.pack(fill="both", expand=True)

        if self._active_tab == "calendar":
            self._render_calendar_tab()
        else:
            self._render_bookmarks_tab()

        self._update_tab_buttons()
        self.win.geometry("340x510")
        self.win.update_idletasks()

    def _update_tab_buttons(self):
        t = themes.get()
        if self._active_tab == "calendar":
            self.btn_tab_cal.config(bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"))
            self.btn_tab_bkm.config(bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_main", "#ffffff"))
        else:
            self.btn_tab_cal.config(bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_main", "#ffffff"))
            self.btn_tab_bkm.config(bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"))

    def _switch_tab(self, tab_key: str):
        self._active_tab = tab_key
        self._build()

    # ══════════════════════════════════════════════════════════════════════
    # ── TAB 1: CALENDAR & DAY NOTES ──
    # ══════════════════════════════════════════════════════════════════════
    def _render_calendar_tab(self):
        t = themes.get()

        # Month Navigation Bar
        nav_bar = tk.Frame(self.content_frame, bg=t.get("bg_card", "#20222e"))
        nav_bar.pack(fill="x", pady=(0, 4))

        btn_prev = tk.Label(
            nav_bar, text="◀", font=("Segoe UI", 9, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_main", "#ffffff"),
            cursor="hand2", padx=6, pady=2
        )
        btn_prev.pack(side="left")
        btn_prev.bind("<Button-1>", lambda e: self._prev_month())

        m_name = calendar.month_name[self._month]
        month_label = tk.Label(
            nav_bar, text=f"{m_name} {self._year}",
            bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"),
            font=("Segoe UI", 10, "bold")
        )
        month_label.pack(side="left", expand=True)

        btn_today = tk.Label(
            nav_bar, text="Today", font=("Segoe UI", 7, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_main", "#ffffff"),
            cursor="hand2", padx=4, pady=2
        )
        btn_today.pack(side="right", padx=(4, 0))
        btn_today.bind("<Button-1>", lambda e: self._jump_to_today())

        btn_next = tk.Label(
            nav_bar, text="▶", font=("Segoe UI", 9, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_main", "#ffffff"),
            cursor="hand2", padx=6, pady=2
        )
        btn_next.pack(side="right")
        btn_next.bind("<Button-1>", lambda e: self._next_month())

        # Calendar Grid Frame
        grid_frame = tk.Frame(self.content_frame, bg=t.get("bg_grid", "#151620"), padx=4, pady=4)
        grid_frame.pack(fill="x", pady=(0, 6))

        for col, d in enumerate(DAYS_HEADER):
            tk.Label(
                grid_frame, text=d, bg=t.get("bg_grid", "#151620"),
                fg=t.get("fg_day_hdr", "#888888"), font=("Segoe UI", 7, "bold"), width=4
            ).grid(row=0, column=col, pady=(0, 2))

        bookmarks_data = self._get_all_bookmarks()
        event_dates = self._get_countdown_dates()

        # Fix weekday offset: use Sunday-first calendar to align with DAYS_HEADER
        cal_obj = calendar.Calendar(firstweekday=calendar.SUNDAY)
        cal = cal_obj.monthdayscalendar(self._year, self._month)

        for row_i, week in enumerate(cal, start=1):
            for col_i, day in enumerate(week):
                if day == 0:
                    tk.Label(
                        grid_frame, text="", bg=t.get("bg_grid", "#151620"),
                        width=4, height=1
                    ).grid(row=row_i, column=col_i)
                    continue

                date_obj = datetime.date(self._year, self._month, day)
                date_str = date_obj.strftime("%Y-%m-%d")
                is_today = (date_obj == self._today)
                is_selected = (date_obj == self._selected_date)
                day_bks = bookmarks_data.get(date_str, [])
                has_event = (date_obj in event_dates)

                # Determine styling
                if is_selected:
                    cell_bg = t.get("accent", "#e74c3c")
                    cell_fg = t.get("fg_white", "#ffffff")
                elif is_today:
                    cell_bg = t.get("bg_today", "#ff69b4")
                    cell_fg = t.get("fg_white", "#ffffff")
                else:
                    cell_bg = t.get("bg_grid", "#151620")
                    cell_fg = t.get("fg_main", "#ffffff")

                cell = tk.Frame(grid_frame, bg=cell_bg, padx=1, pady=1, cursor="hand2")
                cell.grid(row=row_i, column=col_i, padx=1, pady=1, sticky="nsew")

                badge_txt = ""
                if day_bks:
                    # Show first bookmark tag icon
                    first_b = day_bks[0]
                    badge_txt = first_b.get("tag", "🔖") if isinstance(first_b, dict) else "🔖"
                elif has_event:
                    badge_txt = "♡"

                display_txt = str(day)
                if badge_txt:
                    display_txt = f"{day}{badge_txt}"

                num_lbl = tk.Label(
                    cell, text=display_txt, bg=cell_bg, fg=cell_fg,
                    font=("Segoe UI", 7, "bold" if (is_today or is_selected or day_bks) else "normal"),
                    width=4, cursor="hand2"
                )
                num_lbl.pack(expand=True, fill="both")

                # Bind click & hover
                def _on_click(e, d=date_obj):
                    self._selected_date = d
                    self._build()

                def _on_enter(e, c=cell, l=num_lbl, sel=is_selected, tod=is_today, hov=t.get("bg_hover", "#2c2e3f")):
                    if not sel and not tod:
                        c.config(bg=hov)
                        l.config(bg=hov)

                def _on_leave(e, c=cell, l=num_lbl, sel=is_selected, tod=is_today, orig=cell_bg):
                    if not sel and not tod:
                        c.config(bg=orig)
                        l.config(bg=orig)

                cell.bind("<Button-1>", _on_click)
                num_lbl.bind("<Button-1>", _on_click)
                cell.bind("<Enter>", _on_enter)
                cell.bind("<Leave>", _on_leave)
                num_lbl.bind("<Enter>", _on_enter)
                num_lbl.bind("<Leave>", _on_leave)

        # ── Selected Date Bookmark/Notes Section ──
        sel_str = self._selected_date.strftime("%Y-%m-%d")
        sel_display = self._selected_date.strftime("%b %d, %Y")

        day_hdr = tk.Frame(self.content_frame, bg=t.get("bg_card", "#20222e"))
        day_hdr.pack(fill="x", pady=(2, 4))

        tk.Label(
            day_hdr,
            text=f"📌 {sel_display}",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"),
            font=("Segoe UI", 8, "bold")
        ).pack(side="left")

        btn_add = tk.Button(
            day_hdr,
            text="+ Add Bookmark",
            font=("Segoe UI", 7, "bold"),
            bg=t.get("accent", "#e74c3c"),
            fg=t.get("fg_white", "#ffffff"),
            relief="flat",
            bd=0,
            padx=6,
            pady=1,
            cursor="hand2",
            command=lambda: self._open_bookmark_dialog(self._selected_date)
        )
        btn_add.pack(side="right")

        # Scrollable area for day's bookmarks
        notes_box = tk.Frame(self.content_frame, bg=t.get("bg_grid", "#151620"), bd=0)
        notes_box.pack(fill="both", expand=True)

        day_items = bookmarks_data.get(sel_str, [])

        if not day_items:
            empty_lbl = tk.Label(
                notes_box,
                text="No bookmarks or notes for this date.\nClick '+ Add Bookmark' to add one! 🔖",
                bg=t.get("bg_grid", "#151620"),
                fg=t.get("fg_dim", "#888888"),
                font=("Segoe UI", 8, "italic"),
                pady=16,
                justify="center"
            )
            empty_lbl.pack(fill="both", expand=True)
        else:
            canvas = tk.Canvas(notes_box, bg=t.get("bg_grid", "#151620"), highlightthickness=0)
            scrollbar = ttk.Scrollbar(notes_box, orient="vertical", command=canvas.yview)
            scroll_content = tk.Frame(canvas, bg=t.get("bg_grid", "#151620"))

            scroll_content.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            cw_id = canvas.create_window((0, 0), window=scroll_content, anchor="nw")
            canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw_id, width=e.width))

            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True, padx=2, pady=2)
            scrollbar.pack(side="right", fill="y")

            for item in day_items:
                if isinstance(item, dict):
                    self._render_bookmark_card(scroll_content, item, sel_str)

    def _render_bookmark_card(self, parent, item: dict, date_str: str):
        t = themes.get()
        card = tk.Frame(parent, bg=t.get("bg_card", "#20222e"), padx=6, pady=4, relief="flat", bd=0)
        card.pack(fill="x", padx=2, pady=2)

        tag = item.get("tag", "🔖")
        title = item.get("title", "Untitled")
        content = item.get("content", "").strip()
        item_id = item.get("id")

        # Top line: tag + title + actions
        top_row = tk.Frame(card, bg=t.get("bg_card", "#20222e"))
        top_row.pack(fill="x")

        tk.Label(
            top_row,
            text=f"{tag} {title}",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"),
            font=("Segoe UI", 8, "bold")
        ).pack(side="left", anchor="w")

        btn_del = tk.Label(
            top_row,
            text="🗑️",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_dim", "#888888"),
            font=("Segoe UI", 7),
            cursor="hand2"
        )
        btn_del.pack(side="right", padx=(4, 0))
        btn_del.bind("<Button-1>", lambda e, d=date_str, i=item_id: self._delete_bookmark(d, i))

        btn_edit = tk.Label(
            top_row,
            text="✏️",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_dim", "#888888"),
            font=("Segoe UI", 7),
            cursor="hand2"
        )
        btn_edit.pack(side="right")
        btn_edit.bind("<Button-1>", lambda e, it=item, d=date_str: self._open_bookmark_dialog(datetime.datetime.strptime(d, "%Y-%m-%d").date(), edit_item=it))

        if content:
            tk.Label(
                card,
                text=content,
                bg=t.get("bg_card", "#20222e"),
                fg=t.get("fg_dim", "#888888"),
                font=("Segoe UI", 7),
                wraplength=290,
                justify="left",
                anchor="w"
            ).pack(fill="x", pady=(2, 0))

    # ══════════════════════════════════════════════════════════════════════
    # ── TAB 2: ALL BOOKMARKS HUB ──
    # ══════════════════════════════════════════════════════════════════════
    def _render_bookmarks_tab(self):
        t = themes.get()

        # Search Bar
        search_frame = tk.Frame(self.content_frame, bg=t.get("bg_card", "#20222e"))
        search_frame.pack(fill="x", pady=(0, 6))

        tk.Label(
            search_frame,
            text="🔍",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_dim", "#888888"),
            font=("Segoe UI", 8)
        ).pack(side="left", padx=(0, 2))

        search_entry = tk.Entry(
            search_frame,
            font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#151620"),
            fg=t.get("fg_main", "#ffffff"),
            insertbackground=t.get("fg_main", "#ffffff"),
            relief="flat",
            bd=0
        )
        search_entry.insert(0, self._search_query)
        search_entry.pack(side="left", fill="x", expand=True, ipady=2)

        def _on_search_change(e):
            self._search_query = search_entry.get().strip().lower()
            self._render_bookmarks_list()

        search_entry.bind("<KeyRelease>", _on_search_change)

        btn_add_any = tk.Button(
            search_frame,
            text="+ Add",
            font=("Segoe UI", 7, "bold"),
            bg=t.get("accent", "#e74c3c"),
            fg=t.get("fg_white", "#ffffff"),
            relief="flat",
            bd=0,
            padx=6,
            pady=1,
            cursor="hand2",
            command=lambda: self._open_bookmark_dialog(self._selected_date)
        )
        btn_add_any.pack(side="right", padx=(4, 0))

        # List Area
        self.bkm_list_box = tk.Frame(self.content_frame, bg=t.get("bg_grid", "#151620"))
        self.bkm_list_box.pack(fill="both", expand=True)

        self._render_bookmarks_list()

    def _render_bookmarks_list(self):
        for w in self.bkm_list_box.winfo_children():
            w.destroy()

        t = themes.get()
        all_data = self._get_all_bookmarks()
        query = self._search_query.strip().lower()

        # Collect and filter
        matched = []
        for d_str in sorted(all_data.keys()):
            for item in all_data[d_str]:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title", "")).lower()
                content = str(item.get("content", "")).lower()
                tag = str(item.get("tag", "")).lower()
                if not query or query in title or query in content or query in d_str or query in tag:
                    matched.append((d_str, item))

        if not matched:
            msg = "No bookmarks found." if query else "No bookmarks saved yet.\nClick '+ Add' to bookmark important dates and notes!"
            tk.Label(
                self.bkm_list_box,
                text=msg,
                bg=t.get("bg_grid", "#151620"),
                fg=t.get("fg_dim", "#888888"),
                font=("Segoe UI", 8, "italic"),
                pady=20,
                justify="center"
            ).pack(fill="both", expand=True)
            return

        canvas = tk.Canvas(self.bkm_list_box, bg=t.get("bg_grid", "#151620"), highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.bkm_list_box, orient="vertical", command=canvas.yview)
        scroll_content = tk.Frame(canvas, bg=t.get("bg_grid", "#151620"))

        scroll_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        cw_id = canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw_id, width=e.width))

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.pack(side="right", fill="y")

        for date_str, item in matched:
            card = tk.Frame(scroll_content, bg=t.get("bg_card", "#20222e"), padx=6, pady=4)
            card.pack(fill="x", padx=2, pady=2)

            tag = item.get("tag", "🔖")
            title = item.get("title", "Untitled")
            content = item.get("content", "").strip()
            item_id = item.get("id")

            # Header row
            hdr = tk.Frame(card, bg=t.get("bg_card", "#20222e"))
            hdr.pack(fill="x")

            tk.Label(
                hdr,
                text=f"📅 {date_str}  {tag} {title}",
                bg=t.get("bg_card", "#20222e"),
                fg=t.get("fg_main", "#ffffff"),
                font=("Segoe UI", 8, "bold")
            ).pack(side="left")

            btn_del = tk.Label(
                hdr, text="🗑️", bg=t.get("bg_card", "#20222e"),
                fg=t.get("fg_dim", "#888888"), font=("Segoe UI", 7), cursor="hand2"
            )
            btn_del.pack(side="right", padx=(4, 0))
            btn_del.bind("<Button-1>", lambda e, d=date_str, i=item_id: self._delete_bookmark(d, i))

            btn_edit = tk.Label(
                hdr, text="✏️", bg=t.get("bg_card", "#20222e"),
                fg=t.get("fg_dim", "#888888"), font=("Segoe UI", 7), cursor="hand2"
            )
            btn_edit.pack(side="right", padx=(4, 0))
            btn_edit.bind("<Button-1>", lambda e, it=item, d=date_str: self._open_bookmark_dialog(datetime.datetime.strptime(d, "%Y-%m-%d").date(), edit_item=it))

            btn_jump = tk.Label(
                hdr, text="Jump ➔", bg=t.get("bg_card", "#20222e"),
                fg=t.get("accent", "#e74c3c"), font=("Segoe UI", 7, "bold"), cursor="hand2"
            )
            btn_jump.pack(side="right")
            btn_jump.bind("<Button-1>", lambda e, d=date_str: self._jump_to_date(d))

            if content:
                tk.Label(
                    card,
                    text=content,
                    bg=t.get("bg_card", "#20222e"),
                    fg=t.get("fg_dim", "#888888"),
                    font=("Segoe UI", 7),
                    wraplength=290,
                    justify="left",
                    anchor="w"
                ).pack(fill="x", pady=(2, 0))

    # ══════════════════════════════════════════════════════════════════════
    # ── DIALOG: ADD / EDIT BOOKMARK & NOTES ──
    # ══════════════════════════════════════════════════════════════════════
    def _open_bookmark_dialog(self, target_date: datetime.date, edit_item: dict | None = None):
        self._ensure_window()
        assert self.win is not None
        t = themes.get()
        dlg = tk.Toplevel(self.win)
        dlg.title("Edit Bookmark" if edit_item else "Add Bookmark")
        dlg.geometry("300x340")
        dlg.attributes("-topmost", True)
        dlg.configure(bg=t.get("border", "#181920"), padx=2, pady=2)
        dlg.resizable(False, False)

        # Center relative to calendar
        cx = self.win.winfo_x() + 20
        cy = self.win.winfo_y() + 60
        dlg.geometry(f"+{cx}+{cy}")

        outer = tk.Frame(dlg, bg=t.get("bg_card", "#20222e"), padx=10, pady=10)
        outer.pack(fill="both", expand=True)

        is_edit = edit_item is not None
        title_txt = "✏️ Edit Bookmark & Notes" if is_edit else "🔖 Add Bookmark & Notes"
        tk.Label(
            outer,
            text=title_txt,
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("accent", "#e74c3c"),
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 6))

        # Date Row
        date_str = target_date.strftime("%Y-%m-%d")
        date_row = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        date_row.pack(fill="x", pady=(0, 4))
        tk.Label(date_row, text="Date:", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8, "bold")).pack(side="left")
        date_entry = tk.Entry(
            date_row, font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#151620"), fg=t.get("fg_main", "#ffffff"),
            insertbackground=t.get("fg_main", "#ffffff"), relief="flat", bd=0, width=12
        )
        date_entry.insert(0, date_str)
        date_entry.pack(side="right", ipady=2)

        # Tag Icon Selector
        tk.Label(outer, text="Icon Tag:", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(2, 2))
        tag_frame = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        tag_frame.pack(fill="x", pady=(0, 6))

        selected_tag = [edit_item.get("tag", "🔖") if edit_item else "🔖"]
        tag_btns = {}

        def _select_tag(tg):
            selected_tag[0] = tg
            for k, b in tag_btns.items():
                if k == tg:
                    b.config(bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"))
                else:
                    b.config(bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_main", "#ffffff"))

        for tg in TAG_ICONS:
            is_cur = (tg == selected_tag[0])
            b = tk.Button(
                tag_frame,
                text=tg,
                font=("Segoe UI", 8),
                bg=t.get("accent", "#e74c3c") if is_cur else t.get("btn", "#2c2e3f"),
                fg=t.get("fg_white", "#ffffff") if is_cur else t.get("fg_main", "#ffffff"),
                relief="flat",
                bd=0,
                padx=3,
                pady=1,
                cursor="hand2",
                command=lambda val=tg: _select_tag(val)
            )
            b.pack(side="left", padx=1)
            tag_btns[tg] = b

        # Bookmark Title
        tk.Label(outer, text="Title / Summary:", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8, "bold")).pack(anchor="w")
        title_entry = tk.Entry(
            outer, font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#151620"), fg=t.get("fg_main", "#ffffff"),
            insertbackground=t.get("fg_main", "#ffffff"), relief="flat", bd=0
        )
        if edit_item:
            title_entry.insert(0, edit_item.get("title", ""))
        title_entry.pack(fill="x", pady=(2, 6), ipady=3)
        title_entry.focus_set()

        # Detailed Note / Custom Data Area
        tk.Label(outer, text="Important Data / Notes:", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8, "bold")).pack(anchor="w")
        note_text = tk.Text(
            outer, height=4, font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#151620"), fg=t.get("fg_main", "#ffffff"),
            insertbackground=t.get("fg_main", "#ffffff"), relief="flat", bd=0, wrap="word"
        )
        if edit_item:
            note_text.insert("1.0", edit_item.get("content", ""))
        note_text.pack(fill="both", expand=True, pady=(2, 8))

        # Action Buttons
        btn_row = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        btn_row.pack(fill="x")

        def _save():
            d_val = date_entry.get().strip()
            try:
                datetime.datetime.strptime(d_val, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.", parent=dlg)
                return

            t_val = title_entry.get().strip()
            if not t_val:
                t_val = "Untitled Note"
            c_val = note_text.get("1.0", tk.END).strip()

            bkm_dict = self._get_all_bookmarks()
            if d_val not in bkm_dict:
                bkm_dict[d_val] = []

            if is_edit and edit_item:
                edit_id = edit_item.get("id")
                orig_d = target_date.strftime("%Y-%m-%d")
                if orig_d != d_val and orig_d in bkm_dict:
                    bkm_dict[orig_d] = [x for x in bkm_dict[orig_d] if isinstance(x, dict) and x.get("id") != edit_id]
                    if not bkm_dict[orig_d]:
                        del bkm_dict[orig_d]

                for item in bkm_dict[d_val]:
                    if isinstance(item, dict) and item.get("id") == edit_id:
                        item["title"] = t_val
                        item["content"] = c_val
                        item["tag"] = selected_tag[0]
                        break
                else:
                    bkm_dict[d_val].append({
                        "id": edit_id or str(uuid.uuid4())[:8],
                        "title": t_val,
                        "content": c_val,
                        "tag": selected_tag[0],
                        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
            else:
                bkm_dict[d_val].append({
                    "id": str(uuid.uuid4())[:8],
                    "title": t_val,
                    "content": c_val,
                    "tag": selected_tag[0],
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })

            data = self.get_data()
            data["calendar_bookmarks"] = bkm_dict
            self.save_data(data)

            dlg.destroy()
            try:
                self._selected_date = datetime.datetime.strptime(d_val, "%Y-%m-%d").date()
                self._year = self._selected_date.year
                self._month = self._selected_date.month
            except Exception:
                pass
            self._build()

        tk.Button(
            btn_row,
            text="💾 Save Bookmark",
            font=("Segoe UI", 8, "bold"),
            bg=t.get("accent", "#e74c3c"),
            fg=t.get("fg_white", "#ffffff"),
            relief="flat",
            bd=0,
            pady=4,
            cursor="hand2",
            command=_save
        ).pack(side="left", expand=True, fill="x", padx=(0, 2))

        tk.Button(
            btn_row,
            text="Cancel",
            font=("Segoe UI", 8, "bold"),
            bg=t.get("btn", "#2c2e3f"),
            fg=t.get("fg_main", "#ffffff"),
            relief="flat",
            bd=0,
            pady=4,
            cursor="hand2",
            command=dlg.destroy
        ).pack(side="right", expand=True, fill="x", padx=(2, 0))

    def _delete_bookmark(self, date_str: str, item_id: str | None):
        if not item_id:
            return
        bkm_dict = self._get_all_bookmarks()
        if date_str in bkm_dict:
            bkm_dict[date_str] = [x for x in bkm_dict[date_str] if isinstance(x, dict) and x.get("id") != item_id]
            if not bkm_dict[date_str]:
                del bkm_dict[date_str]
            data = self.get_data()
            data["calendar_bookmarks"] = bkm_dict
            self.save_data(data)
            self._build()

    def _jump_to_date(self, date_str: str):
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            self._selected_date = dt
            self._year = dt.year
            self._month = dt.month
            self._active_tab = "calendar"
            self._build()
        except Exception:
            pass

    def _jump_to_today(self):
        now = datetime.date.today()
        self._selected_date = now
        self._year = now.year
        self._month = now.month
        self._build()

    # ── Helpers ──────────────────────────────────────────────────────────
    def _get_all_bookmarks(self) -> dict:
        data = self.get_data()
        bkm = data.get("calendar_bookmarks", {})
        if not isinstance(bkm, dict):
            return {}
        clean_bkm = {}
        for d_str, items in bkm.items():
            if isinstance(items, list):
                clean_list = []
                for it in items:
                    if isinstance(it, dict):
                        clean_list.append(it)
                    elif isinstance(it, str):
                        clean_list.append({
                            "id": str(uuid.uuid4())[:8],
                            "title": it,
                            "content": "",
                            "tag": "🔖",
                            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                clean_bkm[d_str] = clean_list
            elif isinstance(items, str):
                clean_bkm[d_str] = [{
                    "id": str(uuid.uuid4())[:8],
                    "title": items,
                    "content": "",
                    "tag": "🔖",
                    "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }]
        return clean_bkm

    def _get_countdown_dates(self) -> set:
        data = self.get_data()
        event_dates = set()
        for evt in data.get("countdown_events", []):
            if not isinstance(evt, dict):
                continue
            try:
                dt = datetime.datetime.strptime(
                    evt.get("datetime", ""), "%Y-%m-%d %H:%M:%S")
                event_dates.add(dt.date())
            except (ValueError, TypeError):
                pass
        return event_dates

    def apply_theme(self):
        if hasattr(self, "win") and self.win and self.win.winfo_exists():
            self._build()

    # ── month nav ────────────────────────────────────────────────────────
    def _prev_month(self):
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        if self._year == self._today.year and self._month == self._today.month:
            self._selected_date = self._today
        else:
            self._selected_date = datetime.date(self._year, self._month, 1)
        self._build()

    def _next_month(self):
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        if self._year == self._today.year and self._month == self._today.month:
            self._selected_date = self._today
        else:
            self._selected_date = datetime.date(self._year, self._month, 1)
        self._build()

    # ── show / hide / toggle ─────────────────────────────────────────────
    def show(self, near_x: int = 300, near_y: int = 400):
        self._ensure_window()
        assert self.win is not None
        self._today = datetime.date.today()
        self._build()
        self._visible = True
        self.win.deiconify()
        self.win.lift()
        self.win.attributes("-topmost", True)
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

    def hide(self):
        self._visible = False
        if hasattr(self, "win") and self.win and self.win.winfo_exists():
            self.win.withdraw()

    def toggle(self, near_x: int = 300, near_y: int = 400):
        if not hasattr(self, "win") or not self.win or not self.win.winfo_exists():
            self.show(near_x, near_y)
            return
        if self._visible and self.win.winfo_viewable():
            self.hide()
        else:
            self.show(near_x, near_y)

    # ── drag ─────────────────────────────────────────────────────────────
    def _drag_start(self, event):
        if hasattr(self, "win") and self.win and self.win.winfo_exists():
            self._dx = event.x_root - self.win.winfo_x()
            self._dy = event.y_root - self.win.winfo_y()

    def _drag_move(self, event):
        if hasattr(self, "win") and self.win and self.win.winfo_exists():
            self.win.geometry(f"+{event.x_root - self._dx}+{event.y_root - self._dy}")
