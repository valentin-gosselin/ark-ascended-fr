# TradFR — patch de traduction française pour ARK: Survival Ascended

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

1. Téléchargez `TradFR_P.pak` dans la
   [dernière release](../../releases/latest).
2. Copiez-le dans le dossier du jeu :
   `…\SteamLibrary\steamapps\common\ARK Survival Ascended\ShooterGame\Content\Paks\`
   (sous Windows, `installer.bat` fourni dans la release fait la copie pour vous).
3. Lancez le jeu en français. C'est tout.

**Mise à jour** : retéléchargez le fichier de la nouvelle release et remplacez
l'ancien (pas de mise à jour automatique — ce n'est pas un mod CurseForge).

**Désinstallation** : supprimez `TradFR_P.pak` du dossier `Paks`.

## Signaler une erreur, proposer une correction

C'est un projet communautaire : chaque signalement améliore le patch pour tout
le monde.

- **Le plus simple** : [ouvrir une issue](../../issues/new/choose) avec une
  capture d'écran et le texte fautif.
- **Mieux** : proposer une pull request d'une ligne dans
  `data/corrections.json` (`"namespace\tclé": "texte corrigé"` — la clé se
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

    ./build.py              # extrait les locres du jeu, applique data/, packe, installe
    ./build.py --no-install # sans copier dans le dossier du jeu
    ./release.sh vX.Y.Z     # build + tag + release GitHub

Prérequis : le jeu installé (les locres d'origine sont extraits de
`pakchunk0-Windows.pak`, ils ne sont pas distribuables), Python 3, et la
bibliothèque de décompression Oodle (`liboo2corelinux64.so.9` à placer dans
`tools/retoc_cli-x86_64-unknown-linux-gnu/` — non redistribuable, copiez-la
depuis n'importe quel jeu Unreal ou le SDK Oodle).

### Données du patch

- `data/overrides.json` — traductions des chaînes existantes (`"namespace\tclé": "texte"`)
- `data/additions.json` — traductions des clés absentes du locres FR officiel
- `data/corrections.json` — couche prioritaire appliquée en dernier (c'est ici
  que vont les correctifs communautaires)
- `data/noms_officiels_ase.json` — table figée des noms officiels de créatures
  (ARK: Survival Evolved)

### Outils (`tools/`)

- `pakv12.py` — lecteur du format pak V12 custom de Wildcard (index en clair,
  compression Oodle) ; `repak` ne lit que jusqu'à la V11
- `locres.py` — dump/rebuild/merge de fichiers `.locres` v3, bit-exact en
  round-trip ; le merge greffe les clés manquantes en copiant les hashes du
  locres anglais, à leur position native
- `integrer.py` — reconstruit `data/overrides.json` depuis les lots de
  traduction et `data/corrections.json`
- `valider.py` / `audit.py` — contrôles (placeholders, balises, espaces de
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
