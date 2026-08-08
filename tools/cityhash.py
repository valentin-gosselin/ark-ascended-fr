#!/usr/bin/env python3
"""CityHash64, tel qu'Unreal l'emploie pour hacher les cles de localisation.

Les fichiers .locres version 3 s'appellent « Optimized_CityHash64_UTF16 » : les
namespaces, les cles et les chaines sources y sont accompagnes d'un hash 32 bits
qui sert d'index. Tant qu'on se contente de modifier des valeurs existantes on
recopie ces hashes sans les comprendre -- c'est ce que fait locres.py. Mais pour
ajouter une entree qui n'existe dans aucun locres du jeu, il faut savoir la
hacher.

Unreal calcule (TextKey.h) :

    uint32 HashString(const TCHAR* Str, int32 Len)
    {
        return CityHash64((const char*)Str, Len * sizeof(TCHAR));
    }

soit CityHash64 sur les octets UTF-16LE de la chaine, sans terminateur, tronque
aux 32 bits de poids faible. Le module se verifie tout seul contre les hashes
reels du jeu : voir `python3 tools/cityhash.py --verifier`.
"""
import struct
import sys
import zlib

M64 = (1 << 64) - 1
K0 = 0xc3a5c85c97cb3127
K1 = 0xb492b66fbe98f273
K2 = 0x9ae16a3b2f90404f


def _f64(d, p):
    return struct.unpack_from("<Q", d, p)[0]


def _f32(d, p):
    return struct.unpack_from("<I", d, p)[0]


def _rot(v, s):
    return v if s == 0 else ((v >> s) | (v << (64 - s))) & M64


def _melange(v):
    return v ^ (v >> 47)


def _bswap(v):
    return int.from_bytes(v.to_bytes(8, "little"), "big")


def _h16(u, v, mul=0x9ddfea08eb382d69):
    a = ((u ^ v) * mul) & M64
    a ^= a >> 47
    b = ((v ^ a) * mul) & M64
    b ^= b >> 47
    return (b * mul) & M64


def _h0a16(d, p, n):
    if n >= 8:
        mul = (K2 + n * 2) & M64
        a = (_f64(d, p) + K2) & M64
        b = _f64(d, p + n - 8)
        c = (_rot(b, 37) * mul + a) & M64
        e = ((_rot(a, 25) + b) * mul) & M64
        return _h16(c, e, mul)
    if n >= 4:
        mul = (K2 + n * 2) & M64
        a = _f32(d, p)
        return _h16((n + (a << 3)) & M64, _f32(d, p + n - 4), mul)
    if n > 0:
        a, b, c = d[p], d[p + (n >> 1)], d[p + n - 1]
        y = (a + (b << 8)) & M64
        z = (n + (c << 2)) & M64
        return (_melange((y * K2) ^ (z * K0)) * K2) & M64
    return K2


def _h17a32(d, p, n):
    mul = (K2 + n * 2) & M64
    a = (_f64(d, p) * K1) & M64
    b = _f64(d, p + 8)
    c = (_f64(d, p + n - 8) * mul) & M64
    e = (_f64(d, p + n - 16) * K2) & M64
    return _h16((_rot((a + b) & M64, 43) + _rot(c, 30) + e) & M64,
                (a + _rot((b + K2) & M64, 18) + c) & M64, mul)


def _faible(w, x, y, z, a, b):
    a = (a + w) & M64
    b = _rot((b + a + z) & M64, 21)
    c = a
    a = (a + x + y) & M64
    b = (b + _rot(a, 44)) & M64
    return (a + z) & M64, (b + c) & M64


def _faible_d(d, p, a, b):
    return _faible(_f64(d, p), _f64(d, p + 8), _f64(d, p + 16), _f64(d, p + 24), a, b)


def _h33a64(d, p, n):
    mul = (K2 + n * 2) & M64
    a = (_f64(d, p) * K2) & M64
    b = _f64(d, p + 8)
    c = _f64(d, p + n - 24)
    e = _f64(d, p + n - 32)
    f = (_f64(d, p + 16) * K2) & M64
    g = (_f64(d, p + 24) * 9) & M64
    h = _f64(d, p + n - 8)
    i = (_f64(d, p + n - 16) * mul) & M64
    u = (_rot((a + h) & M64, 43) + ((_rot(b, 30) + c) * 9)) & M64
    v = (((a + h) ^ e) + g + 1) & M64
    w = (_bswap(((u + v) * mul) & M64) + i) & M64
    x = (_rot((f + g) & M64, 42) + c) & M64
    y = ((_bswap(((v + w) * mul) & M64) + h) * mul) & M64
    z = (f + g + c) & M64
    a2 = (_bswap(((x + z) * mul + y) & M64) + b) & M64
    b2 = (_melange(((z + a2) * mul + e + i) & M64) * mul) & M64
    return (b2 + x) & M64


def city_hash_64(d, p=0, n=None):
    """CityHash64 sur d[p:p+n]."""
    if n is None:
        n = len(d) - p
    if n <= 32:
        return _h0a16(d, p, n) if n <= 16 else _h17a32(d, p, n)
    if n <= 64:
        return _h33a64(d, p, n)

    x = _f64(d, p + n - 40)
    y = (_f64(d, p + n - 16) + _f64(d, p + n - 56)) & M64
    z = _h16((_f64(d, p + n - 48) + n) & M64, _f64(d, p + n - 24))
    v = _faible_d(d, p + n - 64, n, z)
    w = _faible_d(d, p + n - 32, (y + K1) & M64, x)
    x = (x * K1 + _f64(d, p)) & M64

    reste = (n - 1) & ~63
    while True:
        x = (_rot((x + y + v[0] + _f64(d, p + 8)) & M64, 37) * K1) & M64
        y = (_rot((y + v[1] + _f64(d, p + 48)) & M64, 42) * K1) & M64
        x ^= w[1]
        y = (y + v[0] + _f64(d, p + 40)) & M64
        z = (_rot((z + w[0]) & M64, 33) * K1) & M64
        v = _faible_d(d, p, (v[1] * K1) & M64, (x + w[0]) & M64)
        w = _faible_d(d, p + 32, (z + w[1]) & M64, (y + _f64(d, p + 16)) & M64)
        z, x = x, z
        p += 64
        reste -= 64
        if reste == 0:
            break
    return _h16((_h16(v[0], w[0]) + (_melange(y) * K1) + z) & M64,
                (_h16(v[1], w[1]) + x) & M64)


def hash_cle(s):
    """Hash 32 bits d'un namespace ou d'une cle dans un .locres version 3.

    Unreal calcule CityHash64 sur les octets UTF-16LE, puis replie le resultat
    en 32 bits avec sa recette maison (GetTypeHash sur un uint64) :

        bas32 + haut32 * 23

    Une chaine vide vaut 0 sans passer par le hachage -- c'est le cas des
    FText de widgets, dont le namespace est justement vide.
    """
    if not s:
        return 0
    b = s.encode("utf-16-le")
    h = city_hash_64(b, 0, len(b))
    return ((h & 0xFFFFFFFF) + ((h >> 32) * 23)) & 0xFFFFFFFF


def hash_source(s):
    """Hash 32 bits d'une chaine source (FCrc::StrCrc32 : CRC-32 sur UTF-32LE).

    Il sert au moteur a reperer une traduction perimee : si la chaine source du
    paquet ne redonne pas ce hash, la traduction est ignoree. Il doit donc etre
    calcule sur le texte anglais exact lu dans l'asset, pas sur la traduction.
    """
    return zlib.crc32(s.encode("utf-32-le")) & 0xFFFFFFFF


def _verifier():
    """Confronte l'implementation aux hashes reels d'un locres du jeu.

    Le fichier contient des dizaines de milliers de couples (chaine, hash)
    ecrits par Unreal lui-meme : si tout concorde, l'implementation est juste.
    """
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import locres

    chemin = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "work/ShooterGame_en.locres")
    _, namespaces, chaines, _ = locres.read(chemin)

    total = bons = 0
    exemples = []
    for ns_hash, ns, cles in namespaces:
        total += 1
        calcule = hash_cle(ns)
        bons += calcule == ns_hash
        if calcule != ns_hash and len(exemples) < 5:
            exemples.append((ns, hex(ns_hash), hex(calcule)))
        for cle_hash, cle, src_hash, idx in cles:
            # dans le locres anglais, la chaine stockee EST la chaine source :
            # son hash doit donc concorder lui aussi
            for f, essai, attendu in ((hash_cle, cle, cle_hash),
                                      (hash_source, chaines[idx][0], src_hash)):
                total += 1
                calcule = f(essai)
                bons += calcule == attendu
                if calcule != attendu and len(exemples) < 5:
                    exemples.append((essai[:40], hex(attendu), hex(calcule)))

    print(f"  {bons}/{total} hashes concordent "
          f"({'implementation validee' if bons == total else 'ECHEC'})")
    for e in exemples:
        print(f"    {e[0]!r} attendu {e[1]} calcule {e[2]}")
    return 0 if bons == total else 1


if __name__ == "__main__":
    if "--verifier" in sys.argv:
        sys.exit(_verifier())
    for arg in sys.argv[1:]:
        print(f"cle={hash_cle(arg):#010x}  source={hash_source(arg):#010x}  {arg!r}")
