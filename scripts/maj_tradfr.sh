#!/usr/bin/env bash
# TradFR - mise à jour du patch FR (Linux/Steam Deck/Proton)
# Usage : ./maj_tradfr.sh [dossier Paks]  (détection Steam par défaut)
set -euo pipefail
REPO="valentin-gosselin/ark-ascended-fr"
PAK="TradFR_P.pak"
PAKS="${1:-}"
if [[ -z "$PAKS" ]]; then
    for lib in "$HOME/.steam/steam" "$HOME/.local/share/Steam" /mnt/*/SteamLibrary "$HOME"/*/SteamLibrary; do
        c="$lib/steamapps/common/ARK Survival Ascended/ShooterGame/Content/Paks"
        [[ -d "$c" ]] && PAKS="$c" && break
    done
fi
[[ -d "$PAKS" ]] || { echo "Dossier Paks introuvable ; passez-le en argument." >&2; exit 1; }
distante=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | grep -oPm1 '"tag_name":\s*"\K[^"]+')
locale=$(cat "$PAKS/$PAK.version" 2>/dev/null || echo "(absente)")
if [[ "$locale" == "$distante" && -f "$PAKS/$PAK" ]]; then
    echo "TradFR déjà à jour ($locale)."; exit 0
fi
echo "Téléchargement de TradFR $distante..."
curl -fL -o "$PAKS/$PAK" "https://github.com/$REPO/releases/latest/download/$PAK"
echo "$distante" > "$PAKS/$PAK.version"
echo "Installé : $PAKS/$PAK ($locale -> $distante)"
