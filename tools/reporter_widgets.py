#!/usr/bin/env python3
"""Reporte les traductions déjà faites sur les FText jamais collectées.

Le balayage des assets (tools/balayer_assets.py) trouve des milliers de FText
que Wildcard n'a jamais passées à la collecte de localisation : leur couple
namespace/clé n'est dans aucun .locres, donc elles s'affichent en anglais quelle
que soit la langue. La grande majorité dit pourtant *exactement* la même chose
qu'une chaîne que le patch traduit déjà ailleurs - les tables de primes en sont
l'exemple type : mêmes textes, mais une clé GUID dans l'asset et une clé
numérique dans le locres.

Ce script reporte ces traductions, sous trois garde-fous :

  - correspondance exacte de la source anglaise, jamais approximative ;
  - traduction unique : si le patch rend la même source anglaise de deux façons
    selon le contexte, on ne devine pas, la chaîne part en traduction manuelle ;
  - casse compatible : le patch pré-capitalise certains libellés pour contourner
    le ToUpper du moteur qui mange les accents. Coller « ARMES » dans une phrase
    dont la source est « Weapons » donnerait un texte criard, donc on refuse.

    python3 tools/reporter_widgets.py <orphelines.json> [--ecrire]

Sans --ecrire, le script se contente d'afficher ce qu'il ferait.
"""
import collections
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LETTRES = re.compile(r"[A-Za-zÀ-ÿ]")


def _capitales(s):
    """Vrai si la chaîne est en capitales (au moins 4 lettres, aucune minuscule)."""
    lettres = LETTRES.findall(s)
    return len(lettres) >= 4 and not any(c.islower() for c in lettres)


def table_de_report():
    """EN -> FR, uniquement pour les sources rendues d'une seule façon."""
    en = json.load(open(os.path.join(RACINE, "work/en.json")))
    fr = json.load(open(os.path.join(RACINE, "work/edits_merged.json")))
    rendus = collections.defaultdict(set)
    for cle, trad in fr.items():
        source = en.get(cle)
        if source:
            rendus[source].add(trad)
    return {s: next(iter(t)) for s, t in rendus.items() if len(t) == 1}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ecrire = "--ecrire" in sys.argv
    orphelines = json.load(open(args[0]))
    report = table_de_report()

    sortie = os.path.join(RACINE, "data/textes_widgets.json")
    donnees = json.load(open(sortie)) if os.path.exists(sortie) else {}

    ajoutees = refusees_casse = deja = sans_report = 0
    for cle, entree in orphelines.items():
        if cle in donnees:
            deja += 1
            continue
        source = entree["source"]
        trad = report.get(source)
        if trad is None:
            sans_report += 1
            continue
        if _capitales(trad) and not _capitales(source):
            refusees_casse += 1
            continue
        donnees[cle] = [source, trad]
        ajoutees += 1

    print(f"  {ajoutees:5}  reportées")
    print(f"  {refusees_casse:5}  écartées (casse incompatible)")
    print(f"  {deja:5}  déjà présentes")
    print(f"  {sans_report:5}  sans équivalent : à traduire à la main")
    if ecrire:
        json.dump(donnees, open(sortie, "w"), ensure_ascii=False,
                  indent=1, sort_keys=True)
        print(f"\n  data/textes_widgets.json : {len(donnees)} entrées")
    else:
        print("\n  (essai à blanc : relancer avec --ecrire)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
