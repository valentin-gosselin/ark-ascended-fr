#!/usr/bin/env python3
"""Reconstruit data/overrides.json a partir de la base git + des lots traduits.

Regle d'or (piege n°2) : la base BASE_COMMIT contient les corrections ciblees
verifiees a la main. Les lots ne peuvent QUE completer cette base, jamais
l'ecraser -- sauf via data/corrections.json, qui est applique en dernier et
fait autorite sur tout le reste.
"""

import glob
import json
import os
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_COMMIT = "613747a"  # hash reecrit le 05/08/2026 (purge des binaires Oodle de l'historique)

LOTS = [
    "work/batches/out/C_*.json",
    "work/moi/out_*.json",
    "work/batches/out/D_*.json",
    "work/batches/out/E_*.json",
    "work/lore/out_*.json",
]


def charger_base():
    txt = subprocess.run(
        ["git", "-C", RACINE, "show", f"{BASE_COMMIT}:data/overrides.json"],
        capture_output=True, text=True, check=True).stdout
    return json.loads(txt)


def main():
    base = charger_base()
    ovr = dict(base)
    ajouts = 0
    for motif in LOTS:
        for chemin in sorted(glob.glob(os.path.join(RACINE, motif))):
            lot = json.load(open(chemin))
            if not all(isinstance(v, str) for v in lot.values()):
                continue
            for k, v in lot.items():
                if k not in base:
                    ovr[k] = v
                    ajouts += 1

    corr_path = os.path.join(RACINE, "data", "corrections.json")
    corrections = 0
    if os.path.exists(corr_path):
        for k, v in json.load(open(corr_path)).items():
            ovr[k] = v
            corrections += 1

    dest = os.path.join(RACINE, "data", "overrides.json")
    json.dump(ovr, open(dest, "w"), ensure_ascii=False, indent=0)
    print(f"base {BASE_COMMIT} : {len(base)} entrees")
    print(f"lots : {ajouts} ajouts")
    print(f"corrections.json : {corrections} entrees prioritaires")
    print(f"overrides.json : {len(ovr)} entrees")
    return 0


if __name__ == "__main__":
    sys.exit(main())
