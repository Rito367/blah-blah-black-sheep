"""
keybind_window.py
Interactive manager for global keybinds and keyboard shortcuts.
Allows the user to bind global hotkeys to ANY action:
- Built-in pet actions (Summon, Hide/Show, Feed, Jump, Whip, Bomb, Patrol, etc.)
- Built-in windows & tools (Calendar, Reminders, Countdown, Weather, etc.)
- Any custom application, executable, or file (with file browser)
- Any custom web URL
- Any custom pet speech bubble phrase
- Any custom shell command
Includes interactive hotkey recording, live testing, enable/disable toggling, and editing.
"""

from __future__ import annotations

import os
import uuid
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Callable

try:
    from core import themes
except ImportError:
    import themes  # type: ignore

try:
    from core.hotkey_manager import HotkeyManager
except ImportError:
    try:
        from hotkey_manager import HotkeyManager  # type: ignore
    except ImportError:
        HotkeyManager = Any  # type: ignore


class KeybindWindow:
    def __init__(
        self,
        root: tk.Tk,
        get_data: Callable[[], dict[str, Any]],
        save_data: Callable[[dict[str, Any]], None],
        hotkey_manager: Any = None,
        on_menu: Callable[..., Any] | None = None,
    ):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.hotkey_manager = hotkey_manager
        self.on_menu = on_menu
        self.win: tk.Toplevel | None = None
        self._filter_category: str = "all"
        self._recording_active: bool = False
        self._editor_dlg: tk.Toplevel | None = None
        self._editing_id: str | None = None
        self._check_vars: dict[str, tk.BooleanVar] = {}
        self._editor_enabled_var: tk.BooleanVar | None = None
        self._filter_btns: dict[str, tk.Button] = {}
        self.canvas: Any = None
        self.scrollbar: Any = None
        self.cards_frame: Any = None

    def hide(self):
        if hasattr(self, "_editor_dlg") and self._editor_dlg and self._editor_dlg.winfo_exists():
            try:
                self._editor_dlg.destroy()
            except Exception:
                pass
            self._editor_dlg = None
        if self.win and self.win.winfo_exists():
            try:
                self.win.unbind_all("<MouseWheel>")
            except Exception:
                pass
            self.win.destroy()
            self.win = None

    def toggle(self, near_x: int = 100, near_y: int = 100):
        if self.win and self.win.winfo_exists():
            self.hide()
        else:
            self.show(near_x, near_y)

    def show(self, near_x: int = 100, near_y: int = 100):
        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        t = themes.get()
        self.win = tk.Toplevel(self.root)
        self.win.title("Custom Keybinds & Shortcuts")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 420, 560
        safe_x = max(10, min(near_x, sw - target_w - 10))
        safe_y = max(10, min(near_y, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("border", "#181920"), padx=2, pady=2)
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        outer = tk.Frame(self.win, bg=t.get("bg_card", "#20222e"), padx=12, pady=10)
        outer.pack(fill="both", expand=True)

        # ── Header Bar ──────────────────────────────────────────
        hdr = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        hdr.pack(fill="x", pady=(0, 6))

        tk.Label(
            hdr, text="⌨️ KEYBINDS & SHORTCUTS", bg=t.get("bg_card", "#20222e"),
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
            mb = tk.Label(
                hdr, text="☰", bg=t.get("bg_card", "#20222e"),
                fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 9, "bold"), cursor="hand2"
            )
            mb.pack(side="right", padx=(0, 6))
            mb.bind("<Button-1>", lambda e: on_menu(close_win=self.win, hide_fn=self.hide))

        # Subtitle
        tk.Label(
            outer, text="Trigger any pet action, launch any app, open URLs or speak via global keys.",
            bg=t.get("bg_card", "#20222e"), fg=t.get("fg_dim", "#888888"),
            font=("Segoe UI", 7, "italic"), wraplength=390, justify="left"
        ).pack(anchor="w", pady=(0, 8))

        # ── Top Action & Filter Row ─────────────────────────────
        top_bar = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        top_bar.pack(fill="x", pady=(0, 8))

        add_btn = tk.Button(
            top_bar, text="➕ Add Keybind",
            bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 8, "bold"), relief="flat", bd=0, padx=8, pady=3,
            cursor="hand2", command=self._open_add_dialog
        )
        add_btn.pack(side="left")

        # Category Filter Buttons
        filter_frame = tk.Frame(top_bar, bg=t.get("bg_card", "#20222e"))
        filter_frame.pack(side="right")

        self._filter_btns = {}
        filters = [("all", "All"), ("builtin", "Built-in"), ("app", "Apps"), ("url", "URLs"), ("speech", "Speech")]
        for fkey, flabel in filters:
            def _filter_cb(k: str = fkey) -> None:
                self._set_filter(k)

            btn = tk.Button(
                filter_frame, text=flabel, font=("Segoe UI", 7),
                relief="flat", bd=0, padx=4, pady=2, cursor="hand2",
                command=_filter_cb
            )
            btn.pack(side="left", padx=1)
            self._filter_btns[fkey] = btn
        self._update_filter_button_styles()

        # ── Scrollable Keybind List ──────────────────────────────
        list_outer = tk.Frame(outer, bg=t.get("bg_grid", "#151620"), relief="flat", bd=0)
        list_outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(list_outer, bg=t.get("bg_grid", "#151620"), highlightthickness=0)
        self.canvas = canvas
        scrollbar = ttk.Scrollbar(list_outer, orient="vertical", command=canvas.yview)
        self.scrollbar = scrollbar
        cards_frame = tk.Frame(canvas, bg=t.get("bg_grid", "#151620"))
        self.cards_frame = cards_frame

        cards_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        cw_id = canvas.create_window((0, 0), window=cards_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw_id, width=getattr(e, "width", 400)))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.pack(side="right", fill="y")

        def _on_wheel(e: Any) -> None:
            if self.win and self.win.winfo_exists() and self.canvas:
                try:
                    delta = getattr(e, "delta", 0)
                    if delta:
                        self.canvas.yview_scroll(int(-1 * (delta / 120)), "units")
                except (tk.TclError, RuntimeError, AttributeError):
                    pass

        canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", _on_wheel))
        canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

        self._render_keybind_list()

    def _set_filter(self, category: str):
        self._filter_category = category
        self._update_filter_button_styles()
        self._render_keybind_list()

    def _update_filter_button_styles(self):
        t = themes.get()
        for k, btn in self._filter_btns.items():
            if k == self._filter_category:
                btn.config(bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"))
            else:
                btn.config(bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_main", "#ffffff"))

    def _get_keybinds(self) -> list[dict[str, Any]]:
        data = self.get_data()
        kbs = data.get("custom_keybinds", [])
        if not isinstance(kbs, list):
            kbs = []
        return [kb for kb in kbs if isinstance(kb, dict)]

    def _render_keybind_list(self):
        if not self.win or not self.win.winfo_exists():
            return
        cards_frame = self.cards_frame
        if cards_frame is None or not hasattr(cards_frame, "winfo_children"):
            return

        for w in list(cards_frame.winfo_children()):
            try:
                w.destroy()
            except (tk.TclError, RuntimeError, AttributeError):
                pass

        t = themes.get()
        keybinds = self._get_keybinds()

        # Apply category filter
        if self._filter_category != "all":
            filtered = [kb for kb in keybinds if kb.get("type", "builtin") == self._filter_category]
        else:
            filtered = keybinds

        if not filtered:
            msg = "No keybinds configured yet!\nClick '+ Add Keybind' to create one." if not keybinds else "No keybinds match this filter."
            tk.Label(
                cards_frame, text=msg,
                bg=t.get("bg_grid", "#151620"), fg=t.get("fg_dim", "#888888"),
                font=("Segoe UI", 8, "italic"), pady=30, justify="center"
            ).pack(fill="both", expand=True)
            return

        type_labels = {
            "builtin": "🐾 Built-in",
            "app": "🚀 App / File",
            "url": "🌐 Web URL",
            "speech": "💬 Speech",
            "cmd": "💻 Shell",
        }

        for kb in filtered:
            card = tk.Frame(cards_frame, bg=t.get("bg_card", "#20222e"), padx=8, pady=6)
            card.pack(fill="x", padx=4, pady=3)

            # Top Row: Name + Type Badge + Checkbox
            top_row = tk.Frame(card, bg=t.get("bg_card", "#20222e"))
            top_row.pack(fill="x")

            ktype = str(kb.get("type") or "builtin")
            type_tag = str(type_labels.get(ktype, ktype.upper()))
            name = str(kb.get("name") or "Unnamed Keybind")
            enabled = bool(kb.get("enabled", True))
            k_id = kb.get("id")

            # Checkbox toggle
            var = tk.BooleanVar(value=enabled)
            kid_str = str(k_id) if k_id is not None else ""
            self._check_vars[kid_str] = var

            def _toggle_cb(kid: Any = k_id, v: tk.BooleanVar = var) -> None:
                self._toggle_enable(str(kid), v.get())

            cb = tk.Checkbutton(
                top_row, variable=var,
                bg=t.get("bg_card", "#20222e"), activebackground=t.get("bg_card", "#20222e"),
                selectcolor=t.get("bg_card", "#20222e"),
                relief="flat", bd=0, highlightthickness=0,
                command=_toggle_cb
            )
            cb.pack(side="left")

            # Action Buttons on Right FIRST so they are never clipped by long titles
            btn_box = tk.Frame(top_row, bg=t.get("bg_card", "#20222e"))
            btn_box.pack(side="right")

            def _test_cb(e: Any, item: dict[str, Any] = kb) -> None:
                if self.hotkey_manager:
                    self.hotkey_manager.execute_keybind(item)

            test_btn = tk.Label(
                btn_box, text="▶ Test", bg=t.get("btn", "#2c2e3f"),
                fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 7, "bold"),
                cursor="hand2", padx=4, pady=1
            )
            test_btn.pack(side="left", padx=2)
            test_btn.bind("<Button-1>", _test_cb)

            def _edit_cb(e: Any, item: dict[str, Any] = kb) -> None:
                self._open_edit_dialog(item)

            edit_btn = tk.Label(
                btn_box, text="✏️", bg=t.get("btn", "#2c2e3f"),
                fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 7),
                cursor="hand2", padx=4, pady=1
            )
            edit_btn.pack(side="left", padx=2)
            edit_btn.bind("<Button-1>", _edit_cb)

            def _del_cb(e: Any, kid: Any = k_id) -> None:
                self._delete_keybind(str(kid))

            del_btn = tk.Label(
                btn_box, text="🗑️", bg=t.get("btn", "#2c2e3f"),
                fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 7),
                cursor="hand2", padx=4, pady=1
            )
            del_btn.pack(side="left", padx=2)
            del_btn.bind("<Button-1>", _del_cb)

            # Left items: Type badge and Name (with truncation if long)
            tk.Label(
                top_row, text=type_tag, bg=t.get("bg_grid", "#151620"),
                fg=t.get("accent", "#e74c3c"), font=("Segoe UI", 7, "bold"), padx=4, pady=1
            ).pack(side="left", padx=(2, 6))

            disp_name = (name[:22] + "…") if len(name) > 22 else name
            tk.Label(
                top_row, text=disp_name, bg=t.get("bg_card", "#20222e"),
                fg=t.get("fg_main", "#ffffff") if enabled else t.get("fg_dim", "#777777"),
                font=("Segoe UI", 8, "bold" if enabled else "normal")
            ).pack(side="left")

            # Middle Row: Key Badge + Target Detail
            mid_row = tk.Frame(card, bg=t.get("bg_card", "#20222e"))
            mid_row.pack(fill="x", pady=(3, 0))

            key_combo = kb.get("key", "").upper()
            if key_combo:
                key_pill = tk.Label(
                    mid_row, text=f" ⌨ {key_combo} ",
                    bg=t.get("accent", "#e74c3c") if enabled else t.get("btn", "#3a3c4f"),
                    fg=t.get("fg_white", "#ffffff"),
                    font=("Segoe UI", 7, "bold"), padx=4, pady=1
                )
                key_pill.pack(side="left", padx=(22, 6))

            target = str(kb.get("target", ""))
            if target:
                if ktype == "builtin":
                    reg = self.hotkey_manager.get_registered_actions() if self.hotkey_manager else {}
                    detail_text = reg.get(target, {}).get("name", target)
                else:
                    detail_text = (target[:35] + "...") if len(target) > 35 else target
                pad_left = 0 if key_combo else 22
                tk.Label(
                    mid_row, text=detail_text, bg=t.get("bg_card", "#20222e"),
                    fg=t.get("fg_dim", "#888888"), font=("Segoe UI", 7)
                ).pack(side="left", padx=(pad_left, 0))

    @staticmethod
    def _sync_legacy_hotkeys(data: dict[str, Any], kbs: list[dict[str, Any]]):
        """Keep legacy summon_hotkey and hide_hotkey in data synchronized with custom_keybinds."""
        if not isinstance(data, dict) or not isinstance(kbs, list):
            return
        active_summon = [kb.get("key") for kb in kbs if kb.get("type") == "builtin" and kb.get("target") == "summon" and kb.get("enabled", True)]
        data["summon_hotkey"] = active_summon[0] if active_summon else ""

        active_hide = [kb.get("key") for kb in kbs if kb.get("type") == "builtin" and kb.get("target") == "toggle_hide" and kb.get("enabled", True)]
        data["hide_hotkey"] = active_hide[0] if active_hide else ""

    def _toggle_enable(self, item_id: str, new_val: bool):
        data = self.get_data()
        kbs = data.get("custom_keybinds", [])
        for kb in kbs:
            if kb.get("id") == item_id:
                kb["enabled"] = new_val
                break
        data["custom_keybinds"] = kbs
        self._sync_legacy_hotkeys(data, kbs)
        self.save_data(data)
        if self.hotkey_manager:
            self.hotkey_manager.apply_keybinds(kbs, self.root)
        # Avoid synchronous widget destruction during event handler
        self.root.after_idle(self._render_keybind_list)

    def _delete_keybind(self, item_id: str):
        parent_win = self.win if (self.win and self.win.winfo_exists()) else self.root
        if not messagebox.askyesno("Delete Keybind", "Are you sure you want to delete this keybind?", parent=parent_win):
            return
        if self._editing_id == item_id:
            if self._editor_dlg and self._editor_dlg.winfo_exists():
                try:
                    self._editor_dlg.destroy()
                except Exception:
                    pass
                self._editor_dlg = None
            self._editing_id = None
        data = self.get_data()
        kbs = data.get("custom_keybinds", [])
        data["custom_keybinds"] = [kb for kb in kbs if kb.get("id") != item_id]
        self._sync_legacy_hotkeys(data, data["custom_keybinds"])
        self.save_data(data)
        if self.hotkey_manager:
            self.hotkey_manager.apply_keybinds(data["custom_keybinds"], self.root)
        self.root.after_idle(self._render_keybind_list)

    # ── Editor Modal (Add / Edit) ───────────────────────────────────────────
    def _open_add_dialog(self):
        self._show_editor_dialog(edit_item=None)

    def _open_edit_dialog(self, edit_item: dict[str, Any]):
        self._show_editor_dialog(edit_item=edit_item)

    def _show_editor_dialog(self, edit_item: dict[str, Any] | None = None):
        # Prevent opening multiple stacked modals
        if self._editor_dlg and self._editor_dlg.winfo_exists():
            self._editor_dlg.lift()
            self._editor_dlg.focus_force()
            return

        self._editing_id = edit_item.get("id") if edit_item else None
        parent_win = self.win if (self.win and self.win.winfo_exists()) else self.root
        t = themes.get()
        dlg = tk.Toplevel(parent_win)
        self._editor_dlg = dlg

        is_edit = edit_item is not None
        dlg.title("Edit Keybind" if is_edit else "Add New Keybind")
        dlg.attributes("-topmost", True)
        dlg.configure(bg=t.get("border", "#181920"), padx=2, pady=2)
        dlg.resizable(False, False)

        try:
            dlg.transient(parent_win)
        except Exception:
            pass

        dw, dh = 400, 500
        if parent_win and parent_win.winfo_exists():
            ref_x = parent_win.winfo_x()
            ref_y = parent_win.winfo_y()
            cx = max(10, ref_x + 15)
            cy = max(10, ref_y + 15)
        else:
            sw = dlg.winfo_screenwidth()
            sh = dlg.winfo_screenheight()
            cx = max(10, (sw - dw) // 2)
            cy = max(10, (sh - dh) // 2)
        dlg.geometry(f"{dw}x{dh}+{cx}+{cy}")

        def _close_dlg():
            self._editing_id = None
            self._editor_dlg = None
            try:
                dlg.grab_release()
            except Exception:
                pass
            try:
                dlg.destroy()
            except Exception:
                pass

        dlg.protocol("WM_DELETE_WINDOW", _close_dlg)

        # Safely acquire modal grab after window is mapped
        dlg.after(20, lambda: dlg.grab_set() if (dlg and dlg.winfo_exists()) else None)

        outer = tk.Frame(dlg, bg=t.get("bg_card", "#20222e"), padx=12, pady=10)
        outer.pack(fill="both", expand=True)

        tk.Label(
            outer, text="✏️ Edit Keybind" if is_edit else "➕ Add New Keybind",
            bg=t.get("bg_card", "#20222e"), fg=t.get("accent", "#e74c3c"),
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 8))

        # 1. Action Type Selector
        tk.Label(
            outer, text="Action Type:", bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        type_options = [
            ("builtin", "🐾 Built-in Action (Pet & Windows)"),
            ("app", "🚀 Launch Application / File"),
            ("url", "🌐 Open Web URL"),
            ("speech", "💬 Make Pet Speak Message"),
            ("cmd", "💻 Run Shell Command"),
        ]
        type_var = tk.StringVar(value=edit_item.get("type", "builtin") if edit_item else "builtin")
        type_dropdown = ttk.Combobox(
            outer, values=[label for _, label in type_options],
            state="readonly", font=("Segoe UI", 8)
        )
        for code, label in type_options:
            if code == type_var.get():
                type_dropdown.set(label)
                break
        if not type_dropdown.get():
            type_dropdown.set(type_options[0][1])
        type_dropdown.pack(fill="x", pady=(2, 8))

        # 2. Dynamic Target Container
        target_container = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        target_container.pack(fill="x", pady=(0, 8))

        # Built-in actions dropdown
        registered_actions = self.hotkey_manager.get_registered_actions() if self.hotkey_manager else {}
        action_names = []
        action_id_by_display = {}
        for aid, info in registered_actions.items():
            disp = f"{info.get('icon', '🐾')} {info.get('name', aid)} ({info.get('category', 'Pet')})"
            action_names.append(disp)
            action_id_by_display[disp] = aid

        builtin_combo = ttk.Combobox(
            target_container,
            values=action_names if action_names else ["(No actions available)"],
            state="readonly" if action_names else "disabled",
            font=("Segoe UI", 8)
        )
        if edit_item and edit_item.get("type") == "builtin":
            cur_target = edit_item.get("target")
            for disp, aid in action_id_by_display.items():
                if aid == cur_target:
                    builtin_combo.set(disp)
                    break
        if not builtin_combo.get() and action_names:
            builtin_combo.set(action_names[0])

        # Target string entry + browse button for apps/urls/speech/cmd
        target_entry_row = tk.Frame(target_container, bg=t.get("bg_card", "#20222e"))
        target_label = tk.Label(target_entry_row, text="Path / URL / Text:", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8))
        target_label.pack(anchor="w")

        entry_sub = tk.Frame(target_entry_row, bg=t.get("bg_card", "#20222e"))
        entry_sub.pack(fill="x", pady=(2, 0))
        entry_sub.columnconfigure(0, weight=1)

        target_entry = tk.Entry(
            entry_sub, font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#151620"), fg=t.get("fg_main", "#ffffff"),
            insertbackground=t.get("fg_main", "#ffffff"), relief="flat", bd=0
        )
        if edit_item and edit_item.get("type") != "builtin":
            target_entry.insert(0, str(edit_item.get("target", "")))
        target_entry.grid(row=0, column=0, sticky="ew", ipady=3)

        browse_btn = tk.Button(
            entry_sub, text="Browse...", font=("Segoe UI", 7),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_main", "#ffffff"),
            relief="flat", bd=0, padx=6, cursor="hand2"
        )
        browse_btn.grid(row=0, column=1, padx=(4, 0))

        # 3. Friendly Name Entry
        tk.Label(
            outer, text="Display Name / Label:", bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        name_entry = tk.Entry(
            outer, font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#151620"), fg=t.get("fg_main", "#ffffff"),
            insertbackground=t.get("fg_main", "#ffffff"), relief="flat", bd=0
        )
        if edit_item:
            name_entry.insert(0, edit_item.get("name", ""))
        elif action_names:
            first_aid = action_id_by_display.get(action_names[0])
            if first_aid and first_aid in registered_actions:
                name_entry.insert(0, registered_actions[first_aid].get("name", first_aid))
        name_entry.pack(fill="x", pady=(2, 8), ipady=3)

        def _on_browse():
            try:
                dlg.grab_release()
            except Exception:
                pass
            fn = filedialog.askopenfilename(
                title="Select Executable or File to Launch",
                filetypes=[("All Executables & Files", "*.*"), ("Applications", "*.exe;*.bat;*.cmd;*.py;*.lnk")],
                parent=dlg
            )
            try:
                dlg.grab_set()
            except Exception:
                pass
            if fn:
                norm_fn = os.path.normpath(fn)
                target_entry.delete(0, tk.END)
                target_entry.insert(0, norm_fn)
                cur_n = name_entry.get().strip()
                if not cur_n or cur_n.startswith("Launch "):
                    base = os.path.splitext(os.path.basename(norm_fn))[0]
                    name_entry.delete(0, tk.END)
                    name_entry.insert(0, f"Launch {base.title()}")

        browse_btn.config(command=_on_browse)

        def _update_type_view(*_):
            selected_label = type_dropdown.get()
            selected_code = "builtin"
            for code, label in type_options:
                if label == selected_label:
                    selected_code = code
                    break
            type_var.set(selected_code)

            for w in target_container.winfo_children():
                if isinstance(w, tk.Widget):
                    w.pack_forget()

            if selected_code == "builtin":
                builtin_combo.pack(fill="x", pady=(2, 0))
            else:
                target_entry_row.pack(fill="x")
                if selected_code == "app":
                    target_label.config(text="Executable or File Path (e.g. C:\\Games\\app.exe):")
                    browse_btn.grid()
                elif selected_code == "url":
                    target_label.config(text="Web URL (e.g. https://youtube.com):")
                    browse_btn.grid_remove()
                elif selected_code == "speech":
                    target_label.config(text="Speech Message (Pet will say this in speech bubble):")
                    browse_btn.grid_remove()
                elif selected_code == "cmd":
                    target_label.config(text="Shell / Terminal Command:")
                    browse_btn.grid_remove()

        type_dropdown.bind("<<ComboboxSelected>>", _update_type_view)
        _update_type_view()

        # Auto-fill name when choosing built-in action
        def _on_builtin_select(_):
            disp = builtin_combo.get()
            aid = action_id_by_display.get(disp)
            if aid and aid in registered_actions:
                act = registered_actions[aid]
                cur_n = name_entry.get().strip()
                known_names = {a.get("name") for a in registered_actions.values()}
                if not cur_n or cur_n in known_names:
                    name_entry.delete(0, tk.END)
                    name_entry.insert(0, act.get("name", aid))
        builtin_combo.bind("<<ComboboxSelected>>", _on_builtin_select)

        # 4. Keybind Combo Input + Record Button
        tk.Label(
            outer, text="Hotkey Combination:", bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        key_row = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        key_row.pack(fill="x", pady=(2, 8))

        key_entry = tk.Entry(
            key_row, font=("Segoe UI", 9, "bold"),
            bg=t.get("bg_grid", "#151620"), fg=t.get("accent", "#e74c3c"),
            insertbackground=t.get("fg_main", "#ffffff"), relief="flat", bd=0
        )
        if edit_item:
            key_entry.insert(0, edit_item.get("key", ""))
        key_entry.pack(side="left", fill="x", expand=True, ipady=3)

        rec_btn = tk.Button(
            key_row, text="🔴 Record Key", font=("Segoe UI", 7, "bold"),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, padx=8, cursor="hand2"
        )
        rec_btn.pack(side="right", padx=(4, 0))

        status_lbl = tk.Label(
            outer, text="Type hotkey (e.g. alt+z, ctrl+shift+a, f9) or click 'Record Key'.",
            bg=t.get("bg_card", "#20222e"), fg=t.get("fg_dim", "#888888"),
            font=("Segoe UI", 7, "italic")
        )
        status_lbl.pack(anchor="w", pady=(0, 8))

        is_recording = [False]

        def _toggle_recording():
            if is_recording[0]:
                is_recording[0] = False
                key_entry.config(state="normal")
                rec_btn.config(text="🔴 Record Key", bg=t.get("btn", "#2c2e3f"))
                status_lbl.config(text="Recording stopped. Type hotkey manually.", fg=t.get("fg_dim", "#888888"))
                return

            is_recording[0] = True
            key_entry.config(state="readonly")
            rec_btn.config(text="⏹ Stop", bg="#e74c3c")
            status_lbl.config(text="Press any key combination on your keyboard now...", fg="#e74c3c")

            def _on_captured(combo):
                if not is_recording[0]:
                    return
                is_recording[0] = False

                def _ui():
                    if not dlg.winfo_exists():
                        return
                    key_entry.config(state="normal")
                    key_entry.delete(0, tk.END)
                    key_entry.insert(0, combo)
                    rec_btn.config(text="🔴 Record Key", bg=t.get("btn", "#2c2e3f"))
                    status_lbl.config(text=f"Captured: {combo.upper()}!", fg=t.get("fg_dim", "#888888"))
                try:
                    dlg.after(0, _ui)
                except Exception:
                    pass

            def _on_err(err):
                if not is_recording[0]:
                    return
                is_recording[0] = False

                def _ui():
                    if not dlg.winfo_exists():
                        return
                    key_entry.config(state="normal")
                    rec_btn.config(text="🔴 Record Key", bg=t.get("btn", "#2c2e3f"))
                    status_lbl.config(text=f"Error: {err}", fg="#e74c3c")
                try:
                    dlg.after(0, _ui)
                except Exception:
                    pass

            rec_fn = getattr(self.hotkey_manager, "record_hotkey_async", None) or getattr(HotkeyManager, "record_hotkey_async", None)
            if callable(rec_fn):
                rec_fn(on_success=_on_captured, on_error=_on_err)
            else:
                _on_err("Hotkey recording is not available.")

        rec_btn.config(command=_toggle_recording)

        # 5. Enabled Checkbox
        enabled_var = tk.BooleanVar(value=edit_item.get("enabled", True) if edit_item else True)
        self._editor_enabled_var = enabled_var
        cb_en = tk.Checkbutton(
            outer, text="Enable this hotkey immediately", variable=enabled_var,
            bg=t.get("bg_card", "#20222e"), activebackground=t.get("bg_card", "#20222e"),
            selectcolor=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8),
            relief="flat", bd=0, highlightthickness=0
        )
        cb_en.pack(anchor="w", pady=(0, 10))

        # 6. Action Save / Cancel Buttons
        btn_row = tk.Frame(outer, bg=t.get("bg_card", "#20222e"))
        btn_row.pack(fill="x", pady=(4, 0))

        tk.Button(
            btn_row, text="Cancel", font=("Segoe UI", 8),
            bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_main", "#ffffff"),
            relief="flat", bd=0, padx=10, pady=3, cursor="hand2", command=_close_dlg
        ).pack(side="left")

        def _save_keybind():
            # Synchronize k_type with currently selected label in dropdown
            selected_label = type_dropdown.get()
            k_type = type_var.get()
            for code, label in type_options:
                if label == selected_label:
                    k_type = code
                    break

            raw_key = key_entry.get().strip()
            raw_clean = raw_key.strip("+ ").strip()
            if not raw_clean:
                messagebox.showerror("Invalid Hotkey", "Please enter or record a hotkey combination.", parent=dlg)
                return

            if self.hotkey_manager and hasattr(self.hotkey_manager, "normalize_key_combo"):
                k_key = self.hotkey_manager.normalize_key_combo(raw_clean)
            else:
                k_key = "+".join(p.strip().lower() for p in raw_clean.replace(" ", "").split("+") if p.strip())

            # Deduplicate key parts preserving order (e.g. 'ctrl+ctrl+a' -> 'ctrl+a')
            seen_parts = set()
            clean_parts = []
            for p in k_key.split("+"):
                p_lower = p.strip().lower()
                if p_lower and p_lower not in seen_parts:
                    seen_parts.add(p_lower)
                    clean_parts.append(p_lower)
            k_key = "+".join(clean_parts)

            if not k_key:
                messagebox.showerror("Invalid Hotkey", "Please enter or record a valid hotkey combination.", parent=dlg)
                return

            # Reject hotkey if it consists solely of modifier keys (prevents system lockup)
            MODIFIER_KEYS = {"ctrl", "control", "alt", "alt_l", "alt_r", "shift", "shift_l", "shift_r", "win", "windows", "cmd"}
            if all(p in MODIFIER_KEYS for p in clean_parts):
                messagebox.showerror(
                    "Invalid Hotkey",
                    f"'{k_key.upper()}' consists only of modifier keys.\nPlease add an action key (e.g. {k_key.upper()}+Z).",
                    parent=dlg
                )
                return

            k_name = name_entry.get().strip()
            k_enabled = enabled_var.get()

            if k_type == "builtin":
                disp = builtin_combo.get()
                k_target = action_id_by_display.get(disp, "")
                if not k_target and is_edit and edit_item and edit_item.get("type") == "builtin":
                    k_target = edit_item.get("target", "")
                if not k_target:
                    messagebox.showerror("No Action Selected", "Please select a valid built-in action.", parent=dlg)
                    return
                if not k_name:
                    k_name = registered_actions.get(k_target, {}).get("name", "Action")
            else:
                k_target = target_entry.get().strip().strip('\"\'')
                if not k_target:
                    messagebox.showerror("Missing Target", "Please enter a file path, URL, speech message, or shell command.", parent=dlg)
                    return
                if not k_name:
                    if k_type == "app":
                        base = os.path.splitext(os.path.basename(k_target))[0]
                        k_name = f"Launch {base.title()}" if base else "Launch App"
                    elif k_type == "url":
                        clean_url = k_target.replace("https://", "").replace("http://", "").split("/")[0]
                        k_name = f"Open {clean_url}" if clean_url else "Open Web URL"
                    elif k_type == "speech":
                        k_name = f"Say: \"{k_target[:20]}\""
                    elif k_type == "cmd":
                        k_name = f"Run: {k_target[:20]}"
                    else:
                        k_name = f"{k_type.title()}: {k_target[:20]}"

            data = self.get_data()
            kbs = data.get("custom_keybinds", [])
            if not isinstance(kbs, list):
                kbs = []

            # Check for conflict only if this keybind is enabled
            if k_enabled:
                for other in kbs:
                    if other.get("id") != (edit_item.get("id") if edit_item else None):
                        norm_other = (
                            self.hotkey_manager.normalize_key_combo(other.get("key", ""))
                            if (self.hotkey_manager and hasattr(self.hotkey_manager, "normalize_key_combo"))
                            else other.get("key", "").lower().replace(" ", "")
                        )
                        if other.get("enabled", True) and norm_other == k_key:
                            if not messagebox.askyesno(
                                "Hotkey Conflict",
                                f"The key combination '{k_key.upper()}' is already used by '{other.get('name')}'.\nOverwrite it?",
                                parent=dlg
                            ):
                                return
                            other["enabled"] = False

            # Update existing or append new
            found = False
            if is_edit and edit_item:
                target_id = edit_item.get("id")
                for kb in kbs:
                    if kb.get("id") == target_id:
                        kb["name"] = k_name
                        kb["key"] = k_key
                        kb["type"] = k_type
                        kb["target"] = k_target
                        kb["enabled"] = k_enabled
                        found = True
                        break

            if not found:
                kbs.append({
                    "id": (edit_item.get("id") if (is_edit and edit_item) else None) or f"kb_{uuid.uuid4().hex[:8]}",
                    "name": k_name,
                    "key": k_key,
                    "type": k_type,
                    "target": k_target,
                    "enabled": k_enabled,
                })

            # Sync legacy keys
            self._sync_legacy_hotkeys(data, kbs)

            data["custom_keybinds"] = kbs
            try:
                self.save_data(data)
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save keybind data: {e}", parent=dlg)
                return

            if self.hotkey_manager:
                try:
                    self.hotkey_manager.apply_keybinds(kbs, self.root)
                except Exception as e:
                    print(f"[KeybindWindow] Failed to apply keybinds: {e}")

            _close_dlg()
            self.root.after_idle(self._render_keybind_list)

        tk.Button(
            btn_row, text="💾 Save Keybind", font=("Segoe UI", 8, "bold"),
            bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"),
            relief="flat", bd=0, padx=12, pady=3, cursor="hand2", command=_save_keybind
        ).pack(side="right")

        # Dialog keyboard shortcuts (Enter to save, Escape to cancel or close)
        def _on_enter(e):
            if not is_recording[0]:
                _save_keybind()

        def _on_escape(e):
            if is_recording[0]:
                _toggle_recording()
            else:
                _close_dlg()

        dlg.bind("<Return>", _on_enter)
        dlg.bind("<Escape>", _on_escape)
