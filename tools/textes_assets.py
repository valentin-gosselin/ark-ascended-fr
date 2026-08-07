#!/usr/bin/env python3
"""Extrait les FText litterales des assets d'interface (widgets UMG).

Pourquoi cet outil existe
-------------------------
Certains textes du jeu s'affichent en anglais quoi qu'on mette dans les
fichiers de langue : « ALLOWED », « CUSTOM COSMETICS », « WEAPONS »... On a
longtemps cru qu'ils venaient du code C++, donc hors d'atteinte. C'est faux.

Ce sont des FText posees en dur dans les widgets Blueprint. Une FText porte
toujours un namespace et une cle, et le moteur interroge le locres avec ce
couple au chargement du paquet. Le probleme est ailleurs : Wildcard n'a jamais
lance la collecte de localisation sur ces widgets, donc le couple n'existe dans
aucun locres -- ni anglais, ni francais. Le moteur cherche, ne trouve rien, et
affiche la chaine source.

Il suffit donc de creer nous-memes l'entree manquante dans le locres francais.
Aucune modification d'asset, aucun fichier du jeu touche : la meme mecanique
que le reste du patch.

Le format serialise d'une FText (historique « Base ») :

    flags (int32) | type d'historique (int8 = 0) | namespace | cle | source

chaque chaine etant un FString : longueur (int32, terminateur compris) puis les
octets, terminateur nul inclus. Une longueur negative signalerait de l'UTF-16 ;
on l'ignore, les widgets d'ARK sont en ASCII.

Deux cas se presentent dans un meme widget :

  - namespace « Content », cle numerique  -> collectee, deja dans le locres,
    deja traduite par le patch (« OFFHAND » -> « MAIN SECONDAIRE »)
  - namespace vide, cle en GUID           -> jamais collectee, c'est notre cible

Usage :
    python3 tools/textes_assets.py <dossier|fichier>...   # liste les FText
    python3 tools/textes_assets.py --orphelines <...>     # seulement les non collectees
"""
import json
import os
import re
import struct
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Une cle plausible : GUID de 32 hexa (non collectee) ou identifiant numerique
# ou symbolique (collectee). Ce filtre elimine le bruit du parcours en force.
CLE = re.compile(r"[0-9A-F]{32}|[0-9]+|[A-Za-z][A-Za-z0-9_]{2,63}")
# Un namespace est vide, ou un identifiant : tout le reste est du bruit binaire.
NAMESPACE = re.compile(r"|[A-Za-z0-9_.\[\]/ -]{1,128}")


def _fstring(donnees, pos):
    """Lit un FString a la position donnee. Rend (texte, position_suivante)."""
    if pos + 4 > len(donnees):
        return None, pos
    taille = struct.unpack_from("<i", donnees, pos)[0]
    pos += 4
    if not 1 <= taille <= 8192:
        return None, pos
    brut = donnees[pos:pos + taille]
    pos += taille
    if not brut.endswith(b"\x00"):
        return None, pos
    try:
        return brut[:-1].decode("utf-8"), pos
    except UnicodeDecodeError:
        return None, pos


def extraire(donnees):
    """Rend la liste des (namespace, cle, source) trouvees dans l'asset.

    On ne sait pas ou commencent les proprietes : on balaie tout le fichier a
    la recherche de la signature « flags nuls + historique Base », puis on
    valide en exigeant que les trois chaines se lisent proprement. Un faux
    positif ne coute rien -- il ne ressemblera a aucune cle plausible.
    """
    trouvees, vues = [], set()
    # Recherche chevauchante (lookahead) : la signature est precedee du
    # terminateur nul de la chaine d'avant, si bien qu'un balayage non
    # chevauchant se cale un octet trop tot et rate une FText sur deux.
    for m in re.finditer(rb"(?=\x00{5})", donnees):
        ns, p = _fstring(donnees, m.start() + 5)
        if ns is None or not NAMESPACE.fullmatch(ns):
            continue
        cle, p = _fstring(donnees, p)
        if cle is None or not CLE.fullmatch(cle):
            continue
        src, _ = _fstring(donnees, p)
        if not src or not re.search(r"[A-Za-z]", src):
            continue
        if (ns, cle) in vues:
            continue
        vues.add((ns, cle))
        trouvees.append((ns, cle, src))
    return trouvees


def _fichiers(chemins):
    for c in chemins:
        if os.path.isdir(c):
            for racine, _, noms in os.walk(c):
                for n in sorted(noms):
                    yield os.path.join(racine, n)
        else:
            yield c


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    seules_orphelines = "--orphelines" in sys.argv
    if not args:
        print(__doc__)
        return 2

    connues = set()
    chemin_en = os.path.join(RACINE, "work/en.json")
    if os.path.exists(chemin_en):
        connues = set(json.load(open(chemin_en)))

    resultat = {}
    for chemin in _fichiers(args):
        try:
            donnees = open(chemin, "rb").read()
        except OSError:
            continue
        for ns, cle, src in extraire(donnees):
            plate = f"{ns}\t{cle}"
            if seules_orphelines and plate in connues:
                continue
            resultat.setdefault(plate, {"source": src, "assets": []})
            resultat[plate]["assets"].append(os.path.basename(chemin))

    json.dump(resultat, sys.stdout, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"\n\n  {len(resultat)} FText"
          f"{' non collectees' if seules_orphelines else ''}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
