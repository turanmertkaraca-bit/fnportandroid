#!/usr/bin/env python3
"""Decode the OPTN (options) chunk of a GameMaker 2.x data.win.

The options chunk holds the game's "game options" - which is where FB3 keeps
its remappable control definitions (Left Door, Right Door, Flashlight, ...).
Each option carries a name, a value and a caption, which is exactly what we
need to work out what a touch button should trigger.

Usage:  python3 parse_optn.py <data.win>
"""
import struct
import sys

STRG_MARKER = 0x00000000


def u32(buf, off):
    return struct.unpack('<I', buf[off:off + 4])[0]


def i32(buf, off):
    return struct.unpack('<i', buf[off:off + 4])[0]


def parse_strg(buf):
    off = 8
    while off + 8 <= len(buf):
        cid = buf[off:off + 4]
        size = u32(buf, off + 4)
        if cid == b'STRG':
            base = off + 8
            count = u32(buf, base)
            p = base + 4
            pairs = []
            for _ in range(count):
                pairs.append((u32(buf, p), u32(buf, p + 4)))
                p += 8
            blob = buf[p:base + size]
            return [blob[o:o + ln].decode('utf-8', 'replace') for o, ln in pairs]
        off += 8 + size
        if size % 4:
            off += 4 - (size % 4)
    return []


def find_optn(buf):
    off = 8
    while off + 8 <= len(buf):
        cid = buf[off:off + 4]
        size = u32(buf, off + 4)
        if cid == b'OPTN':
            return off + 8, size
        off += 8 + size
        if size % 4:
            off += 4 - (size % 4)
    return None, 0


def main():
    path = sys.argv[1]
    buf = open(path, 'rb').read()
    strings = parse_strg(buf)
    off, size = find_optn(buf)
    if off is None:
        print("no OPTN chunk")
        return 1

    print(f"OPTN at {off}, size {size}")
    p = off
    count = u32(buf, p)
    p += 4
    print(f"option count: {count}")

    for i in range(count):
        name_idx = u32(buf, p)
        value = u32(buf, p + 4)
        caption_idx = u32(buf, p + 8)
        p += 12

        name = strings[name_idx] if name_idx < len(strings) else f"<{name_idx}>"
        caption = strings[caption_idx] if caption_idx < len(strings) else f"<{caption_idx}>"
        name = name.replace("\x00", "")
        caption = caption.replace("\x00", "")

        # A GameMaker option value is a variant; the low bits say the type.
        # 0 = string, 1 = bool, 2 = int, 3 = double, 4 = colour.
        vtype = value & 0xF
        vval = value >> 4
        typed = {0: "string", 1: "bool", 2: "int", 3: "double"}.get(vtype, f"t{vtype}")
        extra = ""
        if vtype == 0 and vval < len(strings):
            extra = f" -> {strings[vval]!r}"
        elif vtype == 1:
            extra = f" -> {bool(vval)}"
        else:
            extra = f" -> {vval}"

        print(f"[{i:2}] name={name!r:38} type={typed:7}{extra}  caption={caption!r}")


if __name__ == '__main__':
    sys.exit(main())
