# Safety, Scope, and Legal Boundaries

This is a **historical vulnerability demo** for an educational event. The
vulnerability is real, but the payload is intentionally boring. The point is to
show how a logging library can turn user text into remote code execution — and
why patching matters.

---

## 1. Scope

| Item | Value |
|---|---|
| Vulnerability | CVE-2021-44228 (Log4Shell) |
| Victim | Minecraft Java Edition 1.8.8 server, Log4j 2.0-beta9 |
| Environment | Two disposable VMs, host-only network, no internet |
| Payload | Change desktop wallpaper, optional sound, temp proof file |
| Audience | School kids, supervised |
| Operator | EHAX volunteer, briefed on this document |

**Out of scope:** real laptops, college systems, public servers, cloud
instances, phones, friends' machines, “just to test” side quests.

---

## 2. Hard rules

1. **Isolated VMs only.** Both machines are disposable. If a VM touches a real
   network or a real machine, stop.
2. **No internet uplink.** Host-only/private network. Disable NAT and bridged
   adapters for the duration.
3. **No real data.** Do not put personal files, credentials, browser profiles, or
   SSH keys in the victim VM. The snapshot should be clean.
4. **Benign payload only.** No reverse shell, no file reads, no credential
   access, no persistence, no privilege escalation, no destructive command.
5. **Consent and supervision.** A presenter is with each group. Kids do not
   operate the attacker VM unsupervised.
6. **Say the legal line every batch.** Unauthorized access is illegal, even if
   “it's just a demo.” The line is in the stage script; don't skip it.
7. **No teaching the syntax.** Don't write the full trigger on a board or read
   it aloud. The kid presses Enter; the operator handles the string.
8. **No recording of real data.** Photos of kids only with the event's consent
   process. Screen recordings should show the VM, not personal desktops.
9. **Stop on ambiguity.** If you are unsure whether a machine is in scope, stop
   and ask the lead.

---

## 3. Legal context (India)

Unauthorized access, data theft, and disruption of computer systems can attract
criminal liability under the **Information Technology Act, 2000** (including
Sections 43, 66, 66C, 66D, and related provisions), as well as institutional
policies. “I was just demonstrating” is not a defence without authorization.

This demo is authorized because:

- the systems are owned/controlled by the organizers,
- the VMs are isolated and contain no third-party data,
- the payload is harmless and visible,
- participants are supervised,
- the event is educational.

This is not legal advice. If the event has a faculty advisor/legal contact, loop
them in before running any security demo.

---

## 4. What the payload does (and does not do)

### Does

- Checks `EHAX_LAB=1` (refuses otherwise).
- Downloads `ehax-wallpaper.png` only from a private/loopback host.
- Writes the image to the OS temp directory.
- Sets the current user's wallpaper (PowerShell on Windows, `gsettings`/XFCE/
  KDE/`feh` on Linux, `osascript` on macOS).
- Optionally plays a short system sound if `EHAX_PAYLOAD_SOUND=1`.
- Appends a line to `%TEMP%\ehax-payload-proof.txt` and a log.
- Returns `"[EHAX]"` to JNDI to keep the log less noisy.

### Does not

- Open a shell or execute arbitrary commands.
- Read, upload, delete, or encrypt files (other than its own temp image/log).
- Install persistence, services, cron jobs, or startup entries.
- Steal credentials, cookies, tokens, or browser data.
- Scan the network or contact public internet hosts.
- Escalate privileges.
- Touch another user's desktop/session.
- Change system settings other than the current user's wallpaper.

The class runs with the Minecraft server process's permissions. That is the
lesson: even this harmless class could have been a real payload. The demo
deliberately stops at wallpaper.

---

## 5. Interlocks

- `EHAX_LAB=1` environment guard: no accidental run on an unconfigured server.
- Private-host check: the wallpaper URL must resolve to loopback, link-local, or
  RFC1918 space. No public download.
- `-Dcom.sun.jndi.ldap.object.trustURLCodebase=true` only in the lab launch
  script, with a warning.
- `online-mode=false` only inside the disposable VM.
- Runbook stop conditions.

These interlocks reduce accidents; they do not make the vulnerable server safe
to expose. The network isolation is the primary control.

---

## 6. Data handling

- Victim VM contains no personal data.
- Screenshots/recordings should show the demo wallpaper and the terminal, not
  personal notifications or browser tabs.
- If a photo includes a minor's face, follow the event's consent policy.
- Delete raw footage at the end of the event unless the team needs it for the
  report; store it on the society drive, not a personal phone gallery.
- Don't post the trigger string with “how to” instructions on social media. A
  post about the lesson/patch is fine; a copy-paste exploit tutorial is not.

---

## 7. Incident / stop conditions

Stop the demo and shut down the VMs immediately if:

- the network has internet/NAT/bridged connectivity,
- a payload reaches a non-lab IP or a real machine,
- you see unexpected file access, shell, persistence, or outbound traffic,
- someone asks to run it on their own device,
- the victim VM contains real data,
- a kid or volunteer is distressed or unsupervised,
- the hypervisor starts sharing folders/clipboard with the host.

After stopping:

1. Disconnect the VMs from the network.
2. Do not power off the host; snapshot the VM state if you need to investigate.
3. Tell the event lead.
4. Restore clean snapshots.
5. Write down what happened; adjust the runbook.

The demo is never more important than the safety boundary.

---

## 8. After the event

- Restore clean VM snapshots; do not leave the vulnerable server running.
- Remove the lab-only JNDI trust flag from any leftover launch scripts.
- Keep the marshalsec jar and payload in the society's internal demo archive,
  clearly labeled “isolated lab only.”
- If the kit is shared, include this document and the README warning.
- Thank the volunteers; file the one-page retro.
