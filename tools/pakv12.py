#!/usr/bin/env python3
"""Lecteur minimal de fichiers .pak Unreal (version 12, ARK Survival Ascended).

L'index n'est pas chiffré dans ASA, la compression des données est Oodle.
"""
import os
import struct
import sys

MAGIC = 0x5A6F12E1


class Reader:
    def __init__(self, data, pos=0):
        self.d = data
        self.p = pos

    def u32(self):
        v = struct.unpack_from("<I", self.d, self.p)[0]
        self.p += 4
        return v

    def i32(self):
        v = struct.unpack_from("<i", self.d, self.p)[0]
        self.p += 4
        return v

    def u64(self):
        v = struct.unpack_from("<Q", self.d, self.p)[0]
        self.p += 8
        return v

    def bytes(self, n):
        v = self.d[self.p:self.p + n]
        self.p += n
        return v

    def fstring(self):
        n = self.i32()
        if n < 0:  # UTF-16
            raw = self.bytes(-n * 2)
            return raw.decode("utf-16-le").rstrip("\x00")
        raw = self.bytes(n)
        return raw.decode("latin-1").rstrip("\x00")


def read_footer(f):
    f.seek(0, 2)
    fsize = f.tell()
    tail_len = min(4096, fsize)
    f.seek(fsize - tail_len)
    tail = f.read(tail_len)
    magic_bytes = struct.pack("<I", MAGIC)
    idx = tail.rfind(magic_bytes)
    if idx < 0:
        raise SystemExit("magic pak introuvable")
    r = Reader(tail, idx + 4)
    version = r.u32()
    index_offset = r.u64()
    index_size = r.u64()
    index_hash = r.bytes(20)
    comp_names = []
    for _ in range(5):
        name = r.bytes(32).split(b"\x00")[0].decode()
        comp_names.append(name)
    return {
        "file_size": fsize,
        "version": version,
        "index_offset": index_offset,
        "index_size": index_size,
        "compression": comp_names,
        "footer_tail_extra": tail[r.p:],
    }


def decode_entry(data, offset, comp_names):
    """Décode une entrée compacte (bitfield) de l'index — cf. repak entry.rs."""
    r = Reader(data, offset)
    bits = r.u32()
    comp_idx = (bits >> 23) & 0x3F
    encrypted = bool(bits & (1 << 22))
    block_count = (bits >> 6) & 0xFFFF
    block_size = bits & 0x3F
    if block_size == 0x3F:
        block_size = r.u32()
    else:
        block_size <<= 11
    def var(bit):
        return r.u32() if bits & (1 << bit) else r.u64()
    entry_offset = var(31)
    uncompressed = var(30)
    compressed = var(29) if comp_idx != 0 else uncompressed
    blocks = []
    if block_count > 0:
        if block_count == 1 and not encrypted:
            blocks = [compressed]
        else:
            blocks = [r.u32() for _ in range(block_count)]
    return {
        "offset": entry_offset,
        "uncompressed": uncompressed,
        "compressed": compressed,
        "compression": comp_names[comp_idx - 1] if comp_idx else None,
        "encrypted": encrypted,
        "block_sizes": blocks,
        "block_size": block_size,
    }


def read_index(path):
    with open(path, "rb") as f:
        footer = read_footer(f)
        f.seek(footer["index_offset"])
        idx = f.read(footer["index_size"])
    r = Reader(idx)
    mount = r.fstring()
    entry_count = r.i32()
    path_hash_seed = r.u64()
    has_path_hash = r.i32()
    if has_path_hash:
        r.u64(); r.u64(); r.bytes(20)
    has_full_dir = r.i32()
    fdi_offset = fdi_size = None
    if has_full_dir:
        fdi_offset = r.u64()
        fdi_size = r.u64()
        r.bytes(20)
    encoded_size = r.i32()
    encoded = r.bytes(encoded_size)
    files_count = r.i32()  # entrées non encodées, normalement 0
    with open(path, "rb") as f:
        f.seek(fdi_offset)
        fdi = f.read(fdi_size)
    r2 = Reader(fdi)
    dir_count = r2.i32()
    files = {}
    for _ in range(dir_count):
        dname = r2.fstring()
        n = r2.i32()
        for _ in range(n):
            fname = r2.fstring()
            entry_loc = r2.u32()
            files[mount + dname + fname] = entry_loc
    return footer, mount, entry_count, encoded, files


_oodle = None
_appel = None


def _charger_oodle():
    """Oodle officiel si disponible, sinon ooz (implementation libre).

    Oodle n'est pas redistribuable : le depot n'en contient pas. La CI compile
    ooz (github.com/powzix/ooz) et pointe OOZ_LIB dessus.
    """
    import ctypes
    ici = os.path.dirname(os.path.abspath(__file__))
    officiel = os.environ.get("OODLE_LIB") or os.path.join(ici, "oodle/lib/liboodle-data-shared.so")
    if os.path.exists(officiel):
        lib = ctypes.CDLL(officiel)
        lib.OodleLZ_Decompress.restype = ctypes.c_ssize_t

        def appel(src, dst, dst_len):
            return lib.OodleLZ_Decompress(
                src, ctypes.c_ssize_t(len(src)), dst, ctypes.c_ssize_t(dst_len),
                1, 0, 0, None, ctypes.c_ssize_t(0), None, None, None,
                ctypes.c_ssize_t(0), 3)
        return lib, appel
    libre = os.environ.get("OOZ_LIB") or os.path.join(ici, "libooz.so")
    if os.path.exists(libre):
        lib = ctypes.CDLL(libre)
        lib.Ooz_Decompress.restype = ctypes.c_int

        def appel(src, dst, dst_len):
            return lib.Ooz_Decompress(src, ctypes.c_size_t(len(src)), dst,
                                      ctypes.c_size_t(dst_len))
        return lib, appel
    raise RuntimeError(
        "aucun decompresseur Oodle : placez liboodle-data-shared.so dans "
        "tools/oodle/lib/, ou compilez ooz et pointez OOZ_LIB dessus")


def oodle_decompress(src, dst_len):
    global _oodle, _appel
    import ctypes
    if _oodle is None:
        _oodle, _appel = _charger_oodle()
    dst = ctypes.create_string_buffer(dst_len)
    n = _appel(src, dst, dst_len)
    if n != dst_len:
        raise RuntimeError(f"oodle: {n} != {dst_len}")
    return dst.raw


def extract(pak, name, out_path):
    footer, mount, count, encoded, files = read_index(pak)
    loc = files[name]
    e = decode_entry(encoded, loc, footer["compression"])
    with open(pak, "rb") as f:
        f.seek(e["offset"])
        # header FPakEntry local : offset8+csize8+usize8+cmethod4+hash20
        # +[blockcount4+blocks16*n]+flags1+blocksize4
        hdr = 48
        if e["compression"]:
            hdr += 4 + 16 * max(1, len(e["block_sizes"]))
        hdr += 5
        raw_hdr = f.read(hdr)
        blocks = []
        if e["compression"]:
            bc = struct.unpack_from("<I", raw_hdr, 48)[0]
            for i in range(bc):
                s, t = struct.unpack_from("<QQ", raw_hdr, 52 + 16 * i)
                blocks.append((s, t))
        out = bytearray()
        if not e["compression"]:
            f.seek(e["offset"] + hdr - 5 - 4 + 9)  # pas de blocs : header = 53 octets
            f.seek(e["offset"] + 53)
            out = f.read(e["uncompressed"])
        else:
            remaining = e["uncompressed"]
            for (s, t) in blocks:
                f.seek(e["offset"] + s)
                comp = f.read(t - s)
                dst_len = min(e["block_size"], remaining)
                out += oodle_decompress(comp, dst_len)
                remaining -= dst_len
    with open(out_path, "wb") as g:
        g.write(bytes(out))
    print(f"{name} -> {out_path} ({len(out)} octets)")


if __name__ == "__main__":
    if sys.argv[1] == "extract":
        extract(sys.argv[2], sys.argv[3], sys.argv[4])
        sys.exit(0)
    pak = sys.argv[1]
    pattern = sys.argv[2] if len(sys.argv) > 2 else ""
    footer, mount, count, encoded, files = read_index(pak)
    print(f"version={footer['version']} entries={count} mount={mount!r} "
          f"compression={footer['compression']} extra={footer['footer_tail_extra'].hex()}")
    for name, loc in files.items():
        if pattern.lower() in name.lower():
            e = decode_entry(encoded, loc, footer["compression"])
            print(f"{name}  off={e['offset']} usize={e['uncompressed']} "
                  f"csize={e['compressed']} comp={e['compression']} "
                  f"blocks={len(e['block_sizes'])} enc={e['encrypted']}")
