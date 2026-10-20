"""
generate_bomb_sounds.py
Generates procedural 44.1kHz 16-bit WAV sound effects for the bomb explosion and pet scream.
Uses only Python's standard library: wave, struct, math, and random.
"""

import math
import wave
import struct
import random
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 44100


def create_explosion_sound(filename: str = "bomb_explosion.wav"):
    """
    Synthesizes a deep, punchy cinematic explosion:
    - Initial high-impact sub-bass transient
    - Filtered rolling noise rumble
    - Exponential atmospheric decay
    """
    duration = 1.3
    num_samples = int(SAMPLE_RATE * duration)
    out_path = ASSETS_DIR / filename

    samples = []
    
    # Low-pass filter state
    filter_val = 0.0
    filter_cutoff = 0.08  # smooth low rumble

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env_impact = math.exp(-t * 14.0)          # Initial snap
        env_body = math.exp(-t * 3.2)             # Mid rumble decay
        env_sub = math.exp(-t * 2.2)              # Low sub-bass tail

        # Sub-bass pitch drops from 95Hz to 35Hz
        freq = 35.0 + 60.0 * math.exp(-t * 8.0)
        sub = math.sin(2.0 * math.pi * freq * t) * env_sub

        # White/brown noise for combustion blast
        raw_noise = random.uniform(-1.0, 1.0)
        filter_val += filter_cutoff * (raw_noise - filter_val)
        noise = filter_val * env_body

        # Initial distortion punch
        burst = math.sin(2.0 * math.pi * 140.0 * t) * env_impact

        # Combine layers
        val = 0.55 * sub + 0.55 * noise + 0.40 * burst

        # Soft clipping / saturation
        val = math.tanh(val * 1.5)
        int_sample = int(max(-1.0, min(1.0, val)) * 32767)
        samples.append(int_sample)

    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        data = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(data)

    print(f"Generated explosion sound: {out_path} ({len(samples)} samples)")


def create_pet_scream_sound(filename: str = "pet_scream.wav"):
    """
    Synthesizes a comedic cartoon pitch-drop launch scream:
    - High-pitched vocal whistle start (900Hz)
    - Vibrato wobble
    - Fast descending slide down to 220Hz
    """
    duration = 1.1
    num_samples = int(SAMPLE_RATE * duration)
    out_path = ASSETS_DIR / filename

    samples = []
    phase = 0.0

    for i in range(num_samples):
        t = i / SAMPLE_RATE
        # Envelope: quick attack, sustained yell, fast fade out
        if t < 0.05:
            env = t / 0.05
        else:
            env = math.exp(-(t - 0.05) * 2.8)

        # Pitch contour: start around 950Hz, wobble, slide down to 260Hz
        freq = 260.0 + 690.0 * math.exp(-t * 3.5)
        # Vibrato
        vibrato = math.sin(2.0 * math.pi * 12.0 * t) * 25.0
        instant_freq = max(100.0, freq + vibrato)

        phase += 2.0 * math.pi * instant_freq / SAMPLE_RATE
        
        # Fundamental tone + comic harmonics (square-ish/saw harmonic warmth)
        tone = (
            math.sin(phase) * 0.7 +
            math.sin(phase * 2.0) * 0.25 +
            math.sin(phase * 3.0) * 0.15
        )

        val = tone * env
        val = math.tanh(val * 1.3)
        int_sample = int(max(-1.0, min(1.0, val)) * 32767)
        samples.append(int_sample)

    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        data = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(data)

    print(f"Generated pet scream sound: {out_path} ({len(samples)} samples)")


if __name__ == "__main__":
    create_explosion_sound()
    create_pet_scream_sound()
