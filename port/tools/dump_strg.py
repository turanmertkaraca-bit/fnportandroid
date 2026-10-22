#!/usr/bin/env python3
"""Dump the GameMaker STRG (string table) from a data.win.

data.win layout (GameMaker 2.x "FORM" container):
    'FORM' <u32 total_size>
        'GEN8' <u32 size> <gen8 data>
        'STRG' <u32 size> <string table>
        ...

The STRG chunk is:  u32 count, then `count` pairs of (u32 offset, u32 length),
followed by the concatenated UTF-8 blob.

Usage:  python3 dump_strg.py <data.win> [outfile.txt]
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
    out = []
    for o, ln in pairs:
        out.append(blob[o:o + ln].decode('utf-8', 'replace'))
    return out


def find_chunk(buf, want):
    off = 8  # skip 'FORM' + size
    while off + 8 <= len(buf):
        cid = buf[off:off + 4]
        size = u32(buf, off + 4)
        if cid == want:
            return off + 8, size
        off += 8 + size
        if size % 4:
            off += 4 - (size % 4)
    return None, 0


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'data.win'
    buf = open(path, 'rb').read()

    off, size = find_chunk(buf, b'STRG')
    if off is None:
        print("no STRG chunk found")
        return 1
    strings = parse_strg(buf, off, size)
    print(f"{len(strings)} strings")

    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w', encoding='utf-8') as fh:
            for i, s in enumerate(strings):
                fh.write(f"{i}\t{s!r}\n")
        print(f"written to {sys.argv[2]}")
    else:
        for i, s in enumerate(strings):
            print(f"{i}\t{s!r}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
