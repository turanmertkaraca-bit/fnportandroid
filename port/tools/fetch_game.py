#!/usr/bin/env python3
"""Download the Frickbears 3 base game from an itch.io mirror and extract it.

The full game (data.win + Frickbears3.exe) is bundled with several community
character mods on itch.io. This script fetches one of those bundles so the
Android port has the real game assets to work with.
"""
import io
import json
import os
import re
import subprocess
import sys
import zipfile

# itch.io pages that bundle the full Frickbears 3 game.
SOURCES = [
    ("https://jvbb.itch.io/frickbears-3-hoshimi-miyabi-guard", "17640228"),
    ("https://benimismimnikaso.itch.io/frickbears-3-rem-kl-mod", "18045982"),
]
OUT = "vendor/frickbears3-game"


def fetch(url, cookies=None):
    cmd = ["curl", "-sL", "--max-time", "300", "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64)"]
    if cookies:
        cmd += ["-b", cookies, "-c", cookies]
    cmd.append(url)
    return subprocess.run(cmd, capture_output=True).stdout


def main():
    jar = "/tmp/itch_jar.txt"
    os.makedirs(OUT, exist_ok=True)
    for page, uid in SOURCES:
        html = fetch(page, cookies=jar).decode("utf8", "replace")
        m = re.search(r'csrf_token" value="([^"]+)"', html)
        if not m:
            print(f"no csrf for {page}")
            continue
        cmd = [
            "curl", "-s", "--max-time", "120",
            "-b", jar, "-c", jar,
            "-X", "POST", f"{page}/file/{uid}",
            "-H", f"Referer: {page}",
            "-H", f"X-CSRFToken: {m.group(1)}",
            "-H", "User-Agent: Mozilla/5.0",
        ]
        out = subprocess.run(cmd, capture_output=True).stdout
        try:
            url = json.loads(out)["url"]
        except Exception:
            print(f"no signed url for {page}")
            continue
        blob = fetch(url)
        print(f"{page}: downloaded {len(blob)} bytes")
        try:
            z = zipfile.ZipFile(io.BytesIO(blob))
        except zipfile.BadZipFile:
            print("  not a zip, skipping")
            continue
        names = z.namelist()
        if not any("data.win" in n for n in names):
            print("  no data.win, skipping")
            continue
        z.extractall(OUT)
        print(f"  extracted {len(names)} entries to {OUT}")
        return 0
    print("FAILED: no source contained data.win")
    return 1


if __name__ == "__main__":
    sys.exit(main())
