# Victim VM — Minecraft 1.8.8 + Log4j 2.0-beta9

This is the laptop the audience looks at. It runs the vulnerable Minecraft
server, but the screen shows the normal desktop wallpaper. After the kid sends
the chat message, the wallpaper changes.

> **Lab only.** This server is deliberately vulnerable and runs with
> `online-mode=false` and a JNDI trust flag that must never be used on a real
> server. Use a host-only VM network with no internet uplink.

> **Why not the repo's Docker image?** A container has no logged-in desktop
> session, so a wallpaper payload has nothing to change. The original
> `Minecraft-Log4j-Exploit` Docker image is fine for a CTF/reverse-shell demo,
> but this reveal needs a desktop VM. The vulnerable Minecraft 1.8.8 server jar
> is the same; only the runtime environment differs.

## 1. VM

Recommended: **Ubuntu 22.04/24.04 Desktop, 2 vCPU, 2 GB RAM, 15 GB disk**.

- If the host is an Apple Silicon Mac, use an **arm64** Ubuntu VM. Zulu 8 has
  an arm64 Linux build.
- Add a **host-only / private** network adapter. No NAT, no bridged adapter,
  no internet.
- Set a static IP, for example `10.10.10.20/24`.
- Disable screen lock and blanking:
  ```bash
  gsettings set org.gnome.desktop.session idle-delay 0
  gsettings set org.gnome.desktop.screensaver lock-enabled false
  ```
- Set a normal/neutral desktop wallpaper and take a VM snapshot **before** the
  event. Restore that snapshot between batches.

## 2. Java 8

Minecraft 1.8.8 targets Java 8. On Ubuntu arm64:

```bash
cd /tmp
curl -L -O https://cdn.azul.com/zulu/bin/zulu8.98.0.107-ca-jdk8.0.512-linux_aarch64.tar.gz
sudo mkdir -p /opt/java
sudo tar -xzf zulu8.98.0.107-ca-jdk8.0.512-linux_aarch64.tar.gz -C /opt/java
export PATH="/opt/java/zulu8.98.0.107-ca-jdk8.0.512-linux_aarch64/bin:$PATH"
java -version   # should say 1.8.0_512
```

On Windows or x86 Linux, download the matching **JDK 8** package from
[Azul Zulu](https://www.azul.com/downloads/?version=java-8-lts&package=jdk) and
put `java.exe` / `java` on PATH.

> Any Java 8 build works for the demo because the start script sets
> `-Dcom.sun.jndi.ldap.object.trustURLCodebase=true`. That flag is a deliberate
> lab-only re-enable of the old JNDI behaviour. It is not safe for production.

## 3. Minecraft server

Download the official 1.8.8 server jar:

```bash
curl -L -o server.jar \
  https://launcher.mojang.com/v1/objects/5fafba3f58c40dc51b5c3ca72a98f62dfdae1db7/server.jar
sha1sum server.jar
# expected: 5fafba3f58c40dc51b5c3ca72a98f62dfdae1db7
```

Put `server.jar` in this `victim/` folder next to `start-server.sh`.

## 4. Start the server

From a terminal **inside the VM's logged-in GNOME desktop** (not SSH, not
systemd, not root):

```bash
cd victim
./start-server.sh
```

Wait for `Done (…)! For help, type "help" or "?"`.

The script:

- sets `EHAX_LAB=1` (the payload refuses to run without it),
- copies `server.properties.template` to `server.properties` on first run,
- starts Minecraft with the JNDI lab flag,
- prints a reminder to minimise the terminal.

**Minimise the terminal. Do not close it.** The audience should see the normal
desktop wallpaper. If the server console is full-screen, hide the wallpaper.

## 5. Network check

From the attacker VM:

```bash
python3 attacker/chat-send.py --host 10.10.10.20 --port 25565 --message 'hello'
```

The victim server log should show:

```
<EHAX_Guest> hello
```

If that works, the demo path is ready.

## 6. Reset between batches

Preferred: restore the VM snapshot (clean desktop + clean server).

If you are not using snapshots:

```bash
./capture-wallpaper.sh   # once, before the first batch
./reset-wallpaper.sh     # after each batch
```

`reset-wallpaper.sh` restores the GNOME wallpaper URI captured earlier, removes
the temp proof/log/marker files, and leaves the Minecraft server running for the
next group.

On Windows, either restore a snapshot or set the wallpaper back manually from
Settings. The payload writes its proof to `%TEMP%\ehax-payload-proof.txt`.

## Windows notes

Use `start-server.bat` instead of the shell script. Run it from the logged-in
user's desktop session, not as a service or Scheduled Task. Minimise the console
and keep the desktop visible. The payload uses PowerShell's
`SystemParametersInfo` call to change the wallpaper; no Python or JDK is needed
on the victim beyond Java 8 for Minecraft.

## Troubleshooting

See `../docs/TROUBLESHOOTING.md`. The most common mistakes are:

- server started over SSH or as root → payload cannot reach the desktop session,
- server console full-screen → wallpaper changes behind it,
- wrong attacker IP in the trigger → no LDAP callback,
- Java 8u191+ without `-Dcom.sun.jndi.ldap.object.trustURLCodebase=true` → no
  remote class load,
- `EHAX_LAB` missing → payload deliberately refuses to run.
