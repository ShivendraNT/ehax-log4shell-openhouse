#!/usr/bin/env bash
# Save the current GNOME wallpaper URI so reset-wallpaper.sh can restore it.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/.original-wallpaper"

if ! command -v gsettings >/dev/null 2>&1; then
  echo "[-] gsettings not found. Use a VM snapshot instead." >&2
  exit 1
fi

CURRENT="$(gsettings get org.gnome.desktop.background picture-uri)"
printf '%s\n' "$CURRENT" > "$OUT"
echo "[+] Saved current wallpaper:"
echo "    $CURRENT"
echo "[+] To: $OUT"
