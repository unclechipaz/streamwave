#!/usr/bin/env python3
"""
Copies the StreamWave 5-second MP4 demonstration video from Downloads
to the static public media directory (public/media/streamwave-preview.mp4).
"""

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = PROJECT_ROOT / "public" / "media"
TARGET_FILE = TARGET_DIR / "streamwave-preview.mp4"

# Candidate source paths in user Downloads folder
DOWNLOADS_DIR = Path(r"C:\Users\dell\Downloads")
CANDIDATE_SOURCES = [
    DOWNLOADS_DIR / "Use_the_uploaded_StreamWave_lo.mp4",
    DOWNLOADS_DIR / "Download (28).mp4",
]


def copy_preview_video() -> bool:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    for source in CANDIDATE_SOURCES:
        if source.exists() and source.stat().st_size > 0:
            shutil.copyfile(source, TARGET_FILE)
            print(
                f"✅ Successfully copied video asset:\n  Source: {source}\n  Target: {TARGET_FILE} ({TARGET_FILE.stat().st_size} bytes)"
            )
            return True

    print("⚠️ No candidate video source found in Downloads directory.")
    return False


if __name__ == "__main__":
    copy_preview_video()
