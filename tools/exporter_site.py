#!/usr/bin/env python3
"""Produit les donnees de l'interface de traduction communautaire.

L'interface (site/) est une page statique servie par GitHub Pages. Elle a besoin
de toutes les lignes du patch avec, pour chacune, le texte anglais et la
traduction actuelle. Ce fichier est genere a chaque deploiement et n'est jamais
versionne : il derive entierement de data/.

Deux familles de lignes, qui ne se corrigent pas au meme endroit :

  - les chaines du fichier de langue du jeu, dont l'anglais vient de
    data/reference_en.json. Une correction va dans data/corrections.json, la
    couche prioritaire du build.
  - les textes poses dans les assets, que Wildcard n'a jamais collectes. Ils
    vivent dans data/textes_widgets.json et gardent leur source anglaise, dont
    le hash conditionne leur prise en compte par le moteur. Une correction va
    donc dans ce fichier, sous forme de paire.

    python3 tools/exporter_site.py [sortie.json]
"""
import json
import os
import sys
from datetime import date

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCRES, WIDGET = 0, 1


def charger():
    ref = os.path.join(RACINE, "data/reference_en.json")
    en = json.load(open(ref))["chaines"] if os.path.exists(ref) else {}
    trad = {}
    for nom in ("overrides.json", "additions.json", "corrections.json"):
        chemin = os.path.join(RACINE, "data", nom)
        if os.path.exists(chemin):
            trad.update(json.load(open(chemin)))
    widgets = json.load(open(os.path.join(RACINE, "data/textes_widgets.json")))
    return en, trad, widgets


def main():
    sortie = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RACINE, "site/donnees.json")
    en, trad, widgets = charger()

    lignes = []
    for cle, source in en.items():
        lignes.append([cle, source, trad.get(cle, ""), LOCRES])
    for cle, (source, fr) in widgets.items():
        lignes.append([cle, source, fr, WIDGET])

    lignes.sort(key=lambda l: l[1].lower())
    os.makedirs(os.path.dirname(sortie), exist_ok=True)
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump({"genere": date.today().isoformat(), "lignes": lignes},
                  f, ensure_ascii=False, separators=(",", ":"))

    sans = sum(1 for l in lignes if not l[2] or l[2].strip() == l[1].strip())
    print(f"  {len(lignes)} lignes, dont {sans} sans traduction propre")
    print(f"  {os.path.getsize(sortie) / 1e6:.1f} Mo -> {sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
