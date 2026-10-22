#!/usr/bin/env python3
"""Print STRG entries around given control names, to find FB3's key bindings.

Reads the STRG chunk of a GameMaker 2.x data.win and prints a window of
entries around each needle, so the control labels can be matched with the
keyboard constants that sit next to them.

Usage:  python3 strg_context.py <data.win> <needle> [needle...]
"""
import struct
import sys


def u32(buf, off):
    return struct.unpack('<I', buf[off:off + 4])[0]


def parse_strg(buf, off, size):
    count = u32(buf, off)
    p = off + 4
    pairs = []
    for _ in range(count):
        pairs.append((u32(buf, p), u32(buf, p + 4)))
        p += 8
    blob = buf[p:off + size]
    return [blob[o:o + ln].decode('utf-8', 'replace') for o, ln in pairs]


def find_strg(buf):
    off = 8
    while off + 8 <= len(buf):
        cid = buf[off:off + 4]
        size = u32(buf, off + 4)
        if cid == b'STRG':
            return off + 8, size
        off += 8 + size
        if size % 4:
            off += 4 - (size % 4)
    return None, 0


def main():
    path = sys.argv[1]
    needles = sys.argv[2:]
    buf = open(path, 'rb').read()
    off, size = find_strg(buf)
    if off is None:
        print("no STRG")
        return 1
    strings = parse_strg(buf, off, size)

    for needle in needles:
        hits = [i for i, s in enumerate(strings) if needle.lower() in s.lower()]
        print(f"\n=== {needle!r}: {len(hits)} hit(s)")
        for i in hits[:4]:
            lo, hi = max(0, i - 6), min(len(strings), i + 7)
            print(f"  --- window around index {i} ---")
            for j in range(lo, hi):
                s = strings[j].replace("\x00", "\\0")
                if len(s) > 90:
                    s = s[:90] + "..."
                mark = ">>" if j == i else "  "
                print(f"   {mark} {j}: {s!r}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
