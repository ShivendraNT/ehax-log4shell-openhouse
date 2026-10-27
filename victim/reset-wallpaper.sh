#!/usr/bin/env bash
# Restore the GNOME wallpaper captured by capture-wallpaper.sh and clear the
# payload's temporary files. Safe to run between demo batches.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/.original-wallpaper"

if [ ! -f "$SRC" ]; then
  echo "[-] No saved wallpaper. Run ./capture-wallpaper.sh first, or restore the VM snapshot." >&2
  exit 1
fi

VALUE="$(cat "$SRC")"
if [ -z "$VALUE" ]; then
  echo "[-] Saved wallpaper is empty. Use the VM snapshot instead." >&2
  exit 1
fi

gsettings set org.gnome.desktop.background picture-uri "$VALUE"
# Newer GNOME also has a dark-mode URI. Ignore failures on older versions.
gsettings set org.gnome.desktop.background picture-uri-dark "$VALUE" 2>/dev/null || true

rm -f /tmp/ehax-payload-last-run \
      /tmp/ehax-payload-proof.txt \
      /tmp/ehax-payload.log \
      /tmp/ehax-wallpaper.png \
      /tmp/ehax-wallpaper.ps1

echo "[+] Restored wallpaper: $VALUE"
echo "[+] Cleared temporary payload files."
