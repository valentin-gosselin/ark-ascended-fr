#!/usr/bin/env python3
"""Répare les écarts mécaniques entre source anglaise et traduction.

Deux familles de défauts, tous corrigeables sans rejuger la traduction :
  - espaces de bord : le jeu s'appuie dessus pour la mise en page, on recopie
    exactement ceux du source (y compris espace fine U+2009, insécable U+00A0)
  - échappements littéraux : un source contenant la séquence de deux caractères
    \\n ne doit pas devenir un vrai retour à la ligne dans la traduction

Usage : corriger_bords.py <in_dir> <out_dir> <A|B>
"""
import glob
import json
import os
import re
import sys


def bords(s):
    return re.match(r"^\s*", s).group(), re.search(r"\s*$", s).group()


def corriger(en, fr):
    notes = []
    # échappement littéral \n présent dans le source mais déplié dans la trad
    if "\\n" in en and "\n" in fr and "\\n" not in fr:
        fr = fr.replace("\n", "\\n")
        notes.append("échappement \\n restauré")
    deb_en, fin_en = bords(en)
    deb_fr, fin_fr = bords(fr)
    if (deb_en, fin_en) != (deb_fr, fin_fr):
        coeur = fr[len(deb_fr):len(fr) - len(fin_fr) if fin_fr else None]
        fr = deb_en + coeur + fin_en
        notes.append("espaces de bord recopiés")
    return fr, notes


def main(in_dir, out_dir, prefix):
    total = 0
    for out_path in sorted(glob.glob(os.path.join(out_dir, f"{prefix}_*.json"))):
        num = os.path.basename(out_path).split("_")[1].split(".")[0]
        in_path = os.path.join(in_dir, f"in_{num}.json")
        if not os.path.exists(in_path):
            continue
        src = json.load(open(in_path))
        out = json.load(open(out_path))
        change = False
        for k, v in list(out.items()):
            if k not in src:
                continue
            nv, notes = corriger(src[k]["en"], v)
            if notes:
                out[k] = nv
                change = True
                total += 1
                print(f"  [{prefix}_{num}] {', '.join(notes)} : {v[:50]!r}")
        if change:
            json.dump(out, open(out_path, "w"), ensure_ascii=False, indent=1)
    print(f"{total} entrées corrigées")


if __name__ == "__main__":
    main(*sys.argv[1:4])
