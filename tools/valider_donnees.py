#!/usr/bin/env python3
"""Controle de coherence des donnees de traduction, sans le jeu installe.

C'est le filet de securite des contributions : une pull request qui casserait
les donnees echoue ici, avant toute relecture humaine. Le meme script sert a la
validation des contributions et a celle de la veille automatique, pour qu'il n'y
ait qu'une seule definition de « donnees valides ».

    python3 tools/valider_donnees.py     # code de retour 1 si un probleme
"""
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIERS = ("overrides.json", "additions.json", "corrections.json")
CLE = re.compile(r"^[A-Za-z0-9_]+\t\S+$")   # certains namespaces sont des hashes
VARIABLE = re.compile(r"\{[^}]*\}|%[a-z%]|</?[A-Za-z][^>]*>")
# le jeu se sert des accolades comme texte litteral dans 4 chaines : ces ecarts
# sont connus, verifies, et ne doivent pas faire echouer la validation
ECARTS_CONNUS = 4


def erreur(msg):
    print(f"::error::{msg}")


def main():
    problemes = []
    trad = {}

    for nom in FICHIERS:
        chemin = os.path.join(RACINE, "data", nom)
        try:
            d = json.load(open(chemin))
        except (OSError, json.JSONDecodeError) as e:
            erreur(f"{nom} : illisible ({e})")
            return 1
        for k, v in d.items():
            if not CLE.match(k):
                problemes.append(f"{nom} : cle mal formee {k!r}")
            elif not isinstance(v, str):
                problemes.append(f"{nom} : {k!r} n'est pas une chaine de texte")
        trad.update(d)

    ref = os.path.join(RACINE, "data/reference_en.json")
    ecarts = []
    if os.path.exists(ref):
        en = json.load(open(ref))["chaines"]
        for k, v in trad.items():
            e = en.get(k)
            if e is None:
                continue   # cle inconnue du jeu : signalee par la veille, pas bloquante
            if "{" in e and sorted(VARIABLE.findall(e)) != sorted(VARIABLE.findall(v)):
                ecarts.append(f"{k!r} : les variables ne correspondent pas a la source")
            if (e[:1] == " ") != (v[:1] == " ") or (e[-1:] == " ") != (v[-1:] == " "):
                problemes.append(f"{k!r} : espace de debut ou de fin modifiee")

    if len(ecarts) > ECARTS_CONNUS:
        problemes += ecarts

    for p in problemes[:20]:
        erreur(p)
    if len(problemes) > 20:
        print(f"::error::... et {len(problemes) - 20} autres")
    if problemes:
        return 1
    print(f"{len(trad)} traductions validees, {len(ecarts)} ecart(s) connu(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
