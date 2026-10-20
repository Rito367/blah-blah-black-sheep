"""
chopsticks_window.py
Themed Chopsticks finger game window against the Desktop Pet.
"""

import tkinter as tk
import random
from pathlib import Path
import sys

try:
    import paths
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import paths

import themes


class ChopsticksWindow:
    def __init__(self, root: tk.Tk, on_game_over=None, on_menu=None):
        self.root = root
        self.on_game_over = on_game_over
        self.on_menu = on_menu
        self.win: tk.Toplevel | None = None
        self.player_hands = [1, 1]  # [Left, Right]
        self.pet_hands = [1, 1]     # [Left, Right]
        self.selected_user_hand = None
        self.game_active = False

    def show(self, near_x=100, near_y=100):
        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        t = themes.get()
        self.win = tk.Toplevel(self.root)
        self.win.title("Chopsticks")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 260, 320
        safe_x = max(10, min(near_x, sw - target_w - 10))
        safe_y = max(10, min(near_y, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("bg_card", "#ffffff"))
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self.player_hands = [1, 1]
        self.pet_hands = [1, 1]
        self.selected_user_hand = None
        self.game_active = True

        # ── header bar with menu button ───────────────────────────────────
        hdr_bg = t.get("bg_hdr", "#ffb6c1")
        hdr = tk.Frame(self.win, bg=hdr_bg, pady=3, padx=6)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🥢  Chopsticks", bg=hdr_bg, fg="#ffffff",
                 font=("Georgia", 8, "bold")).pack(side="left")
        if self.on_menu:
            on_menu = self.on_menu
            mb = tk.Label(hdr, text="☰", bg=hdr_bg, fg="#ffffff",
                          font=("Georgia", 8, "bold"), cursor="hand2")
            mb.pack(side="right")
            mb.bind("<Button-1>", lambda e: on_menu(close_win=self.win, hide_fn=self.hide))

        self.status_lbl = tk.Label(
            self.win, text="Chopsticks!\nSelect your hand to attack",
            bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#000000"),
            font=("Georgia", 9, "bold")
        )
        self.status_lbl.pack(pady=8)

        pet_frame = tk.LabelFrame(
            self.win, text="Pet's Hands", bg=t.get("bg_card", "#ffffff"),
            fg=t.get("fg_main", "#000000"), font=("Georgia", 8, "bold")
        )
        pet_frame.pack(padx=10, pady=5, fill="x")

        self.pet_btn_l = tk.Button(
            pet_frame, text="L: 1", font=("Georgia", 11, "bold"),
            width=8, bg=t.get("btn", "#cccccc"), fg=t.get("fg_white", "#ffffff"),
            command=lambda: self._on_pet_hand_click(0)
        )
        self.pet_btn_l.pack(side="left", padx=10, pady=5)

        self.pet_btn_r = tk.Button(
            pet_frame, text="R: 1", font=("Georgia", 11, "bold"),
            width=8, bg=t.get("btn", "#cccccc"), fg=t.get("fg_white", "#ffffff"),
            command=lambda: self._on_pet_hand_click(1)
        )
        self.pet_btn_r.pack(side="right", padx=10, pady=5)

        user_frame = tk.LabelFrame(
            self.win, text="Your Hands", bg=t.get("bg_card", "#ffffff"),
            fg=t.get("fg_main", "#000000"), font=("Georgia", 8, "bold")
        )
        user_frame.pack(padx=10, pady=5, fill="x")

        self.user_btn_l = tk.Button(
            user_frame, text="L: 1", font=("Georgia", 11, "bold"),
            width=8, bg=t.get("btn", "#cccccc"), fg=t.get("fg_white", "#ffffff"),
            command=lambda: self._on_user_hand_click(0)
        )
        self.user_btn_l.pack(side="left", padx=10, pady=5)

        self.user_btn_r = tk.Button(
            user_frame, text="R: 1", font=("Georgia", 11, "bold"),
            width=8, bg=t.get("btn", "#cccccc"), fg=t.get("fg_white", "#ffffff"),
            command=lambda: self._on_user_hand_click(1)
        )
        self.user_btn_r.pack(side="right", padx=10, pady=5)

        self.split_btn = tk.Button(
            self.win, text="🔄 Split / Transfer", font=("Georgia", 9, "bold"),
            bg=t.get("btn", "#cccccc"), fg=t.get("fg_white", "#ffffff"),
            command=self._on_split_click
        )
        self.split_btn.pack(pady=10)

        self._update_ui()

    def _update_ui(self):
        t = themes.get()
        for idx, btn in enumerate([self.pet_btn_l, self.pet_btn_r]):
            val = self.pet_hands[idx]
            txt = f"L: {val}" if idx == 0 else f"R: {val}"
            if val == 0:
                txt += " ✊"
                btn.config(text=txt, state="disabled", bg="#888888")
            else:
                btn.config(text=txt, state="normal" if self.game_active else "disabled", bg=t.get("btn", "#cccccc"))

        for idx, btn in enumerate([self.user_btn_l, self.user_btn_r]):
            val = self.player_hands[idx]
            txt = f"L: {val}" if idx == 0 else f"R: {val}"
            if val == 0:
                txt += " ✊"
                btn.config(text=txt, state="disabled", bg="#888888")
            else:
                bg_color = "#e74c3c" if self.selected_user_hand == idx else t.get("btn", "#cccccc")
                btn.config(text=txt, state="normal" if self.game_active else "disabled", bg=bg_color)

        valid_splits = self._get_valid_splits(self.player_hands)
        if valid_splits and self.game_active:
            self.split_btn.config(state="normal")
        else:
            self.split_btn.config(state="disabled")

    def _on_user_hand_click(self, idx: int):
        if not self.game_active or self.player_hands[idx] == 0:
            return
        self.selected_user_hand = idx
        self.status_lbl.config(text=f"Selected {'Left' if idx==0 else 'Right'} hand!\nClick Pet's hand to tap.")
        self._update_ui()

    def _on_pet_hand_click(self, pet_idx: int):
        if not self.game_active or self.selected_user_hand is None or self.pet_hands[pet_idx] == 0:
            return

        user_val = self.player_hands[self.selected_user_hand]
        pet_val = self.pet_hands[pet_idx]

        new_val = (user_val + pet_val) % 5
        self.pet_hands[pet_idx] = new_val

        self.selected_user_hand = None
        self._update_ui()

        if self.pet_hands == [0, 0]:
            self.game_active = False
            self.status_lbl.config(text="You knocked out both pet hands!")
            if self.win:
                self.win.after(800, lambda: self._finish_game("win"))
            return

        self.game_active = False
        self.status_lbl.config(text="Pet is thinking...")
        if self.win:
            self.win.after(600, self._pet_turn)

    def _on_split_click(self):
        if not self.game_active or not self.win or not self.win.winfo_exists():
            return

        valid = self._get_valid_splits(self.player_hands)
        if not valid:
            return

        t = themes.get()
        split_menu = tk.Menu(
            self.win, tearoff=0,
            bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#000000"),
            activebackground=t.get("btn", "#cccccc"), activeforeground=t.get("fg_white", "#ffffff"),
            font=("Georgia", 9, "bold")
        )

        for s_left, s_right in valid:
            label = f"Set to [ L: {s_left} | R: {s_right} ]"
            split_menu.add_command(
                label=label,
                command=lambda l=s_left, r=s_right: self._apply_split(l, r)
            )

        if self.win:
            split_menu.tk_popup(self.win.winfo_pointerx(), self.win.winfo_pointery())

    def _apply_split(self, left: int, right: int):
        self.player_hands = [left, right]
        self.selected_user_hand = None
        self._update_ui()

        self.game_active = False
        self.status_lbl.config(text="Split applied! Pet is thinking...")
        if self.win:
            self.win.after(600, self._pet_turn)

    def _get_valid_splits(self, hands: list[int]) -> list[tuple[int, int]]:
        total = sum(hands)
        valid = []
        for l in range(5):
            r = total - l
            if 0 <= r < 5:
                if [l, r] != hands and [r, l] != hands:
                    if (l, r) not in valid:
                        valid.append((l, r))
        return valid

    def _pet_turn(self):
        if not self.win or not self.win.winfo_exists():
            return

        moves = []
        for p_idx, p_val in enumerate(self.pet_hands):
            if p_val == 0:
                continue
            for u_idx, u_val in enumerate(self.player_hands):
                if u_val == 0:
                    continue
                res = (p_val + u_val) % 5
                moves.append((p_idx, u_idx, res))

        knockout_moves = [m for m in moves if m[2] == 0]

        if knockout_moves:
            chosen = random.choice(knockout_moves)
            p_idx, u_idx, res = chosen
            self.player_hands[u_idx] = res
        else:
            # Consider splitting to revive a dead hand
            valid_splits = self._get_valid_splits(self.pet_hands)
            revive_splits = [
                (l, r) for l, r in valid_splits
                if 0 in self.pet_hands and l > 0 and r > 0
            ]
            if revive_splits:
                sl, sr = random.choice(revive_splits)
                self.pet_hands = [sl, sr]
            elif moves:
                chosen = random.choice(moves)
                p_idx, u_idx, res = chosen
                self.player_hands[u_idx] = res

        if self.player_hands == [0, 0]:
            self._update_ui()
            self.status_lbl.config(text="Pet won!")
            if self.win:
                self.win.after(800, lambda: self._finish_game("lose"))
            return

        self.game_active = True
        self.status_lbl.config(text="Your turn: Select your hand")
        self._update_ui()

    def _finish_game(self, result: str):
        self.game_active = False
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None
        if self.on_game_over:
            self.on_game_over(result)

    def _on_window_close(self):
        self.game_active = False
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None

    def hide(self):
        self._on_window_close()