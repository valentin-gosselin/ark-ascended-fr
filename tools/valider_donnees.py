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
# Les chevrons doubles ne sont pas des balises : les notes d'exploration s'en
# servent pour citer un intervenant (« <<Mei-Yin et Diana Altaras>> »), et ces
# noms se traduisent. Le retrait en tete evite de les confondre avec du balisage.
VARIABLE = re.compile(r"\{[^}]*\}|%[a-z%]|(?<!<)</?[A-Za-z][^>]*>")
# Tirets cadratin et demi-cadratin : proscrits dans les traductions du projet,
# on ecrit un tiret simple. La regle vaut aussi quand la source anglaise en
# contient un.
CADRATIN = re.compile(r"[–—]")
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
            elif CADRATIN.search(v):
                problemes.append(f"{nom} : {k!r} : tiret cadratin, ecrire un tiret simple")
        trad.update(d)

    # textes_widgets.json a une autre forme : {"ns\tcle": ["source EN", "FR"]}.
    # La source anglaise y est indispensable -- ces cles n'existent dans aucun
    # locres du jeu, donc rien d'autre ne permet de retrouver le texte d'origine,
    # ni de calculer le hash qui empeche le moteur de juger la traduction perimee.
    widgets = os.path.join(RACINE, "data/textes_widgets.json")
    n_widgets = 0
    if os.path.exists(widgets):
        try:
            d = json.load(open(widgets))
        except (OSError, json.JSONDecodeError) as e:
            erreur(f"textes_widgets.json : illisible ({e})")
            return 1
        n_widgets = len(d)
        for k, v in d.items():
            # le namespace est souvent vide (FText de widget) : le motif general
            # ne s'applique pas, on verifie seulement qu'il y a une cle
            if "\t" not in k or not k.split("\t", 1)[1]:
                problemes.append(f"textes_widgets.json : cle mal formee {k!r}")
                continue
            if not (isinstance(v, list) and len(v) == 2
                    and all(isinstance(x, str) for x in v)):
                problemes.append(f"textes_widgets.json : {k!r} n'est pas "
                                 f"une paire [source, traduction]")
                continue
            src, fr = v
            if sorted(VARIABLE.findall(src)) != sorted(VARIABLE.findall(fr)):
                problemes.append(f"textes_widgets.json : {k!r} : les variables "
                                 f"ne correspondent pas a la source")
            if (src[:1] == " ") != (fr[:1] == " ") or (src[-1:] == " ") != (fr[-1:] == " "):
                problemes.append(f"textes_widgets.json : {k!r} : espace de debut "
                                 f"ou de fin modifiee")
            # seule la traduction est concernee : la source anglaise doit rester
            # au caractere pres, son hash en depend
            if CADRATIN.search(fr):
                problemes.append(f"textes_widgets.json : {k!r} : tiret cadratin, "
                                 f"ecrire un tiret simple")

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
    print(f"{len(trad)} traductions validees, {n_widgets} textes de widgets, "
          f"{len(ecarts)} ecart(s) connu(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
