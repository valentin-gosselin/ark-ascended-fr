# Contexte officiel d'ARK

Ce que Wildcard a dit de chaque créature, objet, structure et mécanique, depuis
l'accès anticipé d'Evolved en 2015. Ces fichiers ne vont pas dans le pak : ils
servent à traduire en sachant de quoi on parle.

| Fichier | Période |
|---|---|
| `ase_2015_2017.md` | Evolved, accès anticipé à la 1.0 : The Center, Scorched Earth, Ragnarok, Aberration |
| `ase_2018_2023.md` | Evolved, Extinction à la fermeture des serveurs officiels : Valguero, Genesis, Crystal Isles, Lost Island, Fjordur |
| `asa_2023_2025.md` | Ascended, de la sortie à Ragnarok et au Lost Colony Pass (v25 à v67) |
| `asa_2025_2026.md` | Ascended, de juillet 2025 à aujourd'hui, avec le contenu annoncé |

Chaque fichier contient une chronologie, des fiches par catégorie (nom anglais
exact, nom français, origine, rôle, note de traduction) et un glossaire des
termes de jeu. Les noms français viennent de `data/evolved_fr.json` et
`data/noms_officiels_ase.json`, ou du patch quand c'est précisé ; aucun n'est
inventé.

## Sources

- Annonces Steam (patch notes et Community Crunch) : appid 346110 pour Evolved,
  2399830 pour Ascended.

      curl "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=2399830&count=10&maxlength=0&format=json"

- Notes de version et fiches de ark.wiki.gg.

## Tenir à jour

À chaque Community Crunch ou mise à jour, compléter `asa_2025_2026.md` : la
chronologie, les fiches du contenu nouveau, la partie « À venir ». Avant de
traduire un delta de la veille, lire les annonces du build concerné.

Les parties « Contresens possibles » relèvent des écarts entre le patch et ce
que disent les annonces : ce sont des pistes à vérifier, pas des corrections
acquises.
