#!/usr/bin/env python3
"""Aligne le pied d'un pak ecrit par repak sur celui des paks d'ARK.

repak ne sait pas ecrire au-dela de la version 11, et son pied s'arrete apres
les cinq noms de compression. Les paks d'ARK sont en version 12, et Wildcard a
ajoute a leur pied 8 octets de plus : la version du jeu, en deux entiers 32 bits
(93 et 37 pour la v93.37, 98 et 6 pour la v98.6). Avant l'Unreal Engine 5.8 le
moteur acceptait encore notre pied v11 sans ces octets ; depuis la mise a jour
du 6 novembre 2026, le pak est ignore sans un mot (issue #62).

L'index d'une v12 se serialise comme celui d'une v11 tant que les chemins sont
en ASCII, ce qui est notre cas : seuls le numero de version et la fin du pied
changent, l'index et son empreinte restent valides.

Deuxieme defaut de l'UE 5.8, trouve en jeu le 19/11 : quand un pak a un index
complet des repertoires, le moteur le range dans un arbre de repertoires
(pak.UseDirectoryTreeForPakSearch) et n'y retrouve pas nos locres ; il
retombe alors sur ceux du jeu. Sans index complet, il cherche par le hash des
chemins (PathHashIndex) et trouve bien les notres. On retire donc l'index
complet et on recopie les repertoires dans l'index prune, qui suit les hashes
dans le PathHashIndex et que les paks d'ARK remplissent aussi.

Enfin, depuis la 5.8, un pak sans .utoc du meme nom a cote est refuse au
montage (« utoc not found ») : on livre un conteneur IoStore vide.

    python3 tools/pak_asa.py NOTRE.pak PAK_DU_JEU.pak
"""
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import tempfile

MAGIC = struct.pack("<I", 0x5A6F12E1)
# magic, version, offset et taille de l'index, SHA-1, 5 noms de compression
PIED_V11 = 4 + 4 + 8 + 8 + 20 + 5 * 32


def _pied(chemin):
    with open(chemin, "rb") as f:
        f.seek(0, 2)
        taille = f.tell()
        f.seek(taille - 512)
        fin = f.read()
    i = fin.rfind(MAGIC)
    if i < 0:
        raise SystemExit(f"{chemin} : magic pak introuvable")
    return taille - len(fin) + i, fin[i:]


def adapter(pak, reference):
    pos_ref, pied_ref = _pied(reference)
    version_ref = struct.unpack_from("<I", pied_ref, 4)[0]
    supplement = pied_ref[PIED_V11:]
    if version_ref != 12 or len(supplement) != 8:
        raise SystemExit(f"pied inattendu dans {reference} : version "
                         f"{version_ref}, {len(supplement)} octets en plus")
    pos, pied = _pied(pak)
    version = struct.unpack_from("<I", pied, 4)[0]
    if len(pied) != PIED_V11 or version not in (11, 12):
        raise SystemExit(f"{pak} : deja adapte ou pied inconnu "
                         f"(version {version}, {len(pied)} octets)")
    with open(pak, "r+b") as f:
        f.seek(pos + 4)
        f.write(struct.pack("<I", 12))
        f.seek(0, 2)
        f.write(supplement)
    majeur, mineur = struct.unpack("<II", supplement)
    return majeur, mineur


def _fstring(d, p):
    n, = struct.unpack_from("<i", d, p)
    p += 4
    if n < 0:
        return d[p:p - 2 * n].decode("utf-16-le").rstrip("\0"), p - 2 * n
    return d[p:p + n].decode("latin-1").rstrip("\0"), p + n


def _fstring_ecrire(s):
    b = s.encode("ascii") + b"\0"
    return struct.pack("<i", len(b)) + b


def _repertoires(d, p):
    n, = struct.unpack_from("<i", d, p)
    p += 4
    reps = []
    for _ in range(n):
        nom, p = _fstring(d, p)
        nf, = struct.unpack_from("<i", d, p)
        p += 4
        fichiers = []
        for _ in range(nf):
            f, p = _fstring(d, p)
            loc, = struct.unpack_from("<i", d, p)
            p += 4
            fichiers.append((f, loc))
        reps.append((nom, fichiers))
    return reps, p


def _repertoires_ecrire(reps):
    out = [struct.pack("<i", len(reps))]
    for nom, fichiers in reps:
        out += [_fstring_ecrire(nom), struct.pack("<i", len(fichiers))]
        for f, loc in fichiers:
            out += [_fstring_ecrire(f), struct.pack("<i", loc)]
    return b"".join(out)


def sans_index_complet(pak):
    """Retire l'index complet et recopie ses repertoires dans l'index prune."""
    d = open(pak, "rb").read()
    pos, pied = _pied(pak)
    idx_off, idx_taille = struct.unpack_from("<QQ", pied, 8)
    idx = d[idx_off:idx_off + idx_taille]
    montage, p = _fstring(idx, 0)
    n_entrees, graine, a_hash = struct.unpack_from("<iQI", idx, p)
    p += 16
    if not a_hash:
        raise SystemExit(f"{pak} : pas de PathHashIndex")
    phi_off, phi_taille = struct.unpack_from("<QQ", idx, p)
    p += 36
    a_complet, = struct.unpack_from("<I", idx, p)
    p += 4
    if not a_complet:
        raise SystemExit(f"{pak} : index complet deja absent")
    fdi_off, fdi_taille = struct.unpack_from("<QQ", idx, p)
    p += 36
    entrees = idx[p:]  # taille, entrees encodees, nombre d'entrees non encodees
    phi = d[phi_off:phi_off + phi_taille]
    n_hash, = struct.unpack_from("<i", phi, 0)
    hashes = phi[:4 + 12 * n_hash]
    complet, fin = _repertoires(d[fdi_off:fdi_off + fdi_taille], 0)
    if fin != fdi_taille:
        raise SystemExit(f"{pak} : index complet illisible")
    # sans index complet, l'index prune est le seul que le moteur ait pour
    # trouver et enumerer les fichiers : chaque repertoire et tous ses parents
    # doivent y figurer
    noms = {nom for nom, _ in complet}
    for nom, fichiers in complet:
        parties = nom.strip("/").split("/") if nom != "/" else []
        for k in range(len(parties)):
            parent = "".join(x + "/" for x in parties[:k]) or "/"
            if parent not in noms:
                raise SystemExit(f"{pak} : {parent!r} absent de l'index ({nom!r})")
    phi = hashes + _repertoires_ecrire(complet)
    phi_off = idx_off + len(idx) - 36  # l'index perd offset, taille et SHA-1 du complet
    nouvel = (_fstring_ecrire(montage) + struct.pack("<iQI", n_entrees, graine, 1)
              + struct.pack("<QQ", phi_off, len(phi)) + hashlib.sha1(phi).digest()
              + struct.pack("<I", 0) + entrees)
    if idx_off + len(nouvel) != phi_off:
        raise SystemExit("taille d'index inattendue")
    pied = bytearray(pied)
    struct.pack_into("<QQ", pied, 8, idx_off, len(nouvel))
    pied[24:44] = hashlib.sha1(nouvel).digest()
    debut_pied = pos - 17  # GUID de chiffrement et indicateur d'index chiffre
    with open(pak, "wb") as f:
        f.write(d[:idx_off] + nouvel + phi + d[debut_pied:pos] + bytes(pied))
    return len(complet)


def conteneur_vide(pak, retoc):
    """Ecrit a cote du pak un .utoc/.ucas vide, au format des conteneurs du jeu."""
    base = os.path.splitext(pak)[0]
    with tempfile.TemporaryDirectory() as tmp:
        vide = os.path.join(tmp, "vide")
        os.mkdir(vide)
        # retoc ecrit aussi un .pak de 347 octets a cote : il ne doit pas
        # ecraser le notre, d'ou le dossier temporaire
        # l'identifiant du conteneur derive de son nom : garder celui du pak
        nom = os.path.basename(base)
        subprocess.run([retoc, "to-zen", "--version", "UE5_7", vide,
                        os.path.join(tmp, nom + ".utoc")], check=True,
                       stdout=subprocess.DEVNULL)
        for ext in (".utoc", ".ucas"):
            shutil.copyfile(os.path.join(tmp, nom + ext), base + ext)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print("pied v12, version du jeu %d.%d" % adapter(sys.argv[1], sys.argv[2]))
    print("index complet retire, %d repertoires dans l'index prune" % sans_index_complet(sys.argv[1]))
