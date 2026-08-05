# TradFR - patch de traduction française pour ARK: Survival Ascended

La traduction française officielle d'ASA est incomplète (des milliers de chaînes
s'affichent en anglais) et truffée d'erreurs (« Ammo » rendu par « Mais »,
« Hide » par « Masquer », des noms latins déformés…). Ce patch remplace la
traduction française entière par une version **révisée de bout en bout** :

- **~35 400 chaînes relues ou retraduites** depuis l'anglais, lore compris
- **3 466 chaînes ajoutées** qui n'existaient pas en français (elles
  s'affichaient en anglais, même avec le jeu en français)
- noms de créatures et d'objets **alignés sur ARK: Survival Evolved**
  (les noms officiels que les joueurs connaissent : Smilodon, Croquette,
  Argile, artefacts d'Evolved…)
- accents corrigés dans les textes en capitales (fini les « SANTé » et
  « DéGâTS DE MéLéE »), quêtes « Tuez N… » accordées en genre et en nombre,
  séparateurs cassés des cartes au trésor réparés

Aucun fichier du jeu n'est modifié : c'est un pak additionnel, compatible avec
tous les serveurs (il n'agit que sur votre affichage).

## Installation (joueurs)

**Windows (recommandé)** : téléchargez `installer.bat` et `TradFR.ps1` dans la
[dernière release](../../releases/latest), mettez-les dans le même dossier et
double-cliquez `installer.bat`. Le script trouve le jeu tout seul, télécharge
la dernière version du patch, et vous propose d'activer la **mise à jour
automatique** (une tâche planifiée vérifie les nouvelles versions à chaque
ouverture de session ; relancer `installer.bat` sert aussi de mise à jour
manuelle).

**À la main** : téléchargez `TradFR_P.pak` dans la
[dernière release](../../releases/latest) et copiez-le dans
`…\SteamLibrary\steamapps\common\ARK Survival Ascended\ShooterGame\Content\Paks\`.
Pour mettre à jour, remplacez le fichier par celui de la nouvelle release.

**Linux / Steam Deck** : `maj_tradfr.sh` (fourni dans la release) installe et
met à jour.

Lancez le jeu en français, c'est tout.

**Désinstallation** : supprimez `TradFR_P.pak` du dossier `Paks` (et la tâche
planifiée « TradFR MAJ » si vous aviez activé la mise à jour automatique).

## Pourquoi un pak et pas un mod CurseForge ?

Le résultat est le même qu'un mod (rien du jeu n'est modifié, tout est
réversible), mais la porte d'entrée diffère. Un mod ASA est fabriqué dans le
DevKit officiel puis « cuit » par CurseForge avec son propre contenu, monté à
part : cette chaîne ne permet pas de fournir un fichier à la place de la
localisation du jeu de base. Le pak `_P`, lui, est chargé directement par le
moteur au démarrage et peut la recouvrir. C'est pour cela qu'aucune
retraduction du jeu de base n'existe en mod CurseForge, dans aucune langue :
tout le monde passe par un pak. Seul inconvénient : pas de mise à jour par le
jeu lui-même, d'où le script fourni.

## Signaler une erreur, proposer une correction

C'est un projet communautaire : chaque signalement améliore le patch pour tout
le monde.

- **Le plus simple** : [ouvrir une issue](../../issues/new/choose) avec une
  capture d'écran et le texte fautif.
- **Mieux** : proposer une pull request d'une ligne dans
  `data/corrections.json` (`"namespace\tclé": "texte corrigé"` : la clé se
  retrouve en cherchant le texte anglais dans `work/en.json` après extraction,
  ou demandez dans l'issue).

## Limitations connues (bugs du jeu, pas du patch)

- L'ordre des plaques de créatures est imposé par le code du jeu :
  « [Sauvage] Mâle Smilodon » (le nom arrive toujours en dernier).
- Les descriptions d'objets affichées dans le panneau des structures perdent
  leurs accents en capitales (« NéCESSITE… ») : le même texte s'affiche
  normalement ailleurs, aucune donnée ne peut satisfaire les deux widgets.
  La VF officielle a le même artefact.
- « Crafting Requirements », « WEIGHT », « - {NAME} - » et le journal de tribu
  en anglais viennent du code du jeu ou de mods, pas des fichiers de langue.
- Les entrées passées du journal de tribu restent en anglais (elles sont
  figées au moment de l'événement) ; les nouvelles seront en français.

## Reconstruire le patch (mainteneurs)

    ./build.py                    # extrait les locres du jeu, applique data/, packe, installe
    ./build.py --no-install       # sans copier dans le dossier du jeu
    python3 tools/detecteurs.py   # rejoue les contrôles qualité sur le build
    ./release.sh vX.Y.Z           # build + tag + release GitHub

### Après une mise à jour du jeu

Wildcard ajoute et modifie des chaînes à chaque patch, sans rien signaler : le
patch continue de se construire et les nouveaux textes s'affichent simplement en
anglais. `delta.py` rend ce décalage visible et produit le lot de travail exact.

    ./delta.py              # compare le jeu à la référence figée, affiche le rapport
    ./delta.py --lots       # écrit les lots dans work/delta/
    ./delta.py --figer      # fige l'état courant comme nouvelle référence

Les lots produits : `a_traduire.json` (nouvelles chaînes), `a_revoir.json` (l'anglais
a changé, la traduction dit peut-être autre chose — avec la version actuelle en
regard), `orphelines.json` (clés supprimées du jeu que le patch traduisait encore),
`techniques.json` (écarté automatiquement : debug, séparateurs, code du DevKit).

Le cycle : `./delta.py --lots` → traduire → verser dans `data/corrections.json` →
`./build.py` → `python3 tools/detecteurs.py` → `./delta.py --figer` → `./release.sh`.
La référence (`data/reference_en.json`) est versionnée dans le dépôt : n'importe
qui peut donc calculer le delta, pas seulement le mainteneur d'origine.

### Veille automatique

`tools/veille.py` fait tout ça sans qu'on le lui demande. Installé en service
utilisateur (`scripts/installer_veille.sh`), il vérifie chaque heure si le pak du
jeu a changé, attend que Steam ait fini d'écrire, calcule le delta, puis :

- retire des données du patch les clés que le jeu ne contient plus ;
- écarte les chaînes techniques (debug, séparateurs, code du DevKit) ;
- **propose automatiquement la traduction officielle d'ARK: Survival Evolved**
  pour chaque chaîne dont la source anglaise y existe telle quelle — près de la
  moitié du jeu est dans ce cas, ces lignes n'ont plus qu'à être confirmées ;
- commite les lots dans `delta/` et **ouvre une issue GitHub** listant ce qui
  reste à faire, avec le contexte de chaque chaîne.

Chaque mise à jour n'est signalée qu'une fois. Si GitHub est injoignable, le
rapport est écrit dans `delta/rapport.md`. Options : `--forcer` (refaire le
rapport), `--local` (pas d'issue).

Résultat : après une mise à jour d'ARK, une issue apparaît d'elle-même avec le
travail déjà mâché, visible de tout le monde — la traduction ne dépend plus de
quelqu'un qui pense à vérifier.

Prérequis : le jeu installé (les locres d'origine sont extraits de
`pakchunk0-Windows.pak`, ils ne sont pas distribuables), Python 3, et la
bibliothèque de décompression Oodle (`liboo2corelinux64.so.9` à placer dans
`tools/retoc_cli-x86_64-unknown-linux-gnu/` : non redistribuable, copiez-la
depuis n'importe quel jeu Unreal ou le SDK Oodle).

### Données du patch

- `data/overrides.json` : traductions des chaînes existantes (`"namespace\tclé": "texte"`)
- `data/additions.json` : traductions des clés absentes du locres FR officiel
- `data/corrections.json` : couche prioritaire appliquée en dernier (c'est ici
  que vont les correctifs communautaires)
- `data/noms_officiels_ase.json` : table figée des noms officiels de créatures
  (ARK: Survival Evolved)

### Outils (`tools/`)

- `pakv12.py` : lecteur du format pak V12 custom de Wildcard (index en clair,
  compression Oodle) ; `repak` ne lit que jusqu'à la V11
- `locres.py` : dump/rebuild/merge de fichiers `.locres` v3, bit-exact en
  round-trip ; le merge greffe les clés manquantes en copiant les hashes du
  locres anglais, à leur position native
- `integrer.py` : reconstruit `data/overrides.json` depuis les lots de
  traduction et `data/corrections.json`
- `valider.py` / `audit.py` : contrôles (placeholders, balises, espaces de
  bord, anglais résiduel, glossaire)

### Notes techniques

- Les locres des 14 langues sont dans `pakchunk0-Windows.pak`, chemin
  `ShooterGame/Content/Localization/ShooterGame/<lang>/ShooterGame.locres`
- Paks non chiffrés, pas de fichiers .sig : les paks custom `_P` sont chargés
  sans vérification de signature
- Le jeu met certains libellés en capitales avec une routine qui ignore les
  accents (bug moteur `ToUpper` ASCII, présent dans les 14 langues) : les
  libellés concernés (stats, noms d'objets accentués) sont pré-capitalisés
  dans les données

## Crédits et avertissement

Projet non affilié à Studio Wildcard. Les textes traduits dérivent du contenu
d'ARK: Survival Ascended (© Studio Wildcard) et ne sont distribués que pour
permettre aux joueurs francophones de profiter du jeu ; sur demande des ayants
droit, la distribution sera retirée.
