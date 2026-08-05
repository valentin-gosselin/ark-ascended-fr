#!/usr/bin/env python3
"""Compare la version anglaise du jeu a la reference figee du patch.

A chaque mise a jour d'ARK, Wildcard ajoute, modifie et supprime des chaines.
Rien ne le signale : le patch continue de se construire et les nouveaux textes
s'affichent simplement en anglais. Ce script rend le decalage visible et produit
le lot de travail exact a traduire.

    ./delta.py                 compare et affiche le rapport
    ./delta.py --lots          ecrit en plus les lots de travail dans work/delta/
    ./delta.py --figer         fige l'etat courant comme nouvelle reference

Le premier appel doit etre `--figer` : il enregistre l'anglais actuel dans
data/reference_en.json, qui est versionne dans le depot.
"""
import json
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(RACINE, "data/reference_en.json")
EN = os.path.join(RACINE, "work/en.json")
SORTIE = os.path.join(RACINE, "work/delta")
DATA = ["overrides.json", "additions.json", "corrections.json"]
ASA = "/mnt/Apps/SteamLibrary/steamapps/common/ARK Survival Ascended"
SRC_PAK = os.path.join(ASA, "ShooterGame/Content/Paks/pakchunk0-Windows.pak")


def extraire():
    """Force une extraction fraiche de l'anglais depuis le pak du jeu."""
    if os.path.exists(EN):
        os.remove(EN)
    locres = os.path.join(RACINE, "work/ShooterGame_en.locres")
    if os.path.exists(locres):
        os.remove(locres)
    subprocess.run([sys.executable, os.path.join(RACINE, "build.py"), "--no-install"],
                   check=True, capture_output=True)


def empreinte():
    st = os.stat(SRC_PAK)
    return {"taille": st.st_size, "date": int(st.st_mtime)}


def figer():
    en = json.load(open(EN))
    json.dump({"pak": empreinte(), "chaines": en},
              open(REFERENCE, "w"), ensure_ascii=False, indent=0)
    print(f"reference figee : {len(en)} chaines anglaises ({REFERENCE})")


def nos_traductions():
    """Toutes les cles que le patch traduit, couche prioritaire en dernier."""
    trad = {}
    for nom in DATA:
        chemin = os.path.join(RACINE, "data", nom)
        if os.path.exists(chemin):
            trad.update(json.load(open(chemin)))
    return trad


TECHNIQUE = re.compile(
    r"import |unreal\.|cheat |UPROPERTY|\bdef \b|\.py\b|\.uasset|Blueprint'"
    r"|ServerSidePoint|_C\b|Lorem ipsum", re.I)


def traduisible(texte):
    """Ecarte ce qu'un traducteur n'a pas a voir : separateurs, code, debug."""
    t = texte.strip()
    if len(t) < 2 or not re.search(r"[A-Za-z]{2,}", t):
        return False
    if TECHNIQUE.search(t):
        return False
    # marqueurs de dev du type **NotUsed**, **TODO**
    if re.fullmatch(r"\*{1,2}[A-Za-z ]+\*{1,2}", t):
        return False
    # identifiant isole : un seul mot, sans espace, en CamelCase ou tout capitales
    if " " not in t and (re.fullmatch(r"[A-Z][a-z]+(?:[A-Z][a-z]+)+", t)
                         or re.fullmatch(r"[A-Z_]{3,}", t)):
        return False
    return True


def main():
    if "--figer" in sys.argv:
        if not os.path.exists(EN):
            extraire()
        return figer()

    if not os.path.exists(REFERENCE):
        sys.exit("Aucune reference : lancez d'abord ./delta.py --figer")

    ref = json.load(open(REFERENCE))
    if empreinte() == ref["pak"]:
        print("Le pak du jeu n'a pas bouge depuis la reference : aucun delta.")
        return 0
    extraire()
    ancien, nouveau = ref["chaines"], json.load(open(EN))
    trad = nos_traductions()

    ajoutees = {k: v for k, v in nouveau.items() if k not in ancien}
    supprimees = [k for k in ancien if k not in nouveau]
    # l'anglais a change : notre traduction dit peut-etre autre chose
    modifiees = {k: {"avant": ancien[k], "apres": v}
                 for k, v in nouveau.items()
                 if k in ancien and ancien[k] != v}

    nouvelles = {k: v for k, v in ajoutees.items() if k not in trad}
    a_traduire = {k: v for k, v in nouvelles.items() if traduisible(v)}
    techniques = {k: v for k, v in nouvelles.items() if not traduisible(v)}
    a_revoir = {k: d for k, d in modifiees.items() if k in trad}
    orphelines = [k for k in trad if k not in nouveau]

    print(f"pak du jeu : {ref['pak']['taille']} -> {empreinte()['taille']} octets")
    print(f"chaines anglaises : {len(ancien)} -> {len(nouveau)}\n")
    print(f"  {len(ajoutees):6} nouvelles      dont {len(a_traduire)} a traduire "
          f"({len(techniques)} techniques ecartees)")
    print(f"  {len(modifiees):6} modifiees      dont {len(a_revoir)} deja traduites (a revoir)")
    print(f"  {len(supprimees):6} supprimees     dont {len(orphelines)} que le patch traduisait")

    if "--lots" in sys.argv:
        os.makedirs(SORTIE, exist_ok=True)
        json.dump(a_traduire, open(f"{SORTIE}/a_traduire.json", "w"),
                  ensure_ascii=False, indent=0)
        json.dump({k: {**d, "traduction_actuelle": trad[k]} for k, d in a_revoir.items()},
                  open(f"{SORTIE}/a_revoir.json", "w"), ensure_ascii=False, indent=0)
        json.dump(orphelines, open(f"{SORTIE}/orphelines.json", "w"),
                  ensure_ascii=False, indent=0)
        json.dump(techniques, open(f"{SORTIE}/techniques.json", "w"),
                  ensure_ascii=False, indent=0)
        print(f"\nlots ecrits dans {SORTIE}/ (a_traduire, a_revoir, orphelines)")
        print("Une fois traduits, versez-les dans data/corrections.json puis ./delta.py --figer")
    elif a_traduire or a_revoir:
        print("\nRelancez avec --lots pour ecrire les lots de travail.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
