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
- **8 684 textes que le jeu n'a jamais proposés à la traduction** : Wildcard a
  oublié de les collecter, ils s'affichaient donc en anglais dans les 14 langues
  (panneau des cosmétiques, missions du tableau des primes, arbre de compétences
  de Dragontopia, navigateur de mods, commandes des navires…)

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

La question revient souvent, d'autant qu'il existe des mods de traduction sur
CurseForge. Ils existent bel et bien - mais ils ne font pas la même chose.

**Un mod n'a pas accès au fichier de langue.** Un mod ASA est fabriqué dans le
DevKit officiel, « cuit » par CurseForge, et monté sous sa propre racine
(`ShooterGame/Mods/<nom>/`). Le fichier de langue du jeu vit ailleurs, dans le
contenu de base, hors de sa portée. Le pak `_P`, lui, est chargé directement par
le moteur au démarrage et peut le recouvrir.

**Ce que font les mods de traduction, alors.** Ils recréent des widgets
d'interface à la main dans la langue voulue, et surchargent les données de jeu
via un PrimalGameData. Le mod « Arabic Translation » en est l'exemple type. Son
contenu, une fois ouvert :

    Arabic_CharacterStatsPanel     widget d'interface refait
    Arabic_HUD                     widget d'interface refait
    Arabic_Inventory               widget d'interface refait
    Arabic_GameMode                mode de jeu personnalisé
    PrimalGameData_BP_BlankMod     surcharge des données de jeu

Trois écrans refaits, et **aucun fichier de langue**.

**Pourquoi cette voie ne mène pas au même endroit.** Recréer un widget traduit
ses propres libellés - ses titres, ses boutons - mais pas ce qu'il affiche. Un
panneau d'inventaire refait en français continuera de montrer « Narcotic »,
parce que ce nom ne vient pas du widget mais de la base de textes du jeu. Or
c'est là que vit l'essentiel du travail : **37 790 des 46 474 entrées** de ce
patch. Pour les atteindre en mod, il faudrait redéfinir chaque objet, chaque
engramme et chaque créature - autant refaire le jeu.

**Et ce qu'on y perdrait.** Un PrimalGameData ou un GameMode personnalisé se
charge côté serveur : le mod ne s'applique que là où l'administrateur l'a
activé, donc jamais sur les serveurs officiels. Il entre aussi en conflit avec
tout autre mod touchant les mêmes éléments. Ce patch ne touche que votre
affichage : il fonctionne sur n'importe quel serveur, officiels compris, sans
que le serveur en sache quoi que ce soit, et sans conflit avec aucun mod.

Seul inconvénient du pak : pas de mise à jour par le jeu lui-même, d'où le
script fourni.

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
- « Crafting Requirements », « WEIGHT », « Last: », « - {NAME} - » et le journal
  de tribu en anglais ne se trouvent dans aucun asset ni fichier de langue : ils
  sont fabriqués par le code du jeu. Aucun patch de traduction ne peut les
  atteindre.
- Le menu déroulant du panneau des cosmétiques (ALL COSMETICS, ARMOR, HAT…)
  affiche les valeurs de l'énumération C++ `EPrimalCustomCosmeticType`. Le jeu
  ne consulte pas la table de traduction pour ces libellés (le code qui le
  ferait n'existe que dans l'éditeur) : vérifié en jeu, il reste anglais.
- L'écran des raccourcis clavier affiche les noms **bruts** de certaines touches
  (`UnknownCharCode_201`, `MiddleMouseButton`…) : cet écran contourne le système
  de traduction, contrairement à la barre d'objets qui affiche bien « & », « ( »…
- Les lettres accentuées des touches (É, È, Ç, À) viennent directement de la
  disposition clavier du système, pas des fichiers de langue.
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
a changé, la traduction dit peut-être autre chose - avec la version actuelle en
regard), `orphelines.json` (clés supprimées du jeu que le patch traduisait encore),
`techniques.json` (écarté automatiquement : debug, séparateurs, code du DevKit).

Le cycle : `./delta.py --lots` → traduire → verser dans `data/corrections.json` →
`./build.py` → `python3 tools/detecteurs.py` → `./delta.py --figer` → `./release.sh`.
La référence (`data/reference_en.json`) est versionnée dans le dépôt : n'importe
qui peut donc calculer le delta, pas seulement le mainteneur d'origine.

### Veille automatique (GitHub Actions)

Le dépôt se surveille tout seul : `.github/workflows/veille-ark.yml` tourne
quatre fois par jour **sur GitHub**, sans machine allumée, sans le jeu installé
et sans compte Steam.

Comment c'est possible : l'API publique de Steam donne le numéro de build d'ARK.
S'il a changé, le workflow télécharge - en anonyme, et **uniquement ce fichier** -
le pak de langue du *serveur dédié*, qui contient exactement les mêmes textes que
le client pour 1,1 Go au lieu de 212 Go. Les textes s'extraient ensuite en Python
pur (le fichier de langue n'est pas compressé, aucune bibliothèque propriétaire
n'est nécessaire).

Le workflow :

- retire des données du patch les clés que le jeu ne contient plus ;
- écarte les chaînes techniques (debug, séparateurs, code du DevKit) ;
- **propose automatiquement la traduction officielle d'ARK: Survival Evolved**
  pour chaque chaîne dont la source anglaise y existe telle quelle - près de la
  moitié du jeu est dans ce cas, ces lignes n'ont plus qu'à être confirmées ;
- commite les lots dans `delta/` et **ouvre une issue GitHub** listant ce qui
  reste à faire, avec le contexte de chaque chaîne.

Résultat : quelques heures après une mise à jour d'ARK, une issue apparaît d'elle-même
avec le travail déjà mâché, visible de tout le monde. La traduction ne dépend de
personne en particulier - n'importe qui peut répondre dans l'issue ou proposer une
pull request.

Le même script tourne à la main si besoin : `python3 tools/veille.py` (avec le jeu
installé) ou `python3 tools/veille.py --en <dump.json> --local`.

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
- `data/textes_widgets.json` : textes que Wildcard n'a jamais collectés, sous la
  forme `"namespace\tclé": ["source anglaise", "traduction"]`. La source
  anglaise y est obligatoire : ces clés n'existent dans aucun locres, rien
  d'autre ne permet de retrouver le texte d'origine (voir plus bas)

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
- `cityhash.py` : les hashes des .locres v3, indispensables pour créer une clé
  qui n'existe nulle part ; se vérifie contre les 77 535 hashes réels du jeu
  (`python3 tools/cityhash.py --verifier`)
- `textes_assets.py` / `balayer_assets.py` : lecture des FText d'un asset, et
  balayage des 45 662 assets du jeu
- `reporter_widgets.py` : reporte sur ces textes les traductions déjà faites
  ailleurs dans le patch

### Les textes que le jeu n'a jamais proposés à la traduction

Des milliers de chaînes s'affichaient en anglais quoi qu'on mette dans les
fichiers de langue. On les croyait écrites en dur dans le code C++. C'est faux.

Ce sont des `FText` posées dans les assets. Une `FText` porte toujours un
namespace et une clé, et le moteur interroge le locres avec ce couple au
chargement du paquet. Wildcard n'a simplement jamais lancé la collecte de
localisation sur ces assets : le couple n'est dans aucun locres, ni anglais ni
français. Le moteur cherche, ne trouve rien, affiche la source. Dans un même
widget, « OFFHAND » a une vraie clé et se traduit normalement, tandis que
« CUSTOM COSMETICS » a un namespace vide et une clé en GUID, jamais collectée.

Il suffit donc de créer l'entrée manquante. Rien d'autre ne change : ni asset
modifié, ni conteneur `.utoc` à fabriquer, le même pak qu'avant.

La seule difficulté est le calcul des hashes, là où tous les autres chemins
d'ajout se contentent de les recopier depuis le locres anglais. Deux fonctions
différentes, chacune validée contre les hashes réels du jeu :

- **namespace et clé** : CityHash64 sur l'UTF-16, replié en 32 bits par la
  recette d'Unreal (`bas + haut * 23`), une chaîne vide valant 0 ;
- **chaîne source** : `FCrc::StrCrc32`, soit un CRC-32 sur l'UTF-32LE. Le moteur
  s'en sert pour repérer une traduction périmée et l'ignorer - c'est pour cela
  que `data/textes_widgets.json` stocke aussi la source anglaise.

**La veille automatique ne voit pas ces textes.** Elle compare l'anglais du
fichier de langue à une référence figée : un contenu dont les textes ne s'y
trouvent pas ne produit aucun écart, et elle annonce en toute bonne foi qu'il
n'y a rien à traduire. C'est arrivé avec le Concavenator, sorti le 26 août
2026 : 283 paquets d'assets dans le jeu, zéro chaîne dans le fichier de langue,
et l'aide des touches de la créature affichée en anglais.

Détecter cela en intégration continue demanderait de télécharger les assets du
jeu, soit 212 Go, contre 1,1 Go pour le seul pak de langue. **Après une mise à
jour de contenu (nouvelle créature, nouvelle carte), il faut donc relancer le
balayage à la main**, avec le jeu installé :

    tools/retoc_cli-*/retoc manifest <pakchunk0-Windows.utoc>   # ecrit pakstore.json
    python3 tools/balayer_assets.py <liste.json> work/orphelines.json
    python3 tools/reporter_widgets.py work/orphelines.json --ecrire

Le balayage complet prend environ une heure. Écrivez ses fichiers dans `work/`
et non dans `/tmp` : sur bien des systèmes `/tmp` vit en mémoire et disparaît au
redémarrage.

Un contrôle rapide permet de repérer une créature oubliée sans tout balayer :
chercher son nom dans `work/en.json`. S'il n'y est pas alors que ses assets
existent, ses textes n'ont pas été collectés. Attention, les dossiers d'assets
portent souvent un nom de code (`Gorilla` pour le Mégapithèque, `Owl` pour la
Chouette des neiges) : l'absence du nom de dossier ne prouve rien à elle seule.

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

## Fonctionnement du dépôt (contributeurs)

`master` est protégé : personne n'y pousse directement, tout passe par une pull
request qui doit passer la validation automatique. Cela vaut aussi pour la veille
automatique, qui ouvre une pull request comme n'importe quel contributeur.

La validation (`tools/valider_donnees.py`, rejouée sur chaque pull request)
vérifie que les fichiers de données sont du JSON valide, que les clés ont la
forme attendue, que les **variables du jeu** (`{0}`, `%s`, `<RichColor>`) et les
espaces de début et de fin sont préservés - une traduction qui les casse afficherait
un texte tronqué en jeu - et qu'aucun binaire n'est ajouté.

Pour contribuer : forkez, modifiez `data/corrections.json`, ouvrez une pull
request. La validation vous dira tout de suite si quelque chose ne va pas.
