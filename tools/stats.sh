#!/usr/bin/env bash
# Combien de personnes utilisent le patch ?
#
# GitHub compte les telechargements par fichier de release, de facon
# permanente. Le trafic du depot (vues, clones) n'est en revanche conserve
# que 14 jours et n'est visible que par le proprietaire.
set -euo pipefail
R="${1:-valentin-gosselin/ark-ascended-fr}"

echo "TELECHARGEMENTS  (cumul depuis la publication)"
gh api "repos/$R/releases" --paginate --jq '
  .[] | "\n  \(.tag_name)  —  publiee le \(.published_at[:10])\n" +
  ([.assets[] | "     \(.download_count | tostring | (" " * (6 - length)) + .)  \(.name)"] | join("\n"))'

total=$(gh api "repos/$R/releases" --paginate --jq '[.[].assets[] | select(.name | endswith(".pak")) | .download_count] | add // 0')
echo
echo "  => $total telechargement(s) du patch, toutes versions confondues"

echo
echo "TRAFIC DU DEPOT  (14 derniers jours seulement)"
gh api "repos/$R/traffic/views" --jq '"     \(.count) vue(s), \(.uniques) visiteur(s) unique(s)"' 2>/dev/null \
  || echo "     (indisponible : reserve au proprietaire du depot)"
gh api "repos/$R/traffic/clones" --jq '"     \(.count) clone(s), \(.uniques) unique(s)"' 2>/dev/null || true

echo
echo "RETOURS"
ouvertes=$(gh issue list --repo "$R" --state open --json number --jq 'length')
fermees=$(gh issue list --repo "$R" --state closed --json number --jq 'length')
echo "     $ouvertes issue(s) ouverte(s), $fermees fermee(s)"
