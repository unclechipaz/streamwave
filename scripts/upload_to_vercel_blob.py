#!/usr/bin/env python3
"""
Vercel Blob Uploader Script for StreamWave Serverless Media Platform.
Uploads the original demonstration WAV audio file (public/media/demo.wav) to Vercel Blob storage.

Official Documentation References:
- Vercel Blob Overview: https://vercel.com/docs/vercel-blob
- Vercel CLI Blob: https://vercel.com/docs/cli/blob

Usage:
  1. Set your BLOB_READ_WRITE_TOKEN in environment:
     export BLOB_READ_WRITE_TOKEN="vercel_blob_rw_..."
  2. Run script:
     python scripts/upload_to_vercel_blob.py
"""

import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
AUDIO_FILE = PROJECT_ROOT / "public" / "media" / "demo.wav"


def upload_to_vercel_blob():
    print("=== StreamWave Vercel Blob Audio Asset Uploader ===")
    
    if not AUDIO_FILE.exists():
        print(f"❌ Error: Demo audio file not found at {AUDIO_FILE}")
        print("Please run `python scripts/generate_demo_audio.py` first.")
        sys.exit(1)

    token = os.environ.get("BLOB_READ_WRITE_TOKEN")
    
    if not token:
        print("\n⚠️  No BLOB_READ_WRITE_TOKEN environment variable found!")
        print("\nTo upload `public/media/demo.wav` to your Vercel Blob store:")
        print("----------------------------------------------------------------------")
        print("Option A (Using Vercel CLI):")
        print("  1. Authenticate with Vercel: npx vercel login")
        print("  2. Upload demo file:        npx vercel blob upload public/media/demo.wav")
        print("\nOption B (Using Python Script):")
        print("  1. Obtain token from Vercel Dashboard -> Storage -> Vercel Blob")
        print("  2. Set environment variable: export BLOB_READ_WRITE_TOKEN='vercel_blob_rw_...'")
        print("  3. Run:                      python scripts/upload_to_vercel_blob.py")
        print("----------------------------------------------------------------------")
        print("\nLocal static fallback (`/media/demo.wav`) remains fully active.")
        sys.exit(0)

    print(f"📡 Found BLOB_READ_WRITE_TOKEN (length: {len(token)} chars). Uploading {AUDIO_FILE.name}...")

    # Read binary WAV bytes
    with open(AUDIO_FILE, "rb") as f:
        file_bytes = f.read()

    # Vercel Blob REST API endpoint for file PUT
    # Official API endpoint: https://blob.vercel-storage.com/demo.wav
    url = "https://blob.vercel-storage.com/demo.wav"
    
    req = urllib.request.Request(
        url,
        data=file_bytes,
        headers={
            "Authorization": f"Bearer {token}",
            "x-api-version": "7",
            "content-type": "audio/wav",
            "x-add-random-suffix": "false",
        },
        method="PUT",
    )

    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            print("✅ Upload successful!")
            print(f"Response: {resp_body}")
            print("\nCopy the returned URL and set it in your environment:")
            print("export STREAMWAVE_BLOB_URL='<your-blob-url>'")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"❌ Upload failed with HTTP status {e.code}: {err_msg}")
    except Exception as e:
        print(f"❌ Upload failed with error: {e}")


if __name__ == "__main__":
    upload_to_vercel_blob()
