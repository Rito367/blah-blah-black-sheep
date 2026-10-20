"""
decision_window.py
Customizable Decision Maker tool for Desktop Pet:
- Coin Flip with custom Heads & Tails labels
- D6 Dice with custom meanings for all 6 faces
- D20 Dice with target DC & Success/Fail outcome meanings
- Custom Choice List Picker with auto-save
"""

import random
import tkinter as tk
from pathlib import Path
import sys

try:
    import paths
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import paths

import themes


class DecisionWindow:
    def __init__(self, root: tk.Tk, get_data, save_data, on_decision=None, on_menu=None):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.on_decision = on_decision
        self.on_menu = on_menu
        self.win = None
        self._is_rolling = False
        self._active_tab = "coin"

    def hide(self):
        self._on_close()

    def show(self, near_x: int = 100, near_y: int = 100):
        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        t = themes.get()
        self.win = tk.Toplevel(self.root)
        self.win.title("Decision Maker")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 340, 510
        safe_x = max(10, min(near_x, sw - target_w - 10))
        safe_y = max(10, min(near_y, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("border", "#181920"), padx=2, pady=2)
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        self.outer = tk.Frame(self.win, bg=t.get("bg_card", "#20222e"), padx=10, pady=10)
        self.outer.pack(fill="both", expand=True)

        # Header Bar
        hdr = tk.Frame(self.outer, bg=t.get("bg_card", "#20222e"))
        hdr.pack(fill="x", pady=(0, 8))

        tk.Label(
            hdr,
            text="🎯 DECISION MAKER",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("accent", "#e74c3c"),
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")

        close_btn = tk.Label(
            hdr,
            text="✕",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"),
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self._on_close())

        if self.on_menu:
            on_menu = self.on_menu
            mb = tk.Label(hdr, text="☰",
                          bg=t.get("bg_card", "#20222e"),
                          fg=t.get("fg_main", "#ffffff"),
                          font=("Segoe UI", 9, "bold"), cursor="hand2")
            mb.pack(side="right", padx=(0, 6))
            mb.bind("<Button-1>", lambda e: on_menu(close_win=self.win, hide_fn=self.hide))

        # Tab Navigation Bar
        self.nav_frame = tk.Frame(self.outer, bg=t.get("bg_card", "#20222e"))
        self.nav_frame.pack(fill="x", pady=(0, 8))

        self.tab_buttons = {}
        tabs = [("coin", "🪙 Coin"), ("d6", "🎲 D6"), ("d20", "⚔️ D20"), ("list", "✨ List")]
        for key, label in tabs:
            btn = tk.Button(
                self.nav_frame,
                text=label,
                font=("Segoe UI", 8, "bold"),
                bg=t.get("btn", "#2c2e3f"),
                fg=t.get("fg_white", "#ffffff"),
                relief="flat",
                bd=0,
                pady=4,
                cursor="hand2",
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(side="left", expand=True, fill="x", padx=1)
            self.tab_buttons[key] = btn

        # Container for Tab Panels
        self.tab_container = tk.Frame(self.outer, bg=t.get("bg_card", "#20222e"))
        self.tab_container.pack(fill="both", expand=True)

        self._build_coin_tab()
        self._build_d6_tab()
        self._build_d20_tab()
        self._build_list_tab()

        # Bottom Result Banner
        self.result_lbl = tk.Label(
            self.outer,
            text="Ready to decide! 🎯",
            bg=t.get("bg_grid", "#151620"),
            fg=t.get("fg_main", "#ffffff"),
            font=("Segoe UI", 9, "bold"),
            pady=8,
        )
        self.result_lbl.pack(fill="x", pady=(8, 0))

        self._switch_tab("coin")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Tab 1: Coin Flip ──
    def _build_coin_tab(self):
        t = themes.get()
        data = self.get_data()
        self.panel_coin = tk.Frame(self.tab_container, bg=t.get("bg_card", "#20222e"))

        box = tk.LabelFrame(
            self.panel_coin,
            text=" Coin Meanings ",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"),
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=8,
        )
        box.pack(fill="both", expand=True, pady=(0, 8))

        # Heads meaning
        tk.Label(box, text="🪙 Heads represents:", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8)).pack(anchor="w")
        self.coin_heads_entry = tk.Entry(
            box, font=("Segoe UI", 8), bg=t.get("bg_grid", "#151620"), fg=t.get("fg_white", "#ffffff"), insertbackground="#ffffff", relief="flat", bd=0
        )
        self.coin_heads_entry.insert(0, data.get("coin_heads", "Yes / Go for it!"))
        self.coin_heads_entry.pack(fill="x", pady=(2, 8), ipady=3)

        # Tails meaning
        tk.Label(box, text="🪙 Tails represents:", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8)).pack(anchor="w")
        self.coin_tails_entry = tk.Entry(
            box, font=("Segoe UI", 8), bg=t.get("bg_grid", "#151620"), fg=t.get("fg_white", "#ffffff"), insertbackground="#ffffff", relief="flat", bd=0
        )
        self.coin_tails_entry.insert(0, data.get("coin_tails", "No / Take a break!"))
        self.coin_tails_entry.pack(fill="x", pady=(2, 8), ipady=3)

        tk.Button(
            self.panel_coin,
            text="🪙 Flip Coin",
            font=("Segoe UI", 9, "bold"),
            bg=t.get("accent", "#e74c3c"),
            fg=t.get("fg_white", "#ffffff"),
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2",
            command=self._flip_coin,
        ).pack(fill="x")

    # ── Tab 2: D6 Dice (6 Faces) ──
    def _build_d6_tab(self):
        t = themes.get()
        data = self.get_data()
        self.panel_d6 = tk.Frame(self.tab_container, bg=t.get("bg_card", "#20222e"))

        box = tk.LabelFrame(
            self.panel_d6,
            text=" D6 Faces (Sides 1 to 6) ",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"),
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=4,
        )
        box.pack(fill="both", expand=True, pady=(0, 6))

        saved_d6 = data.get("d6_labels", [
            "1: Study / Code",
            "2: Workout / Stretch",
            "3: Read Book",
            "4: Play Game",
            "5: Tidy Room",
            "6: Free Choice",
        ])

        self.d6_entries = []
        for i in range(6):
            row = tk.Frame(box, bg=t.get("bg_card", "#20222e"))
            row.pack(fill="x", pady=1)

            tk.Label(row, text=f"🎲 {i+1}:", width=4, anchor="w", bg=t.get("bg_card", "#20222e"), fg=t.get("accent", "#e74c3c"), font=("Segoe UI", 8, "bold")).pack(side="left")
            entry = tk.Entry(
                row, font=("Segoe UI", 8), bg=t.get("bg_grid", "#151620"), fg=t.get("fg_white", "#ffffff"), insertbackground="#ffffff", relief="flat", bd=0
            )
            val = saved_d6[i] if i < len(saved_d6) else f"Option {i+1}"
            entry.insert(0, val)
            entry.pack(side="left", fill="x", expand=True, ipady=2)
            self.d6_entries.append(entry)

        tk.Button(
            self.panel_d6,
            text="🎲 Roll D6",
            font=("Segoe UI", 9, "bold"),
            bg=t.get("accent", "#e74c3c"),
            fg=t.get("fg_white", "#ffffff"),
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2",
            command=self._roll_d6,
        ).pack(fill="x")

    # ── Tab 3: D20 Dice (Check / Threshold) ──
    def _build_d20_tab(self):
        t = themes.get()
        data = self.get_data()
        self.panel_d20 = tk.Frame(self.tab_container, bg=t.get("bg_card", "#20222e"))

        box = tk.LabelFrame(
            self.panel_d20,
            text=" D20 Challenge / DC Check ",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"),
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=6,
        )
        box.pack(fill="both", expand=True, pady=(0, 6))

        dc_row = tk.Frame(box, bg=t.get("bg_card", "#20222e"))
        dc_row.pack(fill="x", pady=(0, 4))
        tk.Label(dc_row, text="Target Score (DC 1–20):", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 8)).pack(side="left")
        self.d20_dc_spin = tk.Spinbox(
            dc_row, from_=1, to=20, width=4, font=("Segoe UI", 9, "bold"), bg=t.get("bg_grid", "#151620"), fg=t.get("fg_white", "#ffffff"), relief="flat", justify="center"
        )
        self.d20_dc_spin.delete(0, tk.END)
        self.d20_dc_spin.insert(0, str(data.get("d20_target_dc", 10)))
        self.d20_dc_spin.pack(side="right")

        tk.Label(box, text="Pass / Success Outcome (>= Target):", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 7)).pack(anchor="w")
        self.d20_pass_entry = tk.Entry(
            box, font=("Segoe UI", 8), bg=t.get("bg_grid", "#151620"), fg=t.get("fg_white", "#ffffff"), insertbackground="#ffffff", relief="flat", bd=0
        )
        self.d20_pass_entry.insert(0, data.get("d20_pass_text", "Success! Proceed with task."))
        self.d20_pass_entry.pack(fill="x", pady=(1, 6), ipady=2)

        tk.Label(box, text="Fail Outcome (< Target):", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_main", "#ffffff"), font=("Segoe UI", 7)).pack(anchor="w")
        self.d20_fail_entry = tk.Entry(
            box, font=("Segoe UI", 8), bg=t.get("bg_grid", "#151620"), fg=t.get("fg_white", "#ffffff"), insertbackground="#ffffff", relief="flat", bd=0
        )
        self.d20_fail_entry.insert(0, data.get("d20_fail_text", "Failed! Postpone or try alternate."))
        self.d20_fail_entry.pack(fill="x", pady=(1, 4), ipady=2)

        tk.Button(
            self.panel_d20,
            text="⚔️ Roll D20",
            font=("Segoe UI", 9, "bold"),
            bg=t.get("accent", "#e74c3c"),
            fg=t.get("fg_white", "#ffffff"),
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2",
            command=self._roll_d20,
        ).pack(fill="x")

    # ── Tab 4: Custom List Picker ──
    def _build_list_tab(self):
        t = themes.get()
        data = self.get_data()
        self.panel_list = tk.Frame(self.tab_container, bg=t.get("bg_card", "#20222e"))

        box = tk.LabelFrame(
            self.panel_list,
            text=" Custom Choice Picker ",
            bg=t.get("bg_card", "#20222e"),
            fg=t.get("fg_main", "#ffffff"),
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=6,
        )
        box.pack(fill="both", expand=True, pady=(0, 6))

        tk.Label(box, text="Enter items (separated by lines):", bg=t.get("bg_card", "#20222e"), fg=t.get("fg_dim", "#888888"), font=("Segoe UI", 7)).pack(anchor="w")

        self.list_text_area = tk.Text(
            box,
            height=6,
            font=("Segoe UI", 8),
            bg=t.get("bg_grid", "#151620"),
            fg=t.get("fg_white", "#ffffff"),
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            wrap="word",
        )
        self.list_text_area.pack(fill="both", expand=True, pady=(2, 4))

        saved_choices = data.get("custom_decisions", ["Chicken Rice", "Laksa", "Subway", "Ban Mian", "Western"])
        self.list_text_area.insert("1.0", "\n".join(saved_choices) if isinstance(saved_choices, list) else str(saved_choices))

        tk.Button(
            self.panel_list,
            text="✨ Pick Random From List",
            font=("Segoe UI", 9, "bold"),
            bg=t.get("accent", "#e74c3c"),
            fg=t.get("fg_white", "#ffffff"),
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2",
            command=self._pick_list,
        ).pack(fill="x")

    def _switch_tab(self, tab_key: str):
        self._active_tab = tab_key
        t = themes.get()

        for k, btn in self.tab_buttons.items():
            if k == tab_key:
                btn.config(bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"))
            else:
                btn.config(bg=t.get("btn", "#2c2e3f"), fg=t.get("fg_white", "#ffffff"))

        self.panel_coin.pack_forget()
        self.panel_d6.pack_forget()
        self.panel_d20.pack_forget()
        self.panel_list.pack_forget()

        if tab_key == "coin":
            self.panel_coin.pack(fill="both", expand=True)
        elif tab_key == "d6":
            self.panel_d6.pack(fill="both", expand=True)
        elif tab_key == "d20":
            self.panel_d20.pack(fill="both", expand=True)
        elif tab_key == "list":
            self.panel_list.pack(fill="both", expand=True)

    def _save_all_settings(self):
        data = self.get_data()

        # Coin
        data["coin_heads"] = self.coin_heads_entry.get().strip() or "Heads"
        data["coin_tails"] = self.coin_tails_entry.get().strip() or "Tails"

        # D6
        data["d6_labels"] = [e.get().strip() for e in self.d6_entries if e.get().strip()]

        # D20
        try:
            data["d20_target_dc"] = int(self.d20_dc_spin.get().strip())
        except ValueError:
            data["d20_target_dc"] = 10
        data["d20_pass_text"] = self.d20_pass_entry.get().strip()
        data["d20_fail_text"] = self.d20_fail_entry.get().strip()

        # List
        raw_list = self.list_text_area.get("1.0", tk.END).strip()
        if raw_list:
            data["custom_decisions"] = [x.strip() for x in raw_list.split("\n") if x.strip()]

        self.save_data(data)

    def _on_close(self):
        if not self.win or not self.win.winfo_exists():
            return
        self._save_all_settings()
        self.win.destroy()
        self.win = None

    def _animate(self, samples: list, final_result: str, prefix: str):
        if self._is_rolling:
            return
        self._is_rolling = True

        def _step(count):
            if not self.win or not self.win.winfo_exists():
                self._is_rolling = False
                return
            if count < 6:
                sample = random.choice(samples)
                self.result_lbl.config(text=f"Deciding... {sample}")
                self.root.after(70, lambda: _step(count + 1))
            else:
                self.result_lbl.config(text=f"{prefix}: {final_result}")
                self._is_rolling = False
                if self.on_decision:
                    self.on_decision(f"{prefix}\n✨ {final_result} ✨")

        _step(0)

    def _flip_coin(self):
        self._save_all_settings()
        h_text = self.coin_heads_entry.get().strip() or "Heads"
        t_text = self.coin_tails_entry.get().strip() or "Tails"

        side = random.choice(["Heads", "Tails"])
        meaning = h_text if side == "Heads" else t_text
        self._animate(["Heads 🪙", "Tails 🪙"], f"{side} ({meaning})", "Coin Toss")

    def _roll_d6(self):
        self._save_all_settings()
        sides = [e.get().strip() for e in self.d6_entries if e.get().strip()]
        if not sides:
            sides = [f"Side {i+1}" for i in range(6)]

        roll = random.randint(1, len(sides))
        meaning = sides[roll - 1]
        self._animate([f"Side {i+1}" for i in range(len(sides))], f"Rolled {roll} ➔ {meaning}", "D6 Roll")

    def _roll_d20(self):
        self._save_all_settings()
        try:
            target = int(self.d20_dc_spin.get().strip())
        except ValueError:
            target = 10

        pass_txt = self.d20_pass_entry.get().strip() or "Success"
        fail_txt = self.d20_fail_entry.get().strip() or "Fail"

        roll = random.randint(1, 20)
        if roll == 20:
            verdict = f"NAT 20 CRITICAL SUCCESS! 🌟 ({pass_txt})"
        elif roll == 1:
            verdict = f"NAT 1 CRITICAL FAIL! 💀 ({fail_txt})"
        elif roll >= target:
            verdict = f"Rolled {roll} (>= DC {target}): Passed! ({pass_txt})"
        else:
            verdict = f"Rolled {roll} (< DC {target}): Failed! ({fail_txt})"

        self._animate([str(random.randint(1, 20)) for _ in range(10)], verdict, "D20 Check")

    def _pick_list(self):
        self._save_all_settings()
        raw = self.list_text_area.get("1.0", tk.END).strip()
        items = [x.strip() for x in raw.split("\n") if x.strip()]
        if not items:
            self.result_lbl.config(text="Please add items to list first!")
            return

        chosen = random.choice(items)
        self._animate(items, chosen, "I Picked")