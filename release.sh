#!/usr/bin/env bash
# Publie une release : build du pak + tag + release GitHub avec les scripts d'installation.
# Usage : ./release.sh vX.Y.Z ["notes de version"]
set -euo pipefail
V=${1:?usage: ./release.sh vX.Y.Z [notes]}
NOTES=${2:-"Voir les commits depuis la release précédente."}
./build.py --no-install
git tag "$V"
git push origin master "$V"
gh release create "$V" work/TradFR_P.pak scripts/installer.bat scripts/TradFR.ps1 scripts/maj_tradfr.sh \
    --title "TradFR $V" --notes "$NOTES

**Installation** : déposez \`TradFR_P.pak\` dans \`...\\ShooterGame\\Content\\Paks\\\` (ou lancez \`installer.bat\` sous Windows, \`maj_tradfr.sh\` sous Linux)."
echo "Release $V publiée."
