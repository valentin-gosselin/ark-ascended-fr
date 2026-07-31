#!/usr/bin/env python3
"""Compose le prompt d'un lot du chantier C, contexte de domaine inclus.

Usage : lancer_lot.py <numéro de lot>
Affiche le prompt à passer à l'agent traducteur.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from domaines import CONTEXTES

num = sys.argv[1]
index = json.load(open(os.path.join(ROOT, "work/batches/C/domaines_lots.json")))
d = index[num]
print(f"""Tu traduis un lot de la zone **{d}** du jeu.

Contexte de cette zone : {CONTEXTES[d]}

Lis d'abord /home/goss/ark-fr/work/batches/INSTRUCTIONS_C.md (règles générales, \
elles priment) puis /home/goss/ark-fr/work/glossaire_c.tsv (glossaire imposé).

Traduis intégralement /home/goss/ark-fr/work/batches/C/in_{num}.json et écris le \
résultat dans /home/goss/ark-fr/work/batches/out/C_{num}.json : un JSON \
{{clé: "traduction française"}} avec exactement les mêmes clés que l'entrée (elles \
contiennent une tabulation, préserve-les à l'identique), encodé UTF-8 sans \
échappement ASCII.

N'utilise sous aucun prétexte la traduction française officielle du jeu : elle \
est fautive, c'est précisément ce qu'on remplace. Traduis depuis l'anglais seul.

Réponds uniquement : OK n=<nombre de clés écrites>""")
