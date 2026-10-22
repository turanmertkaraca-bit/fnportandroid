#!/usr/bin/env python3
"""Scan itch.io pages for Frickbears 3 uploads and find one containing the base game."""
import json
import re
import subprocess
import io
import zipfile

PAGES = [
    "https://nate-himself-productions.itch.io/frickbears-3-x-marks-home-invasion",
    "https://dice-project.itch.io/bislow-frickbear",
    "https://miskullism.itch.io/five-nights-at-frickbears-vanessa-mod",
    "https://jvbb.itch.io/frickbears-3-hoshimi-miyabi-guard",
    "https://greenbox27.itch.io/five-nights-at-frickbears-jennys-mod",
    "https://benimismimnikaso.itch.io/frickbears-3-rem-kl-mod",
    "https://xx-diabolos-xx.itch.io/frickbearsrosekayla",
    "https://mickeythemfrat.itch.io/the-king-carter-mickeyfan-kenny-frickbears-3-mod",
]


def fetch(url, cookies=None):
    cmd = ["curl", "-sL", "--max-time", "60", "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64)"]
    if cookies:
        cmd += ["-b", cookies, "-c", cookies]
    cmd.append(url)
    return subprocess.run(cmd, capture_output=True).stdout


def main():
    for page in PAGES:
        jar = "/tmp/itch_jar.txt"
        html = fetch(page, cookies=jar).decode("utf8", "replace")
        csrf_m = re.search(r'csrf_token" value="([^"]+)"', html)
        uploads = re.findall(r'data-upload_id="(\d+)"', html)
        if not uploads:
            print(f"{page}: no uploads")
            continue
        csrf = csrf_m.group(1) if csrf_m else ""
        for uid in uploads:
            cmd = [
                "curl", "-s", "--max-time", "60",
                "-b", jar, "-c", jar,
                "-X", "POST", f"{page}/file/{uid}",
                "-H", f"Referer: {page}",
                "-H", f"X-CSRFToken: {csrf}",
                "-H", "User-Agent: Mozilla/5.0",
            ]
            out = subprocess.run(cmd, capture_output=True).stdout
            try:
                url = json.loads(out)["url"]
            except Exception:
                print(f"  {page} file/{uid}: no signed url -> {out[:100]!r}")
                continue
            blob = fetch(url)
            print(f"{page} file/{uid}: {len(blob)} bytes")
            try:
                z = zipfile.ZipFile(io.BytesIO(blob))
                names = z.namelist()
                hits = [n for n in names
                        if "data.win" in n or n.endswith(".unx")
                        or "assets" in n.lower() or n.lower().endswith(".exe")]
                print(f"   entries={len(names)} interesting={hits[:15]}")
            except zipfile.BadZipFile:
                print("   not a zip")


if __name__ == "__main__":
    main()
