#!/usr/bin/env python3
"""Package the FrickBears 3 game data into the Android app's assets.

The game ships as a folder of GameMaker files (data.win, audiogroup*.dat,
texgroup_*/). The app cannot ship them loose in the APK - the audio groups
alone are ~160MB - so they are bundled as a single compressed archive and
extracted to the app's private storage on first launch.

The archive is a plain zip with deflate, stored under the app's assets/
directory as `game/frickbears3.zip`.

Usage:
    python3 package_game.py <game-folder> <assets-dir>
"""
import os
import sys
import zipfile


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}"
        n /= 1024


def main():
    if len(sys.argv) < 3:
        print("usage: package_game.py <game-folder> <assets-dir>")
        return 2

    game_dir = sys.argv[1]
    assets_dir = sys.argv[2]

    if not os.path.isdir(game_dir):
        print(f"game folder not found: {game_dir}")
        return 1

    out_dir = os.path.join(assets_dir, "game")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "frickbears3.zip")

    # Files the runner actually needs. The Windows executable and the
    # mouse-lock DLL are not used by the Android runner, so they are left out.
    skip_names = {"Frickbears3.exe", "display_mouse_lock_x64.dll", "NekoPresence_x64.dll"}

    total_raw = 0
    total_zip = 0
    count = 0

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, _dirs, files in os.walk(game_dir):
            for name in sorted(files):
                if name in skip_names:
                    continue
                full = os.path.join(root, name)
                rel = os.path.relpath(full, game_dir)
                size = os.path.getsize(full)
                z.write(full, rel)
                total_raw += size
                count += 1
                print(f"  + {rel} ({human(size)})")

    total_zip = os.path.getsize(out_path)
    print()
    print(f"{count} files, {human(total_raw)} raw -> {human(total_zip)} compressed")
    print(f"written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
