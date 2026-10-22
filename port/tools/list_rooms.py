#!/usr/bin/env python3
"""List FB3's room names from the ROOM chunk of a GameMaker 2.x data.win.

The ROOM chunk stores, per room: name, path, code, instance list, and the
creation code. The room *name* is a string-table index. Because the chunk is
variable length, this walks it field by field.

Usage:  python3 list_rooms.py <data.win>
"""
import struct
import sys


def u32(buf, off):
    return struct.unpack('<I', buf[off:off + 4])[0]


def i32(buf, off):
    return struct.unpack('<i', buf[off:off + 4])[0]


def find_chunk(buf, want):
    off = 8
    while off + 8 <= len(buf):
        cid = buf[off:off + 4]
        size = u32(buf, off + 4)
        if cid == want:
            return off + 8, size
        off += 8 + size
        if size % 4:
            off += 4 - (size % 4)
    return None, 0


def parse_strg(buf):
    off, size = find_chunk(buf, b'STRG')
    count = u32(buf, off)
    p = off + 4
    pairs = []
    for _ in range(count):
        pairs.append((u32(buf, p), u32(buf, p + 4)))
        p += 8
    blob = buf[p:off + size]
    return [blob[o:o + ln].decode('utf-8', 'replace') for o, ln in pairs]


def main():
    path = sys.argv[1]
    buf = open(path, 'rb').read()
    strings = parse_strg(buf)

    off, size = find_chunk(buf, b'ROOM')
    if off is None:
        print("no ROOM chunk")
        return 1

    p = off
    count = u32(buf, p)
    p += 4
    print(f"room count: {count}\n")

    for i in range(count):
        try:
            name_idx = u32(buf, p)
            path_idx = u32(buf, p + 4)
            code_idx = u32(buf, p + 8)
            # GM2.x: name, path, code, instance_id, creation_code, ...
            instance_id = u32(buf, p + 12)
            creation_idx = u32(buf, p + 16)
            # ...then instance count + list, then background count + list,
            # then view count + list, then the "game controller" flags.
            q = p + 20
            inst_count = u32(buf, q)
            q += 4 + inst_count * 4
            bg_count = u32(buf, q)
            q += 4 + bg_count * 4
            view_count = u32(buf, q)
            q += 4 + view_count * 4
            # 8 bytes of flags/seed
            q += 8

            def s(idx):
                if idx < len(strings):
                    return strings[idx].replace("\x00", "")
                return f"<{idx}>"

            print(f"[{i:3}] {s(name_idx):30} inst={inst_count:3} bg={bg_count} views={view_count}")
            p = q
        except Exception as e:
            print(f"[{i:3}] parse stopped: {e}")
            break


if __name__ == '__main__':
    sys.exit(main())
