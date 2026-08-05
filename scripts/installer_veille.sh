#!/usr/bin/env bash
# Installe la veille TradFR comme service utilisateur systemd.
# La veille tourne sous votre session : elle a donc acces au jeu et a `gh`.
set -euo pipefail
CIBLE="$HOME/.config/systemd/user"
ICI="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$CIBLE"
cp "$ICI/tradfr-veille.service" "$ICI/tradfr-veille.timer" "$CIBLE/"
systemctl --user daemon-reload
systemctl --user enable --now tradfr-veille.timer

echo "Veille activee. Prochaine verification :"
systemctl --user list-timers tradfr-veille.timer --no-pager | sed -n 2p
echo
echo "  journalctl --user -u tradfr-veille -f     suivre l'activite"
echo "  systemctl --user disable --now tradfr-veille.timer   desactiver"
