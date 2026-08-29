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

    # Propositions communautaires deposees depuis l'interface web : un petit
    # fichier par contribution, verifie ici comme le reste. C'est le filet de
    # securite d'un contributeur qui ne connait ni Git ni le format des cles.
    dossier = os.path.join(RACINE, "data/propositions")
    n_prop = 0
    if os.path.isdir(dossier):
        source_en = {}
        chemin_ref = os.path.join(RACINE, "data/reference_en.json")
        if os.path.exists(chemin_ref):
            source_en = json.load(open(chemin_ref))["chaines"]
        widgets_connus = {}
        chemin_w = os.path.join(RACINE, "data/textes_widgets.json")
        if os.path.exists(chemin_w):
            widgets_connus = json.load(open(chemin_w))

        for nom in sorted(os.listdir(dossier)):
            if not nom.endswith(".json"):
                problemes.append(f"propositions/{nom} : seuls des fichiers .json sont acceptes")
                continue
            try:
                p = json.load(open(os.path.join(dossier, nom), encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                erreur(f"propositions/{nom} : illisible ({e})")
                return 1
            if not isinstance(p, dict) or set(p) - {"corrections", "widgets", "auteur"}:
                problemes.append(f"propositions/{nom} : attendu « corrections » et « widgets »")
                continue

            for cle, texte in (p.get("corrections") or {}).items():
                n_prop += 1
                etiq = f"propositions/{nom} : {cle!r}"
                if not isinstance(texte, str) or not texte.strip():
                    problemes.append(f"{etiq} : traduction vide")
                    continue
                if CADRATIN.search(texte):
                    problemes.append(f"{etiq} : tiret cadratin, ecrire un tiret simple")
                src = source_en.get(cle)
                if src is None:
                    problemes.append(f"{etiq} : cle inconnue du jeu")
                    continue
                if sorted(VARIABLE.findall(src)) != sorted(VARIABLE.findall(texte)):
                    problemes.append(f"{etiq} : les variables ne correspondent pas a la source")
                if (src[:1] == " ") != (texte[:1] == " ") or (src[-1:] == " ") != (texte[-1:] == " "):
                    problemes.append(f"{etiq} : espace de debut ou de fin modifiee")

            for cle, paire in (p.get("widgets") or {}).items():
                n_prop += 1
                etiq = f"propositions/{nom} : {cle!r}"
                if not (isinstance(paire, list) and len(paire) == 2
                        and all(isinstance(x, str) for x in paire)):
                    problemes.append(f"{etiq} : attendu une paire [source, traduction]")
                    continue
                src, texte = paire
                if not texte.strip():
                    problemes.append(f"{etiq} : traduction vide")
                    continue
                if CADRATIN.search(texte):
                    problemes.append(f"{etiq} : tiret cadratin, ecrire un tiret simple")
                # la source anglaise doit rester au caractere pres : son hash
                # conditionne la prise en compte de la ligne par le moteur
                if cle in widgets_connus and widgets_connus[cle][0] != src:
                    problemes.append(f"{etiq} : la source anglaise a ete modifiee")
                if sorted(VARIABLE.findall(src)) != sorted(VARIABLE.findall(texte)):
                    problemes.append(f"{etiq} : les variables ne correspondent pas a la source")
                if (src[:1] == " ") != (texte[:1] == " ") or (src[-1:] == " ") != (texte[-1:] == " "):
                    problemes.append(f"{etiq} : espace de debut ou de fin modifiee")

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
          f"{n_prop} proposition(s), {len(ecarts)} ecart(s) connu(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
