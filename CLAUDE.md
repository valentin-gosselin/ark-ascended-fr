# TradFR, notes de travail

Patch de traduction francaise complet pour ARK: Survival Ascended. Ce fichier
rassemble ce qui ne se devine pas en lisant le code.

## Conventions non negociables

- **Jamais de tiret cadratin ni demi-cadratin**, nulle part : ni dans les
  traductions, ni dans le code, ni dans les messages de commit, ni dans les
  docs. Un tiret simple, toujours. `tools/valider_donnees.py` le verifie et
  fait echouer la CI.
- **Pas d'emoji** dans le code ni dans les textes du jeu.
- **Accents partout** dans le francais visible. Seuls les identifiants
  techniques restent sans accent.
- Les **noms d'objets et de creatures** s'ecrivent comme dans ARK: Survival
  Evolved : ce sont les noms que les joueurs connaissent. Casse de phrase, sauf
  les noms propres.
- **Les noms de DLC restent en version originale** (Frontier, Steampunk...).
- Les commentaires et docstrings de ce depot sont en francais, comme le reste.

## Les deux familles de chaines

C'est la distinction structurante du projet.

1. **Les chaines du fichier de langue.** Elles vivent dans le `ShooterGame.locres`
   du jeu. On les corrige dans `data/overrides.json` (revision de l'existant),
   `data/additions.json` (cles jamais traduites) et `data/corrections.json`
   (couche prioritaire, c'est la qu'on ecrit au quotidien).

2. **Les FText jamais collectees.** Wildcard a pose des textes en dur dans les
   assets sans jamais les passer a la collecte de localisation. Leur couple
   namespace/cle n'existe **dans aucun locres, aucune langue** : le moteur ne
   trouve rien et affiche l'anglais, meme en francais. Elles sont pourtant
   traduisibles, il suffit de creer l'entree manquante. Elles vivent dans
   `data/textes_widgets.json`, au format `{"ns\tcle": ["source EN", "FR"]}`.
   **La source anglaise est obligatoire et doit rester au caractere pres** : son
   hash est ce qui empeche le moteur de juger la traduction perimee.

## Les hashes, verifies sur 77 535 cas reels sans une erreur

Dans `tools/cityhash.py`. C'est ce qui permet de creer des entrees de toutes
pieces, donc toute la famille 2 ci-dessus.

- namespace et cle : CityHash64 sur l'UTF-16LE, replie sur 32 bits par la
  formule d'Unreal `bas32 + haut32 * 23`. Chaine vide = 0.
- source anglaise : `FCrc::StrCrc32`, soit un CRC-32 sur l'UTF-32LE.

`python3 tools/cityhash.py --verifier` reverifie tout contre le jeu.

## Pieges deja payes

- **Ne jamais traduire un nom d'argument.** Dans les graphes Blueprint, le nom
  de l'argument d'un `{...}` est lui-meme un texte localisable (namespace
  `GraphLiteral`). La VF officielle en a traduit 141, ce qui cassait la
  substitution de 290 chaines : le jeu affichait `{Time}` tel quel.
- **Ne jamais ecraser le pak pendant que le jeu tourne.** Le moteur le garde
  mappe en memoire : la mise a jour ne prend pas et des textes deja affiches
  repassent en anglais. `build.py` refuse de lui-meme.
- **Le build n'est pas reproductible au bit pres.** `repak` ecrit les fichiers
  dans l'ordre du systeme de fichiers, donc deux builds des memes donnees
  donnent deux paks differents de meme taille. Le contenu, lui, est identique :
  pour comparer deux paks, comparer les locres extraits, jamais les octets.
- **Les enums ne sont pas localisables** et `UObjectDisplayNames` n'est pas
  consulte en build de production (verifie en jeu). Restent donc hors de portee :
  le menu deroulant des cosmetiques, l'ecran des raccourcis clavier, quelques
  libelles poses en C++.
- `retoc` exige le `.ucas` a cote du `.utoc`, meme pour un simple `list`.

## Travailler sans le jeu complet

`tools/chemins.py` localise ARK : variable `ARK_ASA` en priorite, sinon les
emplacements Steam usuels, **client ou serveur dedie indifferemment**. Le locres
d'un serveur dedie est rigoureusement identique a celui du client (verifie :
memes 34 687 chaines FR et 39 201 EN, meme empreinte), ce qui permet de
construire le patch avec 1,5 Go de fichiers au lieu de 212.

En revanche `build.py` **refuse d'installer** quand il trouve un serveur dedie :
y deposer le pak modifierait un serveur de jeu en production.

## Chaine de travail

    ./build.py [--no-install]          construit le pak, l'installe sur le client
    python3 delta.py                   ce qui a change dans le jeu depuis la reference
    python3 tools/veille_assets.py     nouveaux textes d'assets depuis le dernier passage
    python3 tools/valider_donnees.py   filet de securite, ce que verifie la CI
    python3 tools/integrer_propositions.py --ecrire   replie les contributions web

Avant de traduire du contenu, lire `contexte/` : ce que Wildcard a annonce de
chaque creature, objet et mecanique depuis 2015, avec les noms officiels. Le
completer a chaque Community Crunch.

La veille GitHub Actions ouvre une PR a chaque nouveau build d'ARK. Elle ne voit
que le fichier de langue : **le balayage des assets se lance a la main**, la CI
ne peut pas le faire (il faudrait les 212 Go du jeu).

Les contributions de l'interface web (`site/`, publiee sur GitHub Pages)
arrivent dans `data/propositions/`. Le build les applique telles quelles, donc
rien ne presse pour les replier.

## Avant de committer

Proposer les tests manuels, et verifier en jeu, pas seulement dans les fichiers.
Publier par branche puis pull request, jamais directement sur `main`.
