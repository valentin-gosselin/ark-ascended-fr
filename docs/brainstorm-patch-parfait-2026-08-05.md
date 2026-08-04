# Brainstorm : amener le patch FR d'ASA au niveau « parfait »

**Date :** 2026-08-05
**Objectif :** plan d'attaque pour maximiser la qualité du patch de traduction française d'ARK Survival Ascended
**Contexte :** patch complet (31 897 chaînes / 34 324 clés), pipeline reproductible (`integrer.py` → `build.py`), 4 pièges documentés avec détecteurs, table de noms officiels figée, corpus des 8 autres langues extrait. Goulot actuel : la validation en jeu repose sur un seul humain. 4 décisions terminologiques en attente. 961 chaînes toujours en anglais faute de pouvoir ajouter des clés au locres (piège n°1).
**Résultat attendu :** plan d'attaque priorisé et actionnable.

## Techniques utilisées
1. **Brainstorming inversé** — « comment garantir que le patch reste médiocre ? » : révèle les vecteurs d'échec à neutraliser
2. **SWOT** — état des lieux stratégique du projet
3. **Starbursting** — qui/quoi/où/quand/pourquoi/comment : couvre les angles morts (distribution, maintenance, testeurs)

---

## Technique 1 — Brainstorming inversé

*Comment garantir un patch médiocre ?* → chaque anti-solution inversée donne une action.

| Anti-solution | Action (inverse) |
|---|---|
| Ne jamais tester en jeu, se fier aux fichiers | Tournée d'écrans méthodique avec checklist (les 2 régressions passées passaient tous les contrôles fichier) |
| Corriger au cas par cas sans généraliser | Continuer la doctrine « 1 bug vu = 1 détecteur automatique » (déjà fait 4×) |
| Laisser les décisions terminologiques en suspens | Trancher qualités d'objet / Kibble / Adobe / artefacts AVANT publication |
| Ignorer les mises à jour du jeu | Script *delta* : diff des clés EN à chaque patch du jeu, traduire uniquement le delta |
| Rester seul testeur | Publier tôt → transformer la communauté en armée de testeurs |
| Ne pas documenter les choix | `data/noms_officiels_ase.json` + mémoire projet : déjà en place, maintenir |
| Abandonner les 961 chaînes en anglais | Ré-attaquer le piège n°1 (voir Insight n°1 — il est probablement contournable) |
| Toucher aux chaînes techniques | Garder la liste d'exclusion (debug, cheat, TriggerKey) |

## Technique 2 — SWOT

**Forces**
- Pipeline entièrement reproductible, 0 anomalie technique aux contrôles
- Table de noms officiels (créatures + objets) alignée sur Evolved, figée dans le dépôt
- 4 pièges moteur documentés avec leurs détecteurs rejouables
- Corpus comparatif : 8 langues + Evolved (déjà exploité 3×)
- Qualité déjà supérieure à l'officiel (4 % de noms latins déformés contre 12-24 % ailleurs)

**Faiblesses**
- Validation en jeu = un seul humain, couverture d'écrans partielle (boss, événements, DLC jamais vérifiés)
- Cartographie des majuscules incomplète (liste manuelle, code C++ inaccessible)
- 961 chaînes en anglais (clés absentes du locres FR)
- 4 décisions terminologiques en attente

**Opportunités**
- Demande forte et insatisfaite (forums Steam pleins de plaintes, **aucun patch concurrent**)
- L'espagnol embarque 34 701 clés (> FR 34 324) → preuve que le moteur accepte des locres à nombre de clés différent
- Publication = retours gratuits ; wiki FR / Crowdin comme référentiels de terminologie
- Le pak de diagnostic « Àbcdé » peut cartographier la capitalisation en une session

**Menaces**
- Chaque MAJ du jeu peut ajouter/modifier des clés (désynchronisation silencieuse)
- Wildcard pourrait un jour vérifier les signatures de pak (aucun signe aujourd'hui)
- Épuisement du mainteneur unique

## Technique 3 — Starbursting

- **Qui ?** Testeurs : recruter sur les Discord/forums FR d'ARK après publication. Mainteneur : automatiser tout ce qui peut l'être.
- **Quoi ?** Zones jamais vues en jeu : combats de boss, interfaces Tek, événements saisonniers, contenus Bob's Tall Tales, messages serveur, écrans de mort.
- **Où ?** Distribution : GitHub (source + releases) ; Nexus et/ou CurseForge (visibilité). Retours : issues GitHub + un canal simple (formulaire ou Discord).
- **Quand ?** À chaque MAJ du jeu : `build.py` invalide déjà le cache d'extraction ; ajouter la détection du delta de clés.
- **Pourquoi ?** Définir « parfait » de façon mesurable : 0 chaîne EN visible hors technique, 0 accent cassé sur la tournée complète, 100 % de cohérence sur les familles (créatures, objets, quêtes), délai de correction < 1 semaine après signalement.
- **Comment ?** Checklist d'écrans (ci-dessous), pak de diagnostic, script delta, releases versionnées.

---

## Idées consolidées (par catégorie)

### A. Débloquer les 961 chaînes en anglais
1. **Preuve nouvelle** : l'ES contient 961 des 4 427 clés absentes du FR — exactement les 961 chaînes restées en anglais. Le moteur charge un locres de 34 701 clés : le nombre de clés n'est PAS la contrainte.
2. La cause probable du rejet (piège n°1) : les **hashes des clés ajoutées** (CityHash64 UTF-16) non calculés par notre writer, pas l'ajout lui-même.
3. Voie sans risque : **greffer la structure des entrées depuis es.locres** (key hash + source hash tout prêts) en y mettant notre texte FR — zéro hash à calculer pour ces 961 clés.
4. Ensuite seulement : implémenter CityHash64 UTF-16 dans `locres.py` pour les 3 466 restantes d'`additions.json`.
5. Test A/B en jeu à chaque étape (le piège n°1 est silencieux).

### B. Cartographier la capitalisation une bonne fois
6. Pak de diagnostic : remplacer les libellés candidats par un motif témoin `Àbcdé-<n>` → une session de jeu révèle quels widgets transforment.
7. Checklist d'écrans à couvrir : création de perso, HUD, inventaire + infobulles, artisanat, forge/atelier, panneau de stats, montée de niveau, carte + marqueurs, apprivoisement, élevage, tribu, options (toutes les pages), mort/respawn, obélisque/boss, terminal de transfert, chat, notes lore.
8. Chaque découverte → famille entière corrigée + détecteur.

### C. Finitions éditoriales
9. Trancher les 4 décisions en attente : qualités d'objet ([Rare]/[Épique] vs Apprenti/Compagnon), Kibble vs Croquette, Adobe vs Argile, noms d'artefacts.
10. Passe d'accords automatique (genre/nombre après renommages) — le détecteur existe déjà.
11. Passe typographique finale : espaces insécables, œ/æ, guillemets « ».

### D. Publication et communauté
12. Repo GitHub public : source du patch, releases, issues comme canal de retours.
13. Nexus/CurseForge pour la visibilité (aucun concurrent = référencement facile).
14. README : installation (déposer le `_P.pak`), limitations connues (Tamed/Juvenile/Adolescent intraduisibles, ordre des noms de créatures), crédits.
15. Versionnage : `v1.0.0` au premier jet public, patch notes par release.

### E. Industrialisation de la maintenance
16. Script `delta.py` : après MAJ du jeu, lister clés EN nouvelles / modifiées / supprimées → petit lot de traduction ciblé.
17. Rejeu automatique des 4 détecteurs de pièges à chaque build (déjà scriptables, les intégrer à `build.py`).
18. Garder le corpus 8 langues comme oracle de régression.

---

## Insights clés

### Insight 1 : les 961 chaînes anglaises sont probablement débloquables — c'est la plus grosse victoire accessible
**Source :** SWOT (opportunités) + vérification factuelle pendant la session.
**Preuve :** es.locres charge 34 701 clés (377 de plus que le FR) et contient précisément les 961 clés manquantes. Le rejet observé au piège n°1 venait donc vraisemblablement de notre construction du fichier (hashes des clés ajoutées), pas d'une règle du moteur.
**Impact : élevé** (dernier gros morceau d'anglais visible) · **Effort : moyen** (greffe depuis es.locres = faible ; CityHash64 = moyen).

### Insight 2 : le goulot n'est plus la traduction, c'est l'observation — publier devient l'outil qualité n°1
**Source :** inversé + starbursting. Un seul joueur ne verra jamais les 34 324 chaînes. La publication transforme les joueurs en détecteurs, et chaque signalement corrige une famille entière (méthode déjà rodée sur 3 cas réels).
**Impact : élevé** · **Effort : faible** (le patch est déjà au niveau publiable).

### Insight 3 : sans script delta, le patch meurt à la première grosse MAJ
**Source :** inversé + SWOT (menaces). La désynchronisation sera silencieuse, comme tous les pièges de ce projet.
**Impact : élevé** · **Effort : faible** (diff de deux dumps JSON).

### Insight 4 : le pak de diagnostic transforme un problème sans fin en une session de test
**Source :** starbursting. La capitalisation est dans le C++ : ni les widgets ni les autres langues ne la révèlent. Le motif témoin `Àbcdé` la rend observable exhaustivement en ~15 minutes de jeu.
**Impact : moyen** · **Effort : faible**.

### Insight 5 : figer la terminologie avant de publier
**Source :** inversé. Changer « Kibble » en « Croquette » après publication perturbe les utilisateurs ; avant, c'est gratuit.
**Impact : moyen** · **Effort : nul** (4 questions à trancher).

---

## Plan d'attaque priorisé

| Phase | Contenu | Effort | Gain |
|---|---|---|---|
| **0. Trancher** | Les 4 décisions terminologiques (qualités, Kibble, Adobe, artefacts) | 10 min de dialogue | Terminologie figée |
| **1. Débloquer les 961** | Greffe des entrées depuis es.locres avec texte FR → test en jeu → puis CityHash64 pour les 3 466 d'additions.json | 1 session | Quasi-0 anglais visible |
| **2. Cartographier les majuscules** | Pak diagnostic `Àbcdé` + tournée checklist (17 écrans) | 1 build + 15 min de jeu | Capitalisation définitive |
| **3. Audit final** | Accords, typographie, rejeu des 4 détecteurs, échantillon aléatoire relu | 1 session | Qualité éditoriale |
| **4. Publier v1.0** | GitHub + Nexus/CurseForge, README, canal de retours | 1 session | Testeurs illimités |
| **5. Industrialiser** | `delta.py` post-MAJ, détecteurs intégrés à `build.py` | 1 session | Patch pérenne |
| **6. Boucle communautaire** | Signalement → famille corrigée → release | continu | Convergence vers « parfait » |

## Statistiques
- Idées générées : 18 (5 catégories)
- Insights clés : 5
- Techniques appliquées : 3
- Découverte factuelle pendant la session : les 961 clés manquantes existent dans es.locres

## Prochaine étape recommandée
Phase 0 immédiatement (4 questions), puis Phase 1 — c'est l'insight n°1, le meilleur ratio gain/effort du projet.

---
*Généré par BMAD Method v6 — Creative Intelligence*
