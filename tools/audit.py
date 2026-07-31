#!/usr/bin/env python3
"""Signale les traductions suspectes pour relecture humaine.

Complète valider.py (qui vérifie l'intégrité technique) par des heuristiques de
qualité : anglais résiduel, terminologie hors glossaire, typographie, longueur.

Usage : audit.py <in_dir> <out_dir> <prefixe A|B> [glossaire.tsv]
"""
import glob
import json
import os
import re
import sys

# mots anglais courants qui ne devraient pas subsister en français
ANGLAIS = re.compile(
    r"\b(the|your|you|with|from|this|that|and|for|are|was|were|will|"
    r"can|not|all|any|has|have|been|item|items|level|health|damage|"
    r"weight|speed|craft|crafting|resource|resources|player|players|"
    r"enable|disable|settings|default|unknown|none|press|hold|select)\b",
    re.I)
# termes canon : si l'anglais contient X, le français doit contenir Y
CANON = [
    (r"\bengram", r"engramme"),
    (r"\bsaddle", r"selle"),
    (r"\btribe", r"tribu"),
    (r"\bcryopod", r"cryopode"),
    (r"\bimprint", r"imprégn|imprint"),
]


def flags(en, fr, gloss):
    out = []
    if fr == en and re.search(r"[A-Za-z]{4}", en) and not re.fullmatch(r"[\W\d_]*[A-Z][A-Za-z]*[\W\d_]*", en):
        out.append("identique au source")
    mots = ANGLAIS.findall(fr)
    # tolère l'anglais si le source est un nom propre ou du balisage
    if mots and not re.match(r"^[/<]", en.strip()):
        out.append(f"anglais résiduel: {sorted(set(m.lower() for m in mots))[:4]}")
    for pat_en, pat_fr in CANON:
        if re.search(pat_en, en, re.I) and not re.search(pat_fr, fr, re.I):
            out.append(f"terminologie: {pat_en} -> attendu {pat_fr}")
    if re.search(r"\S[?!:%](?:\s|$)", fr) and re.search(r"[?!:%]", en):
        out.append("espace insécable manquant")
    if re.search(r"\boeu(f|r)", fr, re.I):
        out.append("ligature œ manquante")
    if en.isupper() and en.strip() and not fr.isupper():
        out.append("majuscules non préservées")
    if len(en) > 20 and (len(fr) > 2.6 * len(en) or len(fr) < 0.45 * len(en)):
        out.append(f"longueur anormale ({len(en)} -> {len(fr)})")
    en_key = en.strip()
    if en_key in gloss and gloss[en_key].lower() not in fr.lower() and len(en_key) > 4:
        out.append(f"glossaire: attendu {gloss[en_key]!r}")
    return out


def main(in_dir, out_dir, prefix, gloss_path=None):
    gloss = {}
    if gloss_path and os.path.exists(gloss_path):
        for line in open(gloss_path):
            if "\t" in line:
                e, f = line.rstrip("\n").split("\t", 1)
                gloss[e] = f
    total = suspects = 0
    report = {}
    for out_path in sorted(glob.glob(os.path.join(out_dir, f"{prefix}_*.json"))):
        num = os.path.basename(out_path).split("_")[1].split(".")[0]
        in_path = os.path.join(in_dir, f"in_{num}.json")
        if not os.path.exists(in_path):
            continue
        src = json.load(open(in_path))
        out = json.load(open(out_path))
        for k, fr in out.items():
            if k not in src:
                continue
            en = src[k]["en"]
            total += 1
            f = flags(en, fr, gloss)
            if f:
                suspects += 1
                report[k] = {"en": en, "fr": fr, "flags": f}
    print(f"{total} traductions auditées, {suspects} signalées "
          f"({100*suspects/max(total,1):.1f}%)")
    par_type = {}
    for v in report.values():
        for f in v["flags"]:
            cle = f.split(":")[0]
            par_type[cle] = par_type.get(cle, 0) + 1
    for k, v in sorted(par_type.items(), key=lambda kv: -kv[1]):
        print(f"  {v:5d}  {k}")
    json.dump(report, open(os.path.join(out_dir, f"audit_{prefix}.json"), "w"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:5])
