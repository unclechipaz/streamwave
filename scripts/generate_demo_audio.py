#!/usr/bin/env python3
"""
Audio generation script for StreamWave Serverless Media Platform.
Generates an original 3-second PCM 16-bit mono 44.1kHz WAV audio file
using Python standard-library modules (wave, struct, math) to ensure
no copyrighted media is used.
"""

import math
import struct
import wave
from pathlib import Path

# Path configuration relative to this script's directory
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "public" / "media"
OUTPUT_FILE = OUTPUT_DIR / "demo.wav"


def generate_chime_wav(output_path: Path) -> None:
    """Generates a pleasant 3-second synthesized chord chime WAV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sample_rate = 44100  # Hz
    duration = 3.0  # seconds
    total_samples = int(sample_rate * duration)

    # Note frequencies for a harmonic pentatonic sequence (C5, E5, G5, C6)
    frequencies = [523.25, 659.25, 783.99, 1046.50]
    note_stagger = int(sample_rate * 0.15)  # 150ms delay between notes

    # Open WAV file for writing
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit (2 bytes per sample)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            sample_val = 0.0

            # Sum active harmonics
            for note_idx, freq in enumerate(frequencies):
                start_sample = note_idx * note_stagger
                if i >= start_sample:
                    note_t = (i - start_sample) / sample_rate
                    # Envelope: gentle attack (10ms) and exponential decay
                    attack = min(1.0, note_t / 0.01)
                    decay = math.exp(-2.5 * note_t)
                    envelope = attack * decay

                    # Fundamental tone + subtle 2nd harmonic
                    tone = math.sin(2.0 * math.pi * freq * note_t) + 0.3 * math.sin(
                        4.0 * math.pi * freq * note_t
                    )
                    sample_val += tone * envelope * 0.25

            # Overall master fade-out near the end
            fade_out_start = total_samples - int(sample_rate * 0.2)
            if i > fade_out_start:
                fade_out_t = (total_samples - i) / int(sample_rate * 0.2)
                sample_val *= fade_out_t

            # Clamp and convert to 16-bit signed integer (-32768 to 32767)
            clamped = max(-1.0, min(1.0, sample_val))
            int_sample = int(clamped * 32767.0)

            # Pack as 16-bit little-endian integer
            frames.extend(struct.pack("<h", int_sample))

        wav_file.writeframes(frames)

    print(f"✅ Demo WAV audio generated successfully at: {output_path}")


if __name__ == "__main__":
    generate_chime_wav(OUTPUT_FILE)
