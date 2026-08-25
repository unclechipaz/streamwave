#!/usr/bin/env python3
"""
Ensures favicon.png and favicon.ico exist in public/ for browser tab icon rendering.
"""

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = PROJECT_ROOT / "public"
IMAGES_DIR = PUBLIC_DIR / "images"
LOGO_FILE = IMAGES_DIR / "streamwave-logo.png"

FAVICON_PNG = IMAGES_DIR / "favicon.png"
FAVICON_ICO = PUBLIC_DIR / "favicon.ico"


def create_favicon():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    if LOGO_FILE.exists():
        shutil.copyfile(LOGO_FILE, FAVICON_PNG)
        shutil.copyfile(LOGO_FILE, FAVICON_ICO)
        print(f"✅ Favicon successfully created at {FAVICON_PNG} and {FAVICON_ICO}")
    else:
        print(f"❌ Logo file not found at {LOGO_FILE}")


if __name__ == "__main__":
    create_favicon()
