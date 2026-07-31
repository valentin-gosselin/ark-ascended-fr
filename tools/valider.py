#!/usr/bin/env python3
"""Valide les sorties des lots de traduction/arbitrage.

Contrôles par entrée :
  - clés de sortie == clés d'entrée (chantier A) ou sous-ensemble (chantier B)
  - placeholders {...} et balises <...> identiques entre source EN et FR
  - espaces de début/fin préservés
  - valeur non vide si le source ne l'est pas

Usage : valider.py <A|B> <in_dir> <out_dir>
Sortie : rapport par lot ; code retour 1 si au moins une erreur bloquante.
"""
import glob
import json
import os
import re
import sys


# Un placeholder UE est un identifiant (pas d'espace) : {0}, {Multiplier}, {DayPct}.
# Une accolade contenant une phrase est du texte affiché littéralement, donc
# traduisible. Même logique pour les chevrons : <RichColor ...> est une balise,
# « <Web tracing complete> » est du texte.
PLACEHOLDER = re.compile(r"\{[A-Za-z0-9_.:|]*\}")
# Balise = fermeture (</> ou </x>), auto-fermante (<x/>), attributs (<x a="b">)
# ou mot seul (<br>). « <Web tracing complete> » n'entre dans aucun cas : c'est
# du texte entre chevrons, donc traduisible.
BALISE = re.compile(
    r"</[^<>]*>"
    r"|<[A-Za-z][A-Za-z0-9_.]*\s*/>"
    r"|<[A-Za-z][A-Za-z0-9_.]*(?:\s+[A-Za-z0-9_.]+\s*=\s*[^<>]*)+/?>"
    r"|<[A-Za-z][A-Za-z0-9_.]*>")


def tokens(s):
    return sorted(PLACEHOLDER.findall(s)), sorted(BALISE.findall(s))


def edges(s):
    m1 = re.match(r"^\s*", s).group()
    m2 = re.search(r"\s*$", s).group()
    return m1, m2


def check(mode, in_dir, out_dir):
    errors = 0
    for in_path in sorted(glob.glob(os.path.join(in_dir, "in_*.json"))):
        num = os.path.basename(in_path)[3:-5]
        out_path = os.path.join(out_dir, f"{mode}_{num}.json")
        if not os.path.exists(out_path):
            print(f"[{mode}_{num}] MANQUANT")
            errors += 1
            continue
        try:
            src = json.load(open(in_path))
            out = json.load(open(out_path))
        except json.JSONDecodeError as e:
            print(f"[{mode}_{num}] JSON invalide : {e}")
            errors += 1
            continue
        probs = []
        if mode == "A":
            miss = set(src) - set(out)
            if miss:
                probs.append(f"{len(miss)} clés absentes")
        extra = set(out) - set(src)
        if extra:
            probs.append(f"{len(extra)} clés inconnues")
        for k, v in out.items():
            if k not in src:
                continue
            en = src[k]["en"]
            if not isinstance(v, str):
                probs.append(f"{k!r}: valeur non-chaîne")
                continue
            if en.strip() and not v.strip():
                probs.append(f"{k!r}: vide")
            if tokens(en) != tokens(v):
                probs.append(f"{k!r}: placeholders/balises modifiés")
            if edges(en) != edges(v):
                probs.append(f"{k!r}: espaces de bord modifiés")
        if probs:
            errors += 1
            print(f"[{mode}_{num}] {len(probs)} problème(s) :")
            for p in probs[:8]:
                print("   -", p)
        else:
            print(f"[{mode}_{num}] OK ({len(out)} entrées)")
    return errors


if __name__ == "__main__":
    sys.exit(1 if check(sys.argv[1], sys.argv[2], sys.argv[3]) else 0)
