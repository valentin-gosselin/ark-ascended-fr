#!/usr/bin/env python3
"""Construit et installe le patch de traduction FR pour ARK Survival Ascended.

Pipeline :
  1. extrait ShooterGame.locres (fr + en) depuis pakchunk0 du jeu (cache dans work/)
  2. applique data/overrides.json (corrections) et data/additions.json
     (traductions des clés manquantes) via tools/locres.py
  3. packe le résultat en TradFR_P.pak (pak V11, monté par le jeu via le suffixe _P)
  4. l'installe dans le dossier Paks du jeu

Usage : ./build.py [--no-install]
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ASA = "/mnt/Apps/SteamLibrary/steamapps/common/ARK Survival Ascended"
PAKS = os.path.join(ASA, "ShooterGame/Content/Paks")
SRC_PAK = os.path.join(PAKS, "pakchunk0-Windows.pak")
LOCRES_IN_PAK = "../../../ShooterGame/Content/Localization/ShooterGame/{lang}/ShooterGame.locres"
WORK = os.path.join(ROOT, "work")
REPAK = os.path.join(ROOT, "tools/repak_cli-x86_64-unknown-linux-gnu/repak")


def run(*args):
    subprocess.run(args, check=True)


def main():
    os.makedirs(WORK, exist_ok=True)
    # 1. extraction (avec cache : invalidé si le pak du jeu est plus récent)
    for lang in ("fr", "en"):
        out = os.path.join(WORK, f"ShooterGame_{lang}.locres")
        if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(SRC_PAK):
            run(sys.executable, os.path.join(ROOT, "tools/pakv12.py"), "extract",
                SRC_PAK, LOCRES_IN_PAK.format(lang=lang), out)
            run(sys.executable, os.path.join(ROOT, "tools/locres.py"), "dump",
                out, os.path.join(WORK, f"{lang}.json"))
    # 2. fusion des données du patch
    #
    # ATTENTION : ajouter au locres des clés absentes de la version française
    # d'origine fait rejeter le fichier entier par Unreal, qui retombe alors
    # silencieusement sur la traduction officielle — tout le patch est perdu.
    # Vérifié en jeu : un pak sans aucun ajout s'applique, le même pak avec
    # ajouts ne s'applique pas. Les additions sont donc désactivées par défaut ;
    # `--avec-additions` permet de refaire l'essai si on trouve la parade.
    avec_add = "--sans-additions" not in sys.argv  # greffe validee en jeu le 05/08/2026
    edits = {}
    fichiers = ["overrides.json"] + (["additions.json"] if avec_add else [])
    for name in fichiers:
        path = os.path.join(ROOT, "data", name)
        if os.path.exists(path):
            part = json.load(open(path))
            edits.update(part)
            print(f"{name}: {len(part)} entrées")
    if not avec_add:
        n = len(json.load(open(os.path.join(ROOT, "data/additions.json"))))
        print(f"additions.json: {n} entrées NON appliquées (cassent le chargement)")
    # sécurité : aucune clé absente du locres FR ne doit se retrouver dans le build
    fr_keys = set(json.load(open(os.path.join(WORK, "fr.json"))))
    hors = [k for k in edits if k not in fr_keys]
    if hors and not avec_add:
        print(f"{len(hors)} clés inconnues écartées (protection)")
        edits = {k: v for k, v in edits.items() if k in fr_keys}
    merged = os.path.join(WORK, "edits_merged.json")
    json.dump(edits, open(merged, "w"), ensure_ascii=False, indent=0)
    # 3. locres patché + pak
    stage = os.path.join(WORK, "pak_stage/ShooterGame/Content/Localization/ShooterGame/fr")
    os.makedirs(stage, exist_ok=True)
    cmd = [sys.executable, os.path.join(ROOT, "tools/locres.py")]
    if avec_add:
        cmd += ["merge", os.path.join(WORK, "ShooterGame_fr.locres"),
                os.path.join(WORK, "ShooterGame_en.locres")]
    else:
        cmd += ["build", os.path.join(WORK, "ShooterGame_fr.locres")]
    run(*cmd, merged, os.path.join(stage, "ShooterGame.locres"))
    pak = os.path.join(WORK, "TradFR_P.pak")
    run(REPAK, "pack", "--version", "V11", "-m", "../../../", "-q",
        os.path.join(WORK, "pak_stage"), pak)
    print(f"pak : {pak} ({os.path.getsize(pak)} octets)")
    # 4. installation
    if "--no-install" not in sys.argv:
        import shutil
        shutil.copy2(pak, os.path.join(PAKS, "TradFR_P.pak"))
        print(f"installé dans {PAKS}")


if __name__ == "__main__":
    main()
