#!/usr/bin/env python3
"""Replie les propositions communautaires dans les donnees du patch.

Une contribution deposee depuis l'interface web arrive sous forme d'un petit
fichier dans data/propositions/. Le build les applique deja telles quelles, donc
rien ne presse : cet outil sert a faire le menage quand elles s'accumulent, en
les versant dans les fichiers de donnees et en les supprimant.

    python3 tools/integrer_propositions.py            # montre ce qui serait fait
    python3 tools/integrer_propositions.py --ecrire   # replie et supprime

La mise en forme des fichiers de donnees est preservee, faute de quoi le moindre
changement produirait un diff de dizaines de milliers de lignes, illisible en
relecture. Deux traitements selon le fichier : corrections.json tient une entree
par ligne et se modifie ligne a ligne, tandis que textes_widgets.json etale ses
paires sur plusieurs lignes et se reecrit entierement avec sa mise en forme.
"""
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(RACINE, "data/propositions")
LIGNE = re.compile(r'^(\s*)("(?:[^"\\]|\\.)*")(\s*:\s*)(.*?)(,?)\s*$')


def verser_ligne(chemin, valeurs, encoder):
    """Ecrit `valeurs` en remplacant une ligne, pour un fichier a une entree par ligne."""
    lignes = open(chemin, encoding="utf-8").read().splitlines(keepends=True)
    restantes = dict(valeurs)
    for i, ligne in enumerate(lignes):
        m = LIGNE.match(ligne.rstrip("\n"))
        if not m:
            continue
        cle = json.loads(m.group(2))
        if cle in restantes:
            lignes[i] = (m.group(1) + m.group(2) + m.group(3)
                         + encoder(restantes.pop(cle)) + m.group(5) + "\n")
    if restantes:
        for i in range(len(lignes) - 1, -1, -1):
            if lignes[i].strip() == "}":
                avant = i - 1
                lignes[avant] = lignes[avant].rstrip("\n").rstrip().rstrip(",") + ",\n"
                ajouts = [f" {json.dumps(k, ensure_ascii=False)}: {encoder(v)},\n"
                          for k, v in sorted(restantes.items())]
                ajouts[-1] = ajouts[-1].rstrip("\n").rstrip(",") + "\n"
                lignes[i:i] = ajouts
                break
    open(chemin, "w", encoding="utf-8").write("".join(lignes))


def main():
    ecrire = "--ecrire" in sys.argv
    if not os.path.isdir(DOSSIER):
        print("  aucune proposition")
        return 0

    fichiers = sorted(n for n in os.listdir(DOSSIER) if n.endswith(".json"))
    corrections, widgets = {}, {}
    for nom in fichiers:
        p = json.load(open(os.path.join(DOSSIER, nom), encoding="utf-8"))
        corrections.update(p.get("corrections") or {})
        widgets.update(p.get("widgets") or {})

    print(f"  {len(fichiers)} fichier(s) : {len(corrections)} correction(s), "
          f"{len(widgets)} texte(s) de widget")
    if not ecrire:
        for cle, v in list(corrections.items())[:10]:
            print(f"    {cle}  ->  {v[:60]!r}")
        print("\n  (essai a blanc : relancer avec --ecrire)")
        return 0

    if corrections:
        verser_ligne(os.path.join(RACINE, "data/corrections.json"), corrections,
                     lambda v: json.dumps(v, ensure_ascii=False))
    if widgets:
        # textes_widgets.json etale chaque paire sur plusieurs lignes : un
        # remplacement ligne a ligne y laisserait des morceaux orphelins. On
        # reecrit le fichier avec sa mise en forme d'origine, ce qui donne un
        # diff limite aux entrees touchees.
        chemin = os.path.join(RACINE, "data/textes_widgets.json")
        d = json.load(open(chemin, encoding="utf-8"))
        d.update(widgets)
        json.dump(d, open(chemin, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, sort_keys=True)
    for nom in fichiers:
        os.remove(os.path.join(DOSSIER, nom))
    try:
        os.rmdir(DOSSIER)
    except OSError:
        pass
    print("  propositions repliees et supprimees")
    return 0


if __name__ == "__main__":
    sys.exit(main())
