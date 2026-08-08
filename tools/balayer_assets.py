#!/usr/bin/env python3
"""Balaie les assets du jeu à la recherche de FText jamais collectées.

Contexte : certaines FText posées en dur dans les assets n'ont jamais été
passées à la collecte de localisation par Wildcard. Leur couple
namespace/clé n'existe donc dans aucun .locres, le moteur ne trouve rien et
affiche l'anglais - quelle que soit la langue du jeu. Elles sont pourtant
traduisibles : il suffit de créer l'entrée manquante (cf. tools/locres.py,
fonction `creer`, et tools/cityhash.py pour les hashes).

Ce script extrait chaque paquet du conteneur IoStore, en lit les FText, puis
supprime le fichier aussitôt : le balayage complet ne coûte donc que quelques
mégaoctets de disque au lieu de plusieurs gigaoctets.

    python3 tools/balayer_assets.py <liste.json> <sortie.json> [--procs N]

`liste.json` : [[nom_de_paquet, identifiant_de_chunk], ...] tel que produit
depuis le manifeste `retoc manifest`.
"""
import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))
import textes_assets

RETOC = os.path.join(RACINE, "tools/retoc_cli-x86_64-unknown-linux-gnu/retoc")
UTOC = ("/mnt/Apps/SteamLibrary/steamapps/common/ARK Survival Ascended"
        "/ShooterGame/Content/Paks/pakchunk0-Windows.utoc")


def _lot(args):
    """Traite une tranche de paquets dans un processus dédié."""
    debut, entrees = args
    resultat = {}
    fd, tmp = tempfile.mkstemp(suffix=".uasset")
    os.close(fd)
    try:
        for nom, chunk in entrees:
            try:
                subprocess.run([RETOC, "get", UTOC, chunk, tmp],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=60)
                with open(tmp, "rb") as f:
                    donnees = f.read()
            except (OSError, subprocess.SubprocessError):
                continue
            for ns, cle, src in textes_assets.extraire(donnees):
                resultat.setdefault(f"{ns}\t{cle}", {"source": src, "assets": []})
                resultat[f"{ns}\t{cle}"]["assets"].append(nom)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return resultat


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    procs = 10
    for a in sys.argv[1:]:
        if a.startswith("--procs"):
            procs = int(a.split("=", 1)[1]) if "=" in a else procs
    entrees = json.load(open(args[0]))
    sortie = args[1]

    # tranches assez grosses pour amortir la création de processus, assez
    # nombreuses pour que les travailleurs finissent en même temps
    taille = max(20, len(entrees) // (procs * 8))
    lots = [(i, entrees[i:i + taille]) for i in range(0, len(entrees), taille)]

    total = {}
    faits = 0
    with ProcessPoolExecutor(max_workers=procs) as pool:
        for partiel in pool.map(_lot, lots):
            for cle, v in partiel.items():
                total.setdefault(cle, {"source": v["source"], "assets": []})
                total[cle]["assets"].extend(v["assets"])
            faits += taille
            print(f"  {min(faits, len(entrees))}/{len(entrees)} paquets, "
                  f"{len(total)} FText", flush=True)

    # ne garder que celles qu'aucun locres du jeu ne connaît
    connues = set(json.load(open(os.path.join(RACINE, "work/en.json"))))
    connues |= set(json.load(open(os.path.join(RACINE, "work/fr.json"))))
    orphelines = {k: v for k, v in total.items() if k not in connues}
    json.dump(orphelines, open(sortie, "w"), ensure_ascii=False,
              indent=1, sort_keys=True)
    print(f"\n  {len(total)} FText lues, {len(orphelines)} jamais collectées")
    return 0


if __name__ == "__main__":
    sys.exit(main())
