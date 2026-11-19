#!/usr/bin/env bash
# TradFR - mise à jour du patch FR (Linux/Steam Deck/Proton)
# Usage : ./maj_tradfr.sh [dossier Paks]  (détection Steam par défaut)
set -euo pipefail
REPO="valentin-gosselin/ark-ascended-fr"
PAK="TradFR_P.pak"
# depuis l'UE 5.8, le jeu ignore le .pak sans son .utoc/.ucas du meme nom
FICHIERS=(TradFR_P.pak TradFR_P.utoc TradFR_P.ucas)
PAKS="${1:-}"
if [[ -z "$PAKS" ]]; then
    for lib in "$HOME/.steam/steam" "$HOME/.local/share/Steam" /mnt/*/SteamLibrary "$HOME"/*/SteamLibrary; do
        c="$lib/steamapps/common/ARK Survival Ascended/ShooterGame/Content/Paks"
        [[ -d "$c" ]] && PAKS="$c" && break
    done
fi
[[ -d "$PAKS" ]] || { echo "Dossier Paks introuvable ; passez-le en argument." >&2; exit 1; }
# pas de « curl | grep -m1 » : grep s'arrete a la premiere ligne, curl echoue
# alors en ecrivant la suite et pipefail fait sortir le script sans rien dire
json=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest")
distante=$(grep -oPm1 '"tag_name":\s*"\K[^"]+' <<<"$json")
locale=$(cat "$PAKS/$PAK.version" 2>/dev/null || echo "(absente)")
complet=1
for f in "${FICHIERS[@]}"; do [[ -f "$PAKS/$f" ]] || complet=0; done
if [[ "$locale" == "$distante" && $complet == 1 ]]; then
    echo "TradFR déjà à jour ($locale)."; exit 0
fi
if pgrep -f ArkAscended.exe >/dev/null; then
    echo "ARK est en cours d'exécution : fermez le jeu puis relancez la mise à jour." >&2; exit 1
fi
echo "Téléchargement de TradFR $distante..."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
for f in "${FICHIERS[@]}"; do
    curl -fL -o "$tmp/$f" "https://github.com/$REPO/releases/download/$distante/$f"
done
# les trois fichiers ne sont copies qu'une fois tous telecharges
for f in "${FICHIERS[@]}"; do mv -f "$tmp/$f" "$PAKS/$f"; done
echo "$distante" > "$PAKS/$PAK.version"
echo "Installé : $PAKS/$PAK ($locale -> $distante)"
