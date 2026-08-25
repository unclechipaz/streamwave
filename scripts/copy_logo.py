#!/usr/bin/env python3
"""
Copies the uploaded StreamWave logo image to public/images/streamwave-logo.png
"""

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_IMAGE = PROJECT_ROOT / ".user_uploaded" / "media_1787682860034.png"
TARGET_DIR = PROJECT_ROOT / "public" / "images"
TARGET_IMAGE = TARGET_DIR / "streamwave-logo.png"


def copy_logo():
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    if SOURCE_IMAGE.exists():
        shutil.copyfile(SOURCE_IMAGE, TARGET_IMAGE)
        print(f"✅ Logo successfully copied to {TARGET_IMAGE} ({TARGET_IMAGE.stat().st_size} bytes)")
    else:
        print(f"❌ Source image not found at {SOURCE_IMAGE}")


if __name__ == "__main__":
    copy_logo()
