"""
sound_manager.py
Centralized manager for whip hit sound effects.
Supports:
- Dynamic discovery of whip_hit audio files in assets/
- Equal chance-based random selection pool
- Configurable per-sound playback duration (0 = Full sound, >0 = seconds cutoff)
- Uploading and indexing custom audio files (.wav, .mp3, .ogg, .m4a)
- Safe deletion with COM/WMP handle release
- Audio preview player with accurate duration stop
"""

from __future__ import annotations

import re
import random
import shutil
import ctypes
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

import data_store

try:
    import paths
    ASSETS_DIR = paths.ASSETS_DIR
except ImportError:
    ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
WHIP_CRACK_SOUND = ASSETS_DIR / "whip_crack.wav"
WHIP_HIT_SOUND = ASSETS_DIR / "whip_hit.wav"
WHIP_HIT_TRIMMED = ASSETS_DIR / "whip_hit_trimmed.wav"
BOMB_EXPLOSION_SOUND = ASSETS_DIR / "bomb_explosion.wav"
PET_SCREAM_SOUND = ASSETS_DIR / "pet_scream.wav"

SUPPORTED_EXTENSIONS = (".wav", ".mp3", ".ogg", ".m4a")


@dataclass
class HitSoundInfo:
    path: Path
    filename: str
    display_name: str
    index: int
    duration: float        # 0.0 = Full sound, >0 = play for X seconds
    chance_percent: float  # e.g. 25.0
    is_default: bool       # True for base hit sound (Sound 1)


def _get_base_hit_sound() -> Path:
    """Returns the primary hit sound (prefer trimmed 2s-3s slice if it exists)."""
    if WHIP_HIT_TRIMMED.exists():
        return WHIP_HIT_TRIMMED
    return WHIP_HIT_SOUND


def get_sound_durations() -> dict[str, float]:
    """Loads configured sound durations from pet_data.json."""
    try:
        data = data_store.load()
        durations = data.get("whip_sound_durations", {})
        if isinstance(durations, dict):
            return {str(k): float(v) for k, v in durations.items()}
    except Exception:
        pass
    return {}


def get_sound_duration(filename: str) -> float:
    """
    Returns configured duration for a sound in seconds.
    0.0 means Full sound.
    Defaults:
      - 'whip_hit.wav' / 'whip_hit_trimmed.wav': 1.0s (as requested)
      - All other sounds: 0.0s (Full sound)
    """
    durations = get_sound_durations()
    if filename in durations:
        return max(0.0, durations[filename])

    # Default rules
    if filename in ("whip_hit.wav", "whip_hit_trimmed.wav"):
        return 1.0
    return 0.0


def set_sound_duration(filename: str, duration: float) -> None:
    """Saves duration preference for a given sound file."""
    try:
        data = data_store.load()
        raw_durations = data.get("whip_sound_durations", {})
        durations: dict[str, float] = {}
        if isinstance(raw_durations, dict):
            for k, v in raw_durations.items():
                try:
                    durations[str(k)] = float(v)
                except (ValueError, TypeError):
                    pass
        durations[filename] = round(max(0.0, duration), 2)
        data["whip_sound_durations"] = durations
        data_store.save(data)
    except Exception:
        pass


def _extract_sound_index(path: Path) -> int:
    """Extracts integer index from filename like whip_hit_2.wav -> 2."""
    stem = path.stem.lower()
    if stem in ("whip_hit", "whip_hit_trimmed"):
        return 1
    m = re.match(r"^whip_hit_(\d+)", stem)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return 999


def _generate_display_name(path: Path, index: int, is_default: bool) -> str:
    """Generates a clean human-readable name for UI lists."""
    if is_default:
        return "Sound 1 (Default Base Hit)"

    stem = path.stem
    # If name is whip_hit_4_vineboom, extract vineboom
    m = re.match(r"^whip_hit_\d+_(.+)$", stem)
    if m:
        original_label = m.group(1).replace("_", " ").title()
        return f"Sound {index} ({original_label})"

    m2 = re.match(r"^whip_hit_(\d+)$", stem)
    if m2:
        return f"Sound {m2.group(1)}"

    return f"Sound {index} ({path.name})"


def get_hit_sounds() -> list[HitSoundInfo]:
    """
    Discovers all hit sound files in assets/ matching whip_hit*.
    Computes equal random chance percentage and duration for each sound.
    """
    sound_files: list[Path] = []
    base_sound = _get_base_hit_sound()

    if base_sound.exists():
        sound_files.append(base_sound)

    # Scan for any additional whip_hit_* audio files in ASSETS_DIR
    if ASSETS_DIR.exists():
        for file in ASSETS_DIR.iterdir():
            if not file.is_file():
                continue
            if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            fname = file.name.lower()
            if not fname.startswith("whip_hit_"):
                continue
            if fname in ("whip_hit_trimmed.wav", "whip_hit.wav"):
                continue
            if file not in sound_files:
                sound_files.append(file)

    # Sort files: base sound first, then by index, then filename
    def sort_key(p: Path) -> tuple[int, str]:
        if p.resolve() == base_sound.resolve():
            return (1, "")
        idx = _get_sound_index_for_path(p)
        return (idx, p.name.lower())

    sound_files.sort(key=sort_key)

    total_sounds = len(sound_files)
    chance_per_sound = round(100.0 / total_sounds, 1) if total_sounds > 0 else 0.0

    result: list[HitSoundInfo] = []
    for pos, sound_path in enumerate(sound_files, start=1):
        is_default = (sound_path.resolve() == base_sound.resolve())
        # Index can be the sequential position or parsed index
        idx = 1 if is_default else pos
        duration = get_sound_duration(sound_path.name)
        display_name = _generate_display_name(sound_path, idx, is_default)

        result.append(
            HitSoundInfo(
                path=sound_path,
                filename=sound_path.name,
                display_name=display_name,
                index=idx,
                duration=duration,
                chance_percent=chance_per_sound,
                is_default=is_default,
            )
        )

    return result


def _get_sound_index_for_path(p: Path) -> int:
    return _extract_sound_index(p)


def get_random_hit_sound() -> tuple[Path, float] | None:
    """
    Picks a random hit sound from the available pool with uniform chance.
    Returns (sound_path, duration_seconds) or None if no sounds exist.
    """
    sounds = get_hit_sounds()
    if not sounds:
        return None
    chosen = random.choice(sounds)
    return (chosen.path, chosen.duration)


def add_custom_sound(src_file: Path | str) -> HitSoundInfo:
    """
    Copies an audio file into assets/ as whip_hit_{next_idx}_{clean_stem}.ext.
    Automatically assigns it to the chance pool and sets default duration (0.0 = Full).
    """
    src_path = Path(src_file)
    if not src_path.exists():
        raise FileNotFoundError(f"Selected audio file does not exist: {src_path}")

    ext = src_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported audio format '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")

    # Find highest existing index
    existing_sounds = get_hit_sounds()
    highest_idx = 3
    for s in existing_sounds:
        if s.index > highest_idx:
            highest_idx = s.index
    next_idx = highest_idx + 1

    clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", src_path.stem).strip("_")
    if not clean_stem:
        clean_stem = "custom"

    dest_filename = f"whip_hit_{next_idx}_{clean_stem}{ext}"
    dest_path = ASSETS_DIR / dest_filename

    # Ensure ASSETS_DIR exists
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # Release preview lock if needed
    stop_preview()

    # Copy file into assets
    shutil.copy2(src_path, dest_path)

    # Set default duration to 0.0 (Full sound)
    set_sound_duration(dest_filename, 0.0)

    # Refresh sounds and return info for newly added sound
    all_sounds = get_hit_sounds()
    for s in all_sounds:
        if s.path.name == dest_filename:
            return s

    return HitSoundInfo(
        path=dest_path,
        filename=dest_filename,
        display_name=f"Sound {next_idx} ({clean_stem})",
        index=next_idx,
        duration=0.0,
        chance_percent=round(100.0 / len(all_sounds), 1) if all_sounds else 100.0,
        is_default=False,
    )


def delete_custom_sound(sound_path: Path | str) -> bool:
    """
    Safely deletes a custom sound file, releasing any active audio handles first.
    Base sound 1 cannot be deleted.
    """
    path = Path(sound_path)
    base_sound = _get_base_hit_sound()

    if path.resolve() == base_sound.resolve() or path.name in ("whip_hit.wav", "whip_hit_trimmed.wav"):
        return False  # Base sound is protected

    # Stop preview player and hit channel to ensure file handles are released
    stop_preview()
    stop_hit_sound()

    try:
        if path.exists():
            path.unlink()

        # Remove from saved durations
        data = data_store.load()
        durations = data.get("whip_sound_durations", {})
        if isinstance(durations, dict) and path.name in durations:
            del durations[path.name]
            data["whip_sound_durations"] = durations
            data_store.save(data)

        return True
    except Exception as e:
        print(f"Failed to delete sound {path}: {e}")
        return False


# ── Native Windows Multi-Channel MCI Sound Engine ──────────────────────

def _mci_send(cmd: str) -> int:
    """Safely executes an MCI command string via winmm.dll."""
    try:
        if hasattr(ctypes, "windll") and hasattr(ctypes.windll, "winmm"):
            return ctypes.windll.winmm.mciSendStringW(cmd, None, 0, 0)
    except Exception:
        pass
    return -1


def _get_mci_path(path: Path | str) -> str:
    """Returns safe 8.3 short path on Windows or quoted path."""
    p_str = str(Path(path).resolve())
    try:
        buf = ctypes.create_unicode_buffer(512)
        res = ctypes.windll.kernel32.GetShortPathNameW(p_str, buf, 512)
        if res > 0 and buf.value:
            return buf.value
    except Exception:
        pass
    return f'"{p_str}"'


_crack_loaded_file: str | None = None


def play_crack_sound() -> None:
    """
    Plays the whip crack sound on its dedicated 'mci_crack' channel.
    Runs concurrently with any hit sound without stopping or interrupting it.
    """
    global _crack_loaded_file
    if not WHIP_CRACK_SOUND.exists():
        return

    mci_path = _get_mci_path(WHIP_CRACK_SOUND)
    sound_key = str(WHIP_CRACK_SOUND.resolve())

    # Fast path: already open, rewind and play
    if _crack_loaded_file == sound_key:
        err = _mci_send("play mci_crack from 0")
        if err == 0:
            return

    # Open channel
    _mci_send("stop mci_crack")
    _mci_send("close mci_crack")
    err = _mci_send(f"open {mci_path} alias mci_crack")
    if err == 0:
        _crack_loaded_file = sound_key
        _mci_send("play mci_crack from 0")
        return

    # Fallback to winsound
    try:
        import winsound
        winsound.PlaySound(str(WHIP_CRACK_SOUND), winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass


_hit_loaded_file: str | None = None
_hit_stop_timer: Any = None
_hit_tk_root: Any = None


def play_hit_sound(sound_path: Path | str, duration_sec: float = 0.0, tk_root: Any = None) -> None:
    """
    Plays a hit reaction sound on its dedicated 'mci_hit' channel.
    Runs concurrently with the whip crack sound without stopping or interrupting it.
    """
    global _hit_loaded_file, _hit_stop_timer, _hit_tk_root
    path = Path(sound_path)
    if not path.exists():
        return

    # Cancel previous hit auto-stop timer
    if _hit_stop_timer and _hit_tk_root:
        try:
            _hit_tk_root.after_cancel(_hit_stop_timer)
        except Exception:
            pass
        _hit_stop_timer = None

    _hit_tk_root = tk_root
    mci_path = _get_mci_path(path)
    sound_key = str(path.resolve())

    if _hit_loaded_file == sound_key:
        err = _mci_send("play mci_hit from 0")
        if err == 0:
            if duration_sec > 0 and tk_root:
                stop_ms = int(duration_sec * 1000)
                _hit_stop_timer = tk_root.after(stop_ms, stop_hit_sound)
            return

    _mci_send("stop mci_hit")
    _mci_send("close mci_hit")
    err = _mci_send(f"open {mci_path} alias mci_hit")
    if err == 0:
        _hit_loaded_file = sound_key
        _mci_send("play mci_hit from 0")
        if duration_sec > 0 and tk_root:
            stop_ms = int(duration_sec * 1000)
            _hit_stop_timer = tk_root.after(stop_ms, stop_hit_sound)
        return

    # Fallback to winsound
    try:
        import winsound
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        if duration_sec > 0 and tk_root:
            def _stop_ws():
                try:
                    winsound.PlaySound(None, winsound.SND_PURGE)
                except Exception:
                    pass
            _hit_stop_timer = tk_root.after(int(duration_sec * 1000), _stop_ws)
    except Exception:
        pass


def stop_hit_sound() -> None:
    """Stops mci_hit channel and clears stop timer."""
    global _hit_stop_timer, _hit_tk_root
    if _hit_stop_timer and _hit_tk_root:
        try:
            _hit_tk_root.after_cancel(_hit_stop_timer)
        except Exception:
            pass
        _hit_stop_timer = None
    _hit_tk_root = None
    _mci_send("stop mci_hit")


_bomb_loaded_file: str | None = None
_pet_blast_loaded_file: str | None = None


def play_explosion_sound() -> None:
    """
    Plays the bomb explosion sound on its dedicated 'mci_bomb' channel.
    Runs concurrently with other sounds without stopping or interrupting them.
    """
    global _bomb_loaded_file
    if not BOMB_EXPLOSION_SOUND.exists():
        return

    mci_path = _get_mci_path(BOMB_EXPLOSION_SOUND)
    sound_key = str(BOMB_EXPLOSION_SOUND.resolve())

    if _bomb_loaded_file == sound_key:
        err = _mci_send("play mci_bomb from 0")
        if err == 0:
            return

    _mci_send("stop mci_bomb")
    _mci_send("close mci_bomb")
    err = _mci_send(f"open {mci_path} alias mci_bomb")
    if err == 0:
        _bomb_loaded_file = sound_key
        _mci_send("play mci_bomb from 0")
        return

    try:
        import winsound
        winsound.PlaySound(str(BOMB_EXPLOSION_SOUND), winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass


def play_pet_blast_sound(custom_path: Path | str | None = None) -> None:
    """
    Plays the pet blast reaction sound on its dedicated 'mci_pet_blast' channel.
    Runs concurrently with the bomb explosion sound.
    """
    global _pet_blast_loaded_file
    target_path = Path(custom_path) if custom_path else PET_SCREAM_SOUND
    if not target_path.exists():
        target_path = _get_base_hit_sound()
    if not target_path.exists():
        return

    mci_path = _get_mci_path(target_path)
    sound_key = str(target_path.resolve())

    if _pet_blast_loaded_file == sound_key:
        err = _mci_send("play mci_pet_blast from 0")
        if err == 0:
            return

    _mci_send("stop mci_pet_blast")
    _mci_send("close mci_pet_blast")
    err = _mci_send(f"open {mci_path} alias mci_pet_blast")
    if err == 0:
        _pet_blast_loaded_file = sound_key
        _mci_send("play mci_pet_blast from 0")
        return

    try:
        import winsound
        winsound.PlaySound(str(target_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass


def stop_all() -> None:
    """Stops and closes all active audio playback channels."""
    global _crack_loaded_file, _hit_loaded_file, _bomb_loaded_file, _pet_blast_loaded_file
    stop_hit_sound()
    stop_preview()
    _mci_send("stop mci_crack")
    _mci_send("close mci_crack")
    _crack_loaded_file = None
    _mci_send("stop mci_hit")
    _mci_send("close mci_hit")
    _hit_loaded_file = None
    _mci_send("stop mci_bomb")
    _mci_send("close mci_bomb")
    _bomb_loaded_file = None
    _mci_send("stop mci_pet_blast")
    _mci_send("close mci_pet_blast")
    _pet_blast_loaded_file = None


# ── Audio Preview Controller ──────────────────────────────────────────
class _PreviewController:
    def __init__(self):
        self._current_file: str | None = None
        self._stop_timer_id: Any = None
        self._tk_root: Any = None
        self._on_stop_cb: Callable[[], None] | None = None
        self._loaded_path: str | None = None

    def is_playing(self, filename: str | None = None) -> bool:
        if self._current_file is None:
            return False
        if filename is not None:
            return self._current_file == filename
        return True

    def current_playing_file(self) -> str | None:
        return self._current_file

    def play(
        self,
        sound_path: Path | str,
        duration_sec: float = 0.0,
        tk_root: Any = None,
        on_stop: Callable[[], None] | None = None,
    ) -> None:
        path = Path(sound_path)
        if not path.exists():
            return

        self.stop()
        self._tk_root = tk_root
        self._on_stop_cb = on_stop
        self._current_file = path.name

        mci_path = _get_mci_path(path)
        sound_key = str(path.resolve())

        _mci_send("stop mci_preview")
        _mci_send("close mci_preview")
        err = _mci_send(f"open {mci_path} alias mci_preview")
        if err == 0:
            self._loaded_path = sound_key
            _mci_send("play mci_preview from 0")
        else:
            try:
                import winsound
                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                self._current_file = None
                return

        if duration_sec > 0 and self._tk_root:
            stop_ms = int(duration_sec * 1000)
            self._stop_timer_id = self._tk_root.after(stop_ms, self.stop)

    def stop(self) -> None:
        if self._stop_timer_id and self._tk_root:
            try:
                self._tk_root.after_cancel(self._stop_timer_id)
            except Exception:
                pass
            self._stop_timer_id = None

        _mci_send("stop mci_preview")
        _mci_send("close mci_preview")
        self._loaded_path = None

        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

        cb = self._on_stop_cb
        self._current_file = None
        self._on_stop_cb = None
        if cb:
            try:
                cb()
            except Exception:
                pass


_preview_controller = _PreviewController()


def play_preview(
    sound_path: Path | str,
    duration_sec: float = 0.0,
    tk_root: Any = None,
    on_stop: Callable[[], None] | None = None,
) -> None:
    """Plays an audio preview with accurate duration cutoff."""
    _preview_controller.play(sound_path, duration_sec=duration_sec, tk_root=tk_root, on_stop=on_stop)


def stop_preview() -> None:
    """Stops any running preview playback and releases handles."""
    _preview_controller.stop()


def is_preview_playing(filename: str | None = None) -> bool:
    """Returns True if a preview is currently active."""
    return _preview_controller.is_playing(filename)
