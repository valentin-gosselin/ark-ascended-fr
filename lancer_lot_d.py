#!/usr/bin/env python3
"""Compose le prompt d'un gros lot (chantier D), contexte de domaine inclus.

Usage : lancer_lot_d.py <numéro de lot>
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from domaines import CONTEXTES

num = sys.argv[1]
index = json.load(open(os.path.join(ROOT, "work/batches/D/domaines_lots.json")))
d = index[num]
print(f"""Tu traduis un gros lot de la zone **{d}** du jeu ARK: Survival Ascended.

Contexte de cette zone : {CONTEXTES[d]}

Lis d'abord /home/goss/ark-fr/work/batches/INSTRUCTIONS_C.md (règles générales, \
elles priment) puis /home/goss/ark-fr/work/glossaire_c.tsv (glossaire imposé).

Traduis intégralement /home/goss/ark-fr/work/batches/D/in_{num}.json et écris le \
résultat dans /home/goss/ark-fr/work/batches/out/D_{num}.json : un JSON \
{{clé: "traduction française"}} avec exactement les mêmes clés que l'entrée (elles \
contiennent une tabulation, préserve-les à l'identique), encodé UTF-8 sans \
échappement ASCII.

CONSIGNES D'EFFICACITÉ, importantes :
- Le lot contient jusqu'à 1200 chaînes. Traite-le en UNE SEULE passe de \
traduction, puis écris le fichier. Ne sous-traite RIEN à des sous-agents.
- N'écris PAS de script de vérification élaboré : un validateur central \
vérifie déjà placeholders, balises et espaces. Une simple lecture attentive suffit.
- N'omets aucune clé : la sortie doit contenir exactement autant d'entrées que \
l'entrée.

N'utilise sous aucun prétexte la traduction française officielle du jeu : elle \
est fautive, c'est précisément ce qu'on remplace. Traduis depuis l'anglais seul.

Réponds uniquement : OK n=<nombre de clés écrites>""")
