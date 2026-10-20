"""
git_sync.py
Handles one-way project saves to GitHub in a background thread
and sends status messages back to the pet's speech bubble.

Order of operations matters:
  add -> commit -> pull --rebase --autostash -> push
Pulling BEFORE committing makes git refuse with
"cannot pull with rebase: You have unstaged changes."
"""

import sys
import os
import subprocess
import shutil
import threading
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            getattr(sys.stderr, "reconfigure")(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).parent


def _git(args, timeout=15, check=False):
    """Runs a git command inside the project root completely silently with no popup windows."""
    git_env = os.environ.copy()
    git_env["GIT_TERMINAL_PROMPT"] = "0"
    git_env["GIT_ASKPASS"] = "echo"

    git_exe = shutil.which("git") or "git"

    kwargs = {}
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    return subprocess.run(
        [git_exe] + args,
        cwd=PROJECT_ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
        env=git_env,
        **kwargs,
    )


def _short_error(proc, fallback: str) -> str:
    """Pulls the last meaningful line out of a failed git command."""
    err = (proc.stderr or "").strip() or (proc.stdout or "").strip() or fallback
    lines = [ln.strip() for ln in err.splitlines() if ln.strip()]
    return lines[-1] if lines else fallback


def _run_git_save(commit_msg: str | None = None, on_complete=None):
    if commit_msg is None:
        commit_msg = f"Save project: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def done(ok, msg):
        if on_complete:
            on_complete(ok, msg)

    try:
        # 1. Stage everything first
        add = _git(["add", "-A"], timeout=15)
        if add.returncode != 0:
            done(False, f"Add error: {_short_error(add, 'Stage failed')[:30]}")
            return

        # 2. Commit changes or create named save checkpoint
        commit = _git(["commit", "--allow-empty", "-m", commit_msg], timeout=15)
        if commit.returncode != 0:
            done(False, f"Commit error: {_short_error(commit, 'Commit failed')[:30]}")
            return

        # 3. Fast path: try pushing directly if local is already ahead
        push = _git(["push"], timeout=30)
        if push.returncode == 0:
            done(True, f"Saved as '{commit_msg[:25]}'!")
            return

        # 4. Remote has newer commits: try rebase first
        pull = _git(["pull", "--rebase", "--autostash"], timeout=30)
        if pull.returncode != 0:
            # Rebase encountered conflict: abort rebase and fallback to auto-merge favoring local changes
            _git(["rebase", "--abort"], timeout=10)
            pull_merge = _git(["pull", "--no-rebase", "-X", "ours", "--no-edit"], timeout=30)
            if pull_merge.returncode != 0:
                err = _short_error(pull, "Sync conflict")
                done(False, f"Sync error: {err[:30]}")
                return

        # 5. Final push to GitHub
        push2 = _git(["push"], timeout=30)
        if push2.returncode == 0:
            done(True, f"Saved as '{commit_msg[:25]}'!")
        else:
            done(False, f"Push error: {_short_error(push2, 'Push failed')[:30]}")

    except subprocess.TimeoutExpired:
        done(False, "Git timed out! Check internet.")
    except FileNotFoundError:
        done(False, "Git not installed / not on PATH.")
    except Exception as e:
        done(False, f"Error: {str(e)[:30]}")


def push_to_github_async(commit_msg: str | None = None, on_complete=None):
    """Runs the git save in a background daemon thread."""
    thread = threading.Thread(
        target=_run_git_save,
        args=(commit_msg, on_complete),
        daemon=True,
    )
    thread.start()


def pull_from_github_async(on_complete=None):
    """Pulls latest updates from GitHub in a background daemon thread."""
    def _run():
        def done(ok, msg):
            if on_complete:
                on_complete(ok, msg)

        try:
            # Stash temporary uncommitted changes (like runtime pet coordinates)
            _git(["stash"], timeout=15)
            pull = _git(["pull", "--no-rebase", "-X", "theirs", "--no-edit"], timeout=30)
            _git(["stash", "pop"], timeout=10)

            if pull.returncode == 0:
                done(True, "📥 Updated from GitHub!")
            else:
                err = _short_error(pull, "Pull failed")
                done(False, f"Pull error: {err[:30]}")
        except subprocess.TimeoutExpired:
            done(False, "Git timed out! Check internet.")
        except FileNotFoundError:
            done(False, "Git not installed / not on PATH.")
        except Exception as e:
            done(False, f"Error: {str(e)[:30]}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()