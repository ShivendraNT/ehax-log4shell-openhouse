#!/usr/bin/env bash
# EHAX Open House - victim-side Minecraft 1.8.8 server launcher.
#
# IMPORTANT:
#   - Run this inside the isolated victim VM, from a terminal in the logged-in
#     desktop session (not over SSH/systemd).
#   - Use Java 8. Minecraft 1.8.8 is happiest there.
#   - Minimise this terminal after the server starts so the wallpaper is
#     visible on the victim screen. Do not close it.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

JAVA_BIN="${JAVA_BIN:-java}"
DRY_RUN="${EHAX_PAYLOAD_DRY_RUN:-0}"
SOUND="${EHAX_PAYLOAD_SOUND:-0}"

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --sound) SOUND=1; shift ;;
    -h|--help)
      echo "Usage: ./start-server.sh [--dry-run] [--sound]"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if ! command -v "$JAVA_BIN" >/dev/null 2>&1; then
  echo "[-] Java not found. Install Java 8 (Zulu/Temurin) and put it on PATH," >&2
  echo "    or run: JAVA_BIN=/path/to/java ./start-server.sh" >&2
  exit 1
fi

JAVA_VERSION="$("$JAVA_BIN" -version 2>&1 | head -n1)"
echo "[*] $JAVA_VERSION"
case "$JAVA_VERSION" in
  *1.8.*) ;;
  *)
    echo "[!] This demo targets Java 8. Newer Java versions can break 1.8.8." >&2
    echo "    Continuing anyway, but expect trouble." >&2
    ;;
esac

if [ ! -f server.jar ]; then
  echo "[-] server.jar is missing." >&2
  echo "    Download Minecraft 1.8.8 server.jar into:" >&2
  echo "    $HERE" >&2
  echo "    https://mcversions.net/ or the Mojang version manifest." >&2
  exit 1
fi

if [ ! -f eula.txt ]; then
  cat > eula.txt <<'EOF'
# By setting eula=true you agree to the Minecraft EULA:
# https://aka.ms/MinecraftEULA
eula=true
EOF
  echo "[*] Created eula.txt (eula=true)."
fi

if [ ! -f server.properties ]; then
  cp server.properties.template server.properties
  echo "[*] Created server.properties from the lab template."
fi

if [ "$(id -u)" -eq 0 ]; then
  echo "[!] You are running as root. For the desktop wallpaper demo, run as the" >&2
  echo "    normal logged-in user instead. Root's desktop session is different." >&2
fi

if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
  echo "[!] No DISPLAY/WAYLAND_DISPLAY detected. If this is an SSH session, the" >&2
  echo "    payload may not be able to update the desktop wallpaper." >&2
  echo "    Start the server from a terminal inside the VM's desktop instead." >&2
fi

if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ] && [ ! -S "/run/user/$(id -u)/bus" ]; then
  echo "[!] No DBus session bus found. GNOME wallpaper updates may fail." >&2
fi

export EHAX_LAB=1
export EHAX_PAYLOAD_DRY_RUN="$DRY_RUN"
export EHAX_PAYLOAD_SOUND="$SOUND"

cat <<EOF
============================================================
  EHAX // VICTIM MINECRAFT SERVER
============================================================
  Java        : $(command -v "$JAVA_BIN")
  Lab guard   : EHAX_LAB=1
  Dry run     : $DRY_RUN  (1 = do not change wallpaper)
  Sound       : $SOUND  (1 = play a short sound)
  JNDI trust  : true (LAB ONLY - never use on a real server)

  Keep this terminal MINIMISED after startup so the
  victim desktop wallpaper is visible. Do not close it.

  This server is intentionally vulnerable (Minecraft
  1.8.8 + Log4j 2.0-beta9). Isolated VM only.
============================================================

EOF

exec "$JAVA_BIN" \
  -Dcom.sun.jndi.ldap.object.trustURLCodebase=true \
  -Djava.net.preferIPv4Stack=true \
  -Xms1024M -Xmx1024M \
  -jar server.jar nogui
