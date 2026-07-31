#!/usr/bin/env python3
"""Classe chaque chaîne du jeu dans une zone fonctionnelle.

Le domaine est donné à l'agent traducteur : c'est ce qui lève l'ambiguïté des
mots polysémiques (« Charge » énergie ou facturation, « Hide » peau ou masquer,
« Back » retour ou dos) que la traduction officielle a systématiquement ratée.

Usage : domaines.py <en.json> <clés.json> [rapport]
"""
import json
import re
import sys

# Ordre important : la première règle qui correspond gagne.
REGLES = [
    ("technique", lambda k, e, ns: (
        re.match(r"^\s*(import|from|def |class |if |for |#|//)", e)
        or "://" in e or e.startswith("/") or e.startswith("Z:\\")
        or re.fullmatch(r"[A-Za-z0-9_.]+", e) and re.search(r"[_.]|[a-z][A-Z]", e)
        or re.search(r"::|_Delegate_|Blueprint|BP_|DT_[A-Z]|\bSocket\b|_C\b", e))),
    ("missions", lambda k, e, ns: (
        ns.startswith("DT_Bounties") or ns.startswith("DT_Milestones")
        or re.search(r"\b(mission|bounty|objective|quest)\b", e, re.I))),
    ("notes_exploration", lambda k, e, ns: (
        re.search(r"Explorer Note|Dossier\b|Chronicles|\bRecord\b", e)
        or len(e) > 220)),
    ("creatures", lambda k, e, ns: (
        re.search(r"\b(Saddle|Dino|Creature|Tame|Taming|Breed|Egg|Baby|Juvenile|"
                  r"Imprint|Wyvern|Rex|Raptor|Dodo|Argentavis|Chibi)\b", e, re.I))),
    ("objets", lambda k, e, ns: (
        re.search(r"\b(Craft|Crafted|Resource|Consumable|Armor|Weapon|Ammo|"
                  r"Blueprint|Engram|Recipe|Durability|Spoil)\b", e, re.I)
        or re.match(r"^(A|An|The)\s+\w+.*(that|which|used to|for)\b", e))),
    ("structures", lambda k, e, ns: (
        re.search(r"\b(Structure|Foundation|Ceiling|Wall|Pillar|Gate|Door|"
                  r"Snap|Demolish|Pipe|Wire|Generator)\b", e, re.I))),
    ("interface_options", lambda k, e, ns: (
        e.rstrip().endswith(":") or e.isupper() and len(e) < 60
        or re.search(r"\b(Enable|Disable|Toggle|Slider|Setting|Option|Volume|"
                     r"Quality|Resolution|Sensitivity|Keybind)\b", e, re.I))),
    ("messages_systeme", lambda k, e, ns: (
        re.search(r"\b(Failed|Error|Warning|Cannot|Unable|Connection|Server|"
                  r"Timeout|Disconnect|Retry|Loading)\b", e, re.I))),
    # dialogue : réplique attribuée « Personnage : ... » ou récit à la 1re personne
    ("dialogues", lambda k, e, ns: (
        re.match(r"^[A-Z][A-Za-z' -]{2,20}:\s{2,}", e)
        or (len(e) > 60 and re.search(r"\b(I|I'm|I've|my|you're|we'll)\b", e)))),
    # noms d'objets et de créatures : groupe nominal court sans verbe conjugué
    ("noms_contenu", lambda k, e, ns: (
        ns == "Content" and len(e) <= 45
        and re.fullmatch(r"[A-Za-z0-9' ()’-]+", e)
        and not re.search(r"\b(the|you|your|to|is|are|can|will|of|and|a|an)\b", e, re.I))),
    # phrases de jeu : description, aide, texte affiché en jeu
    ("textes_jeu", lambda k, e, ns: len(e) > 45),
]

CONTEXTES = {
    "interface_options": (
        "Libellés du menu Paramètres (audio, vidéo, graphismes, interface, "
        "caméra, commandes, manette). Style : impératif court et net, comme "
        "dans les options d'un jeu PC. « Reset » -> « Réinitialiser », "
        "« Gamepad » -> « Manette », « Cosmetics » -> « Cosmétiques », "
        "« UI » -> « Interface ». **« Toggle X » se traduit par le verbe "
        "d'action seul**, jamais par « Activer/Désactiver X » qui est trop long "
        "pour un libellé : « Toggle HUD » -> « Afficher l'ATH », « Toggle "
        "Fists » -> « Sortir les poings », « Toggle Lights » -> « Allumer les "
        "lumières », « Toggle Map » -> « Afficher la carte »."),
    "interface_generale": (
        "Boutons, onglets, menus, navigateur de serveurs et ATH. Style : très "
        "concis, ce sont des libellés cliquables. « Back » -> « Retour » (JAMAIS "
        "« Dos »), « Hide » -> « Masquer », « Join Game » -> « Rejoindre une "
        "partie », « Ping » reste « Ping », « Refresh » -> « Actualiser ». "
        "**« Toggle X » se traduit par le verbe d'action seul** (« Afficher », "
        "« Allumer », « Sortir »...), jamais par « Activer/Désactiver X »."),
    "creatures": (
        "Créatures, apprivoisement, élevage, selles. « Tame » -> « apprivoiser », "
        "« Saddle » -> « Selle », « Imprint » -> « Imprégnation », « Torpidity » "
        "-> « Torpeur ». Les genres latins ne se traduisent pas (Rex, Argentavis, "
        "Therizinosaurus) ; les noms descriptifs si (Direwolf -> Loup sinistre)."),
    "objets": (
        "Objets, ressources, armes, armures, engrammes et leurs descriptions. "
        "« Hide » (matériau) -> « Peau », « Ammo » -> « Munitions », « Engram » "
        "-> « Engramme », « Blueprint » -> « Plan », « Craft » -> « Fabriquer ». "
        "Les descriptions d'objets sont rédigées, naturelles et immersives."),
    "structures": (
        "Constructions et mécanismes. « Foundation » -> « Fondation », "
        "« Ceiling » -> « Plafond », « Snap » -> « Aimantation », « Demolish » "
        "-> « Démolir », « Charge » (énergie) -> « Charge », jamais « facturer »."),
    "missions": (
        "Missions, contrats, objectifs et récompenses. « Mission » -> "
        "« Mission », « Bounty » -> « Contrat », « Objective » -> « Objectif ». "
        "Style : consignes claires données au joueur, au vouvoiement."),
    "notes_exploration": (
        "Notes d'exploration, dossiers de créatures et textes de lore, écrits à "
        "la première personne par des personnages (Helena, Rockwell, Santiago, "
        "Diana, Mei-Yin, Nerva). Style littéraire et soigné, on garde le ton du "
        "narrateur. Format des notes : « Note d'exploration <Personnage> <n> », "
        "des dossiers : « Dossier : <Créature> ». Noms propres jamais traduits."),
    "messages_systeme": (
        "Messages d'erreur, avertissements, réseau et connexion. Style : phrase "
        "complète, informative, au vouvoiement. « Failed to join » -> « Échec de "
        "la connexion », « Server » -> « Serveur »."),
    "dialogues": (
        "Répliques et récits de personnages (Bob, Meeka, Helena, Rockwell, "
        "Santiago, Diana, Mei-Yin, Nerva, le Roi). Format « Personnage :  "
        "réplique » à préserver tel quel, y compris le double espace. Style "
        "vivant et oral, on garde le tutoiement entre personnages qui se "
        "connaissent et le registre propre à chacun. Apostrophes typographiques "
        "du source (’) conservées telles quelles."),
    "noms_contenu": (
        "Noms d'objets, de créatures, de tenues, de pièces d'armure et de lieux. "
        "Groupes nominaux courts, sans phrase. Les genres latins et noms propres "
        "ne se traduisent pas (Basilosaurus, Kapro, Trike, Dodorex) ; les mots "
        "descriptifs qui les accompagnent si (« Trike Bone Helmet » -> « Casque "
        "en os de Trike », « Basilosaurus Embryo » -> « Embryon de "
        "Basilosaurus »). Accord et ordre des mots à la française."),
    "textes_jeu": (
        "Phrases affichées en jeu : descriptions, aide contextuelle, infobulles, "
        "effets de statut, messages d'événement. Style naturel et fluide, au "
        "vouvoiement quand on s'adresse au joueur."),
    "technique": (
        "Chaînes techniques : identifiants, noms de variables, chemins d'assets, "
        "code, messages de debug interne. La règle par défaut est de RECOPIER "
        "TEL QUEL. Ne traduis que si la chaîne est manifestement une phrase "
        "lisible destinée à l'écran."),
}


def classer(cle, texte):
    ns = cle.split("\t")[0]
    for nom, test in REGLES:
        try:
            if test(cle, texte, ns):
                return nom
        except Exception:
            continue
    return "interface_generale"


if __name__ == "__main__":
    en = json.load(open(sys.argv[1]))
    cles = json.load(open(sys.argv[2]))
    import collections
    c = collections.Counter()
    out = {}
    for k in cles:
        d = classer(k, en[k] if isinstance(en.get(k), str) else cles[k])
        out[k] = d
        c[d] += 1
    for d, n in c.most_common():
        print(f"{n:7d}  {d}")
    if len(sys.argv) > 3:
        json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False)
