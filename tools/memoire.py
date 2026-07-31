#!/usr/bin/env python3
"""Mémoire de traduction ASE -> ASA.

Apparie les locres EN/FR d'ARK Survival Evolved par clé pour construire un
dictionnaire texte-anglais -> texte-français, puis propose une traduction pour
chaque clé d'ASA absente du locres FR dont le texte anglais est connu d'ASE.

Usage :
  memoire.py <ase_en.json> <ase_fr.json> <asa_en.json> <asa_fr.json> <candidats.json>
"""
import collections
import json
import sys


def main(ase_en_p, ase_fr_p, asa_en_p, asa_fr_p, out_p):
    ase_en = json.load(open(ase_en_p))
    ase_fr = json.load(open(ase_fr_p))
    asa_en = json.load(open(asa_en_p))
    asa_fr = json.load(open(asa_fr_p))
    # dictionnaire EN -> FR depuis ASE (vote majoritaire si plusieurs FR)
    votes = collections.defaultdict(collections.Counter)
    for k, en_text in ase_en.items():
        fr_text = ase_fr.get(k)
        if not en_text or not fr_text or fr_text == en_text:
            continue  # vide ou non traduit dans ASE
        votes[en_text.strip()][fr_text] += 1
    memoire = {en: c.most_common(1)[0][0] for en, c in votes.items()}
    print(f"mémoire ASE : {len(memoire)} paires EN->FR")
    # application aux clés manquantes d'ASA
    candidats = {}
    for k, en_text in asa_en.items():
        if k in asa_fr:
            continue
        fr = memoire.get(en_text.strip())
        if fr is not None:
            candidats[k] = fr
    json.dump(candidats, open(out_p, "w"), ensure_ascii=False, indent=0)
    manquantes = sum(1 for k in asa_en if k not in asa_fr)
    print(f"clés ASA manquantes : {manquantes}, couvertes par ASE : {len(candidats)}")


if __name__ == "__main__":
    main(*sys.argv[1:6])
