"""
tictactoe_window.py
Themed Tic-Tac-Toe pop-up window with live Win/Loss/Draw tracking and difficulty selection.
"""

import tkinter as tk
import random
import themes

WINNING_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]


class TicTacToeWindow:
    def __init__(self, root, get_data=None, save_data=None, on_game_over=None, on_menu=None):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.on_game_over = on_game_over
        self.on_menu = on_menu
        self.win = None
        self.board = [""] * 9
        self.buttons = []
        self.game_active = False
        self.difficulty = "Medium"

    def show(self, near_x=100, near_y=100):
        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            return

        t = themes.get()
        self.win = tk.Toplevel(self.root)
        self.win.title("Tic-Tac-Toe")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 230, 315
        safe_x = max(10, min(near_x, sw - target_w - 10))
        safe_y = max(10, min(near_y, sh - target_h - 40))
        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.attributes("-topmost", True)
        self.win.configure(bg=t.get("bg_card", "#ffffff"))
        self.win.resizable(False, False)
        # Bug #36 fix: handle manual window close gracefully
        self.win.protocol("WM_DELETE_WINDOW", self._on_window_close)

        self.board = [""] * 9
        self.buttons = []
        self.game_active = True

        # ── header bar with menu button ───────────────────────────────────
        hdr_bg = themes.get().get("bg_hdr", "#ffb6c1")
        hdr = tk.Frame(self.win, bg=hdr_bg, pady=3, padx=6)
        hdr.pack(fill="x")
        tk.Label(hdr, text="❌⭕  Tic-Tac-Toe", bg=hdr_bg, fg="#ffffff",
                 font=("Georgia", 8, "bold")).pack(side="left")
        if self.on_menu:
            mb = tk.Label(hdr, text="☰", bg=hdr_bg, fg="#ffffff",
                          font=("Georgia", 8, "bold"), cursor="hand2")
            mb.pack(side="right")
            mb.bind("<Button-1>", lambda e: self.on_menu(close_win=self.win, hide_fn=self.hide))

        title_lbl = tk.Label(
            self.win, text="Tic-Tac-Toe\n(You: ❌ | Pet: ⭕)",
            bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#000000"),
            font=("Georgia", 9, "bold")
        )
        title_lbl.pack(pady=(4, 2))

        # Stats Display Label
        self.score_lbl = tk.Label(
            self.win, text=self._format_stats(),
            bg=t.get("bg_card", "#ffffff"), fg=t.get("fg_main", "#555555"),
            font=("Georgia", 7, "bold")
        )
        self.score_lbl.pack(pady=(0, 2))

        # Difficulty selector frame
        diff_frame = tk.Frame(self.win, bg=t.get("bg_card", "#ffffff"))
        diff_frame.pack(pady=(0, 4))

        self.diff_btns = {}
        for diff in ["Easy", "Medium", "Hard"]:
            mapped_diff = "Unbeatable" if diff == "Hard" else diff
            btn = tk.Button(
                diff_frame, text=diff, font=("Georgia", 7, "bold"),
                relief="flat", bd=0, padx=4, pady=1,
                command=lambda d=mapped_diff: self._set_difficulty(d)
            )
            btn.pack(side="left", padx=2)
            self.diff_btns[mapped_diff] = btn

        self._update_diff_buttons()

        grid_frame = tk.Frame(self.win, bg=t.get("bg_card", "#ffffff"))
        grid_frame.pack(padx=10, pady=2)

        for i in range(9):
            btn = tk.Button(
                grid_frame, text="", font=("Georgia", 14, "bold"),
                width=3, height=1, bg=t.get("btn", "#cccccc"), fg=t.get("fg_white", "#ffffff"),
                activebackground=t.get("fg_main", "#888888"), relief="flat", bd=0,
                command=lambda idx=i: self._user_move(idx)
            )
            btn.grid(row=i // 3, column=i % 3, padx=3, pady=3)
            self.buttons.append(btn)

    def _format_stats(self) -> str:
        if not self.get_data:
            return "W: 0 | L: 0 | D: 0"
        stats = self.get_data().get("ttt_stats", {"wins": 0, "losses": 0, "draws": 0})
        return f"🏆 W: {stats.get('wins', 0)} | 💀 L: {stats.get('losses', 0)} | 🤝 D: {stats.get('draws', 0)}"

    def _update_stats(self, result: str):
        if not self.get_data or not self.save_data:
            return

        data = self.get_data()
        stats = data.setdefault("ttt_stats", {"wins": 0, "losses": 0, "draws": 0})

        if result == "win":
            stats["wins"] = stats.get("wins", 0) + 1
        elif result == "lose":
            stats["losses"] = stats.get("losses", 0) + 1
        elif result == "draw":
            stats["draws"] = stats.get("draws", 0) + 1

        self.save_data(data)
        if hasattr(self, "score_lbl") and self.score_lbl.winfo_exists():
            self.score_lbl.config(text=self._format_stats())

    def _set_difficulty(self, diff: str):
        self.difficulty = diff
        self._update_diff_buttons()

    def _update_diff_buttons(self):
        t = themes.get()
        for diff_name, btn in self.diff_btns.items():
            if self.difficulty == diff_name:
                btn.config(bg=t.get("accent", "#e74c3c"), fg=t.get("fg_white", "#ffffff"))
            else:
                btn.config(bg=t.get("btn", "#cccccc"), fg=t.get("fg_white", "#ffffff"))

    def _user_move(self, idx: int):
        if not self.game_active or self.board[idx] != "":
            return

        self.game_active = False
        self._make_move(idx, "❌")

        res = self._check_result(self.board)
        if res == "❌":
            self._update_stats("win")
            self.win.after(500, self._finish_game, "win")
            return
        elif res == "draw":
            self._update_stats("draw")
            self.win.after(500, self._finish_game, "draw")
            return

        self.win.after(300, self._pet_move)

    def _pet_move(self):
        if not self.win or not self.win.winfo_exists():
            return

        empty_indices = [i for i, val in enumerate(self.board) if val == ""]
        if not empty_indices:
            return

        if self.difficulty == "Easy":
            move = random.choice(empty_indices)
        elif self.difficulty == "Medium":
            if random.random() < 0.5:
                move = self._best_move(self.board)
            else:
                move = random.choice(empty_indices)
        else:
            move = self._best_move(self.board)

        if move is not None:
            self._make_move(move, "⭕")

        res = self._check_result(self.board)
        if res == "⭕":
            self._update_stats("lose")
            self.win.after(500, self._finish_game, "lose")
            return
        elif res == "draw":
            self._update_stats("draw")
            self.win.after(500, self._finish_game, "draw")
            return

        self.game_active = True

    def _make_move(self, idx: int, symbol: str):
        t = themes.get()
        self.board[idx] = symbol
        
        btn_bg = t.get("btn", "#4a4a4a")
        text_color = t.get("fg_white", "#ffffff") if symbol == "❌" else t.get("fg_main", "#ff69b4")

        self.buttons[idx].config(
            text=symbol,
            state="disabled",
            disabledforeground=text_color,
            bg=btn_bg
        )

    def _check_result(self, board):
        for a, b, c in WINNING_LINES:
            if board[a] and board[a] == board[b] == board[c]:
                return board[a]

        if all(cell != "" for cell in board):
            return "draw"

        return None

    def _minimax(self, board, maximizing):
        result = self._check_result(board)

        if result == "⭕":
            return 1
        if result == "❌":
            return -1
        if result == "draw":
            return 0

        if maximizing:
            best_score = -float("inf")
            for i in range(9):
                if board[i] == "":
                    board[i] = "⭕"
                    score = self._minimax(board, False)
                    board[i] = ""
                    best_score = max(best_score, score)
            return best_score
        else:
            best_score = float("inf")
            for i in range(9):
                if board[i] == "":
                    board[i] = "❌"
                    score = self._minimax(board, True)
                    board[i] = ""
                    best_score = min(best_score, score)
            return best_score

    def _best_move(self, board):
        best_score = -float("inf")
        move = None

        for i in range(9):
            if board[i] == "":
                board[i] = "⭕"
                score = self._minimax(board, False)
                board[i] = ""

                if score > best_score:
                    best_score = score
                    move = i

        return move

    def _finish_game(self, result: str):
        self.game_active = False
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None
        if self.on_game_over:
            self.on_game_over(result)

    def hide(self):
        self._on_window_close()

    def _on_window_close(self):
        """Bug #36 fix: user closed window manually mid-game — clean up without firing on_game_over."""
        self.game_active = False
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None