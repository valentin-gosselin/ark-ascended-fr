#!/usr/bin/env python3
"""Normalise les sorties de traduction (uniformité interne au patch).

Deux passes seulement :
  1. apostrophe : U+2019 -> ' (l'officiel utilise l'apostrophe droite à 96 %)
  2. format « Dossier : X » (forme majoritaire dans l'officiel, 131 contre 47)

ATTENTION : ne JAMAIS réaligner automatiquement une traduction sur celle du jeu
officiel. Une passe de ce type a été essayée puis retirée : la traduction FR
officielle est justement celle qu'on corrige, et elle a réécrit des traductions
correctes en absurdités (« Trike » -> « Tricycle », « Retour » -> « ouvrir »,
identifiants techniques massacrés). L'officiel sert de référence de style et de
glossaire consulté par un humain ou un agent, jamais de source de vérité
appliquée mécaniquement.

Usage : normaliser.py <in_dir> <out_dir> <A|B>
Modifie les fichiers de sortie en place et affiche le détail des corrections.
"""
import glob
import json
import os
import re
import sys


def normaliser(texte, en):
    corrections = []
    avant = texte
    texte = texte.replace("’", "'")
    if texte != avant:
        corrections.append("apostrophe")
    # format Dossier
    m = re.fullmatch(r"Dossier (?:du |de la |de l'|des |d')?(.+)", texte)
    if m and re.search(r"\bDossier\b", en) and not texte.startswith("Dossier :"):
        nouveau = f"Dossier : {m.group(1)}"
        corrections.append(f"format dossier: {texte!r} -> {nouveau!r}")
        texte = nouveau
    return texte, corrections


def main(in_dir, out_dir, prefix):
    total = 0
    detail = []
    for out_path in sorted(glob.glob(os.path.join(out_dir, f"{prefix}_*.json"))):
        num = os.path.basename(out_path).split("_",1)[1].rsplit(".",1)[0]
        in_path = os.path.join(in_dir, f"in_{num}.json")
        if not os.path.exists(in_path):
            continue
        src = json.load(open(in_path))
        out = json.load(open(out_path))
        change = False
        for k, v in list(out.items()):
            if k not in src:
                continue
            nv, corr = normaliser(v, src[k]["en"])
            if corr:
                out[k] = nv
                change = True
                total += len(corr)
                detail.extend(c for c in corr if c != "apostrophe")
        if change:
            json.dump(out, open(out_path, "w"), ensure_ascii=False, indent=1)
    print(f"{total} corrections appliquées")
    for d in detail[:40]:
        print("  ", d)
    if len(detail) > 40:
        print(f"   ... et {len(detail)-40} autres")


if __name__ == "__main__":
    main(*sys.argv[1:6])
