#!/usr/bin/env python3
"""Repere le contenu neuf dont les textes n'ont jamais ete collectes.

Pourquoi cet outil existe
-------------------------
La veille automatique compare l'anglais du fichier de langue a une reference
figee. Un contenu dont les textes ne s'y trouvent pas ne produit donc aucun
ecart, et elle annonce en toute bonne foi qu'il n'y a rien a traduire. C'est
arrive avec le Concavenator, sorti le 26/08/2026 : 283 paquets d'assets dans le
jeu, zero chaine dans le locres, et l'aide des touches de la creature affichee
en anglais.

Detecter cela en integration continue demanderait de telecharger les assets du
jeu, soit 212 Go, contre 1,1 Go pour le seul pak de langue. Cet outil fait donc
le travail en local, mais sans repayer le prix fort : il ne balaie que les
paquets APPARUS depuis le dernier passage. Le premier balayage prend une heure,
les suivants quelques secondes.

    python3 tools/veille_assets.py            # signale le contenu neuf
    python3 tools/veille_assets.py --figer    # fige l'etat courant sans balayer

L'etat est garde dans work/reference_assets.json, hors du depot : la liste des
paquets pese 12,6 Mo et changerait a chaque mise a jour du jeu.
"""
import json
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RACINE, "tools"))

# Hors du depot : 160 908 noms de paquets pesent 12,6 Mo et changent a
# chaque mise a jour du jeu. Le premier passage sur une machine coute donc
# un balayage complet, les suivants sont instantanes.
REFERENCE = os.path.join(RACINE, "work/reference_assets.json")
MANIFESTE = os.path.join(RACINE, "work/pakstore.json")
RETOC = os.path.join(RACINE, "tools/retoc_cli-x86_64-unknown-linux-gnu/retoc")
UTOC = ("/mnt/Apps/SteamLibrary/steamapps/common/ARK Survival Ascended"
        "/ShooterGame/Content/Paks/pakchunk0-Windows.utoc")

# Memes exclusions que le balayage complet : ni textures, ni sons, ni modeles.
EXCLU = re.compile(
    r"/(Textures?|Materials?|Meshes?|Animations?|Sounds?|Audio|Icons?|Fonts?|"
    r"FX|VFX|Particles?|Skeletons?|Physics|Cinematics?|Landscape|Foliage|"
    r"Environment|Rigs?|Curves?|Poses?|Morphs?)/|"
    r"(_Icon|_Mat|_MIC|_Tex|_Mesh|_Anim|_Cue|_SW|_BC|_M|_N|_D|_MSK)$|"
    r"^/(Engine|ACLPlugin|Niagara|Paper2D|MovieRender)/", re.I)

# Dossiers dont on sait qu'ils ne contiennent pas de texte joueur : outils
# d'edition tiers, bancs d'essai, et les dossiers de missions dont les FText
# sont des libelles de placement d'IA (Guard, Cannon, Loot, Spike Wall).
SANS_INTERET = re.compile(
    r"^/(MovieRenderPipeline|NiagaraFluids|Niagara|Engine|DeformerGraph|ControlRig)/|"
    r"^/Game/(UltraDynamicSky|FluidNinjaLive|TestAssets|Art_Tools|Waterline|DevKit)/|"
    r"/Missions/|/Test_Dave/|/DeformerGraphs/|/Enums/ENiagara", re.I)


def regenerer_manifeste():
    """Relit la liste des paquets du jeu. Sans cela on travaille sur du perime."""
    if not os.path.exists(UTOC):
        sys.exit(f"Jeu introuvable : {UTOC}")
    os.makedirs(os.path.join(RACINE, "work"), exist_ok=True)
    subprocess.run([RETOC, "manifest", UTOC], cwd=RACINE, check=True,
                   stdout=subprocess.DEVNULL)
    os.replace(os.path.join(RACINE, "pakstore.json"), MANIFESTE)


def paquets():
    d = json.load(open(MANIFESTE))["oplog"]["entries"]
    return {e["packagestoreentry"]["packagename"]: e["packagedata"][0]["id"]
            for e in d}


def main():
    figer = "--figer" in sys.argv
    regenerer_manifeste()
    tous = paquets()
    connus = set(json.load(open(REFERENCE))["paquets"]) if os.path.exists(REFERENCE) else set()

    nouveaux = {n: i for n, i in tous.items()
                if n not in connus and not EXCLU.search(n)}
    print(f"  {len(tous)} paquets dans le jeu, {len(connus)} connus, "
          f"{len(nouveaux)} nouveaux a examiner")

    if not figer and nouveaux:
        liste = os.path.join(RACINE, "work/nouveaux_paquets.json")
        sortie = os.path.join(RACINE, "work/orphelines_nouvelles.json")
        json.dump(sorted(nouveaux.items()), open(liste, "w"))
        subprocess.run([sys.executable, os.path.join(RACINE, "tools/balayer_assets.py"),
                        liste, sortie, "--procs=12"], check=True)

        trouve = json.load(open(sortie))
        deja = json.load(open(os.path.join(RACINE, "data/textes_widgets.json")))
        a_voir = {k: v for k, v in trouve.items()
                  if k not in deja and not SANS_INTERET.search(v["assets"][0])}
        print(f"\n  {len(a_voir)} textes a traduire dans le contenu neuf :\n")
        vus = set()
        for k, v in sorted(a_voir.items(), key=lambda x: x[1]["source"]):
            if v["source"] in vus:
                continue
            vus.add(v["source"])
            print(f"    {v['source'][:80]!r}\n        <- {v['assets'][0]}")
        if not a_voir:
            print("    (rien : le contenu neuf n'apporte aucun texte non collecte)")

    json.dump({"paquets": sorted(tous)}, open(REFERENCE, "w"), indent=0)
    print(f"\n  reference mise a jour : {len(tous)} paquets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
