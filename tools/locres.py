#!/usr/bin/env python3
"""Lecture/écriture de fichiers .locres UE (version 3, Optimized_CityHash64_UTF16).

Les hashes de namespaces/clés sont préservés tels quels : on ne modifie que les
valeurs des chaînes, donc aucun recalcul CityHash n'est nécessaire.

Usage :
  locres.py dump <in.locres> <out.json>
  locres.py build <in.locres> <edits.json> <out.locres>
  locres.py merge <fr.locres> <en.locres> <edits.json> <out.locres>
    edits.json : {"namespace\tkey": "nouvelle valeur", ...}
    merge : comme build, mais les clés absentes du FR et présentes dans edits
    sont ajoutées en copiant les hashes (namespace, clé, source) du fichier EN.
"""
import json
import struct
import sys

MAGIC = bytes([0x0E, 0x14, 0x74, 0x75, 0x67, 0x4A, 0x03, 0xFC,
               0x4A, 0x15, 0x90, 0x9D, 0xC3, 0x37, 0x7F, 0x1B])


class R:
    def __init__(self, d, p=0):
        self.d = d
        self.p = p

    def u8(self):
        v = self.d[self.p]; self.p += 1; return v

    def u32(self):
        v = struct.unpack_from("<I", self.d, self.p)[0]; self.p += 4; return v

    def i32(self):
        v = struct.unpack_from("<i", self.d, self.p)[0]; self.p += 4; return v

    def u64(self):
        v = struct.unpack_from("<Q", self.d, self.p)[0]; self.p += 8; return v

    def fstring(self):
        n = self.i32()
        if n == 0:
            return ""
        if n < 0:
            raw = self.d[self.p:self.p + (-n) * 2]; self.p += (-n) * 2
            return raw.decode("utf-16-le")[:-1]
        raw = self.d[self.p:self.p + n]; self.p += n
        return raw.decode("utf-8", "replace")[:-1]


def w_fstring(out, s):
    # UE : ASCII pur -> UTF-8/latin, sinon UTF-16LE (longueur négative)
    if s == "":
        out += struct.pack("<i", 0)
        return
    try:
        s.encode("ascii")
        b = (s + "\x00").encode("ascii")
        out += struct.pack("<i", len(b)) + b
    except UnicodeEncodeError:
        b = (s + "\x00").encode("utf-16-le")
        out += struct.pack("<i", -(len(b) // 2)) + b


def read_legacy(d):
    """Locres v0 (ASE/UE4) : pas de magic, valeurs en ligne, pas de table."""
    r = R(d)
    ns_count = r.u32()
    namespaces = []
    strings = []
    for _ in range(ns_count):
        ns = r.fstring()
        key_count = r.u32()
        keys = []
        for _ in range(key_count):
            key = r.fstring()
            src_hash = r.u32()
            val = r.fstring()
            keys.append((0, key, src_hash, len(strings)))
            strings.append((val, 1))
        namespaces.append((0, ns, keys))
    total = sum(len(k) for _, _, k in namespaces)
    return 0, namespaces, strings, total


def read(path):
    d = open(path, "rb").read()
    if d[:16] != MAGIC:
        return read_legacy(d)
    r = R(d, 16)
    version = r.u8()
    assert version >= 2, f"version locres {version} non gérée"
    strings_offset = r.u64()
    total_keys = r.u32()
    # tableau des chaînes localisées
    rs = R(d, strings_offset)
    scount = rs.i32()
    strings = []
    for _ in range(scount):
        s = rs.fstring()
        refs = rs.i32()
        strings.append((s, refs))
    # namespaces
    ns_count = r.u32()
    namespaces = []
    for _ in range(ns_count):
        ns_hash = r.u32()
        ns = r.fstring()
        key_count = r.u32()
        keys = []
        for _ in range(key_count):
            key_hash = r.u32()
            key = r.fstring()
            src_hash = r.u32()
            idx = r.i32()
            keys.append((key_hash, key, src_hash, idx))
        namespaces.append((ns_hash, ns, keys))
    return version, namespaces, strings, total_keys


def dump(path, out_json):
    version, namespaces, strings, total = read(path)
    data = {}
    for _, ns, keys in namespaces:
        for _, key, _, idx in keys:
            data[f"{ns}\t{key}"] = strings[idx][0]
    json.dump(data, open(out_json, "w"), ensure_ascii=False, indent=0)
    print(f"{path}: {len(data)} chaînes, {len(strings)} uniques, version {version}")


def build(src_path, edits_json, out_path, en_path=None):
    version, namespaces, strings, total = read(src_path)
    edits = json.load(open(edits_json))
    n_add = 0
    if en_path:
        # ajoute les clés absentes du FR, hashes copiés depuis le EN
        present = {(ns, k) for _, ns, keys in namespaces for _, k, _, _ in keys}
        ns_map = {ns: i for i, (_, ns, _) in enumerate(namespaces)}
        namespaces = [(h, ns, list(keys)) for h, ns, keys in namespaces]
        _, en_namespaces, _, _ = read(en_path)
        for ns_hash, ns, keys in en_namespaces:
            for key_hash, key, src_hash, idx in keys:
                ek = f"{ns}\t{key}"
                if ek in edits and (ns, key) not in present:
                    val = edits[ek]
                    strings.append((val, 1))
                    if ns not in ns_map:
                        ns_map[ns] = len(namespaces)
                        namespaces.append((ns_hash, ns, []))
                    namespaces[ns_map[ns]][2].append(
                        (key_hash, key, src_hash, len(strings) - 1))
                    n_add += 1
    # nouvelle table de chaînes dédupliquée
    new_strings = []
    string_index = {}

    def intern(s):
        if s not in string_index:
            string_index[s] = len(new_strings)
            new_strings.append(s)
        return string_index[s]

    out_ns = []
    n_edit = 0
    for ns_hash, ns, keys in namespaces:
        out_keys = []
        for key_hash, key, src_hash, idx in keys:
            val = strings[idx][0]
            ek = f"{ns}\t{key}"
            if ek in edits and edits[ek] != val:
                val = edits[ek]
                n_edit += 1
            out_keys.append((key_hash, key, src_hash, intern(val)))
        out_ns.append((ns_hash, ns, out_keys))
    refs = [0] * len(new_strings)
    for _, _, keys in out_ns:
        for _, _, _, idx in keys:
            refs[idx] += 1
    # sérialisation
    body = bytearray()
    total_keys = sum(len(k) for _, _, k in out_ns)
    body += struct.pack("<I", len(out_ns))
    for ns_hash, ns, keys in out_ns:
        body += struct.pack("<I", ns_hash)
        w_fstring(body, ns)
        body += struct.pack("<I", len(keys))
        for key_hash, key, src_hash, idx in keys:
            body += struct.pack("<I", key_hash)
            w_fstring(body, key)
            body += struct.pack("<II", src_hash, idx)
    header = bytearray()
    header += MAGIC
    header.append(version)
    strings_offset = 16 + 1 + 8 + 4 + len(body)
    header += struct.pack("<Q", strings_offset)
    header += struct.pack("<I", total_keys)
    out = bytes(header) + bytes(body)
    tail = bytearray()
    tail += struct.pack("<i", len(new_strings))
    for i, s in enumerate(new_strings):
        w_fstring(tail, s)
        tail += struct.pack("<i", refs[i])
    open(out_path, "wb").write(out + bytes(tail))
    print(f"{out_path}: {n_edit} modif(s), {n_add} ajout(s), "
          f"{len(new_strings)} chaînes uniques")


if __name__ == "__main__":
    if sys.argv[1] == "dump":
        dump(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "merge":
        build(sys.argv[2], sys.argv[4], sys.argv[5], en_path=sys.argv[3])
