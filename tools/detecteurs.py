#!/usr/bin/env python3
"""Rejoue tous les detecteurs d'anomalies sur le build courant.

Chaque detecteur vient d'un defaut reellement observe (en jeu ou en relecture) :
la regle du projet est qu'un bug vu une fois devient un detecteur rejouable.

Usage : python3 tools/detecteurs.py [work/en.json] [work/edits_merged.json]
Sortie : une ligne par detecteur, code de retour 1 si une anomalie reste.
"""
import collections
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PH = re.compile(r"\{[^}]*\}|%[a-z%]|</?[A-Za-z][^>]*>")

# Les 4 divergences de placeholders connues et legitimes : le jeu utilise les
# accolades comme segments de texte litteral, pas seulement comme variables.
PLACEHOLDERS_LEGITIMES = 4


def detecteurs(en, ed):
    def ph_diff(k, v):
        e = en.get(k, "")
        return "{" in e and sorted(PH.findall(e)) != sorted(PH.findall(v))

    def bords(k, v):
        e = en.get(k)
        return e is not None and (
            (e[:1] == " ") != (v[:1] == " ") or (e[-1:] == " ") != (v[-1:] == " "))

    def latin(k, v):
        m = re.search(r"Species:\s*([A-Z][a-z]+)\s+([a-z]+)", en.get(k, ""))
        if not m:
            return False
        return any(x.group(1).lower() != m.group(1).lower()
                   for x in re.finditer(r"([A-ZÀ-Ý][a-zà-ÿéèêë\-]+)\s+" + m.group(2) + r"\b", v))

    return [
        ("placeholders divergents", ph_diff, PLACEHOLDERS_LEGITIMES),
        ("espaces de bord modifies", bords, 0),
        # piege n°4 : source sans lettres (separateur) traduite quand meme
        ("separateurs pollues", lambda k, v: k in en and not re.search(r"[A-Za-z]", en[k])
         and re.search(r"[A-Za-zÀ-ÿ]", v), 0),
        ("accolades doublees", lambda k, v: "{{" in v and "{{" not in en.get(k, ""), 0),
        ("apostrophes typographiques", lambda k, v: "’" in v, 0),
        ("'nº' ordinal espagnol", lambda k, v: "nº" in v, 0),
        ("elision 'de/DE <voyelle>'", lambda k, v: (re.search(r"\bde [AEIOUÉÈaeiouéè]", v)
         or re.search(r"\bDE [AEIOUÉÈ]", v))
         and not re.search(r"\b(de|DE) (Un|UN|Uma|UMA|Umbra|UMBRA|Oasis|OASIS)", v), 0),
        # bavure de substitution : elision conservee devant un nom devenu consonantique
        ("elision + consonne", lambda k, v: re.search(r"\b[dl]'(Serviteur|Baudroie)", v), 0),
        ("binomes latins alteres", latin, 0),
        ("milliers a l'anglaise", lambda k, v: re.search(r"\d,\d{3}\b", v)
         and re.search(r"\d,\d{3}", en.get(k, "")), 0),
        ("anglais residuel", lambda k, v: re.search(r"\bwild [A-Z]|\bat level \d|\bThralls?\b", v), 0),
        ("'note d'exploration'", lambda k, v: "ote d'exploration" in v, 0),
        ("esclave/larbin (Thrall)", lambda k, v: re.search(r"\b(esclave|larbin)", v, re.I)
         and "hrall" in en.get(k, ""), 0),
        ("Smithy rendu 'forge'", lambda k, v: re.search(r"\bSmithy\b", en.get(k, ""), re.I)
         and re.search(r"[Ff]orge", v), 0),
        ("'monté(e)'", lambda k, v: "monté(e)" in v, 0),
        ("'immunisé à/aux'", lambda k, v: re.search(r"[Ii]mmunis[ée]e?s? (à|aux|au)\b", v), 0),
        ("serie animee traduite", lambda k, v: "érie animée" in v.lower(), 0),
    ]


def main():
    en_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RACINE, "work/en.json")
    ed_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(RACINE, "work/edits_merged.json")
    en = json.load(open(en_path))
    ed = json.load(open(ed_path))
    anomalies = 0
    for label, pred, tolere in detecteurs(en, ed):
        n = sum(1 for k, v in ed.items() if pred(k, v))
        etat = "ok" if n <= tolere else f"{n - tolere} ANOMALIE(S)"
        print(f"  {label:32} {n:5}  {etat}")
        anomalies += max(0, n - tolere)

    # deux objets distincts sous un meme nom francais (pieces de construction)
    struct = re.compile(r"\b(Door|Doorway|Gate|Gateway|Gateframe|Trapdoor|Hatchframe)\b")
    noms = collections.defaultdict(set)
    for k, v in ed.items():
        e = en.get(k, "").strip()
        if k.startswith("Content\t") and 4 <= len(e) <= 46 and struct.search(e):
            noms[v.strip().lower()].add(e)
    # les doublons d'orthographe anglaise du meme objet sont legitimes
    def meme_objet(noms_en):
        # l'anglais ecrit le meme objet de plusieurs facons : "Wood"/"Wooden",
        # "Gateframe"/"Gateway", et l'ordre des qualificatifs varie librement
        # ("Adobe Giant Trapdoor" = "Giant Adobe Trapdoor")
        norm = {tuple(sorted(re.sub(r"\b(Wood|Wooden)\b", "Wood", n)
                            .replace("Gateframe", "Gateway")
                            .replace("Trapdoor Ceiling", "Hatchframe")
                            .replace("Hatchframe", "Gateway").split()))
                for n in noms_en}
        return len(norm) == 1
    collisions = [ns for f, ns in noms.items() if len(ns) > 1 and not meme_objet(ns)]
    print(f"  {'collisions de noms':32} {len(collisions):5}  "
          f"{'ok' if not collisions else 'A VERIFIER'}")

    # meme source anglaise traduite de deux facons
    jum = collections.defaultdict(set)
    for k, v in ed.items():
        e = en.get(k, "").strip()
        if 20 < len(e) < 200 and re.search(r"[a-z]{4,}", e):
            jum[e].add(v.strip())
    n_jum = sum(1 for fs in jum.values() if len(fs) > 1)
    print(f"  {'chaines jumelles divergentes':32} {n_jum:5}  {'ok' if not n_jum else 'ANOMALIE(S)'}")
    anomalies += n_jum

    print(f"\n  {len(ed)} chaines controlees, {anomalies} anomalie(s)")
    return 1 if anomalies else 0


if __name__ == "__main__":
    sys.exit(main())
