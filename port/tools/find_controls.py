#!/usr/bin/env python3
"""Find the control/option definitions inside a GameMaker 2.x data.win.

FB3 ships a "Controls Options" screen that remaps keyboard/mouse input, so the
game's control *names* live in the data.win as option/constant strings. This
script locates the OPTN (options) and/or the relevant STRG strings so the
Android touch layout can be bound to the right game actions.

Usage:  python3 find_controls.py <data.win>
"""
import re
import struct
import sys


def u32(buf, off):
    return struct.unpack('<I', buf[off:off + 4])[0]


def iter_chunks(buf, off=8):
    while off + 8 <= len(buf):
        cid = buf[off:off + 4]
        size = u32(buf, off + 4)
        yield cid, size, off + 8
        off += 8 + size
        if size % 4:
            off += 4 - (size % 4)


def parse_strg(buf, off, size):
    count = u32(buf, off)
    p = off + 4
    pairs = []
    for _ in range(count):
        pairs.append((u32(buf, p), u32(buf, p + 4)))
        p += 8
    blob = buf[p:off + size]
    return [blob[o:o + ln].decode('utf-8', 'replace') for o, ln in pairs]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'data.win'
    buf = open(path, 'rb').read()

    chunks = {}
    for cid, size, off in iter_chunks(buf):
        chunks.setdefault(cid, []).append((size, off))
        if len(chunks) > 40:
            break

    print("chunks:", {k.decode('latin1'): len(v) for k, v in chunks.items()})

    if b'STRG' in chunks:
        size, off = chunks[b'STRG'][0]
        strings = parse_strg(buf, off, size)
        print(f"STRG: {len(strings)} strings")

        # The GML bytecode blob is one huge string; look for the option names
        # FB3 registers for the controls screen.
        joined = "\n".join(strings)
        for needle in ("ControlsOptions", "remapFunction", "controlslist",
                       "is_mouse_input", "newbind", "check_mouse"):
            idx = joined.find(needle)
            print(f"  {needle!r}: {'found @%d' % idx if idx >= 0 else 'NOT FOUND'}")

        # Print short, label-like strings that look like control names.
        cands = []
        for s in strings:
            s = s.strip("\x00").strip()
            if not s or len(s) > 24:
                continue
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 _\-/]{2,23}", s):
                continue
            if re.search(r"gml_Script|gml_Object|_Script_|__", s):
                continue
            cands.append(s)
        uniq = sorted(set(cands))
        print(f"\n{len(uniq)} label-like strings; showing control-ish ones:")
        keys = ("door", "light", "cam", "monitor", "flash", "fan", "power",
                "vent", "music", "mask", "tool", "left", "right", "up", "down",
                "move", "interact", "use", "toggle")
        hits = [u for u in uniq if any(k in u.lower() for k in keys)]
        for h in hits:
            print("  ", h)


if __name__ == '__main__':
    main()
