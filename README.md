# Patch de traduction française pour ARK: Survival Ascended

La traduction française officielle d'ASA est incomplète (~4 400 chaînes manquantes
qui s'affichent en anglais) et truffée d'erreurs. Ce projet reconstruit un
`ShooterGame.locres` français corrigé et le distribue sous forme d'un pak patch
(`TradFR_P.pak`) à déposer dans le dossier `Paks` du jeu.

## Utilisation

    ./build.py              # extrait, applique data/, packe et installe
    ./build.py --no-install # sans copier dans le dossier du jeu

Désinstallation : supprimer `TradFR_P.pak` du dossier
`ShooterGame/Content/Paks` du jeu (aucun fichier d'origine n'est modifié).

## Contenu actuel

- **3 466 chaînes traduites** qui s'affichaient en anglais faute de version
  française (les textes manquants passent de 4 427 à 961, le reliquat étant des
  chemins d'assets et identifiants jamais montrés au joueur)
- **555 traductions fautives corrigées**, arbitrées contre la traduction
  d'ARK: Survival Evolved quand le texte anglais source est identique
  (« Ammo » rendu par « Mais », « Back » par « ouvrir », « Cannot Charge » par
  « Impossible de facturer »...)

## Données du patch

- `data/overrides.json` — corrections de chaînes existantes (`"namespace\tclé": "texte"`)
- `data/additions.json` — traductions des clés absentes du locres FR officiel

## Contrôles

    python3 tools/valider.py A work/batches/A work/batches/out   # intégrité technique
    python3 tools/audit.py work/batches/A work/batches/out A work/glossaire.tsv
    python3 tools/corriger_bords.py work/batches/A work/batches/out A

`valider.py` vérifie que placeholders, balises et espaces de bord du source sont
préservés ; `audit.py` signale anglais résiduel, typographie et écarts de
glossaire ; `corriger_bords.py` répare mécaniquement les espaces de bord et les
échappements littéraux.

## Outils (`tools/`)

- `pakv12.py` — lecteur du format pak V12 custom de Wildcard (index en clair,
  compression Oodle) ; `repak` ne lit que jusqu'à la V11
- `locres.py` — dump/rebuild/merge de fichiers `.locres` v3 ; le rebuild à vide
  est bit-exact avec le fichier d'origine
- `repak` — packe le pak patch final (V11, accepté par le jeu)
- `oodle/` — bibliothèque de décompression Oodle (build officiel Epic)

## Notes techniques

- Les locres des 14 langues sont dans `pakchunk0-Windows.pak`, chemin
  `ShooterGame/Content/Localization/ShooterGame/<lang>/ShooterGame.locres`
- Paks non chiffrés, pas de fichiers .sig : les paks custom `_P` sont chargés
  sans vérification de signature
- Les hashes (namespace, clé, source) sont préservés tels quels ; l'ajout de
  clés manquantes copie les hashes depuis le locres anglais
