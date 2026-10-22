#!/usr/bin/env python3
"""Fetch the FrickBears 3 game data.

The game itself is not redistributed in this repository - it belongs to
SpookyRick and is distributed on Game Jolt:
https://gamejolt.com/games/frickbears3/930477

This helper pulls the game from a public mirror so the CI can bundle it into
the APK. Several community character mods on itch.io ship the complete base
game alongside the mod, so those are used as the mirror. Each one is tried in
turn until one yields a data.win.

Usage:  python3 fetch_game.py [output-dir]
"""
import io
import json
import os
import re
import subprocess
import sys
import zipfile

# Mirrors that bundle the complete FrickBears 3 game (data.win + assets).
# Each entry is (page url, upload id).
SOURCES = [
    ("https://jvbb.itch.io/frickbears-3-hoshimi-miyabi-guard", "17640228"),
    ("https://benimismimnikaso.itch.io/frickbears-3-rem-kl-mod", "18045982"),
    ("https://whitefox-fcp.itch.io/fb3playerguymod", "19089593"),
]

DEFAULT_OUT = "vendor/frickbears3-game"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch(url, cookies=None, timeout=180):
    cmd = ["curl", "-sL", "--max-time", str(timeout), "-H", f"User-Agent: {UA}"]
    if cookies:
        cmd += ["-b", cookies, "-c", cookies]
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True)
    return result.stdout


def try_source(page, upload_id, out_dir):
    """Try to download the full game from one mirror. Returns True on success."""
    jar = f"/tmp/itch_jar_{abs(hash(page))}.txt"

    html = fetch(page, cookies=jar).decode("utf-8", "replace")
    if not html:
        print(f"  ! {page}: no response")
        return False

    csrf_match = re.search(r'csrf_token" value="([^"]+)"', html)
    if not csrf_match:
        print(f"  ! {page}: no csrf token (page may have changed)")
        return False
    csrf = csrf_match.group(1)

    # The signed download URL is handed out by a POST to the file endpoint.
    cmd = [
        "curl", "-s", "--max-time", "120",
        "-b", jar, "-c", jar,
        "-X", "POST", f"{page}/file/{upload_id}",
        "-H", f"Referer: {page}",
        "-H", f"X-CSRFToken: {csrf}",
        "-H", f"User-Agent: {UA}",
    ]
    raw = subprocess.run(cmd, capture_output=True).stdout
    try:
        url = json.loads(raw)["url"]
    except Exception:
        print(f"  ! {page}: no signed url")
        return False

    blob = fetch(url, timeout=600)
    if not blob:
        print(f"  ! {page}: empty download")
        return False

    try:
        z = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile:
        print(f"  ! {page}: not a zip")
        return False

    names = z.namelist()
    if not any("data.win" in n for n in names):
        print(f"  ! {page}: no data.win in the archive")
        return False

    os.makedirs(out_dir, exist_ok=True)
    z.extractall(out_dir)
    print(f"  + extracted {len(names)} entries to {out_dir}")
    return True


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT

    # Already have it? Nothing to do.
    if os.path.exists(os.path.join(out_dir, "data.win")):
        print(f"game data already present in {out_dir}")
        return 0

    for page, upload_id in SOURCES:
        print(f"trying {page}")
        try:
            if try_source(page, upload_id, out_dir):
                print(f"done: {out_dir}")
                return 0
        except Exception as e:
            print(f"  ! {page}: {e}")

    print()
    print("FAILED: could not fetch the game data from any mirror.")
    print("Get it from Game Jolt instead:")
    print("  https://gamejolt.com/games/frickbears3/930477")
    print(f"and unpack it into {out_dir}/")
    return 1


if __name__ == "__main__":
    sys.exit(main())
