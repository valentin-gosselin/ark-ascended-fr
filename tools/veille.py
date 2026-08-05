#!/usr/bin/env python3
"""Veille sur les mises a jour d'ARK : detecte, prepare le travail, ouvre une issue.

Steam ne previent de rien. Ce script tourne en tache de fond, repere le moment ou
le pak du jeu change, calcule le delta, fait tout ce qui peut l'etre sans humain,
et publie le reste sur GitHub pour que n'importe qui puisse s'en saisir.

Ce qui est automatise :
  - les cles disparues du jeu sont retirees des donnees du patch
  - les chaines techniques (debug, separateurs, code) sont ecartees d'office
  - chaque chaine a traduire recoit une proposition tiree de la traduction
    officielle d'ARK Survival Evolved quand la source anglaise y existe telle quelle

Ce qui reste humain : valider ou ecrire les traductions restantes.

    python3 tools/veille.py            # cycle complet (silencieux si rien a signaler)
    python3 tools/veille.py --forcer   # ignore l'etat, refait le rapport
    python3 tools/veille.py --local    # n'ouvre pas d'issue, ecrit rapport.md
"""
import datetime
import json
import os
import re
import subprocess
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
ETAT = os.path.join(RACINE, "work/veille_etat.json")
LOTS = os.path.join(RACINE, "delta")
DATA = ["overrides.json", "additions.json", "corrections.json"]
MAX_INLINE = 40


def sh(*args, **kw):
    return subprocess.run(args, cwd=RACINE, capture_output=True, text=True, **kw)


def stable(chemin, essais=30, pause=20):
    """Steam ecrit le pak par morceaux : on attend que la taille cesse de bouger."""
    taille = -1
    for _ in range(essais):
        actuelle = os.path.getsize(chemin)
        if actuelle == taille:
            return True
        taille = actuelle
        time.sleep(pause)
    return False


def corpus_evolved():
    """EN -> FR officiel d'ARK Survival Evolved, notre source d'autorite.

    Versionne dans data/ pour que la veille tourne aussi en CI, sans le jeu.
    """
    fige = os.path.join(RACINE, "data/evolved_fr.json")
    if os.path.exists(fige):
        return json.load(open(fige))
    try:
        ase_en = json.load(open(os.path.join(RACINE, "work/ase_en.json")))
        ase_fr = json.load(open(os.path.join(RACINE, "work/ase_fr.json")))
    except FileNotFoundError:
        return {}
    return {ase_en[k]: ase_fr[k] for k in ase_en if k in ase_fr}


def nettoyer_orphelines(orphelines):
    """Retire des donnees du patch les cles que le jeu ne contient plus."""
    if not orphelines:
        return 0
    mortes, total = set(orphelines), 0
    for nom in DATA:
        chemin = os.path.join(RACINE, "data", nom)
        if not os.path.exists(chemin):
            continue
        d = json.load(open(chemin))
        garde = {k: v for k, v in d.items() if k not in mortes}
        if len(garde) != len(d):
            total += len(d) - len(garde)
            json.dump(garde, open(chemin, "w"), ensure_ascii=False, indent=0)
    return total


def cle(k):
    """La cle contient une tabulation : illisible dans un tableau markdown."""
    return k.replace("\t", " / ")


def cellule(texte, taille=110):
    """Un tableau markdown ne survit ni aux retours a la ligne ni aux barres."""
    t = re.sub(r"[\r\n]+", " ⏎ ", texte.strip())[:taille]
    return t.replace("|", "\\|")


def corps_issue(rapport, a_traduire, a_revoir, propositions, n_tech, n_orph):
    d = rapport
    L = [
        f"Le pak du jeu est passe de {d['avant']} a {d['apres']} octets.",
        "",
        "| | |",
        "|---|---|",
        f"| Chaines anglaises | {d['n_avant']} -> {d['n_apres']} |",
        f"| A traduire | **{len(a_traduire)}** dont **{len(propositions)}** avec une "
        f"proposition officielle Evolved |",
        f"| A revoir (l'anglais a change) | **{len(a_revoir)}** |",
        f"| Traitees automatiquement | {n_tech} techniques ecartees, "
        f"{n_orph} cles orphelines retirees |",
        "",
        "## Comment participer",
        "",
        "Repondez dans ce fil avec vos traductions au format `cle` = `texte`, ou "
        "proposez directement une pull request sur `data/corrections.json`.",
        "Les propositions marquees **Evolved** viennent de la traduction officielle "
        "d'ARK Survival Evolved : elles sont normalement bonnes telles quelles, il "
        "suffit de les confirmer.",
        "",
        "Les listes completes sont dans "
        "[`delta/`](../tree/master/delta) (`a_traduire.json`, `a_revoir.json`).",
        "",
    ]
    if a_traduire:
        L += ["## A traduire", "", "| Cle | Anglais | Proposition |", "|---|---|---|"]
        for k, v in list(a_traduire.items())[:MAX_INLINE]:
            prop = propositions.get(k)
            if prop is None:
                cell = "_a ecrire_"
            elif prop.strip() == v.strip():
                # Evolved a laisse cette chaine en anglais : l'information vaut
                # une proposition, elle dit au traducteur de ne pas y toucher
                cell = "_Evolved la laisse en anglais_"
            else:
                cell = f"**Evolved** : {cellule(prop, 90)}"
            L.append(f"| `{cle(k)}` | {cellule(v)} | {cell} |")
        if len(a_traduire) > MAX_INLINE:
            L.append(f"\n_(+ {len(a_traduire) - MAX_INLINE} autres dans `delta/a_traduire.json`)_")
        L.append("")
    if a_revoir:
        L += ["## A revoir : l'anglais a change", "",
              "La traduction actuelle dit peut-etre autre chose que le jeu.", "",
              "| Cle | Avant | Apres | Traduction actuelle |", "|---|---|---|---|"]
        for k, d2 in list(a_revoir.items())[:MAX_INLINE]:
            L.append(f"| `{cle(k)}` | {cellule(d2['avant'], 70)} | "
                     f"{cellule(d2['apres'], 70)} | "
                     f"{cellule(d2['traduction_actuelle'], 70)} |")
        if len(a_revoir) > MAX_INLINE:
            L.append(f"\n_(+ {len(a_revoir) - MAX_INLINE} autres dans `delta/a_revoir.json`)_")
    return "\n".join(L)


def main():
    from delta import EN, REFERENCE, SRC_PAK, empreinte, extraire, nos_traductions, traduisible

    forcer = "--forcer" in sys.argv
    local = "--local" in sys.argv
    # --en <dump.json> : l'anglais est fourni (CI), le jeu n'a pas besoin d'etre installe
    fourni = None
    if "--en" in sys.argv:
        fourni = sys.argv[sys.argv.index("--en") + 1]
    if not os.path.exists(REFERENCE):
        sys.exit("Aucune reference : lancez d'abord ./delta.py --figer")

    ref = json.load(open(REFERENCE))
    if fourni:
        nouveau = json.load(open(fourni))
        emp = {"taille": os.path.getsize(fourni), "date": 0}
        if nouveau == ref["chaines"] and not forcer:
            print("aucun changement de texte dans cette mise a jour")
            return 0
    else:
        emp = empreinte()
        if emp == ref["pak"] and not forcer:
            return 0  # le jeu n'a pas bouge
        etat = json.load(open(ETAT)) if os.path.exists(ETAT) else {}
        if etat.get("signale") == emp and not forcer:
            return 0  # cette mise a jour a deja fait l'objet d'une issue
        if not stable(SRC_PAK):
            print("le pak est encore en cours d'ecriture, on reessaiera")
            return 0
        extraire()
        nouveau = json.load(open(EN))
    ancien = ref["chaines"]
    trad = nos_traductions()
    ajoutees = {k: v for k, v in nouveau.items() if k not in ancien}
    nouvelles = {k: v for k, v in ajoutees.items() if k not in trad}
    a_traduire = {k: v for k, v in nouvelles.items() if traduisible(v)}
    techniques = {k: v for k, v in nouvelles.items() if not traduisible(v)}
    a_revoir = {k: {"avant": ancien[k], "apres": v, "traduction_actuelle": trad[k]}
                for k, v in nouveau.items()
                if k in ancien and ancien[k] != v and k in trad}
    orphelines = [k for k in trad if k not in nouveau]

    if not a_traduire and not a_revoir and not orphelines:
        print("mise a jour du jeu sans impact sur les textes")
        json.dump({"signale": emp}, open(ETAT, "w"))
        return 0

    # ce qui peut etre fait sans humain
    evolved = corpus_evolved()
    propositions = {k: evolved[v] for k, v in a_traduire.items() if v in evolved}
    n_orph = nettoyer_orphelines(orphelines)

    os.makedirs(LOTS, exist_ok=True)
    json.dump({k: {"en": v, "proposition_evolved": propositions.get(k)}
               for k, v in a_traduire.items()},
              open(f"{LOTS}/a_traduire.json", "w"), ensure_ascii=False, indent=1)
    json.dump(a_revoir, open(f"{LOTS}/a_revoir.json", "w"), ensure_ascii=False, indent=1)

    rapport = {"avant": ref["pak"]["taille"], "apres": emp["taille"],
               "n_avant": len(ancien), "n_apres": len(nouveau)}
    corps = corps_issue(rapport, a_traduire, a_revoir, propositions,
                        len(techniques), n_orph)
    jour = datetime.date.today().isoformat()
    titre = (f"MAJ du jeu du {jour} : {len(a_traduire)} chaines a traduire, "
             f"{len(a_revoir)} a revoir")

    if local:
        open(os.path.join(RACINE, "delta/rapport.md"), "w").write(f"# {titre}\n\n{corps}")
        print("rapport ecrit dans delta/rapport.md")
    else:
        sh("git", "add", "delta", "data")
        sh("git", "commit", "-m",
           f"MAJ du jeu du {jour} : lots de traduction, {n_orph} cles orphelines retirees")
        push = sh("git", "push")
        r = sh("gh", "issue", "create", "--title", titre, "--body", corps,
               "--label", "traduction")
        if r.returncode:
            open(os.path.join(RACINE, "delta/rapport.md"), "w").write(f"# {titre}\n\n{corps}")
            print(f"issue impossible ({r.stderr.strip()[:120]}), rapport local ecrit")
        else:
            print(f"issue ouverte : {r.stdout.strip()}")
        if push.returncode:
            print(f"push echoue : {push.stderr.strip()[:120]}")

    json.dump({"signale": emp}, open(ETAT, "w"))
    print(f"{len(a_traduire)} a traduire ({len(propositions)} pre-remplies), "
          f"{len(a_revoir)} a revoir, {n_orph} orphelines retirees, "
          f"{len(techniques)} techniques ecartees")
    return 0


if __name__ == "__main__":
    sys.exit(main())
