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

    python3 tools/pak_asa.py NOTRE.pak PAK_DU_JEU.pak
"""
import struct
import sys

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


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    print("pied v12, version du jeu %d.%d" % adapter(sys.argv[1], sys.argv[2]))
