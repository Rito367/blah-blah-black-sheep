"""
password_dialog.py
Custom UI dialogs for Menu Password Protection in Desktop Pet:
1. PasswordUnlockDialog: Fast, beautiful popup at cursor to unlock menus.
2. PasswordManagerWindow: Comprehensive settings UI to configure, change, or remove password.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Any, Callable

_CUR_DIR = os.path.dirname(os.path.abspath(__file__))
if _CUR_DIR not in sys.path:
    sys.path.insert(0, _CUR_DIR)

import themes


class PasswordUnlockDialog:
    """Sleek modal popup that prompts for password before granting access to pet menus."""

    def __init__(self, root: tk.Tk, get_data: Callable[[], dict[str, Any]], save_data: Callable[[dict[str, Any]], None]):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.win: tk.Toplevel | None = None
        self.entry: tk.Entry | None = None
        self.toggle_btn: tk.Button | None = None
        self.err_lbl: tk.Label | None = None
        self.on_success: Callable[[], None] | None = None
        self.on_fail: Callable[[], None] | None = None
        self._show_plain: bool = False
        self._is_shaking: bool = False

    def hide(self) -> None:
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None

    def show(self, near_x: int, near_y: int, on_success: Callable[[], None], on_fail: Callable[[], None] | None = None) -> None:
        self.on_success = on_success
        self.on_fail = on_fail
        self._show_plain = False

        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            if self.entry is not None:
                self.entry.focus_set()
                self.entry.select_range(0, tk.END)
            return

        t = themes.get()
        self.win = tk.Toplevel(self.root)
        self.win.title("Menu Security")
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        self.win.configure(bg=t.get("bg_card", "#ffffff"))
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        target_w, target_h = 300, 200
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        safe_x = max(10, min(near_x - target_w // 2, sw - target_w - 10))
        safe_y = max(10, min(near_y - 20, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")

        # ── Header Bar ────────────────────────────────────────────────────────
        hdr_bg = t.get("bg_hdr", "#ffb6c1")
        hdr = tk.Frame(self.win, bg=hdr_bg, pady=4, padx=10)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="🔐 Menu Security", bg=hdr_bg,
            fg=t.get("fg_white", "#ffffff"), font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        close_btn = tk.Label(
            hdr, text="✕", bg=hdr_bg, fg=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.hide())

        # ── Body Content ──────────────────────────────────────────────────────
        body = tk.Frame(self.win, bg=t.get("bg_card", "#ffffff"), padx=14, pady=10)
        body.pack(fill="both", expand=True)

        tk.Label(
            body, text="Enter password to open menu:",
            bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#333333"),
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(0, 6))

        # Input row with Show/Hide Eye Toggle
        input_row = tk.Frame(body, bg=t.get("bg_card", "#ffffff"))
        input_row.pack(fill="x", pady=(0, 4))

        self.entry = tk.Entry(
            input_row, show="•", font=("Segoe UI", 10),
            relief="solid", bd=1, bg="#ffffff", fg="#222222"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.entry.focus_set()

        self.toggle_btn = tk.Button(
            input_row, text="👁️", font=("Segoe UI", 8),
            relief="flat", bd=0, padx=5, pady=2,
            bg=t.get("btn", "#e0e0e0"), fg=t.get("fg_main", "#333333"),
            command=self._toggle_show
        )
        self.toggle_btn.pack(side="right")

        # Password Hint display (if configured)
        data = self.get_data()
        hint = data.get("menu_password_hint", "").strip()
        if hint:
            tk.Label(
                body, text=f"💡 Hint: {hint}",
                bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_dim", "#777777"),
                font=("Segoe UI", 8, "italic"), wraplength=270, justify="left"
            ).pack(anchor="w", pady=(0, 2))

        # Error notification label
        self.err_lbl = tk.Label(
            body, text="",
            bg=t.get("bg_card", "#ffffff"), fg="#e74c3c",
            font=("Segoe UI", 8, "bold")
        )
        self.err_lbl.pack(anchor="w", pady=(0, 6))

        # Action button row
        btn_row = tk.Frame(body, bg=t.get("bg_card", "#ffffff"))
        btn_row.pack(fill="x", pady=(4, 0))

        unlock_btn = tk.Button(
            btn_row, text="🔓 Unlock Menu",
            font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
            bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"),
            padx=10, pady=5, cursor="hand2",
            command=self._verify_password
        )
        unlock_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        cancel_btn = tk.Button(
            btn_row, text="Cancel",
            font=("Segoe UI", 8), relief="flat", bd=0,
            bg=t.get("btn", "#e0e0e0"), fg=t.get("fg_main", "#333333"),
            padx=10, pady=5, cursor="hand2",
            command=self.hide
        )
        cancel_btn.pack(side="right", expand=True, fill="x", padx=(4, 0))

        # Keyboard shortcuts
        self.win.bind("<Return>", lambda e: self._verify_password())
        self.win.bind("<Escape>", lambda e: self.hide())

    def _toggle_show(self) -> None:
        self._show_plain = not self._show_plain
        if self.entry is not None:
            self.entry.configure(show="" if self._show_plain else "•")
        if self.toggle_btn is not None:
            self.toggle_btn.configure(text="🙈" if self._show_plain else "👁️")

    def _verify_password(self) -> None:
        if self.entry is None:
            return
        entered = self.entry.get()
        data = self.get_data()
        correct = str(data.get("menu_password", ""))

        if entered == correct:
            cb = self.on_success
            self.hide()
            if cb:
                cb()
        else:
            if self.err_lbl is not None:
                self.err_lbl.configure(text="❌ Incorrect password! Please try again.")
            self._shake()
            self.entry.select_range(0, tk.END)
            self.entry.focus_set()
            if self.on_fail:
                self.on_fail()

    def _shake(self) -> None:
        """Playful horizontal shake animation on incorrect password entry."""
        if not self.win or not self.win.winfo_exists() or self._is_shaking:
            return

        self._is_shaking = True
        orig_x = self.win.winfo_x()
        orig_y = self.win.winfo_y()

        offsets = [8, -8, 6, -6, 4, -4, 2, -2, 0]

        def _step(idx: int) -> None:
            if not self.win or not self.win.winfo_exists():
                self._is_shaking = False
                return
            if idx < len(offsets):
                dx = offsets[idx]
                self.win.geometry(f"+{orig_x + dx}+{orig_y}")
                self.win.after(22, lambda: _step(idx + 1))
            else:
                self.win.geometry(f"+{orig_x}+{orig_y}")
                self._is_shaking = False

        _step(0)


class PasswordManagerWindow:
    """Full settings and configuration window for setting, changing, or removing the menu password."""

    def __init__(
        self,
        root: tk.Tk,
        get_data: Callable[[], dict[str, Any]],
        save_data: Callable[[dict[str, Any]], None],
        on_updated: Callable[[], None] | None = None,
    ):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.on_updated = on_updated
        self.win: tk.Toplevel | None = None
        self._show_pass: bool = False
        self.curr_entry: tk.Entry | None = None
        self.new_entry: tk.Entry | None = None
        self.confirm_entry: tk.Entry | None = None
        self.hint_entry: tk.Entry | None = None
        self.enabled_var: tk.BooleanVar | None = None
        self.toggle_btn: tk.Button | None = None

    def hide(self) -> None:
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None

    def show(self, near_x: int = 200, near_y: int = 200) -> None:
        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        t = themes.get()
        data = self.get_data()
        current_pass = str(data.get("menu_password", ""))
        is_enabled = bool(data.get("menu_password_enabled", True))
        has_existing = bool(current_pass)

        self.win = tk.Toplevel(self.root)
        self.win.title("Menu Security & Password")
        self.win.attributes("-topmost", True)
        self.win.resizable(False, False)
        self.win.configure(bg=t.get("bg_card", "#ffffff"))
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        target_w, target_h = 340, 380 if has_existing else 330
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        safe_x = max(10, min(near_x - target_w // 2, sw - target_w - 10))
        safe_y = max(10, min(near_y - 20, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")

        # ── Header ────────────────────────────────────────────────────────────
        hdr_bg = t.get("bg_hdr", "#ffb6c1")
        hdr = tk.Frame(self.win, bg=hdr_bg, pady=5, padx=10)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="🛡️ Menu Password Settings", bg=hdr_bg,
            fg=t.get("fg_white", "#ffffff"), font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        close_btn = tk.Label(
            hdr, text="✕", bg=hdr_bg, fg=t.get("fg_white", "#ffffff"),
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.hide())

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self.win, bg=t.get("bg_card", "#ffffff"), padx=16, pady=12)
        body.pack(fill="both", expand=True)

        # Status badge
        status_bg = "#e8f5e9" if (is_enabled and has_existing) else "#f5f5f5"
        status_fg = "#2e7d32" if (is_enabled and has_existing) else "#757575"
        status_text = "🔒 Password Protection: ACTIVE" if (is_enabled and has_existing) else "🔓 Password Protection: NOT SET / DISABLED"

        status_frame = tk.Frame(body, bg=status_bg, padx=10, pady=5)
        status_frame.pack(fill="x", pady=(0, 10))
        tk.Label(
            status_frame, text=status_text, bg=status_bg, fg=status_fg,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        # Enable checkbox
        self.enabled_var = tk.BooleanVar(value=is_enabled)
        chk = tk.Checkbutton(
            body, text="Require password to open pet menus",
            variable=self.enabled_var,
            bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#333333"),
            activebackground=t.get("bg_card", "#ffffff"),
            font=("Segoe UI", 9, "bold")
        )
        chk.pack(anchor="w", pady=(0, 8))

        # Current password row (only if already set)
        self.curr_entry = None
        if has_existing:
            tk.Label(
                body, text="Current Password:",
                bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#333333"),
                font=("Segoe UI", 8, "bold")
            ).pack(anchor="w")
            self.curr_entry = tk.Entry(body, show="•", font=("Segoe UI", 9), relief="solid", bd=1)
            self.curr_entry.pack(fill="x", pady=(2, 6))

        # New Password
        tk.Label(
            body, text="New Password:" if has_existing else "Choose Password:",
            bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#333333"),
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        new_pass_frame = tk.Frame(body, bg=t.get("bg_card", "#ffffff"))
        new_pass_frame.pack(fill="x", pady=(2, 6))

        self.new_entry = tk.Entry(new_pass_frame, show="•", font=("Segoe UI", 9), relief="solid", bd=1)
        self.new_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.toggle_btn = tk.Button(
            new_pass_frame, text="👁️", font=("Segoe UI", 8),
            relief="flat", bd=0, padx=5, pady=2,
            bg=t.get("btn", "#e0e0e0"), fg=t.get("fg_main", "#333333"),
            command=self._toggle_show
        )
        self.toggle_btn.pack(side="right")

        # Confirm Password
        tk.Label(
            body, text="Confirm Password:",
            bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#333333"),
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")
        self.confirm_entry = tk.Entry(body, show="•", font=("Segoe UI", 9), relief="solid", bd=1)
        self.confirm_entry.pack(fill="x", pady=(2, 6))

        # Password Hint
        tk.Label(
            body, text="Password Hint (Optional):",
            bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#333333"),
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")
        self.hint_entry = tk.Entry(body, font=("Segoe UI", 9), relief="solid", bd=1)
        self.hint_entry.insert(0, data.get("menu_password_hint", ""))
        self.hint_entry.pack(fill="x", pady=(2, 10))

        # ── Action Buttons ────────────────────────────────────────────────────
        btn_frame = tk.Frame(body, bg=t.get("bg_card", "#ffffff"))
        btn_frame.pack(fill="x", pady=(6, 0))

        save_btn = tk.Button(
            btn_frame, text="💾 Save Password",
            font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
            bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"),
            padx=10, pady=5, cursor="hand2", command=self._save_password
        )
        save_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        if has_existing:
            remove_btn = tk.Button(
                btn_frame, text="🗑️ Remove Lock",
                font=("Segoe UI", 8), relief="flat", bd=0,
                bg="#f44336", fg="#ffffff",
                padx=8, pady=5, cursor="hand2", command=self._remove_password
            )
            remove_btn.pack(side="left", expand=True, fill="x", padx=(2, 4))

        cancel_btn = tk.Button(
            btn_frame, text="Cancel",
            font=("Segoe UI", 8), relief="flat", bd=0,
            bg=t.get("btn", "#e0e0e0"), fg=t.get("fg_main", "#333333"),
            padx=10, pady=5, cursor="hand2", command=self.hide
        )
        cancel_btn.pack(side="right", expand=True, fill="x", padx=(4, 0))

        self.win.bind("<Escape>", lambda e: self.hide())
        if self.curr_entry:
            self.curr_entry.focus_set()
        elif self.new_entry:
            self.new_entry.focus_set()

    def _toggle_show(self) -> None:
        self._show_pass = not self._show_pass
        show_char = "" if self._show_pass else "•"
        if self.new_entry is not None:
            self.new_entry.configure(show=show_char)
        if self.confirm_entry is not None:
            self.confirm_entry.configure(show=show_char)
        if self.curr_entry is not None:
            self.curr_entry.configure(show=show_char)
        if self.toggle_btn is not None:
            self.toggle_btn.configure(text="🙈" if self._show_pass else "👁️")

    def _save_password(self) -> None:
        win: tk.Misc = self.win if self.win is not None else self.root
        data = self.get_data()
        current_pass = str(data.get("menu_password", ""))
        has_existing = bool(current_pass)

        # If existing password, verify current password first
        if has_existing and self.curr_entry is not None:
            typed_curr = self.curr_entry.get()
            if typed_curr != current_pass:
                messagebox.showerror(
                    "Security Verification Failed",
                    "The current password you entered is incorrect.",
                    parent=win
                )
                return

        new_pass = self.new_entry.get() if self.new_entry is not None else ""
        confirm_pass = self.confirm_entry.get() if self.confirm_entry is not None else ""
        is_enabled = self.enabled_var.get() if self.enabled_var is not None else True
        hint_text = self.hint_entry.get().strip() if self.hint_entry is not None else ""

        # If checkbox is disabled and no new password typed, just save the enabled state
        if not is_enabled and not new_pass:
            data["menu_password_enabled"] = False
            self.save_data(data)
            if self.on_updated:
                self.on_updated()
            messagebox.showinfo("Security Updated", "Menu password protection has been disabled.", parent=win)
            self.hide()
            return

        if not new_pass:
            if not has_existing:
                messagebox.showerror("Error", "Password cannot be empty.", parent=win)
                return
            # User kept existing password, just updated enabled status or hint
            new_pass = current_pass
        else:
            if new_pass != confirm_pass:
                messagebox.showerror("Error", "New Password and Confirm Password do not match.", parent=win)
                return

        data["menu_password"] = new_pass
        data["menu_password_enabled"] = is_enabled
        data["menu_password_hint"] = hint_text
        self.save_data(data)

        if self.on_updated:
            self.on_updated()

        messagebox.showinfo(
            "Password Saved",
            "Menu password protection settings have been saved successfully!",
            parent=win
        )
        self.hide()

    def _remove_password(self) -> None:
        win: tk.Misc = self.win if self.win is not None else self.root
        data = self.get_data()
        current_pass = str(data.get("menu_password", ""))

        if current_pass and self.curr_entry is not None:
            typed_curr = self.curr_entry.get()
            if typed_curr != current_pass:
                messagebox.showerror(
                    "Security Verification Failed",
                    "Enter your current password before removing protection.",
                    parent=win
                )
                return

        confirm = messagebox.askyesno(
            "Remove Password",
            "Are you sure you want to completely remove the menu password protection?",
            parent=win
        )
        if confirm:
            data["menu_password"] = ""
            data["menu_password_enabled"] = False
            data["menu_password_hint"] = ""
            self.save_data(data)
            if self.on_updated:
                self.on_updated()
            messagebox.showinfo("Password Removed", "Menu password has been removed.", parent=win)
            self.hide()
